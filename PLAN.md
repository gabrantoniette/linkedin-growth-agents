# PLAN.md — `agent_code_revisor`

Entrega da §12 do `PROMPT.md`. Nenhuma linha de código do revisor foi escrita.

**Aviso antes de tudo:** ao sondar a CLI do impeccable rodei `npx impeccable install --help`. O subcomando `install` não trata `--help` — ele **executou a instalação**, em escopo de projeto: criou `.claude/skills/impeccable/` e mesclou hooks `PostToolUse` (matcher `Edit|Write`) e `Stop` em `.claude/settings.local.json`. Era um item da Fase 0, mas aconteceu sem a aprovação que a §11 exige. **Resolvido — ver §7.**

**Status:** o `blueprint_revisor_v2_agno.md` apareceu na raiz do repo depois da primeira versão deste plano. A Q1, que era a única pergunta bloqueante, está **fechada** — ver §5.

---

## 1. CLIs: o que o `--help` diz e onde a Fase 0 diverge

Versões observadas: `skills` **1.5.23**, `impeccable` **3.6.0**, node v26.8.1, npm 12.0.2.

### 1.1 `npx skills --help` (íntegra, sem os códigos de cor)

```
Usage: skills <command> [options]

Manage Skills:
  add <package>        Add a skill package (alias: a)
                       e.g. vercel-labs/agent-skills
                            https://github.com/vercel-labs/agent-skills
  use <package>@<skill>
                       Generate a prompt for using one skill without installing it
  remove [skills]      Remove installed skills
  list, ls             List installed skills
  find [query]         Search for skills interactively

Find Options:
  --owner <owner>        Search only repositories from a GitHub owner

Updates:
  update [skills...]   Update skills to latest versions (alias: upgrade)

Update Options:
  -g, --global           Update global skills only
  -p, --project          Update project skills only
  -y, --yes              Skip scope prompt (auto-detect: project if in a project, else global)

Project:
  experimental_install Restore skills from skills-lock.json
  init [name]          Initialize a skill (creates <name>/SKILL.md or ./SKILL.md)
  experimental_sync    Sync skills from node_modules into agent directories

Add Options:
  -g, --global           Install skill globally (user-level) instead of project-level
  -a, --agent <agents>   Specify agents to install to (use '*' for all agents)
  -s, --skill <skills>   Specify skill names to install (use '*' for all skills)
  -l, --list             List available skills in the repository without installing
  -y, --yes              Skip confirmation prompts
  --copy                 Copy files instead of symlinking to agent directories
  --metadata <json>      Attach valid JSON to the install telemetry event
  --subagent <names>     Install to Eve subagents (use 'root' for the root agent)
  --all                  Shorthand for --skill '*' --agent '*' -y
  --full-depth           Search all subdirectories even when a root SKILL.md exists

Use Options / Remove Options / Experimental Sync Options / List Options:
  (--skill, --agent, --global, --yes, --all, --json, --full-depth — nada novo de relevante)

  --help, -h        Show this help message
  --version, -v     Show version number

Discover more skills at https://skills.sh/
```

### 1.2 `npx impeccable --help` (íntegra)

```
Usage: impeccable <command> [options]

Commands:
  detect [file-or-dir-or-url...]   Scan for UI anti-patterns and design quality issues
  ignores                          Manage detector ignore rules, files, and values
  help                             List all available skills and commands
  install                          Install impeccable skills into your project or global harness
  link                             Symlink skills from a local checkout or submodule
  update                           Update skills to the latest version
  check                            Check if skill updates are available

Options:
  --help       Show this help message
  --version    Show version number

Compatibility:
  impeccable skills <command>       Legacy namespace; still supported.
```

`npx impeccable detect --help`, no que importa para a `tools.py`:

```
Options:
  --json              Output results as JSON
  --scope <name>      Only report rules in the given design domain (type, layout). Comma-separated.
  --no-config         Do not apply project config, detector ignores, inline ignore comments, or DESIGN.md
  --no-inline-ignores Do not honor in-file impeccable-disable* ignore comments
  --no-design-system  Do not load local DESIGN.md / .impeccable/design.json context
  --no-advisory       Suppress advisory findings entirely (e.g. em-dash overuse)

Advisory findings:
  Some rules are advisory: detected and listed in a separate section, but never counted as
  failures and never changing the exit code.

Detection modes:
  HTML files     Static HTML/CSS analysis (default, catches linked CSS)
  Non-HTML files Regex pattern matching (CSS, JSX, TSX, etc.)
  URLs           Puppeteer full browser rendering
```

### 1.3 Divergências em relação à Fase 0

| # | O documento diz | O que a CLI diz | Ação proposta |
|---|---|---|---|
| D1 | `npx skills add vercel-labs/skills --skill find-skills -a claude-code -y` | Confere. `vercel-labs/skills` existe e contém **exatamente 1** skill, `find-skills`. As flags `-s`/`-a`/`-y` são reais. | Rodar como está (mais `--copy`, ver D5). |
| D2 | `npx skills add neondatabase/agent-skills -a claude-code -y` | O repo tem **7** skills: `neon`, `neon-ai-gateway`, `neon-functions`, `neon-object-storage`, `neon-postgres`, `neon-postgres-branches`, `neon-postgres-egress-optimizer`. Sem `--skill`, instala as 7. | Instalar **3**: `neon`, `neon-postgres`, `neon-postgres-branches`. As outras 4 não têm uso aqui, e cada `SKILL.md` é instrução entrando no contexto (§10.7, §14). **Precisa da sua aprovação — Q4.** |
| D3 | `npx impeccable install`, depois `/impeccable init` gera `PRODUCT.md` | `install` existe, e a própria saída do instalador manda digitar `/impeccable init` — o comando está certo. Mas entre os 24 comandos instalados, `/init` é "Sets up a project for impeccable. Runs a multi-round discovery interview" e quem gera arquivo é `/document`: "Generate a **DESIGN.md** file". Nenhuma descrição menciona `PRODUCT.md`. | Manter o comando; **trocar o critério de aceite** de "gerou `PRODUCT.md`" para "gerou o artefato de contexto de design que o `/impeccable init` produzir (provavelmente `DESIGN.md` e/ou `.impeccable/`), e ele está commitado". |
| D4 | (não mencionado) | `install` **ignora `--help` e instala**. Já aconteceu. | Q5. |
| D5 | (não mencionado) | `skills add` faz **symlink** por padrão; `--copy` copia. Symlink no Windows exige Developer Mode ou admin, e symlink não é o que se commita. A §0 pede que as skills sejam commitadas e o time herde a mesma configuração. | Usar `--copy` nos dois `skills add`. |
| D6 | (não mencionado) | `skills` 1.5.23 gera `skills-lock.json`, com `experimental_install` para restaurar. | Commitar o `skills-lock.json`. É o que transforma "atualização de skill" em diff legível, como a §14 pede. |
| D7 | `impeccable detect --json <arquivo>` vira `Finding` | Em arquivos não-HTML — o caso de `apps/web`, que é `.tsx` — o modo é **regex pattern matching**, não análise estática. E achados *advisory* nunca mudam o exit code. | O parser lê **stdout JSON**, nunca o exit code. E a lente `design` fica com severidade teto `minor` para achados vindos do modo regex: não vale gastar `blocker` em heurística de regex. |

---

## 2. Agno: versão pinada e verificação de assinaturas

**Versão instalada e a pinar: `agno==3.0.0`** (exata, §10.4). Hoje o `pyproject.toml` traz `agno>=3.0.0` — um range, que é exatamente o que a §10.4 proíbe antes de escrever volume de código. Pinar junto: `anthropic==1.1.0`, `pydantic==2.13.4`, `sqlalchemy==2.0.52`.

Tudo abaixo veio de `inspect.signature` e da leitura do fonte em `.venv/Lib/site-packages/agno/`, não de memória.

### 2.1 `Loop(end_condition=...)` — o que exatamente o callable recebe

