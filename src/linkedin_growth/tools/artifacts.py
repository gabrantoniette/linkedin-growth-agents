"""Ferramentas de arquivo: os agentes escrevem e leem dentro de `conteudo/`.

Tudo é confinado a `conteudo/`. Um agente não tem por que escrever em qualquer
lugar do disco, e uma checagem de caminho custa três linhas.

Convenção do projeto: ferramenta não levanta exceção — devolve o erro como
texto. Assim o agente lê a falha, entende e tenta outro caminho, em vez de
derrubar a execução inteira.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path

from agno.tools import tool

from linkedin_growth.config import CONTEUDO_DIR


def _resolver(caminho_relativo: str) -> Path | None:
    """Resolve um caminho dentro de `conteudo/`, ou None se tentar escapar."""
    alvo = (CONTEUDO_DIR / caminho_relativo).resolve()
    raiz = CONTEUDO_DIR.resolve()
    if raiz not in alvo.parents and alvo != raiz:
        return None
    return alvo


@tool
def salvar_artefato(caminho_relativo: str, conteudo: str) -> str:
    """Salva um arquivo de texto dentro da pasta `conteudo/` do projeto.

    Use ao final de uma tarefa para gravar o resultado — diagnóstico, estratégia,
    calendário, rascunho de post. Sobrescreve se o arquivo já existir.

    Args:
        caminho_relativo: Caminho a partir de `conteudo/`, com extensão.
            Exemplos: 'diagnostico.md', 'posts/2026-09-02-rag.md'.
        conteudo: Texto completo do arquivo, em markdown.

    Returns:
        Confirmação com o caminho gravado, ou a descrição do erro.
    """
    alvo = _resolver(caminho_relativo)
    if alvo is None:
        return f"ERRO: '{caminho_relativo}' sai da pasta conteudo/. Use um caminho relativo simples."
    try:
        alvo.parent.mkdir(parents=True, exist_ok=True)
        alvo.write_text(conteudo, encoding="utf-8")
        return f"Gravado em conteudo/{caminho_relativo} ({len(conteudo)} caracteres)."
    except OSError as erro:
        return f"ERRO ao gravar: {erro}"


@tool
def ler_artefato(caminho_relativo: str) -> str:
    """Lê um arquivo de texto de dentro da pasta `conteudo/`.

    Use para consultar algo que você ou outro agente já produziu — a estratégia
    antes de planejar o calendário, o calendário antes de escrever um post.

    Args:
        caminho_relativo: Caminho a partir de `conteudo/`.
            Exemplos: 'estrategia.md', 'calendario/2026-W36.md'.

    Returns:
        O conteúdo do arquivo, ou a descrição do erro.
    """
    alvo = _resolver(caminho_relativo)
    if alvo is None:
        return f"ERRO: '{caminho_relativo}' sai da pasta conteudo/."
    if not alvo.exists():
        return f"ERRO: conteudo/{caminho_relativo} não existe ainda."
    try:
        return alvo.read_text(encoding="utf-8")
    except OSError as erro:
        return f"ERRO ao ler: {erro}"


@tool
def listar_artefatos(subpasta: str = "") -> str:
    """Lista os arquivos já produzidos dentro de `conteudo/`.

    Use para descobrir o que já existe antes de criar algo do zero.

    Args:
        subpasta: Subpasta a listar. Vazio lista tudo, recursivamente.
            Exemplos: '', 'posts', 'calendario'.

    Returns:
        Um caminho por linha, ou aviso de pasta vazia.
    """
    base = _resolver(subpasta) if subpasta else CONTEUDO_DIR
    if base is None:
        return f"ERRO: '{subpasta}' sai da pasta conteudo/."
    if not base.exists():
        return "Nenhum arquivo ainda."

    raiz = CONTEUDO_DIR.resolve()
    encontrados = sorted(
        str(p.resolve().relative_to(raiz)).replace("\\", "/")
        for p in base.rglob("*")
        if p.is_file()
    )
    return "\n".join(encontrados) if encontrados else "Nenhum arquivo ainda."


@tool
def data_de_hoje() -> str:
    """Retorna a data de hoje em ISO (AAAA-MM-DD) e o número da semana.

    Use ao nomear arquivos de post ou de calendário, para não chutar a data.
    """
    hoje = date.today()
    ano, semana, _ = hoje.isocalendar()
    return f"data={hoje.isoformat()} semana_iso={ano}-W{semana:02d}"
