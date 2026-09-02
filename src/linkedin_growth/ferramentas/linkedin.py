"""Publicação no LinkedIn pela API oficial.

Só o caminho sancionado: OAuth + produto `Share on LinkedIn` (escopo
`w_member_social`), publicando no seu próprio perfil, com o seu consentimento.
Nada de scraping, cookie `li_at` ou automação de navegador — isso é proibido
pelos Termos de Uso e derruba conta.

Duas sutilezas da API que este módulo resolve:

1. **Dois endpoints.** `/rest/posts` é o atual, mas a documentação nunca afirma
   que um app apenas com `Share on LinkedIn` pode chamá-lo. `/v2/ugcPosts` é o
   legado e é o que a própria página self-serve documenta. Tentamos o primeiro
   e caímos para o segundo em 403.

2. **`commentary` não é texto puro.** Ele usa o "little text format", em que
   quinze caracteres são reservados e precisam de contrabarra — inclusive
   parênteses, que aparecem o tempo todo em texto escrito por IA. Sem escapar,
   o post falha ou sai deformado. `/v2/ugcPosts` usa texto puro, sem escape.
"""

from __future__ import annotations

import json
import re
from typing import Any

import httpx
from agno.tools import tool

from linkedin_growth.config import (
    LINKEDIN_VERSION,
    ConfiguracaoAusente,
    exigir_linkedin,
)

URL_USERINFO = "https://api.linkedin.com/v2/userinfo"
URL_POSTS = "https://api.linkedin.com/rest/posts"
URL_UGC = "https://api.linkedin.com/v2/ugcPosts"

TIMEOUT = httpx.Timeout(30.0)

# Caracteres reservados do "little text format". A documentação é explícita:
# "All reserved characters need to be escaped with a backslash, even if those
# characters are not used in one of the supported elements or templates."
RESERVADOS_LITTLE = set(r"\|{}@[]()<>#*_~")

# Hashtag: '#' seguido de letras/números. Sem underscore — o LinkedIn não o
# aceita em hashtag, e ele é caractere reservado do formato.
_HASHTAG = re.compile(r"(?<![\w#])#([0-9A-Za-zÀ-ÖØ-öø-ÿ]+)")


# ==============================================================================
# Formatação do texto
# ==============================================================================


def escapar_little(texto: str) -> str:
    """Escapa todo caractere reservado do little text format."""
    return "".join("\\" + c if c in RESERVADOS_LITTLE else c for c in texto)


def para_little(texto: str) -> str:
    """Converte texto comum para little text format, preservando hashtags.

    As hashtags viram o template `{hashtag|\\#|valor}`, que é o que faz o
    LinkedIn renderizar um link clicável. Todo o resto é escapado.
    """
    partes: list[str] = []
    ultimo = 0
    for achado in _HASHTAG.finditer(texto):
        partes.append(escapar_little(texto[ultimo : achado.start()]))
        partes.append("{hashtag|\\#|" + achado.group(1) + "}")
        ultimo = achado.end()
    partes.append(escapar_little(texto[ultimo:]))
    return "".join(partes)


# ==============================================================================
# Cliente HTTP
# ==============================================================================


def _cabecalhos(*, versionado: bool) -> dict[str, str]:
    cabecalhos = {
        "Authorization": f"Bearer {exigir_linkedin()}",
        "X-Restli-Protocol-Version": "2.0.0",
        "Content-Type": "application/json",
    }
    if versionado:
        cabecalhos["LinkedIn-Version"] = LINKEDIN_VERSION
    return cabecalhos


def perfil_do_token() -> dict[str, Any]:
    """Identidade do dono do token, via endpoint OIDC `userinfo`.

    É o único jeito self-serve de saber quem é o usuário. Note que `sub` é
    específico do seu app: o mesmo membro tem `sub` diferente em outro app.
    """
    resposta = httpx.get(
        URL_USERINFO,
        headers={"Authorization": f"Bearer {exigir_linkedin()}"},
        timeout=TIMEOUT,
    )
    resposta.raise_for_status()
    return resposta.json()


def urn_do_membro() -> str:
    """URN do autor, no formato `urn:li:person:{sub}`."""
    dados = perfil_do_token()
    sub = dados.get("sub")
    if not sub:
        raise RuntimeError(
            "A resposta de /v2/userinfo não trouxe o campo 'sub'. "
            "Confira se o token tem os escopos 'openid' e 'profile'."
        )
    return f"urn:li:person:{sub}"


# ==============================================================================
# Montagem do payload
# ==============================================================================


def payload_rest(texto: str, autor: str, visibilidade: str = "PUBLIC") -> dict[str, Any]:
    """Corpo para `POST /rest/posts` (endpoint atual, little text format)."""
    return {
        "author": autor,
        "commentary": para_little(texto),
        "visibility": visibilidade,
        "distribution": {
            "feedDistribution": "MAIN_FEED",
            "targetEntities": [],
            "thirdPartyDistributionChannels": [],
        },
        "lifecycleState": "PUBLISHED",
        "isReshareDisabledByAuthor": False,
    }


def payload_ugc(texto: str, autor: str, visibilidade: str = "PUBLIC") -> dict[str, Any]:
    """Corpo para `POST /v2/ugcPosts` (endpoint legado, texto puro)."""
    return {
        "author": autor,
        "lifecycleState": "PUBLISHED",
        "specificContent": {
            "com.linkedin.ugc.ShareContent": {
                "shareCommentary": {"text": texto},
                "shareMediaCategory": "NONE",
            }
        },
        "visibility": {"com.linkedin.ugc.MemberNetworkVisibility": visibilidade},
    }