```python
Loop(
    steps: List[Step | Callable[[StepInput], StepOutput] | Steps | Loop | Parallel | Condition | Router | Workflow],
    name: Optional[str] = None,
    description: Optional[str] = None,
    max_iterations: int = 3,
    end_condition: Union[Callable[[List[StepOutput]], bool], str, None] = None,
    forward_iteration_output: bool = False,
    human_review: Optional[HumanReview] = None,
)
```

- O callable recebe **`List[StepOutput]`** — os outputs *daquela iteração*, não o histórico acumulado. Devolve `bool`.
- Pode ser **async**: `_aevaluate_end_condition` faz `if inspect.iscoroutinefunction(...)` e dá `await`.
- Também aceita **string CEL** (`CEL_AVAILABLE` está exportado em `agno.workflow`). Não vamos usar: um predicado Python é testável.
- Consequência de projeto: como só chegam os outputs da iteração corrente, o estado do loop de verificação (quais achados já foram julgados) tem que viajar dentro de `StepOutput.content`.

### 2.2 `Condition(evaluator=...)` vs `Condition(condition=...)`

**É `evaluator`.** Não existe parâmetro `condition`.

```python
Condition(
    steps: List[...],                      # primeiro posicional, obrigatório
    evaluator: Union[Callable[[StepInput], bool],
                     Callable[[StepInput], Awaitable[bool]],
                     bool, str] = True,
    else_steps: Optional[List[...]] = None,
    name=None, description=None, human_review=<factory>,
) -> None
```

- `evaluator` recebe **`StepInput`** e devolve `bool`; pode ser async.
- Se a função declarar um parâmetro `run_context`, o Agno o injeta (`_evaluator_has_run_context_param`).
- Aceita também `bool` literal e string CEL. Usaremos callable Python.

### 2.3 Import do decorator `@tool`

**`from agno.tools import tool`.** O módulo real é `agno.tools.decorator`; `agno.tools` reexporta. **`agno.tool` não existe** (`hasattr(agno, "tool") is False`).

Assinatura: `tool(*args, **kwargs) -> Function | Callable[[F], Function]` — funciona como `@tool` e como `@tool(...)`.

### 2.4 `agno.workflow.types` vs `agno.workflow` para `StepInput` / `StepOutput`

Os dois importam. O módulo canônico é **`agno.workflow.types`**; `agno.workflow` e `agno.workflow.step` reexportam, e todas as anotações internas apontam para `agno.workflow.types`. **Vamos importar de `agno.workflow.types`.**

Campos que importam:

- `StepInput`: `input`, `previous_step_content`, `previous_step_outputs`, `additional_data`, `images`, `videos`, `audio`, `files`, `workflow_session`.
  → o gate do `Condition` lê o diff de `previous_step_outputs` (saída do Step de contexto) ou de `additional_data`.
- `StepOutput`: `step_name`, `step_id`, `step_type`, `executor_type`, `executor_name`, `content`, `step_run_id`, `images`, `videos`, `audio`, `files`, `metrics`, `success`, `error`, `stop`, `is_paused`, `steps`, `requires_iteration_review_pause`.
  → `metrics` é de onde sai custo e latência para o critério de aceite da Fase 5.

Outras assinaturas confirmadas:

- **`Parallel(*args, name=None, description=None, human_review=None)`** — os steps entram como **varargs**, não como lista: `Parallel(a, b, c, name="lentes")`, não `Parallel([a, b, c])`.
- **`Step(name=None, agent=None, team=None, executor=None, workflow=None, step_id=None, description=None, max_retries=3, skip_on_failure=False, strict_input_validation=False, add_workflow_history=None, num_history_runs=3, human_review=None)`** — `executor` é o callable `StepInput -> StepOutput` dos steps determinísticos.
- **`Workflow(*, id, name, description, db, steps, ...)`** — só keyword. `Workflow.arun(input=..., additional_data=..., ...) -> WorkflowRunOutput`.

### 2.5 `Knowledge` + `PgVector`: import e assinatura

```python
from agno.knowledge.knowledge import Knowledge   # agno.knowledge.Knowledge também reexporta

Knowledge(
    name=None, description=None,
    vector_db: Optional[Any] = None,
    contents_db: Optional[BaseDb | AsyncBaseDb] = None,
    max_results: int = 10,
    readers: Optional[Dict[str, Reader]] = None,
    content_sources: Optional[List[BaseStorageConfig]] = None,
    isolate_vector_search: bool = False,
) -> None
# tem caminho async: ainsert, ainsert_many, asearch, aretrieve, aget_tools
```

