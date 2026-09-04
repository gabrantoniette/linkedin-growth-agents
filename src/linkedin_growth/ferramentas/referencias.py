"""Ferramentas de leitura: consulta a material de referência em `referencias/`.

Separado de `artefatos.py` de propósito. `conteudo/` é o que o sistema
PRODUZ; `referencias/` é material de apoio que o sistema só CONSULTA — fórmulas
de gancho, heurísticas do algoritmo, listas de vocabulário a evitar. Por isso
não existe `salvar_referencia`: um agente não deveria poder reescrever a
própria base de consulta.

O objetivo é reproduzir, dentro do Agno, a divulgação progressiva das Claude
Skills: o conteúdo só entra no contexto quando o agente decide chamar a
ferramenta, em vez de ficar sempre presente nas instructions.
"""

from __future__ import annotations

from pathlib import Path

from agno.tools import tool

from linkedin_growth.config import REFERENCIAS_DIR


def _resolver(caminho_relativo: str) -> Path | None:
    """Resolve um caminho dentro de `referencias/`, ou None se tentar escapar."""
    alvo = (REFERENCIAS_DIR / caminho_relativo).resolve()
    raiz = REFERENCIAS_DIR.resolve()
    if raiz not in alvo.parents and alvo != raiz:
        return None
    return alvo


@tool
def ler_referencia(caminho_relativo: str) -> str:
    """Lê um arquivo de material de referência de dentro da pasta `referencias/`.

    Use quando precisar de fórmulas de gancho, heurísticas do algoritmo do
    LinkedIn, vocabulário a evitar ou fórmulas de headline — antes de escrever,
    não depois. Chame `listar_referencias` primeiro se não souber o nome exato
    do arquivo.

    Args:
        caminho_relativo: Caminho a partir de `referencias/`, com extensão.
            Exemplos: 'ganchos.md', 'algoritmo-linkedin.md'.

    Returns:
        O conteúdo do arquivo, ou a descrição do erro.
    """
    alvo = _resolver(caminho_relativo)
    if alvo is None:
        return f"ERRO: '{caminho_relativo}' sai da pasta referencias/."
    if not alvo.exists():
        return f"ERRO: referencias/{caminho_relativo} não existe."
    try:
        return alvo.read_text(encoding="utf-8")
    except OSError as erro:
        return f"ERRO ao ler: {erro}"


@tool
def listar_referencias() -> str:
    """Lista os arquivos de referência disponíveis em `referencias/`.

    Use para descobrir o que existe antes de pedir um arquivo específico com
    `ler_referencia`.

    Returns:
        Um caminho por linha, ou aviso de pasta vazia.
    """
    if not REFERENCIAS_DIR.exists():
        return "Nenhuma referência ainda."

    raiz = REFERENCIAS_DIR.resolve()
    encontrados = sorted(
        str(p.resolve().relative_to(raiz)).replace("\\", "/")
        for p in REFERENCIAS_DIR.rglob("*")
        if p.is_file()
    )
    return "\n".join(encontrados) if encontrados else "Nenhuma referência ainda."
