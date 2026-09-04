# Mapa mental do projeto

Este documento responde a uma pergunta: **o que existe aqui dentro e como as
peças se ligam.** Para a sequência temporal — o que rodar primeiro, o que rodar
depois — veja [roadmap.md](roadmap.md).

Os diagramas são Mermaid. Renderizam direto no GitHub e no preview de Markdown
do VS Code.

---

## 1. O projeto inteiro

```mermaid
mindmap
  root((LinkedIn Growth))
    Entrada
      Export de dados do LinkedIn
      perfil.yaml revisado à mão
      voz.md com posts antigos
      objetivo escrito por você
    Núcleo
      principios.py
        Honestidade
        Posicionamento
        Cinco pilares
        Regras de escrita
        Rubrica do editor
      config.py
        Chaves e caminhos
        Opus 5 para julgamento
        Sonnet 5 para volume
        SQLite compartilhado
      contexto.py
        Perfil inteiro no prompt
        Sem RAG por decisão
        Cache de uma execução
    Agentes
      Diagnóstico de Perfil
      Redator de Perfil
      Estrategista de Conteúdo
      Pesquisador
      Planejador Editorial
      Redator
      Editor
      Publicador
    Orquestração
      Team em modo coordinate
        linkedin chat
        agent_ui no navegador
      Workflows determinísticos
        fluxo_post
        fluxo_semana
      CLI com Typer
      AgentOS na porta 7777
    Ferramentas
      Arquivos
        salvar_artefato
        ler_artefato
        listar_artefatos
        data_de_hoje
      Web
        busca_recente
        busca_ampla
      LinkedIn
        verificar_conexao_linkedin
        publicar_post
    Saída
      diagnostico.md
      perfil_otimizado.md
      estrategia.md
      calendario semanal
      posts em pt e en
      Post publicado no feed
    Retorno
      metricas.csv à mão
      Realimenta o estrategista
      Ajusta os pilares
```

---

## 2. Como os artefatos dependem uns dos outros

A seta significa **"lê"**. Nenhum agente inventa contexto: ou o dado está no
perfil, ou está num artefato que outro agente já gravou.

```mermaid
flowchart TD
    EXPORT["Export do LinkedIn<br/>perfil/linkedin_export/*.csv"] --> YAML["perfil/perfil.yaml<br/><i>fonte de verdade</i>"]
    EXPORT --> VOZ["perfil/voz.md<br/><i>amostra de tom</i>"]

    YAML --> CTX["contexto_do_perfil<br/><i>injetado em todo agente</i>"]
    VOZ --> CTX

    CTX --> DIAG["conteudo/diagnostico.md"]
    CTX --> PERF["conteudo/perfil_otimizado.md"]
    CTX --> ESTR["conteudo/estrategia.md"]
    CTX --> CAL["conteudo/calendario/AAAA-Wxx.md"]
    CTX --> POST["conteudo/posts/AAAA-MM-DD-tema.md"]

    DIAG --> PERF
    DIAG --> ESTR
    MET["conteudo/metricas.csv<br/><i>preenchido por você</i>"] --> ESTR
    ESTR --> CAL
    CAL -.->|tema do dia| POST
    POST --> PUB(["Post publicado no LinkedIn"])
    PUB -.->|dias depois, à mão| MET

    classDef entrada fill:#e8f0fe,stroke:#4a6fa5,color:#1a2332
    classDef saida fill:#e9f5ec,stroke:#4a8a5e,color:#1a2332
    classDef externo fill:#fdf0e3,stroke:#b07d3a,color:#1a2332
    class EXPORT,YAML,VOZ,MET entrada
    class DIAG,PERF,ESTR,CAL,POST saida
    class PUB externo
```

O ciclo fecha em `metricas.csv`. Sem ele o sistema produz para sempre, mas nunca
aprende o que funcionou.

---

## 3. Os oito agentes

Todos herdam `instrucoes_base()` de `principios.py` e recebem o perfil inteiro
em `additional_context`. O que muda entre eles é o papel, as ferramentas e o
modelo.