```python
from agno.vectordb.pgvector import PgVector

PgVector(
    table_name: str,
    schema: str = "ai",
    name=None, description=None, id=None,
    db_url: Optional[str] = None,
    db_engine: Optional[Engine] = None,
    embedder: Optional[Embedder] = None,
    search_type: SearchType = SearchType.vector,
    vector_index: Ivfflat | HNSW = HNSW(),
    distance: Distance = Distance.cosine,
    prefix_match: bool = False,
    vector_score_weight: float = 0.5,
    content_language: str = "english",
    schema_version: int = 1,
    reranker: Optional[Reranker] = None,
    create_schema: bool = True,
    similarity_threshold: Optional[float] = None,
)
```

Três coisas que a Fase 3 precisa resolver e que não estavam no documento:

1. **`pgvector` e `psycopg` não estão instalados.** O import de `PgVector` levanta `ImportError` na hora (`"pgvector" not installed`). Entram no `pyproject.toml` pinados.
2. **`embedder=None` cai em `OpenAIEmbedder()`** (`vectordb/pgvector/pgvector.py`: `if embedder is None: from agno.knowledge.embedder.openai import OpenAIEmbedder`). O `.env` deste repo tem **só `ANTHROPIC_API_KEY`**, e a Anthropic não tem endpoint de embeddings. É uma decisão real → **Q2**.
3. **A tool de RAG do `Agent` chama-se `search_knowledge_base`, não `search_knowledge`.** (`agno/agent/_default_tools.py`: `Function.from_callable(..., name="search_knowledge_base")`.) O texto da §3.4 vai literal para as `instructions` de cada lente e cita `search_knowledge` — um nome que o modelo não vai achar na lista de tools. **Corrigir para `search_knowledge_base` ao escrever as instructions.**

### 2.6 Id de modelo aceito por `Claude(...)`

`Claude.__init__` recebe `id: str` e **não valida contra lista** — quem rejeita id inválido é a API. E os ids da §1 **não são ids de API**:

| §1 do PROMPT.md | Id de API válido | O que o sufixo era |
|---|---|---|
| `claude-opus-5-high` | `claude-opus-5` | `-high` é *effort*, não parte do id |
| `claude-opus-4.8-high` | `claude-opus-4-8` | idem; e o separador é `-`, não `.` |

Effort é `output_config={"effort": "high"}` — parâmetro real do `Claude` do Agno (`models/anthropic/claude.py:135`), repassado ao request em `claude.py:546`. Verificado construindo os dois modelos:

```python
Claude(id="claude-opus-5",   output_config={"effort": "high"}, thinking={"type": "adaptive"})
Claude(id="claude-opus-4-8", output_config={"effort": "high"}, thinking={"type": "adaptive"})
# ambos -> supports_native_structured_outputs = True
```

Dois detalhes que mudam comportamento e não estavam no documento:

- **`supports_native_structured_outputs = True` nos dois.** O `output_schema` do `Agent` vira `output_config.format` de verdade (`claude.py:688-698` monta o `output_format` e faz merge com o `output_config` do effort), não prompt pedindo JSON. É o que sustenta o critério de aceite da Fase 4 — "`ReviewOutput` real, não texto que parece JSON".
- **Em `claude-opus-4-8`, omitir `thinking` significa rodar *sem* thinking.** Só em `claude-opus-5` o default é adaptativo. Como o verifier roda em Opus 4.8 e o trabalho dele é conferir uma alegação contra a linha lida, o `thinking={"type": "adaptive"}` vai **explícito** no verifier — senão a "concordância do verifier" da §14 piora por configuração, não por escolha de modelo.

### 2.7 `get_step_content` stringifica a saída do `Parallel` — a §7 do blueprint precisa mudar

Não estava na lista da §12, mas o blueprint v2 depende disso em dois pontos, e ele quebra o produto do revisor.

