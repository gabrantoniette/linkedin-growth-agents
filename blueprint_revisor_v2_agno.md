# Blueprint do Revisor — v2 (sintaxe Agno)

`agent_code_revisor` · substitui a v1 (esboço de orquestração genérico)

---

## 1. O que mudou

A v1 descrevia o padrão em abstrato: orchestrator–workers com fan-out paralelo, mais um evaluator–optimizer no fim. A v2 traduz isso para primitivas reais do Agno — e no caminho corrige uma decisão registrada em `decisoes-arquitetura.md`:

> **O fan-out não deve ser um `Team(mode=TeamMode.broadcast)`. Vira `Workflow` + `Parallel`.**

Justificativa na seção 3.

## 2. Mapeamento: padrão → primitiva Agno

| Papel na v1 | Primitiva Agno |
|---|---|
| Orchestrator | `Workflow` — sequência determinística de steps |
| Fan-out das 5 lentes | `Parallel(...)` dentro do workflow |
| Workers (revisores) | `Agent` com `output_schema` Pydantic |
| Verifier (evaluator) | `Step` com agente verificador dentro de um `Loop` |
| Gate condicional (rodar `contract-reviewer` só quando o diff toca schema) | `Condition` |
| Relatório final | `Step(executor=...)` — Python puro, sem LLM |
| Coleta de diff/contexto | `Step(executor=...)` — Python puro, sem LLM |

Note que só 6 dos 8 estágios gastam token. Coleta e relatório são determinísticos e devem continuar assim.

## 3. Por que `Workflow` + `Parallel` e não `Team`

`Team` sempre instancia um **leader**, que faz uma chamada de modelo própria para decidir a delegação e outra para sintetizar as respostas dos membros. Para um revisor de código isso é ruim em três frentes:

1. **A síntese destrói o que importa.** O valor de um achado está no par (arquivo, linha) mais a evidência literal. Um leader que resume cinco relatórios em prosa perde ancoragem — é exatamente o modo de falha que o verifier existe para combater.
2. **Não há decisão a tomar.** O conjunto de lentes é fixo em tempo de design. Delegação dinâmica só faz sentido quando o roteamento é incerto.
3. **Custo de coordenação.** Duas chamadas extras por review, com o diff inteiro no contexto do leader.

`Parallel` dá fan-out determinístico, zero token de coordenação, e acesso nominal a cada saída:

```python
security = step_input.get_step_content("security")
```

**Quando `Team` volta à mesa:** se mais adiante você quiser um triador que escolhe as lentes por tipo de PR, `TeamMode.route` resolve. Mas `Router`/`Condition` dentro do workflow resolve o mesmo sem pagar o leader — comece por aí.

## 4. Contratos de dados

O campo que sustenta a arquitetura inteira é `evidence`: o trecho **literal** que o revisor alega ter visto. É contra ele que o verifier trabalha. Sem esse campo, verificar vira uma segunda opinião, não uma checagem.

```python
# contracts.py
from typing import Literal
from pydantic import BaseModel, Field

Severity = Literal["blocker", "major", "minor", "nit"]
Lens = Literal["security", "correctness", "performance", "contract", "coverage"]


class Finding(BaseModel):
    id: str = Field(description="slug estável: <lente>-<arquivo>-<n>")
    lens: Lens
    file: str
    line_start: int
    line_end: int
    severity: Severity
    title: str = Field(description="uma linha, imperativa")
    rationale: str
    evidence: str = Field(
        description="trecho LITERAL do diff ou do arquivo que sustenta o achado. "
                    "Copie, não parafraseie. Se não conseguir copiar, não reporte."
    )
    suggested_fix: str | None = None


class ReviewOutput(BaseModel):
    findings: list[Finding]


class Verdict(BaseModel):
    finding_id: str
    status: Literal["confirmed", "rejected", "needs_context"]
    reason: str


class VerificationOutput(BaseModel):
    verdicts: list[Verdict]
```

## 5. Ferramentas de repositório

Leitura apenas. O revisor nunca escreve.

