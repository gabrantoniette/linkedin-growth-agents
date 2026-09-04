"""Fluxos determinísticos de produção.

Quando a ordem dos passos é conhecida de antemão, um `Workflow` é melhor que um
`Team`: ele não gasta tokens decidindo quem faz o quê, e o resultado é o mesmo
toda vez.

Nota: a `agent_ui` deste repositório só conhece Agents e Teams — Workflows não
aparecem no chat. Eles rodam pela CLI (`linkedin post`, `linkedin calendario`).

**Por que os passos são executores e não `Step(agent=...)`:** o Agno monta a
mensagem de um passo de agente com `_prepare_message`, que *substitui* a
entrada do workflow pelo conteúdo do passo anterior. Ou seja, do segundo passo
em diante o pedido original desaparece. Na prática isso significava que
`linkedin post --tema "X"` produzia um post sobre outro assunto (o redator via
só a lista de notícias que o pesquisador tinha levantado) e que
`linkedin calendario --semanas 4` era ignorado — o planejador nunca ficava
sabendo quantas semanas planejar. Compondo a mensagem à mão, cada passo recebe
as duas coisas: o pedido e o trabalho de quem veio antes.
"""

from __future__ import annotations

import re
import time
from collections.abc import Callable
from datetime import date
from pathlib import Path

from agno.agent import Agent
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


def passo(
    nome: str,
    construir: Callable[[], Agent],
    mensagem: Callable[[str, str], str],
) -> Step:
    """Um passo de agente que decide explicitamente o que o agente vai ler.

    `mensagem` recebe o pedido original do usuário e a saída do passo anterior,
    e devolve o texto que o agente vê. É o ponto em que o fluxo garante que o
    tema pedido não se perde no meio da esteira.
    """

    def executar(entrada: StepInput) -> StepOutput:
        agente = construir()
        saida = agente.run(
            mensagem(
                entrada.get_input_as_string() or "",
                entrada.previous_step_content or "",
            )
        )
        return StepOutput(content=str(saida.content or ""), step_name=nome)

    return Step(name=nome, executor=executar)


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
            passo(
                "pesquisa",
                pesquisador.construir,
                lambda tema, _: (
                    f"TEMA JÁ DECIDIDO: {tema}\n\n"
                    "Levante material de apoio para um post sobre ESTE tema. "
                    "Não faça a curadoria da semana e não sugira outras pautas: "
                    "a escolha já foi feita pelo usuário."
                ),
            ),
            passo(
                "redacao",
                redator.construir,
                lambda tema, pesquisa: (
                    f"TEMA DO POST: {tema}\n\n"
                    "Escreva o post sobre esse tema, e só sobre ele.\n\n"
                    f"Material que a pesquisa levantou:\n{pesquisa}"
                ),
            ),
            passo(
                "edicao",
                editor.construir,
                lambda tema, rascunho: (
                    f"TEMA DO POST: {tema}\n\n"
                    "Revise o rascunho abaixo. Se ele tiver escapado do tema, "
                    "isso é um problema de conteúdo: aponte e corrija.\n\n"
                    f"Rascunho:\n{rascunho}"
                ),
            ),
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
            passo("pesquisa", pesquisador.construir, lambda pedido, _: pedido),
            passo(
                "calendario",
                planejador.construir,
                lambda pedido, pautas: (
                    f"PEDIDO DO USUÁRIO: {pedido}\n\n"
                    "Monte o calendário exatamente com o número de semanas "
                    "pedido acima.\n\n"
                    f"Pautas que a pesquisa levantou:\n{pautas}"
                ),
            ),
        ],
    )


def todos() -> list[Workflow]:
    return [fluxo_post(), fluxo_semana()]