`StepInput.get_step_content(name) -> str | Dict[str, str] | None`. Quando o step é um `Parallel`, o Agno monta o dicionário assim (`agno/workflow/types.py`):

```python
parallel_content[sub_step.step_name] = str(sub_step.content)   # <- str()
```

Ou seja: `get_step_content("lentes")` devolve os seis `ReviewOutput` **como texto**. Quem chamar isso no `build_report` recebe o `repr` de um modelo Pydantic e teria que reparsear string para recuperar `evidence`, `file`, `line_start` — exatamente o que a §2.3 do `PROMPT.md` existe para proteger.

O caminho tipado existe e é outro: **`StepInput.get_step_output(name) -> StepOutput`**, que busca recursivamente nos steps aninhados (`_search_nested_steps`) e devolve o objeto. E em step de agente o Agno faz `StepOutput(content=result.content)` — **sem** `str()` (`agno/workflow/step.py:1136`) — então `StepOutput.content` guarda o `ReviewOutput` do `output_schema` como objeto.

Duas consequências para o código:

- **`build_report` usa `get_step_output("lentes")` e percorre `.steps`**, lendo `.content` de cada sub-step. Nunca `get_step_content`.
- **`touches_schemas` pode continuar com `get_step_content("contexto")`**, porque o step de contexto é um `Step` simples cujo conteúdo já é a string do diff — e o blueprint acerta aí.

O `all_adjudicated` do blueprint (`outputs[-1].content.verdicts`) está **correto**: os outputs que o `end_condition` do `Loop` recebe são `StepOutput` de verdade, com `content` tipado.

---

## 3. Árvore de diretórios proposta

```
agno-ai-agents-development/
├── PROMPT.md                       # renomear prompt.md -> PROMPT.md (o doc se refere a si mesmo assim)
├── PLAN.md
├── pyproject.toml                  # versões exatas (§10.4)
├── skills-lock.json                # commitado (D6)
├── .claude/
│   ├── settings.local.json
│   └── skills/
│       ├── find-skills/            # Fase 0, --copy
│       ├── neon/  neon-postgres/  neon-postgres-branches/
│       ├── impeccable/             # já instalado (ver aviso e Q5)
│       ├── lean-diff/              # local, §0.1, se nada de terceiro passar nos critérios
│       └── review-checklist/       # §4: o CHECKLIST sai do Python já na Fase 4
├── src/
│   ├── agno_ai_agents_development/ # exemplo existente, intocado
│   └── agent_code_revisor/
│       ├── __init__.py
│       ├── config.py               # REPO_ALVO, FRONTEND_ALVO, ids de modelo, gates.
│       │                           #   Único ponto onde credencial e connection string
│       │                           #   são lidas (§10.6)
│       ├── contracts.py            # Fase 1.1: Severity, Lens, Finding, ReviewOutput,
│       │                           #   Verdict, VerificationOutput
│       ├── tools.py                # Fase 1.2: get_diff, read_file_range, grep_repo,
│       │                           #   impeccable_detect — todas read-only
│       ├── neon.py                 # Fase 2: branch efêmera, migration_smoke, cleanup 24h
│       ├── knowledge.py            # Fase 3: Knowledge + PgVector, indexar e reindexar
│       ├── agents.py               # Fase 4: reviewer() factory, 6 lentes LLM, verifier
│       ├── workflow.py             # Fase 5: Step / Parallel / Condition / Loop
│       ├── report.py               # Fase 6: build_report
│       └── __main__.py             # Fase 7: entrypoint, --dry-run, comentário via gh
├── tests/
│   ├── test_tools.py               # read_file_range: limites, arquivo inexistente
│   ├── test_impeccable_parser.py   # JSON do detector -> Finding
│   ├── test_gates.py               # os dois Condition (Q7)
│   └── test_report.py              # dedup, ordenação, colapso de nit
└── evals/                          # §13 — construído ANTES de mexer em prompt
    ├── cases.yaml                  # PRs fixos, bugs conhecidos, controles limpos
    └── run_eval.py                 # recall e precisão por rodada
```