```python
# tools.py
import subprocess
from pathlib import Path
from agno.tools import tool

REPO = Path("/caminho/halcyon-goods-product-control")


@tool
def get_diff(base: str = "origin/main") -> str:
    """Diff unificado do HEAD contra a base, com 5 linhas de contexto."""
    return subprocess.run(
        ["git", "diff", f"{base}...HEAD", "-U5"],
        cwd=REPO, capture_output=True, text=True, check=True,
    ).stdout


@tool
def read_file_range(path: str, start: int = 1, end: int = 400) -> str:
    """Lê um intervalo de linhas de um arquivo do repo, numerado."""
    lines = (REPO / path).read_text().splitlines()
    return "\n".join(f"{i}: {l}" for i, l in enumerate(lines[start - 1:end], start))


@tool
def grep_repo(pattern: str, glob: str = "*.py") -> str:
    """Busca literal no repo. Use para confirmar se algo existe em outro lugar."""
    return subprocess.run(
        ["rg", "-n", "--glob", glob, pattern],
        cwd=REPO, capture_output=True, text=True,
    ).stdout[:20_000]
```

`read_file_range` e `grep_repo` importam mais para o verifier que para os revisores — é como ele confere a `evidence` contra o código real em vez de confiar na alegação.

## 6. Agentes

```python
# agents.py
from agno.agent import Agent
from agno.models.anthropic import Claude
from contracts import ReviewOutput, VerificationOutput
from tools import read_file_range, grep_repo

CHECKLIST = open("skills/review-checklist/SKILL.md").read()  # instruções compartilhadas


def reviewer(name: str, role: str, focus: str) -> Agent:
    return Agent(
        name=name,
        role=role,
        model=Claude(id="claude-sonnet-4-6"),
        tools=[read_file_range, grep_repo],
        instructions=[CHECKLIST, focus],
        output_schema=ReviewOutput,
    )


security_reviewer = reviewer(
    "security-reviewer",
    "Segurança de aplicação",
    "Procure: segredos commitados, authz ausente ou incorreta em rotas, "
    "injeção (SQL, comando, template), desserialização insegura, CORS permissivo. "
    "Ignore estilo. Se não houver achado, retorne lista vazia.",
)

correctness_reviewer = reviewer(
    "correctness-reviewer",
    "Corretude e edge cases",
    "Procure: lógica invertida, off-by-one, nulos não tratados, migrations "
    "irreversíveis ou sem backfill, transações faltando.",
)

performance_reviewer = reviewer(
    "performance-reviewer",
    "Performance",
    "Procure: N+1 em ORM, I/O bloqueante em path async, queries sem índice, "
    "carregamento de coleção inteira em memória.",
)

contract_reviewer = reviewer(
    "contract-reviewer",
    "Drift de contrato Pydantic ↔ Zod",
    "Compare os schemas Pydantic do backend com os Zod correspondentes no front. "
    "Reporte campo divergente, opcionalidade divergente e enum dessincronizado.",
)

coverage_reviewer = reviewer(
    "coverage-reviewer",
    "Cobertura de testes",
    "Para cada comportamento novo ou alterado no diff, aponte se falta teste. "
    "Não peça teste para refactor puro.",
)

verifier = Agent(
    name="verifier",
    role="Auditor de achados",
    model=Claude(id="claude-sonnet-4-6"),
    tools=[read_file_range, grep_repo],
    instructions=[
        "Você recebe achados de outros revisores. Para cada um, leia o código real "
        "citado e decida: o trecho em `evidence` existe literalmente naquele arquivo "
        "e naquelas linhas? A conclusão se sustenta?",
        "confirmed = evidência existe e a conclusão se sustenta.",
        "rejected = evidência não existe, está em outro lugar, ou a conclusão não segue.",
        "needs_context = evidência existe mas depende de código fora do diff.",
        "Rejeitar é o resultado esperado com frequência. Não confirme por educação.",
    ],
    output_schema=VerificationOutput,
)
```

Uma nota sobre o verifier: usar o mesmo modelo dos revisores tende a produzir concordância. Duas mitigações que valem testar — trocar o modelo do verifier (Opus, ou outro provedor) e exigir que ele cite a linha lida, não só o veredito.

## 7. Workflow