def previa(texto: str, visibilidade: str = "PUBLIC") -> str:
    """Mostra o que seria enviado, sem enviar. Usado pelo `--dry-run` da CLI."""
    try:
        autor = urn_do_membro()
    except (httpx.HTTPError, ConfiguracaoAusente, RuntimeError) as erro:
        autor = f"urn:li:person:<não foi possível obter: {erro}>"

    return (
        f"POST {URL_POSTS}\n"
        f"LinkedIn-Version: {LINKEDIN_VERSION}\n\n"
        + json.dumps(payload_rest(texto, autor, visibilidade), indent=2, ensure_ascii=False)
        + f"\n\n--- alternativa em caso de 403 ---\nPOST {URL_UGC}\n\n"
        + json.dumps(payload_ugc(texto, autor, visibilidade), indent=2, ensure_ascii=False)
    )


# ==============================================================================
# Publicação
# ==============================================================================


def _url_do_post(resposta: httpx.Response) -> str:
    """Monta o link do post a partir do URN devolvido no header `x-restli-id`."""
    urn = resposta.headers.get("x-restli-id", "")
    if not urn:
        try:
            urn = resposta.json().get("id", "")
        except (ValueError, json.JSONDecodeError):
            urn = ""
    if not urn:
        return "(publicado, mas o LinkedIn não devolveu o identificador)"
    return f"https://www.linkedin.com/feed/update/{urn}/"


def publicar(texto: str, visibilidade: str = "PUBLIC") -> dict[str, Any]:
    """Publica um post de texto no perfil do dono do token.

    Tenta o endpoint versionado e cai para o legado se o app não tiver acesso.
    """
    autor = urn_do_membro()

    resposta = httpx.post(
        URL_POSTS,
        headers=_cabecalhos(versionado=True),
        json=payload_rest(texto, autor, visibilidade),
        timeout=TIMEOUT,
    )

    if resposta.status_code == 403:
        # O app provavelmente só tem 'Share on LinkedIn'. O endpoint legado é o
        # que a página self-serve documenta e aceita texto puro.
        resposta = httpx.post(
            URL_UGC,
            headers=_cabecalhos(versionado=False),
            json=payload_ugc(texto, autor, visibilidade),
            timeout=TIMEOUT,
        )
        endpoint = "/v2/ugcPosts (legado)"
    else:
        endpoint = "/rest/posts"

    if resposta.status_code not in (200, 201):
        return {
            "ok": False,
            "endpoint": endpoint,
            "status": resposta.status_code,
            "erro": resposta.text[:1000],
        }

    return {
        "ok": True,
        "endpoint": endpoint,
        "status": resposta.status_code,
        "url": _url_do_post(resposta),
    }


# ==============================================================================
# Ferramentas expostas aos agentes
# ==============================================================================


@tool(requires_confirmation=True)
def publicar_post(texto: str, visibilidade: str = "PUBLIC") -> str:
    """Publica um post de texto no perfil do usuário no LinkedIn.

    Isto é irreversível e público: o post aparece no feed imediatamente. O
    usuário sempre aprova antes da execução.

    Args:
        texto: Conteúdo completo do post, já revisado e pronto. Quebras de
            linha simples são preservadas. Hashtags no formato '#palavra'
            viram links clicáveis.
        visibilidade: 'PUBLIC' (qualquer pessoa) ou 'CONNECTIONS' (só conexões).

    Returns:
        JSON com o resultado e a URL do post publicado, ou a descrição do erro.
    """
    try:
        resultado = publicar(texto, visibilidade)
    except ConfiguracaoAusente as erro:
        return json.dumps({"ok": False, "erro": str(erro)}, ensure_ascii=False)
    except httpx.HTTPError as erro:
        return json.dumps({"ok": False, "erro": f"Falha de rede: {erro}"}, ensure_ascii=False)
    except RuntimeError as erro:
        return json.dumps({"ok": False, "erro": str(erro)}, ensure_ascii=False)
    return json.dumps(resultado, indent=2, ensure_ascii=False)


@tool
def verificar_conexao_linkedin() -> str:
    """Confere se o token do LinkedIn está válido e de quem ele é.

    Use antes de tentar publicar, ou quando o usuário perguntar se a conexão
    com o LinkedIn está funcionando.

    Returns:
        JSON com o nome do dono do token, ou a descrição do problema.
    """
    try:
        dados = perfil_do_token()
    except ConfiguracaoAusente as erro:
        return json.dumps({"ok": False, "erro": str(erro)}, ensure_ascii=False)
    except httpx.HTTPStatusError as erro:
        if erro.response.status_code == 401:
            return json.dumps(
                {
                    "ok": False,
                    "erro": (
                        "Token inválido ou expirado. Tokens do LinkedIn duram 60 "
                        "dias. Gere outro em "
                        "https://www.linkedin.com/developers/tools/oauth/token-generator"
                    ),
                },
                ensure_ascii=False,
            )
        return json.dumps(
            {"ok": False, "status": erro.response.status_code, "erro": erro.response.text[:500]},
            ensure_ascii=False,
        )
    except httpx.HTTPError as erro:
        return json.dumps({"ok": False, "erro": f"Falha de rede: {erro}"}, ensure_ascii=False)

    return json.dumps(
        {
            "ok": True,
            "nome": dados.get("name"),
            "email": dados.get("email"),
            "urn": f"urn:li:person:{dados.get('sub')}",
        },
        indent=2,
        ensure_ascii=False,
    )