Nenhum arquivo deve passar de ~300 linhas (§9). O candidato mais provável a estourar é `agents.py` — seis lentes mais o verifier. Se estourar, a fronteira real é *instructions* (texto) contra *fábrica* (código), e o texto vai para `skills/review-checklist/`, que é para onde a §4 já manda ir.

---

## 4. Objeções à §2

**Nenhuma.** Os sete itens me parecem certos, e dois deles são os que mais mudam o resultado:

- **§2.2 (`Workflow` + `Parallel`, não `Team`)** — confirmado no código instalado: `Parallel` recebe os steps e os executa direto, sem leader; não há segunda chamada de modelo e nada dissolve o par (arquivo, linha).
- **§2.3 (`evidence`)** — é o que separa "verifier" de "segunda opinião". A §2.5 acima mostra que `output_schema` vira restrição de formato de verdade nos dois modelos, então dá para **exigir** `evidence` no schema em vez de pedir por prompt, que é bem mais forte.

Registro aqui duas coisas que **não** são objeções à §2 — são notas de projeto sobre a §5, para você decidir junto com o resto.

**N1. `migration_smoke` dentro do `Parallel` briga com o "destruir a branch sempre" da Fase 2.**
A §5 desenha `Condition(toca migration) → migration_smoke` como um ramo do `Parallel`, ao lado de seis lentes LLM. Se outro ramo levantar exceção, o `Parallel` cancela o gather, e uma `CancelledError` no meio do smoke pode atravessar o `try/finally` que apaga a branch Neon — que é exatamente a branch órfã que custa dinheiro em silêncio (§14). Proposta: manter o step onde o desenho põe, mas **não** confiar o ciclo de vida da branch ao `finally` de dentro do workflow. O `migration_smoke` registra a branch criada num arquivo de estado do processo, e o `__main__.py` destrói num `finally` de nível de processo, que roda mesmo se o workflow inteiro morrer. O `cleanup` de 24h continua sendo a rede de segurança, não o mecanismo.

**N2. O revisor precisa ler os arquivos *do PR*, e o `REPO_ALVO` em disco está na `main`.**
`read_file_range`, `grep_repo` e `impeccable_detect` precisam ver o código como está no PR. Fazer `git checkout` ou `git worktree add` no `REPO_ALVO` escreve nele (`.git/worktrees`, ou pior, a árvore de trabalho) e colide com a §10.1. Proposta: **nunca tocar no `REPO_ALVO`**; materializar os arquivos tocados pelo PR num diretório temporário fora dele, lendo objetos com `git --git-dir=<REPO_ALVO>/.git cat-file` (leitura pura), e apontar as três tools para esse diretório. Isso também é o que faz o revisor rodar em CI, onde o `REPO_ALVO` pode nem existir em disco. Ver **Q8**.

---

## 5. Perguntas antes da Fase 1

Ordenadas por quanto travam.

**~~Q1 — Onde está o "blueprint v2"?~~ FECHADA.**
É o `blueprint_revisor_v2_agno.md`, na raiz do `REPO_AGENTE`. Li inteiro. Ele traz `Finding`, `ReviewOutput`, `Verdict`, `VerificationOutput`, a fábrica `reviewer()`, as cinco lentes, as três tools e o `Workflow` montado. Três ajustes que a verificação da §2 impõe ao que está escrito lá:

1. **`Claude(id="claude-sonnet-4-6")`** nas §6 do blueprint → `claude-opus-5` nos revisores e `claude-opus-4-8` no verifier, por causa da §1 e da §4 do `PROMPT.md`. O próprio blueprint já antecipa isso na nota da §6 ("trocar o modelo do verifier").
2. **`build_report` não pode usar `get_step_content`** — ver §2.7 acima.
3. **`REPO = Path("/caminho/...")` hardcoded** na §5 do blueprint vai para `config.py`, junto com o `FRONTEND_ALVO` e os ids de modelo.

O blueprint também usa `rg` no `grep_repo`. Confirmar que o ripgrep está disponível no ambiente de CI, ou trocar por `git grep`, que já vem com o git e não é dependência nova.

**Não há mais pergunta bloqueante para a Fase 1.**