```python
# workflow.py
from agno.workflow import Workflow, Step, Parallel, Loop, Condition
from agno.workflow.types import StepInput, StepOutput

import agents
from tools import get_diff


def collect_context(step_input: StepInput) -> StepOutput:
    return StepOutput(content=get_diff(base=str(step_input.input or "origin/main")))


def touches_schemas(step_input: StepInput) -> bool:
    diff = step_input.get_step_content("contexto") or ""
    return any(m in diff for m in ("schemas/", ".zod.ts", "BaseModel"))


def all_adjudicated(outputs: list[StepOutput]) -> bool:
    last = outputs[-1].content
    return all(v.status != "needs_context" for v in last.verdicts)


def build_report(step_input: StepInput) -> StepOutput:
    # junta achados das 5 lentes, cruza com os veredictos, ordena por severidade,
    # descarta rejected, formata markdown para comentário de PR.
    ...


review_workflow = Workflow(
    name="agent_code_revisor",
    steps=[
        Step(name="contexto", executor=collect_context),
        Parallel(
            Step(name="security", agent=agents.security_reviewer),
            Step(name="correctness", agent=agents.correctness_reviewer),
            Step(name="performance", agent=agents.performance_reviewer),
            Step(name="coverage", agent=agents.coverage_reviewer),
            Condition(
                name="contract_gate",
                evaluator=touches_schemas,
                steps=[Step(name="contract", agent=agents.contract_reviewer)],
            ),
            name="lentes",
        ),
        Loop(
            name="verificacao",
            steps=[Step(name="verifier", agent=agents.verifier)],
            end_condition=all_adjudicated,
            max_iterations=2,
        ),
        Step(name="relatorio", executor=build_report),
    ],
)
```

Execute com `await review_workflow.arun(...)`, não `run()` — as cinco lentes são I/O-bound e o ganho do `Parallel` só aparece no caminho async.

## 8. Persistência

Agno v2 é stateless por design: sessão, histórico e memória vão para o banco. Para a v1 do revisor isso é dispensável (cada review é uma execução isolada). Passa a importar quando você quiser: retomar um review interrompido, comparar reviews do mesmo PR entre pushes, ou plugar no AgentOS para tracing. Aí é `Workflow(db=PostgresDb(...))`.

## 9. Roadmap de construção

Cada passo é testável sozinho antes do próximo.

1. `contracts.py` + `tools.py` — sem LLM nenhum. Rode `get_diff` num PR real e confira a saída.
2. Um revisor só (`security`) rodando direto, sem workflow. Objetivo: validar que `output_schema` volta `ReviewOutput` de verdade com o modelo escolhido.
3. Workflow de dois steps: contexto → security. Valida a passagem de `StepInput`.
4. `Parallel` com as cinco lentes. Meça latência e custo aqui — é o ponto de decisão sobre chunking.
5. `Loop` + verifier. Meça a taxa de rejeição; se ficar perto de zero, o verifier não está funcionando.
6. `build_report` e integração com comentário de PR.
7. `skills/review-checklist/SKILL.md` — extrair as instruções compartilhadas que hoje estão hardcoded em `reviewer()`.
8. Gate no CI.

## 10. A confirmar contra a sua versão do Agno

A API mudou bastante entre v1 e v2. Pin a versão no `pyproject.toml` antes de escrever muito código, e confira:

- assinatura de `Loop(end_condition=...)` — o que exatamente o callable recebe
- `Condition(evaluator=...)` vs. `Condition(condition=...)`
- import do decorator `@tool` (`agno.tools` vs. `agno`)
- `agno.workflow.types` vs. `agno.workflow` para `StepInput`/`StepOutput`
- id do modelo aceito por `Claude(...)`

## 11. Riscos abertos

- **Custo.** Cinco agentes × diff grande, cada um com tools que podem puxar arquivos inteiros. Mitigação: mandar só o diff mais os arquivos tocados; se o diff passar de ~800 linhas, quebrar por arquivo e rodar o workflow por chunk.
- **Concordância do verifier.** Ver seção 6.
- **Falso negativo silencioso.** `output_schema` garante forma, não cobertura. Vale montar um conjunto fixo de PRs com bugs conhecidos e medir recall a cada mudança de prompt — sem isso você não sabe se uma alteração no checklist melhorou ou piorou.
- **Acoplamento ao repo.** `contract-reviewer` é específico do `halcyon-goods-product-control`. Manter isolado atrás do `Condition` para não vazar para os outros.