| Agente | Papel | Ferramentas | Modelo | Grava |
|---|---|---|---|---|
| **Diagnóstico de Perfil** | Audita o perfil contra vagas reais e nota cada seção de 0 a 10 | `busca_ampla`, `salvar_artefato` | Opus 5 | `diagnostico.md` |
| **Redator de Perfil** | Headline, Sobre, experiências, projetos e skills, pt + en | `ler_artefato`, `salvar_artefato` | Opus 5 | `perfil_otimizado.md` |
| **Estrategista de Conteúdo** | Posicionamento, público, pilares, cadência, métricas, 30 dias | `ler_artefato`, `salvar_artefato` | Opus 5 | `estrategia.md` |
| **Pesquisador** | O que aconteceu em IA nesta semana, com ângulo pessoal para cada item | `busca_recente`, `data_de_hoje` | Sonnet 5 | nada — alimenta outro agente |
| **Planejador Editorial** | Calendário com seis campos por post, incluindo o ativo de prova | `data_de_hoje`, `ler_artefato`, `listar_artefatos`, `salvar_artefato` | Opus 5 | `calendario/AAAA-Wxx.md` |
| **Redator** | Escreve o post em português e reescreve para o leitor internacional | `ler_artefato` | Opus 5 | nada — passa ao Editor |
| **Editor** | Aplica a rubrica de sete critérios, corta e finaliza | `data_de_hoje`, `salvar_artefato` | Opus 5 | `posts/AAAA-MM-DD-tema.md` |
| **Publicador** | Última porta antes do público. Verifica token, extrai o corpo, publica | `verificar_conexao_linkedin`, `ler_artefato`, `listar_artefatos`, `publicar_post` | Sonnet 5 | nada — publica |

**Por que Sonnet em dois deles:** Pesquisador e Publicador fazem trabalho de
volume e de execução, não de julgamento. Opus ali seria dinheiro gasto sem
ganho. Trocável em `.env` por `MODELO_PRINCIPAL` e `MODELO_RAPIDO`.

---

## 4. As três formas de acionar o sistema

O mesmo conjunto de agentes é exposto por três superfícies diferentes. Elas não
competem — cada uma serve a um momento.

```mermaid
flowchart LR
    subgraph VOCE["Você"]
        CLI["Terminal<br/>uv run linkedin ..."]
        WEB["Navegador<br/>localhost:3000"]
    end

    subgraph SIST["O sistema"]
        direction TB
        WF["Workflows<br/><i>ordem fixa, sem decisão</i>"]
        TEAM["Team coordinate<br/><i>o líder escolhe quem faz</i>"]
        AG["Agente único<br/><i>chamada direta</i>"]
    end

    subgraph EXEC["Os oito especialistas"]
        A8["Diagnóstico · Perfil · Estrategista<br/>Pesquisador · Planejador<br/>Redator · Editor · Publicador"]
    end

    CLI -->|post, calendario| WF
    CLI -->|chat| TEAM
    CLI -->|diagnosticar, perfil, estrategia| AG
    WEB -->|AgentOS :7777| TEAM
    WEB --> AG

    WF --> A8
    TEAM --> A8
    AG --> A8

    classDef voce fill:#e8f0fe,stroke:#4a6fa5,color:#1a2332
    classDef sist fill:#f4f1e8,stroke:#8a7a4a,color:#1a2332
    class CLI,WEB voce
    class WF,TEAM,AG sist
```

**Quando usar cada uma:**

- **Workflow** (`post`, `calendario`) — a ordem dos passos já é conhecida.
  Pesquisa, escreve, edita, grava. Não gasta token decidindo quem faz o quê, e
  o resultado é o mesmo toda vez. É o caminho de produção.
- **Team** (`chat`, ou a UI web no modo Team) — você não sabe de antemão quem
  precisa responder. O líder lê o pedido, delega e sintetiza. É o caminho de
  conversa.
- **Agente único** (`diagnosticar`, `perfil`, `estrategia`) — uma tarefa, um
  especialista, sem intermediário.

A `agent_ui` só enxerga Agents e Teams. Workflows existem no AgentOS por HTTP,
mas não aparecem no chat — rode-os pela CLI.

---

## 5. Anatomia de um agente

Todo `construir()` em `agentes/` monta a mesma estrutura. Entender uma vez é
entender as oito.

