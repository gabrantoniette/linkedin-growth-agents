# LinkedIn Growth — sistema multiagente para engenharia de IA

Um time de oito agentes [Agno](https://github.com/agno-agi/agno) que trabalha o
seu perfil do LinkedIn para você ser encontrado por recrutadores de engenharia
de IA: audita o perfil, reescreve os textos, define a estratégia de conteúdo,
planeja o calendário, escreve os posts em português e inglês, revisa contra uma
rubrica e publica pela API oficial.

Foi construído para um caso específico: **quem está migrando para IA e ainda não
tem experiência na área.** A estratégia inteira parte disso. Sem histórico para
alegar, o que funciona é evidência — projetos, código, notas de estudo — bem
apresentada. O sistema é instruído a nunca inventar experiência.

**Visão do projeto em diagramas:** [docs/roadmap.md](docs/roadmap.md) descreve
o ciclo de ponta a ponta, etapa por etapa. [docs/mindmap.md](docs/mindmap.md)
mapeia as peças e como elas se ligam.

---



## Começando



### 1. Dependências

Requer Python 3.13+ e [uv](https://docs.astral.sh/uv/).

```bash
uv sync
```



### 2. Chave da Anthropic

```bash
cp .env.example .env
```

Preencha `ANTHROPIC_API_KEY` com a sua chave do
[console da Anthropic](https://console.anthropic.com/settings/keys).

### 3. Seus dados reais

O LinkedIn **não** permite ler o seu perfil por API. O caminho oficial é o
export de dados:

1. LinkedIn → **Configurações e privacidade** → **Privacidade de dados** →
  **Obter uma cópia dos seus dados**
2. Escolha o arquivo completo e peça o arquivo. O e-mail chega em minutos ou
  até 24 horas.
3. Descompacte o `.zip` dentro de `perfil/linkedin_export/`
4. Rode:

```bash
uv run linkedin importar
```

Isso gera `perfil/perfil.yaml`. **Abra e revise.** É a fonte de verdade de todos
os agentes — o que estiver errado ali sai errado em tudo. Preencha em especial o
campo `objetivo` com as suas palavras. Reimportar não apaga o que você escreveu
ali.

Se você tem posts antigos, o importador também gera `perfil/voz.md`, que os
agentes usam para escrever com o seu tom em vez do tom genérico de LLM.

### 4. Rode o ciclo

```bash
uv run linkedin status          # o que já existe e qual o próximo passo
uv run linkedin diagnosticar    # audita o perfil contra vagas reais de IA
uv run linkedin perfil          # textos prontos para colar no LinkedIn
uv run linkedin estrategia      # posicionamento, pilares e cadência
uv run linkedin calendario --semanas 2
uv run linkedin post --tema "como voce tem mantido a qualidade do seu sistema RAG?"
```

Tudo vai para `conteudo/`.

---



## Conectar o LinkedIn (para publicar)

Só é preciso para o comando `publicar`. Todo o resto funciona sem.

1. **Crie uma LinkedIn Page** se você não administra nenhuma
  ([criar](https://www.linkedin.com/company/setup/new/)). Todo app precisa
   estar associado a uma Page — pode ser uma página sua, sem conteúdo.
2. **Crie o app** em [https://www.linkedin.com/developers/apps](https://www.linkedin.com/developers/apps) e associe à Page.
  Confirme a verificação (você mesmo aprova, como admin da Page).
3. Na aba **Products**, adicione:
  - **Share on LinkedIn** → dá o escopo `w_member_social`
  - **Sign In with LinkedIn using OpenID Connect** → dá `openid` e `profile`
   Os dois são liberados na hora, sem aprovação de parceiro.
4. **Gere o token** em
  [https://www.linkedin.com/developers/tools/oauth/token-generator](https://www.linkedin.com/developers/tools/oauth/token-generator),
   marcando `openid`, `profile` e `w_member_social`.
5. Cole em `LINKEDIN_ACCESS_TOKEN` no `.env` e confira:

```bash
uv run linkedin conexao
```

**O token dura 60 dias.** Refresh automático só existe para parceiros
aprovados, então quando expirar é só gerar outro no mesmo lugar.

### Publicar

```bash
uv run linkedin publicar conteudo/posts/2026-09-02-tema.md --dry-run   # vê o JSON
uv run linkedin publicar conteudo/posts/2026-09-02-tema.md             # publica
uv run linkedin publicar conteudo/posts/2026-09-02-tema.md --idioma en # versão em inglês
```

Sempre pede confirmação antes de enviar. Um post publicado é público e imediato.

---



## Interface web

O repositório já traz a [Agno Agent UI](https://github.com/agno-agi/agent-ui)
em `agent_ui/`. Em dois terminais:

```bash
uv run linkedin serve          # backend em :7777
```

```bash
cd agent_ui && pnpm dev        # interface em :3000
```

Abra [http://localhost:3000](http://localhost:3000), escolha o modo **Team** e converse com o time.

A UI só conhece Agents e Teams — os fluxos (`post`, `calendario`) rodam pela CLI.

---



## O que dá e o que não dá para automatizar

O LinkedIn é restritivo, e o sistema é honesto sobre isso.


|                                                |                                                                                         |
| ---------------------------------------------- | --------------------------------------------------------------------------------------- |
| Publicar post (texto, imagem, PDF)             | **Automatizado**, pela API oficial                                                      |
| Ler o próprio perfil                           | **Não existe API.** Por isso o export de dados                                          |
| Editar headline, Sobre, experiências, projetos | **Não existe API, em nenhum nível.** O sistema entrega o texto pronto e diz onde colar  |
| Ler métricas dos próprios posts                | **Bloqueado** pelo LinkedIn (acesso restrito). Você anota à mão com `linkedin metricas` |
| Listar posts já publicados                     | **Bloqueado** (`r_member_social` está fechado)                                          |


O sistema usa **apenas** a API oficial com o seu consentimento. Não faz scraping,
não usa cookie de sessão, não dirige navegador, não automatiza conexão nem
mensagem — tudo isso é proibido pelos Termos de Uso do LinkedIn e derruba conta.

### O ciclo de aprendizado

Como as métricas não vêm por API, elas entram à mão:

```bash
uv run linkedin metricas
```

Isso alimenta `conteudo/metricas.csv`, que o estrategista lê para ajustar os
pilares. Sem isso, o sistema nunca aprende o que funciona para você.

---



## Memória

O sistema lembra de uma conversa para a outra. São três camadas, e vale saber
qual é qual — elas falham de jeitos diferentes.

| Camada | O que guarda | Onde vive | Quem lê |
| --- | --- | --- | --- |
| Perfil | Seus dados reais e verificáveis | `perfil/perfil.yaml` | todo agente, em toda execução |
| Conversa | Os últimos turnos, na íntegra | sessão no SQLite | o time e os agentes com histórico |
| Memória | Frases destiladas sobre você | `agno_memories`, presas ao seu usuário | todo agente, em toda execução |

**Quem escreve memória é o time, na conversa.** É ali que você conta o que
prefere, o que construiu e o que deu resultado. Os comandos da CLI recebem
sempre o mesmo pedido enlatado, então não aprendem nada novo — mas leem tudo.
Na prática: você comenta no chat que um post rendeu contato de recrutador, e o
`linkedin post` da semana seguinte já sabe disso.

O que vale a pena guardar (e o que não vale) está escrito em
`agentes/principios.py`, na função `instrucoes_de_memoria`.

### Ver e apagar

```bash
uv run linkedin memoria                      # o que o sistema aprendeu sobre você
uv run linkedin memoria --esquecer a1b2c3d4  # apaga uma
uv run linkedin memoria --limpar             # apaga tudo (pede confirmação)
```

Memória que não dá para inspecionar não dá para confiar. Se um agente começar a
repetir uma bobagem, é aqui que se descobre de onde veio.

### Conversas separadas

```bash
uv run linkedin chat                       # continua a conversa "principal"
uv run linkedin chat --sessao experimento  # uma linha paralela, que não se mistura
```

O histórico é por sessão; a memória é por usuário. Ou seja: o que você disse na
conversa `experimento` não aparece na `principal`, mas o que virou memória vale
para as duas.

---



## Como está organizado

```
perfil/                       seus dados (fora do git)
  linkedin_export/            o export do LinkedIn, descompactado
  perfil.yaml                 gerado e revisável — a fonte de verdade
  voz.md                      amostras da sua escrita

conteudo/                     o que o sistema produz (fora do git)
  diagnostico.md              auditoria do perfil
  perfil_otimizado.md         textos prontos para colar
  estrategia.md               posicionamento e pilares
  calendario/AAAA-Wxx.md      calendário editorial
  posts/AAAA-MM-DD-tema.md    posts em pt-BR e inglês
  metricas.csv                preenchido por você

referencias/                  material de apoio, só consulta (não gera nada)
  ganchos.md                  fórmulas de gancho, uma por pilar
  algoritmo-linkedin.md       heurísticas de formato e timing do LinkedIn
  vocabulario-ia.md           vocabulário e tiques que denunciam texto de IA
  headline-formulas.md        fórmula de headline para o Redator de Perfil

src/linkedin_growth/
  config.py                   segredos, caminhos, modelos, banco, memória
  perfil/                     esquema, importador e contexto
  ferramentas/                artefatos, referências, busca web, API do LinkedIn
  agentes/                    os oito especialistas
    principios.py             a estratégia codificada — comece por aqui
  times.py                    o time coordenador (chat)
  fluxos.py                   os workflows determinísticos
  cli.py                      os comandos
  agentos.py                  o servidor da interface web

docs/
  roadmap.md                  o ciclo de ponta a ponta, etapa por etapa
  mindmap.md                  o mapa das peças e como elas se ligam

tests/                        a suíte — nenhum teste chama API paga
  conftest.py                 fixtures, o helper de ferramentas @tool e o ModeloEspiao
  test_artefatos.py           confinamento a conteudo/, gravar e ler
  test_referencias.py         consulta somente leitura a referencias/
  test_linkedin_formato.py    little text format e montagem de payload
  test_importador.py          leitura dos CSVs do export do LinkedIn
  test_esquema.py             o contrato de dados do perfil
  test_principios.py          invariantes da estratégia codificada
  test_memoria_dos_agentes.py o que o sistema lembra, e o que não pode vazar
  test_cli_memoria.py         o comando que mostra e apaga memória
  test_agentos.py             o que a interface web precisa receber do servidor
```



### Os oito agentes


| Agente                   | Faz                                                       |
| ------------------------ | --------------------------------------------------------- |
| Diagnóstico de Perfil    | Busca vagas reais de IA e nota cada seção do seu perfil   |
| Redator de Perfil        | Headline, Sobre, experiências, projetos e skills, pt e en |
| Estrategista de Conteúdo | Posicionamento, pilares, público, cadência, métricas      |
| Pesquisador              | O que aconteceu em IA nesta semana, com ângulo para você  |
| Planejador Editorial     | Calendário com tema específico e ativo de prova por post  |
| Redator                  | Escreve o post em português e inglês                      |
| Editor                   | Critica contra uma rubrica de sete critérios e finaliza   |
| Publicador               | Publica pela API, sempre com aprovação                    |




### Onde mexer primeiro

`src/linkedin_growth/agentes/principios.py` concentra a estratégia: as regras de
honestidade, o posicionamento, os pilares de conteúdo, as regras de escrita e a
rubrica do editor. Mudar o comportamento do sistema é mudar esse arquivo — não
sete arquivos de agente.

### Adicionando material de referência ("skills")

Este projeto usa agentes [Agno](https://github.com/agno-agi/agno), não Claude
Skills — não existe um mecanismo para simplesmente "instalar" uma skill do
formato `SKILL.md`. O padrão adotado aqui para portar conhecimento externo
(por exemplo, de [sergebulaev/linkedin-skills](https://github.com/sergebulaev/linkedin-skills))
é:

1. Curar o conteúdo relevante — traduzido e adaptado ao contexto deste
  projeto, não colado — como um `.md` novo em `referencias/`.
2. Dar ao agente que precisa dele a ferramenta `ler_referencia`
  (`ferramentas/referencias.py`) e uma instrução dizendo quando chamá-la.

Isso imita a divulgação progressiva das Claude Skills: o conteúdo só entra no
contexto do agente quando ele decide que precisa, em vez de inflar o prompt
de toda chamada. Regra curta e universal (uma linha, vale para todo post) vai
direto em `principios.py`; conteúdo longo ou consultado só às vezes vai em
`referencias/`.

---



## Testes

```bash
uv run pytest              # a suíte inteira, ~10s
uv run pytest -k linkedin  # só um assunto
```

No Windows, se o `linkedin serve` estiver rodando em outro terminal, o `uv run`
falha ao tentar sincronizar o ambiente (não consegue substituir `linkedin.exe`,
que está em uso). Use `uv run --no-sync pytest` sem parar o servidor.

**Nenhum teste chama a API da Anthropic nem a do LinkedIn.** A suíte cobre a
lógica pura e o I/O em disco: o confinamento das ferramentas de arquivo (um
agente não pode escrever fora de `conteudo/`), o *little text format* do
LinkedIn (escape e hashtags), a leitura dos CSVs do export — que vêm com
preâmbulo e nomes de coluna variáveis — e os invariantes de `principios.py`.

Esse último grupo é o menos óbvio e o mais útil: como a estratégia é o produto,
os testes fixam que certas regras continuam chegando a todo agente (a
honestidade é eliminatória, a rubrica tem os sete critérios) e travam
regressões de regras decididas com motivo, como o limite de hashtags.

Os testes de memória (`test_memoria_dos_agentes.py`) rodam agentes de verdade,
com um `ModeloEspiao` no lugar do `Claude`. É a única forma de responder "o
agente lembra?": a resposta está nas mensagens que chegam ao modelo, e só
executando dá para vê-las. O espião grava cada chamada, então o teste consegue
afirmar que a memória chegou ao prompt — e, nos testes de isolamento, que **não**
chegou onde não devia.

Os de `test_agentos.py` batem no servidor via `TestClient`, sem abrir porta.
Existem porque uma classe inteira de bug só aparece ali: um campo que só é lido
na hora de montar a resposta HTTP e em nenhum outro lugar do sistema. Foi assim
que o time sumiu da interface web sem que nada no terminal indicasse erro.

O que a suíte **não** cobre: a qualidade do texto que os agentes geram. Isso
não é teste unitário, é avaliação — e hoje quem faz esse papel é o agente
Editor, com a rubrica.

---



## Custo

Por padrão os agentes de julgamento usam `claude-opus-5` e os de volume usam
`claude-sonnet-5`. Para gastar menos, no `.env`:

```
MODELO_PRINCIPAL=claude-sonnet-5
```

