"""Formatação e montagem de payload para a API do LinkedIn.

Nada aqui faz requisição: são funções puras, testadas contra o comportamento
que a API espera. É o trecho do projeto com maior chance de quebrar em
silêncio — um escape errado não estoura exceção, só publica um post com
`\\#` visível no meio do texto.
"""

from __future__ import annotations

import httpx
import pytest

from linkedin_growth.ferramentas.linkedin import (
    RESERVADOS_LITTLE,
    _url_do_post,
    escapar_little,
    para_little,
    payload_rest,
    payload_ugc,
)

AUTOR = "urn:li:person:abc123"


# ==============================================================================
# Escape
# ==============================================================================


@pytest.mark.parametrize("reservado", sorted(RESERVADOS_LITTLE))
def test_escapar_little_escapa_todo_caractere_reservado(reservado: str):
    """A doc do LinkedIn é explícita: todo reservado é escapado, sempre."""
    assert escapar_little(reservado) == "\\" + reservado


def test_escapar_little_nao_mexe_em_texto_comum():
    texto = "Construí um agente em Python e ele funcionou."

    assert escapar_little(texto) == texto


def test_escapar_little_preserva_acentuacao():
    assert escapar_little("programação, ação e manutenção") == "programação, ação e manutenção"


# ==============================================================================
# Hashtags
# ==============================================================================


def test_para_little_converte_hashtag_em_template_clicavel():
    assert para_little("#IA") == "{hashtag|\\#|IA}"


def test_para_little_converte_varias_hashtags_no_meio_do_texto():
    resultado = para_little("texto antes #IA e #RAG fim")

    assert resultado == "texto antes {hashtag|\\#|IA} e {hashtag|\\#|RAG} fim"


def test_para_little_aceita_hashtag_acentuada():
    """Os posts são em português: #programação precisa virar hashtag de verdade."""
    assert para_little("#programação") == "{hashtag|\\#|programação}"


def test_para_little_nao_trata_sustenido_colado_em_palavra_como_hashtag():
    """'C#' é nome de linguagem, não hashtag. Tem que sair escapado."""
    assert para_little("escrevo em C# às vezes") == "escrevo em C\\# às vezes"


def test_para_little_nao_trata_sustenido_duplo_como_hashtag():
    assert para_little("##IA") == "\\#\\#IA"


def test_para_little_corta_hashtag_no_underscore():
    """O LinkedIn não aceita underscore em hashtag, e ele é reservado.

    O comportamento correto é a hashtag terminar antes do underscore e o resto
    virar texto escapado.
    """
    assert para_little("#foo_bar") == "{hashtag|\\#|foo}\\_bar"


def test_para_little_escapa_reservados_ao_redor_da_hashtag():
    resultado = para_little("veja (isto) #IA [aqui]")

    assert resultado == "veja \\(isto\\) {hashtag|\\#|IA} \\[aqui\\]"


# ==============================================================================
# Payloads
# ==============================================================================


def test_payload_rest_usa_little_text_no_commentary():
    payload = payload_rest("post com #IA", AUTOR)

    assert payload["commentary"] == "post com {hashtag|\\#|IA}"
    assert payload["author"] == AUTOR
    assert payload["lifecycleState"] == "PUBLISHED"


def test_payload_ugc_usa_texto_puro_sem_escape():
    """O endpoint legado não entende little text: mandar escapado publicaria as barras."""
    payload = payload_ugc("post com #IA", AUTOR)

    conteudo = payload["specificContent"]["com.linkedin.ugc.ShareContent"]
    assert conteudo["shareCommentary"]["text"] == "post com #IA"


def test_payloads_respeitam_a_visibilidade_pedida():
    rest = payload_rest("texto", AUTOR, "CONNECTIONS")
    ugc = payload_ugc("texto", AUTOR, "CONNECTIONS")

    assert rest["visibility"] == "CONNECTIONS"
    assert ugc["visibility"]["com.linkedin.ugc.MemberNetworkVisibility"] == "CONNECTIONS"


# ==============================================================================
# URL do post publicado
# ==============================================================================


def test_url_do_post_usa_o_header_x_restli_id():
    resposta = httpx.Response(201, headers={"x-restli-id": "urn:li:share:7000"})

    assert _url_do_post(resposta) == "https://www.linkedin.com/feed/update/urn:li:share:7000/"


def test_url_do_post_cai_para_o_id_do_corpo_quando_nao_ha_header():
    resposta = httpx.Response(201, json={"id": "urn:li:share:8000"})

    assert _url_do_post(resposta) == "https://www.linkedin.com/feed/update/urn:li:share:8000/"


def test_url_do_post_sem_identificador_avisa_em_vez_de_montar_link_quebrado():
    resposta = httpx.Response(201, content=b"resposta que nao e json")

    resultado = _url_do_post(resposta)

    assert "publicado" in resultado
    assert "http" not in resultado
