"""Configuração central: segredos, caminhos, modelos e banco compartilhado.

Todo módulo do sistema importa daqui. Se alguma coisa precisa de uma chave, de
um caminho ou de um modelo, o lugar de decidir é este arquivo — não espalhado.
"""

from __future__ import annotations

import os
from pathlib import Path

from agno.db.sqlite import SqliteDb
from agno.memory import MemoryManager
from agno.models.anthropic import Claude
from dotenv import load_dotenv

load_dotenv()

# ==============================================================================
# Caminhos
# ==============================================================================
# config.py fica em src/linkedin_growth/, então a raiz do projeto é dois níveis
# acima do pacote.
RAIZ = Path(__file__).resolve().parents[2]

PERFIL_DIR = RAIZ / "perfil"
EXPORT_DIR = PERFIL_DIR / "linkedin_export"
PERFIL_YAML = PERFIL_DIR / "perfil.yaml"
VOZ_MD = PERFIL_DIR / "voz.md"

CONTEUDO_DIR = RAIZ / "conteudo"
CALENDARIO_DIR = CONTEUDO_DIR / "calendario"
POSTS_DIR = CONTEUDO_DIR / "posts"
METRICAS_CSV = CONTEUDO_DIR / "metricas.csv"

REFERENCIAS_DIR = RAIZ / "referencias"

TMP_DIR = RAIZ / "tmp"
DB_FILE = TMP_DIR / "linkedin_growth.db"


def garantir_diretorios() -> None:
    """Cria a árvore de pastas que o sistema usa. Idempotente."""
    for diretorio in (
        PERFIL_DIR,
        EXPORT_DIR,
        CONTEUDO_DIR,
        CALENDARIO_DIR,
        POSTS_DIR,
        REFERENCIAS_DIR,
        TMP_DIR,
    ):
        diretorio.mkdir(parents=True, exist_ok=True)


# ==============================================================================
# Segredos
# ==============================================================================
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
LINKEDIN_ACCESS_TOKEN = os.getenv("LINKEDIN_ACCESS_TOKEN")
LINKEDIN_VERSION = os.getenv("LINKEDIN_VERSION", "202609")


class ConfiguracaoAusente(RuntimeError):
    """Erro de configuração com instrução de como resolver."""


def exigir_anthropic() -> str:
    """Devolve a chave da Anthropic ou explica como configurá-la."""
    if not ANTHROPIC_API_KEY:
        raise ConfiguracaoAusente(
            "ANTHROPIC_API_KEY não encontrada.\n"
            "Crie um arquivo .env na raiz do projeto com:\n"
            "    ANTHROPIC_API_KEY=sk-ant-...\n"
            "Use .env.example como base."
        )
    return ANTHROPIC_API_KEY


def exigir_linkedin() -> str:
    """Devolve o token do LinkedIn ou explica como obtê-lo."""
    if not LINKEDIN_ACCESS_TOKEN:
        raise ConfiguracaoAusente(
            "LINKEDIN_ACCESS_TOKEN não encontrado.\n"
            "Gere um token em:\n"
            "    https://www.linkedin.com/developers/tools/oauth/token-generator\n"
            "com o escopo 'w_member_social' (produto 'Share on LinkedIn') e o "
            "escopo 'openid profile'.\n"
            "Depois coloque no .env:\n"
            "    LINKEDIN_ACCESS_TOKEN=...\n"
            "O passo a passo completo está no README, seção 'Conectar o LinkedIn'."
        )
    return LINKEDIN_ACCESS_TOKEN


# ==============================================================================
# Modelos
# ==============================================================================
# Opus 5 para o trabalho que exige julgamento (estratégia, diagnóstico, edição).
# Sonnet 5 para trabalho volumoso e mais mecânico (pesquisa, primeiras versões).
MODELO_PRINCIPAL = os.getenv("MODELO_PRINCIPAL", "claude-opus-5")
MODELO_RAPIDO = os.getenv("MODELO_RAPIDO", "claude-sonnet-5")

