"""Transforma o `Perfil` em texto para injetar no contexto dos agentes.

Decisão de projeto: **não usamos banco vetorial nem RAG aqui.** O perfil de uma
pessoa cabe em poucos milhares de tokens, e o embedder padrão do Agno exigiria
uma chave da OpenAI que este projeto não tem. Injetar o perfil inteiro via
`additional_context` é mais simples, mais barato de manter e mais confiável —
o agente nunca "não encontra" um dado que está ali.
"""

from __future__ import annotations

from functools import lru_cache

import yaml

from linkedin_growth.config import PERFIL_YAML, VOZ_MD
from linkedin_growth.perfil.esquema import Perfil

# Quanto da amostra de voz cabe no contexto sem inchar toda chamada.
MAX_CARACTERES_VOZ = 4000


class PerfilAusente(RuntimeError):
    """O perfil ainda não foi importado."""


def carregar_perfil() -> Perfil:
    """Lê `perfil/perfil.yaml`. Levanta erro com instrução se não existir."""
    if not PERFIL_YAML.exists():
        raise PerfilAusente(
            "perfil/perfil.yaml não existe.\n"
            "Coloque os CSVs do export do LinkedIn em perfil/linkedin_export/ "
            "e rode:\n"
            "    uv run linkedin importar"
        )
    dados = yaml.safe_load(PERFIL_YAML.read_text(encoding="utf-8")) or {}
    return Perfil.model_validate(dados)


def _bloco(titulo: str, linhas: list[str]) -> list[str]:
    """Só emite a seção se ela tiver conteúdo. Seção vazia é ruído no prompt."""
    if not linhas:
        return []
    return [f"### {titulo}", *linhas, ""]


def _periodo(inicio: str | None, fim: str | None) -> str:
    if not inicio and not fim:
        return ""
    return f" ({inicio or '?'} — {fim or 'atual'})"


def renderizar(perfil: Perfil) -> str:
    """Perfil -> markdown compacto para o `additional_context` dos agentes."""
    partes: list[str] = [
        "## DADOS REAIS DO USUÁRIO",
        "",
        "Tudo abaixo é verdade verificável. Use só isto como base factual.",
        "Se algo que você precisa não está aqui, pergunte — não invente.",
        "",
    ]

    identidade = []
    if perfil.nome:
        identidade.append(f"- Nome: {perfil.nome}")
    if perfil.headline:
        identidade.append(f"- Headline atual: {perfil.headline}")
    if perfil.setor:
        identidade.append(f"- Setor: {perfil.setor}")
    if perfil.localizacao:
        identidade.append(f"- Localização: {perfil.localizacao}")
    for site in perfil.sites:
        identidade.append(f"- Site: {site}")
    partes += _bloco("Identidade", identidade)

    if perfil.sobre:
        partes += _bloco("Seção 'Sobre' atual", [perfil.sobre])

    partes += _bloco("Objetivo de carreira", [perfil.objetivo])

    if perfil.temas_de_interesse:
        partes += _bloco(
            "Temas de interesse", [", ".join(perfil.temas_de_interesse)]
        )

    experiencias = []
    for exp in perfil.experiencias:
        cabecalho = f"- **{exp.cargo or 'Cargo não informado'}**"
        if exp.empresa:
            cabecalho += f" — {exp.empresa}"
        cabecalho += _periodo(exp.inicio, exp.fim)
        experiencias.append(cabecalho)
        if exp.descricao:
            experiencias.append(f"  {exp.descricao}")
    partes += _bloco("Experiência profissional", experiencias)

    formacoes = []
    for form in perfil.formacoes:
        linha = f"- {form.grau or 'Formação'}"
        if form.curso:
            linha += f" em {form.curso}"
        if form.instituicao:
            linha += f" — {form.instituicao}"
        linha += _periodo(form.inicio, form.fim)
        formacoes.append(linha)
    partes += _bloco("Formação", formacoes)

    certificacoes = [
        f"- {c.nome or 'Certificação'}"
        + (f" — {c.emissor}" if c.emissor else "")
        + (f" ({c.url})" if c.url else "")
        for c in perfil.certificacoes
    ]
    partes += _bloco("Certificações", certificacoes)

    projetos = []
    for proj in perfil.projetos:
        projetos.append(f"- **{proj.titulo or 'Projeto'}**" + (f" — {proj.url}" if proj.url else ""))
        if proj.descricao:
            projetos.append(f"  {proj.descricao}")
    partes += _bloco("Projetos", projetos)

    if perfil.skills:
        partes += _bloco("Skills declaradas", [", ".join(perfil.skills)])

    idiomas = [
        f"- {i.nome}" + (f" ({i.proficiencia})" if i.proficiencia else "")
        for i in perfil.idiomas
        if i.nome
    ]
    partes += _bloco("Idiomas", idiomas)

    return "\n".join(partes).strip()


def amostra_de_voz() -> str:
    """Trecho de `perfil/voz.md` para o agente imitar o tom do usuário."""
    if not VOZ_MD.exists():
        return ""
    texto = VOZ_MD.read_text(encoding="utf-8")
    if len(texto) > MAX_CARACTERES_VOZ:
        texto = texto[:MAX_CARACTERES_VOZ] + "\n\n[...amostra truncada]"
    return (
        "\n\n## COMO O USUÁRIO ESCREVE\n\n"
        "Posts que ele já publicou. Imite o ritmo e o vocabulário, não o assunto.\n"
        "Se estiver vazio, use um tom direto e sem jargão de marketing.\n\n"
        + texto
    )


SEM_PERFIL = """## DADOS REAIS DO USUÁRIO

O perfil ainda não foi importado, então você não sabe nada de concreto sobre
este usuário.

Não invente nada. Se a tarefa depender de dados do perfil, responda dizendo que
é preciso rodar primeiro:

    uv run linkedin importar

depois de colocar os CSVs do export do LinkedIn em `perfil/linkedin_export/`.
"""


@lru_cache(maxsize=1)
def contexto_do_perfil() -> str:
    """Contexto completo, montado uma vez por processo.

    Cacheado porque todo agente pede o mesmo texto: montar sete vezes o mesmo
    markdown seria desperdício, e o conteúdo não muda durante uma execução.

    Se o perfil ainda não foi importado, devolve um bloco que instrui o agente
    a pedir a importação — em vez de estourar. Assim o chat e o servidor sobem
    mesmo antes do primeiro `importar`.
    """
    try:
        return renderizar(carregar_perfil()) + amostra_de_voz()
    except (PerfilAusente, ValueError):
        return SEM_PERFIL
