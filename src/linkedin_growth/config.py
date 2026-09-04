"""Configuração central: segredos, caminhos, modelos e banco compartilhado.

Todo módulo do sistema importa daqui. Se alguma coisa precisa de uma chave, de
um caminho ou de um modelo, o lugar de decidir é este arquivo — não espalhado.
"""

from __future__ import annotations

import os
from pathlib import Path

from agno.db.sqlite import SqliteDb
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


def modelo(id_modelo: str | None = None) -> Claude:
    """Instancia o modelo Claude usado pelos agentes."""
    return Claude(
        id=id_modelo or MODELO_PRINCIPAL,
        api_key=exigir_anthropic()
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
