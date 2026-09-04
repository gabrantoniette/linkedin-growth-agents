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
uv run linkedin post --tema "o erro de encoding que me custou 3 horas"
```

Tudo vai para `conteudo/`.

---

## Conectar o LinkedIn (para publicar)

Só é preciso para o comando `publicar`. Todo o resto funciona sem.

1. **Crie uma LinkedIn Page** se você não administra nenhuma
   ([criar](https://www.linkedin.com/company/setup/new/)). Todo app precisa
   estar associado a uma Page — pode ser uma página sua, sem conteúdo.
2. **Crie o app** em <https://www.linkedin.com/developers/apps> e associe à Page.
   Confirme a verificação (você mesmo aprova, como admin da Page).
3. Na aba **Products**, adicione:
   - **Share on LinkedIn** → dá o escopo `w_member_social`
   - **Sign In with LinkedIn using OpenID Connect** → dá `openid` e `profile`

   Os dois são liberados na hora, sem aprovação de parceiro.
4. **Gere o token** em
   <https://www.linkedin.com/developers/tools/oauth/token-generator>,
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

Abra <http://localhost:3000>, escolha o modo **Team** e converse com o time.

A UI só conhece Agents e Teams — os fluxos (`post`, `calendario`) rodam pela CLI.

---

## O que dá e o que não dá para automatizar

O LinkedIn é restritivo, e o sistema é honesto sobre isso.

| | |
|---|---|
| Publicar post (texto, imagem, PDF) | **Automatizado**, pela API oficial |
| Ler o próprio perfil | **Não existe API.** Por isso o export de dados |
| Editar headline, Sobre, experiências, projetos | **Não existe API, em nenhum nível.** O sistema entrega o texto pronto e diz onde colar |
| Ler métricas dos próprios posts | **Bloqueado** pelo LinkedIn (acesso restrito). Você anota à mão com `linkedin metricas` |
| Listar posts já publicados | **Bloqueado** (`r_member_social` está fechado) |

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

## Como está organizado

```
perfil/                       seus dados (fora do git)
  linkedin_export/            o export do LinkedIn, descompactado
  perfil.yaml                 gerado e revisável — a fonte de verdade
  voz.md                      amostras da sua escrita

conteudo/                     o que o sistema produz
  diagnostico.md              auditoria do perfil
  perfil_otimizado.md         textos prontos para colar
  estrategia.md               posicionamento e pilares
  calendario/AAAA-Wxx.md      calendário editorial
  posts/AAAA-MM-DD-tema.md    posts em pt-BR e inglês
  metricas.csv                preenchido por você

src/linkedin_growth/
  config.py                   segredos, caminhos, modelos, banco
  perfil/                     esquema, importador e contexto
  ferramentas/                artefatos, busca web, API do LinkedIn
  agentes/                    os oito especialistas
    principios.py             a estratégia codificada — comece por aqui
  times.py                    o time coordenador (chat)
  fluxos.py                   os workflows determinísticos
  cli.py                      os comandos
  agentos.py                  o servidor da interface web

docs/
  roadmap.md                  o ciclo de ponta a ponta, etapa por etapa
  mindmap.md                  o mapa das peças e como elas se ligam
```

### Os oito agentes

| Agente | Faz |
|---|---|
| Diagnóstico de Perfil | Busca vagas reais de IA e nota cada seção do seu perfil |
| Redator de Perfil | Headline, Sobre, experiências, projetos e skills, pt e en |
| Estrategista de Conteúdo | Posicionamento, pilares, público, cadência, métricas |
| Pesquisador | O que aconteceu em IA nesta semana, com ângulo para você |
| Planejador Editorial | Calendário com tema específico e ativo de prova por post |
| Redator | Escreve o post em português e inglês |
| Editor | Critica contra uma rubrica de sete critérios e finaliza |
| Publicador | Publica pela API, sempre com aprovação |

### Onde mexer primeiro

`src/linkedin_growth/agentes/principios.py` concentra a estratégia: as regras de
honestidade, o posicionamento, os pilares de conteúdo, as regras de escrita e a
rubrica do editor. Mudar o comportamento do sistema é mudar esse arquivo — não
sete arquivos de agente.

---

## Custo

Por padrão os agentes de julgamento usam `claude-opus-5` e os de volume usam
`claude-sonnet-5`. Para gastar menos, no `.env`:

```
MODELO_PRINCIPAL=claude-sonnet-5
```
