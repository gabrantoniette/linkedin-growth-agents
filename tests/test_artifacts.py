"""Ferramentas de arquivo dos agentes.

O que mais importa aqui é o confinamento: um agente só pode escrever dentro de
`conteudo/`. Se essa checagem quebrar, um post mal formatado vira sobrescrita
de `.env` ou de código-fonte.

A segunda convenção testada é a do próprio módulo: ferramenta não levanta
exceção, devolve o erro como texto — para o agente ler a falha e tentar outro
caminho em vez de derrubar a execução.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from linkedin_growth.ferramentas.artefatos import (
    _resolver,
    data_de_hoje,
    ler_artefato,
    listar_artefatos,
    salvar_artefato,
)
from tests.conftest import chamar


# ==============================================================================
# Confinamento a conteudo/
# ==============================================================================


def test_resolver_com_caminho_simples_devolve_alvo_dentro_de_conteudo(conteudo_temp: Path):
    alvo = _resolver("posts/2026-09-03-rag.md")

    assert alvo is not None
    assert conteudo_temp.resolve() in alvo.parents


@pytest.mark.parametrize(
    "fuga",
    [
        "../segredo.md",
        "../../.env",
        "posts/../../../pyproject.toml",
        "posts/../../src/linkedin_growth/config.py",
    ],
)
def test_resolver_com_path_traversal_devolve_none(conteudo_temp: Path, fuga: str):
    """Qualquer caminho que escape de conteudo/ tem que ser recusado."""
    assert _resolver(fuga) is None


def test_salvar_artefato_com_path_traversal_nao_grava_e_devolve_erro(
    conteudo_temp: Path, tmp_path: Path
):
    alvo_proibido = tmp_path / "invadido.md"

    resultado = chamar(salvar_artefato, "../invadido.md", "conteudo malicioso")

    assert resultado.startswith("ERRO")
    assert not alvo_proibido.exists()


# ==============================================================================
# Gravar e ler
# ==============================================================================


def test_salvar_artefato_grava_o_conteudo_e_cria_a_subpasta(conteudo_temp: Path):
    resultado = chamar(salvar_artefato, "posts/2026-09-03-agentes.md", "# Post\n\ncorpo")

    gravado = conteudo_temp / "posts" / "2026-09-03-agentes.md"
    assert gravado.read_text(encoding="utf-8") == "# Post\n\ncorpo"
    assert "posts/2026-09-03-agentes.md" in resultado


def test_salvar_e_ler_artefato_preserva_acentuacao(conteudo_temp: Path):
    """Todo o conteúdo do projeto é em português: perder acento aqui é perder tudo."""
    original = "Construí um agente. A pergunta é: compensou?"

    chamar(salvar_artefato, "estrategia.md", original)
    lido = chamar(ler_artefato, "estrategia.md")

    assert lido == original


def test_ler_artefato_inexistente_devolve_erro_como_texto(conteudo_temp: Path):
    """A convenção do módulo: erro é texto de retorno, não exceção."""
    resultado = chamar(ler_artefato, "nao-existe.md")

    assert resultado.startswith("ERRO")
    assert "não existe" in resultado


def test_salvar_artefato_sobrescreve_arquivo_existente(conteudo_temp: Path):
    chamar(salvar_artefato, "estrategia.md", "primeira versão")
    chamar(salvar_artefato, "estrategia.md", "segunda versão")

    assert chamar(ler_artefato, "estrategia.md") == "segunda versão"


# ==============================================================================
# Listagem
# ==============================================================================


def test_listar_artefatos_sem_nada_avisa_que_esta_vazio(conteudo_temp: Path):
    assert chamar(listar_artefatos) == "Nenhum arquivo ainda."


def test_listar_artefatos_usa_barra_normal_mesmo_no_windows(conteudo_temp: Path):
    """O agente recebe caminhos que ele vai repassar para `ler_artefato`.

    Se vierem com barra invertida no Windows, o caminho volta diferente do que
    o agente mandou gravar.
    """
    chamar(salvar_artefato, "posts/2026-09-03-rag.md", "x")
    chamar(salvar_artefato, "calendario/2026-W36.md", "y")

    listagem = chamar(listar_artefatos)

    assert "posts/2026-09-03-rag.md" in listagem
    assert "calendario/2026-W36.md" in listagem
    assert "\\" not in listagem


def test_listar_artefatos_com_subpasta_filtra_so_ela(conteudo_temp: Path):
    chamar(salvar_artefato, "posts/um.md", "x")
    chamar(salvar_artefato, "calendario/dois.md", "y")

    listagem = chamar(listar_artefatos, "posts")

    assert "posts/um.md" in listagem
    assert "dois.md" not in listagem


# ==============================================================================
# Data
# ==============================================================================


def test_data_de_hoje_devolve_iso_e_semana_iso():
    """O Editor usa isto para nomear arquivo; formato errado quebra o nome."""
    resultado = chamar(data_de_hoje)

    assert re.fullmatch(r"data=\d{4}-\d{2}-\d{2} semana_iso=\d{4}-W\d{2}", resultado)