**Q2 — Qual embedder? (bloqueia a Fase 3, não a 1)**
`PgVector` sem `embedder` cai em `OpenAIEmbedder`, e só existe `ANTHROPIC_API_KEY` aqui. Opções: (a) **local**, `fastembed` ou `sentence_transformer` — sem chave nova, sem corpus saindo da máquina, e o corpus (docs do Agno, convenções, ADRs, histórico de achados) é pequeno o bastante para isso não pesar; (b) chave de OpenAI, Voyage ou Cohere. **Recomendo (a)**, com o efeito colateral bom de manter a §10.6 trivialmente verdadeira.

**Q3 — Neon: crio o projeto, e como o CI autentica? (bloqueia a Fase 2)**
`neon`/`neonctl` não está instalado nesta máquina e não há `NEON_API_KEY` em lugar nenhum. A §1 diz que o `NEON_PROJECT_ID` é escolha minha "quando criado", mas a §11 exige sua aprovação antes de criar recurso pago. Confirma: crio um projeto free tier (nome proposto `halcyon-code-revisor`), com uma branch persistente `rag` para o pgvector da Fase 3, separada das `review-*` efêmeras? E o CI autentica por `NEON_API_KEY` em secret — ou é aqui que o Neon MCP da §8 se justifica, pelo OAuth interativo?

**Q4 — Instalo 3 skills do Neon ou as 7?**
Ver D2. Proponho `neon`, `neon-postgres`, `neon-postgres-branches`, com `--copy`. Leio os três `SKILL.md` inteiros antes (§10.7) e reporto qualquer coisa estranha.

**~~Q5 — O impeccable instalado por acidente: mantém ou reverto?~~ DECIDIDA — ver §7.**