# O padrão do Agno é 8192, e é pouco para este sistema. Os agentes daqui
# escrevem um documento longo (diagnóstico, estratégia, calendário) e, no fim,
# chamam `salvar_artefato` com o documento inteiro no argumento. Com 8192 o
# texto consome a cota sozinho: a resposta é cortada no meio, a chamada da
# ferramenta nunca acontece e o arquivo não é criado — enquanto o modelo já
# escreveu "salvei o relatório". Falha cara e silenciosa.
#
# 16000 é o valor recomendado para requisição sem streaming, que é o caso aqui
# (`agente.run()`). Opus 5 e Sonnet 5 aceitam até 128000, mas passar disso sem
# streaming esbarra no timeout HTTP do SDK.
MAX_TOKENS = int(os.getenv("MAX_TOKENS", "16000"))


def modelo(id_modelo: str | None = None) -> Claude:
    """Instancia o modelo Claude usado pelos agentes."""
    return Claude(
        id=id_modelo or MODELO_PRINCIPAL,
        api_key=exigir_anthropic(),
        max_tokens=MAX_TOKENS,
    )


# ==============================================================================
# Banco compartilhado (sessões, histórico e memória dos agentes)
# ==============================================================================
_db: SqliteDb | None = None


def db() -> SqliteDb:
    """Banco único do sistema. Criado sob demanda para não tocar o disco no import."""
    global _db
    if _db is None:
        TMP_DIR.mkdir(parents=True, exist_ok=True)
        _db = SqliteDb(db_file=str(DB_FILE))
    return _db


# ==============================================================================
# Memória
# ==============================================================================
# O sistema é de uma pessoa só, mas o Agno indexa memória por `user_id`. Sem um
# id fixo tudo cairia num balde anônimo e nada seria recuperável — então ele
# existe, e é configurável para quem clonar o projeto.
USUARIO_ID = os.getenv("USUARIO_ID", "usuario")

# Conversa padrão da CLI. Um id estável é o que faz `linkedin chat` de hoje
# continuar o `linkedin chat` de ontem: sem ele, o Agno sorteia uma sessão nova
# a cada processo e o histórico recomeça do zero.
SESSAO_PADRAO = os.getenv("SESSAO_PADRAO", "principal")


def sessao_do_agente(id_agente: str) -> str:
    """Sessão estável de um agente da CLI.

    Cada comando (`diagnosticar`, `estrategia`, ...) tem a sua, para que o
    agente veja as próprias execuções anteriores sem misturá-las com as dos
    outros nem com a conversa do time.
    """
    return f"cli-{id_agente}"


_memoria: MemoryManager | None = None


def memoria() -> MemoryManager:
    """O gerente de memória de longo prazo, compartilhado por todo o sistema.

    Roda no modelo rápido de propósito: destilar uma frase do que acabou de ser
    dito é trabalho mecânico, e essa chamada acontece ao fim de toda conversa.

    `delete_memories` e `clear_memories` ficam desligados: apagar memória é
    decisão do usuário, pelo comando `linkedin memoria`, não de um modelo no
    meio de uma conversa.
    """
    # Import tardio: `principios` mora dentro do pacote `agentes`, cujo
    # `__init__` importa os agentes, que importam este módulo. No topo do
    # arquivo isso seria um ciclo.
    from linkedin_growth.agentes.principios import instrucoes_de_memoria

    global _memoria
    if _memoria is None:
        _memoria = MemoryManager(
            db=db(),
            model=modelo(MODELO_RAPIDO),
            memory_capture_instructions=instrucoes_de_memoria(),
            add_memories=True,
            update_memories=True,
            delete_memories=False,
            clear_memories=False,
        )
    return _memoria


def parametros_de_memoria(id_agente: str) -> dict[str, object]:
    """Os parâmetros de memória que todo agente recebe, num lugar só.

    Fica aqui, e não repetido em oito arquivos, pelo mesmo motivo que os
    princípios ficam em `principios.py`: quando a política mudar, muda em um
    lugar.

    A divisão de trabalho é deliberada: **os agentes leem a memória, o time
    escreve.** Um agente da CLI recebe sempre o mesmo comando enlatado, então
    quase nunca aprende algo novo sobre o usuário — extrair memória ao fim de
    cada execução seria uma chamada de modelo a mais para não guardar nada. É
    na conversa, no `Team`, que o usuário conta as coisas.
    """
    return {
        "db": db(),
        "user_id": USUARIO_ID,
        "session_id": sessao_do_agente(id_agente),
        "memory_manager": memoria(),
        "add_memories_to_context": True,
    }
