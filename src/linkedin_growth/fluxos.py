"""Fluxos determinísticos de produção.

Quando a ordem dos passos é conhecida de antemão, um `Workflow` é melhor que um
`Team`: ele não gasta tokens decidindo quem faz o quê, e o resultado é o mesmo
toda vez.

Nota: a `agent_ui` deste repositório só conhece Agents e Teams — Workflows não
aparecem no chat. Eles rodam pela CLI (`linkedin post`, `linkedin calendario`).
"""

from __future__ import annotations

import re
import time
from datetime import date
from pathlib import Path

from agno.workflow import Step, StepInput, StepOutput, Workflow

from linkedin_growth.agentes import editor, pesquisador, planejador, redator
from linkedin_growth.config import POSTS_DIR, db

ID_POST = "fluxo-post"
ID_SEMANA = "fluxo-semana"

# Janela para considerar um arquivo "escrito por esta execução".
SEGUNDOS_RECENTE = 300


def _slug(texto: str, limite: int = 5) -> str:
    """'Por que meu RAG piorou' -> 'por-que-meu-rag-piorou'."""
    sem_acento = (
        texto.lower()
        .replace("ã", "a").replace("á", "a").replace("â", "a").replace("à", "a")
        .replace("é", "e").replace("ê", "e")
        .replace("í", "i")
        .replace("ó", "o").replace("ô", "o").replace("õ", "o")
        .replace("ú", "u").replace("ü", "u")
        .replace("ç", "c")
    )
    palavras = re.findall(r"[a-z0-9]+", sem_acento)[:limite]
    return "-".join(palavras) or "post"


def _mais_recente(pasta: Path) -> Path | None:
    arquivos = [p for p in pasta.glob("*.md") if p.is_file()]
    if not arquivos:
        return None
    return max(arquivos, key=lambda p: p.stat().st_mtime)


def registrar_post(step_input: StepInput) -> StepOutput:
    """Garante que o post virou arquivo e informa o caminho.

    O Editor normalmente salva sozinho, pela ferramenta `salvar_artefato`. Este
    passo confere: se nada foi gravado nos últimos minutos, ele mesmo grava. Um
    fluxo que roda até o fim e não deixa arquivo é pior que um que falha.
    """
    conteudo = step_input.previous_step_content or ""
    tema = step_input.get_input_as_string() or "post"

    POSTS_DIR.mkdir(parents=True, exist_ok=True)
    recente = _mais_recente(POSTS_DIR)

    if recente and (time.time() - recente.stat().st_mtime) < SEGUNDOS_RECENTE:
        caminho = recente
    else:
        caminho = POSTS_DIR / f"{date.today().isoformat()}-{_slug(tema)}.md"
        caminho.write_text(str(conteudo), encoding="utf-8")

    return StepOutput(
        content=f"{conteudo}\n\n---\n\nArquivo: {caminho}",
        step_name="registrar_post",
    )


def fluxo_post() -> Workflow:
    """Pesquisa -> escreve (pt + en) -> edita -> grava o arquivo."""
    return Workflow(
        id=ID_POST,
        name="Produção de Post",
        description="Pesquisa o tema, escreve em português e inglês, revisa e salva.",
        db=db(),
        steps=[
            Step(name="pesquisa", agent=pesquisador.construir()),
            Step(name="redacao", agent=redator.construir()),
            Step(name="edicao", agent=editor.construir()),
            Step(name="registro", executor=registrar_post),
        ],
    )


def fluxo_semana() -> Workflow:
    """Pesquisa a semana -> monta o calendário editorial."""
    return Workflow(
        id=ID_SEMANA,
        name="Planejamento Semanal",
        description="Levanta as pautas da semana e monta o calendário editorial.",
        db=db(),
        steps=[
            Step(name="pesquisa", agent=pesquisador.construir()),
            Step(name="calendario", agent=planejador.construir()),
        ],
    )


def todos() -> list[Workflow]:
    return [fluxo_post(), fluxo_semana()]