**Q6 — Qual é o conjunto fixo de PRs da §13?**
O `halcyon-goods-product-control` tem **zero PRs abertos** e cinco merged (#1 a #5). A §13 pede um conjunto fixo com bugs conhecidos mais controles limpos, montado *antes* de mexer em prompt. Os merged servem de controle limpo, já que foram revisados e aprovados. Para os bugs conhecidos: quer que eu escreva PRs sintéticos com bugs plantados — em branches locais, sem abrir no GitHub — ou você tem PRs reais com defeito para apontar?

**Q7 — Confirma os dois gates? (registro da decisão que a Fase 2 pede)**
A Fase 2 manda decidir e registrar se o `migration_smoke` compartilha o `Condition` do `contract-reviewer` ou tem o seu. **São dois `Condition` separados**, porque os gatilhos não coincidem:

| Gate | Dispara quando o diff toca | Step |
|---|---|---|
| contrato | `apps/api/src/halcyon_api/schemas.py`, `models.py`, ou `.ts`/`.tsx` de `apps/web` que declare schema Zod (`zod@4.4.3` está no `package.json`) | `contract-reviewer` (LLM) |
| migração | `apps/api/migrations/versions/**` | `migration_smoke` (determinístico) |

Um PR que altera `models.py` sem gerar migration bate no primeiro e não no segundo — e essa assimetria é justamente um achado que a gente quer. O smoke roda `alembic upgrade head` seguido de `pytest`, com `HALCYON_DATABASE_URL` (prefixo `HALCYON_`, confirmado em `apps/api/src/halcyon_api/config.py`) apontando para a branch efêmera **via variável de ambiente do processo, nunca no contexto de nenhum agente** (§10.5, §10.6).

**Q8 — Confirma a leitura sem checkout do N2?**
Materializar os arquivos tocados pelo PR num diretório temporário via `git --git-dir=<REPO_ALVO>/.git cat-file`, e apontar `read_file_range`, `grep_repo` e `impeccable_detect` para lá. A alternativa que eu **não** recomendo é `git worktree add`, que escreve em `<REPO_ALVO>/.git/worktrees` e portanto viola a §10.1 na letra.

---

## 6. Ambiente verificado

| Item | Estado |
|---|---|
| `REPO_ALVO` | existe; monorepo `apps/{api,cli,web}`; FastAPI + Pydantic + Alembic (2 migrations); Next.js + `zod@4.4.3`; CI em `.github/workflows/ci.yml` (ruff, pytest em 3.11/3.12/3.13, e um job contra Postgres 18) |
| `FRONTEND_ALVO` | existe; Next.js, `.tsx` → o `impeccable detect` roda em modo regex (D7) |
| Python | 3.13.9, `.venv` de pé; `agno 3.0.0`, `anthropic 1.1.0`, `pydantic 2.13.4`, `sqlalchemy 2.0.52` |
| Faltando no venv | `pgvector`, `psycopg` — a Fase 3 nem importa sem eles |
| `gh` | 2.83.2, autenticado como `gabrantoniette`, escopos `gist, read:org, repo, workflow` — dá para comentar em PR |
| `neon` / `neonctl` | **não instalado** (Q3) |
| `psql` | não instalado — irrelevante, as migrations são Alembic/SQLAlchemy |
| `docker` | 29.7.2 |
| Segredos | só `ANTHROPIC_API_KEY` no `.env` do repo do agente; `.env` está no `.gitignore` |

---

## 7. Decisão registrada: hooks do impeccable removidos, skill e CLI mantidas

Auditei os scripts antes de decidir. `hook.mjs` (79 linhas) é um adaptador de stdin; `hook-lib.mjs` (2447 linhas) tem a lógica. **Não faz rede e não cria subprocesso** — nenhum `fetch`, nenhum `spawn`/`exec`. Escreve três coisas: um cache de sessão, um log de auditoria opcional, e um bloco em `.git/info/exclude` para esconder o próprio cache. Código limpo, com contrato explícito de nunca quebrar o turno (`process.exit(0)` em todo caminho de erro).

**Removi mesmo assim.** O que decidiu foi `hook-lib.mjs:68`:

```js
export const ALLOWED_EXTS = new Set([
  '.tsx', '.jsx', '.html', '.htm', '.vue', '.svelte', '.astro',
  '.css', '.scss', '.sass', '.less', '.ts', '.js',
]);
```

Sem `.py`, sem `.md`. O `agent_code_revisor` é Python e Markdown de ponta a ponta, e o único `.tsx` do escopo está em `apps/web`, dentro do `REPO_ALVO`, onde a §10.1 proíbe escrever. **O hook não dispara uma vez sequer em trabalho real deste repositório** — seria node startup a cada Edit/Write e a cada Stop por zero retorno. Verificado na prática: os hooks ficaram ativos durante a escrita da primeira versão deste arquivo e não deixaram rastro nenhum.

Os outros três motivos:

1. **A integração que o projeto quer é outra.** O `design` da §5 chama `npx impeccable detect --json` como subprocesso a partir de `tools.py`, contra o `FRONTEND_ALVO`. Isso funciona sem instalação — foi assim que rodei o detector antes de instalar qualquer coisa. Um hook que escaneia as *minhas* edições é feature diferente, ausente de todas as fases.
2. **A §14 chama skill de terceiro de superfície de injeção.** Um `SKILL.md` é texto entrando no contexto; um hook é código executando a cada edição. Limpo hoje não é limpo depois do próximo `npx impeccable update` — e a §14 pede tratar update de skill como bump de dependência, com leitura de diff. Hook ativo transforma esse descuido em execução.
3. **Foi parar no `settings.local.json`**, estado local de máquina. A §0 pediu escopo de projeto justamente para o time herdar a configuração; um hook que só existe na minha máquina é o oposto disso.

Feito: removidas as chaves `hooks` e `description` de `.claude/settings.local.json` (o arquivo não pôde ser apagado — tem permissões do usuário nele). Mantidos `.claude/skills/impeccable/` e a CLI, que é a parte que o revisor usa.

**Se quiser reverter:** `npx impeccable install` reinstala os hooks.

---

**Parado aqui, conforme a §12.** Com a Q1 fechada, a Fase 1 está desbloqueada e depende só do seu "vai". As demais perguntas (Q2 embedder, Q3 Neon, Q4 escopo das skills do Neon, Q6 corpus de PRs, Q7 gates, Q8 leitura sem checkout) travam as fases 2, 3 e 13 — nenhuma trava a Fase 1.