```mermaid
flowchart TB
    subgraph AGENTE["Agent do Agno"]
        direction TB
        DESC["description<br/><i>quem ele é</i>"]
        INST["instructions<br/><i>instrucoes_base + regras do papel</i>"]
        CTX["additional_context<br/><i>DADOS REAIS DO USUÁRIO + voz</i>"]
        TOOLS["tools<br/><i>o que ele pode fazer no mundo</i>"]
        MOD["model<br/><i>Opus 5 ou Sonnet 5</i>"]
        DB["db<br/><i>SQLite de sessão</i>"]
        LIM["tool_call_limit<br/><i>teto de gasto</i>"]
    end

    PRINC["principios.py"] --> INST
    PERFIL["perfil.yaml + voz.md"] --> CTX
    CONF["config.py"] --> MOD
    CONF --> DB

    classDef fonte fill:#e8f0fe,stroke:#4a6fa5,color:#1a2332
    class PRINC,PERFIL,CONF fonte
```

**A regra de ouro do repositório:** comportamento se muda em
`agentes/principios.py`, não em oito arquivos. Lá estão a honestidade, o
posicionamento, os cinco pilares, as regras de escrita, o que é proibido, e a
rubrica do Editor.

---

## 6. Mapa dos arquivos

```
perfil/                          seus dados — fora do git
  linkedin_export/               o .zip do LinkedIn, descompactado
  perfil.yaml                    gerado e revisado à mão · fonte de verdade
  voz.md                         até 25 posts antigos, como amostra de tom

conteudo/                        tudo que o sistema produz
  diagnostico.md                 auditoria do perfil contra vagas reais
  perfil_otimizado.md            textos prontos para colar, pt e en
  estrategia.md                  posicionamento, pilares, cadência
  calendario/AAAA-Wxx.md         calendário editorial por semana ISO
  posts/AAAA-MM-DD-tema.md       post em pt e en + avaliação do Editor
  metricas.csv                   preenchido por você, à mão

src/linkedin_growth/
  config.py                      segredos, caminhos, modelos, banco
  perfil/
    esquema.py                   o contrato Pydantic do perfil
    importador.py                lê os CSVs com tolerância a variação
    contexto.py                  perfil -> markdown para o prompt
  ferramentas/
    artefatos.py                 ler, salvar, listar — confinado a conteudo/
    pesquisa.py                  busca web via DDGS, sem chave de API
    linkedin.py                  API oficial: token, URN, payload, publicação
  agentes/
    principios.py                a estratégia codificada · comece por aqui
    <oito arquivos>              um construir() cada
  times.py                       o Team coordenador
  fluxos.py                      os dois workflows
  cli.py                         os doze comandos
  agentos.py                     o servidor da interface web

agent_ui/                        a interface Next.js, em :3000
tmp/linkedin_growth.db           sessões, histórico e memória dos agentes
docs/                            este mapa e o roadmap
```

---

## 7. As fronteiras do sistema

Três limites são estruturais — não são falta de implementação, são o que o
LinkedIn permite. Eles explicam o formato de metade dos artefatos.

```mermaid
flowchart LR
    subgraph OK["O que a API permite"]
        P1["Publicar post de texto"]
        P2["Identificar o dono do token"]
    end

    subgraph NAO["O que não existe"]
        N1["Ler o próprio perfil<br/>→ por isso o export de dados"]
        N2["Editar headline, Sobre,<br/>experiências, projetos<br/>→ por isso o 'cole em:'"]
    end

    subgraph BLOQ["O que é restrito"]
        B1["Métricas dos posts<br/>→ por isso o metricas.csv à mão"]
        B2["Listar posts publicados"]
    end

    classDef ok fill:#e9f5ec,stroke:#4a8a5e,color:#1a2332
    classDef nao fill:#fdeaea,stroke:#a55,color:#1a2332
    classDef bloq fill:#fdf0e3,stroke:#b07d3a,color:#1a2332
    class P1,P2 ok
    class N1,N2 nao
    class B1,B2 bloq
```

O sistema usa **apenas** a API oficial, com o seu consentimento. Nada de
scraping, cookie de sessão, navegador dirigido, conexão ou mensagem
automatizada — tudo isso viola os Termos de Uso e derruba conta.

E o destino de tudo é o **seu perfil pessoal**: o autor do post é
`urn:li:person:<você>`. A Company Page existe só porque o LinkedIn exige uma
para cadastrar qualquer app de desenvolvedor.
