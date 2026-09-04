"""Consulta ao material de apoio em `referencias/`.

`referencias/` é somente leitura por decisão de projeto: é a base de consulta
dos agentes (fórmulas de gancho, heurísticas do algoritmo, vocabulário
proibido), e um agente não deveria poder reescrever a própria referência.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from linkedin_growth.ferramentas import referencias as modulo_referencias
from linkedin_growth.ferramentas.referencias import (
    _resolver,
    ler_referencia,
    listar_referencias,
)
from tests.conftest import chamar


# ==============================================================================
# Só leitura
# ==============================================================================


def test_modulo_nao_expoe_ferramenta_de_escrita():
    """Se alguém adicionar um `salvar_referencia`, este teste chama a atenção."""
    nomes = dir(modulo_referencias)

    assert not [n for n in nomes if n.startswith("salvar") or n.startswith("gravar")]


# ==============================================================================
# Confinamento
# ==============================================================================


@pytest.mark.parametrize(
    "fuga",
    ["../.env", "../../pyproject.toml", "subpasta/../../fora.md"],
)
def test_resolver_com_path_traversal_devolve_none(referencias_temp: Path, fuga: str):
    assert _resolver(fuga) is None


def test_ler_referencia_com_path_traversal_devolve_erro(referencias_temp: Path):
    resultado = chamar(ler_referencia, "../.env")

    assert resultado.startswith("ERRO")
    assert "referencias/" in resultado


# ==============================================================================
# Leitura
# ==============================================================================


def test_ler_referencia_devolve_o_conteudo_do_arquivo(referencias_temp: Path):
    (referencias_temp / "ganchos.md").write_text("# Fórmulas\n\nF1 — teste", encoding="utf-8")

    assert chamar(ler_referencia, "ganchos.md") == "# Fórmulas\n\nF1 — teste"


def test_ler_referencia_inexistente_devolve_erro_como_texto(referencias_temp: Path):
    resultado = chamar(ler_referencia, "nao-existe.md")

    assert resultado.startswith("ERRO")
    assert "não existe" in resultado


def test_listar_referencias_sem_nada_avisa_que_esta_vazio(referencias_temp: Path):
    assert chamar(listar_referencias) == "Nenhuma referência ainda."


def test_listar_referencias_devolve_um_por_linha_com_barra_normal(referencias_temp: Path):
    (referencias_temp / "ganchos.md").write_text("x", encoding="utf-8")
    (referencias_temp / "algoritmo-linkedin.md").write_text("y", encoding="utf-8")

    listagem = chamar(listar_referencias)

    assert sorted(listagem.splitlines()) == ["algoritmo-linkedin.md", "ganchos.md"]
    assert "\\" not in listagem


# ==============================================================================
# Os arquivos de referência de verdade, que os agentes citam pelo nome
# ==============================================================================


@pytest.mark.parametrize(
    "arquivo",
    [
        "ganchos.md",
        "algoritmo-linkedin.md",
        "vocabulario-ia.md",
        "headline-formulas.md",
    ],
)
def test_referencia_citada_nas_instrucoes_existe_no_repositorio(arquivo: str):
    """Os agentes chamam `ler_referencia` com estes nomes exatos.

    Renomear um arquivo sem atualizar a instrução do agente deixaria o agente
    pedindo um arquivo que não existe — falha silenciosa, difícil de notar.
    """
    caminho = Path(__file__).resolve().parents[1] / "referencias" / arquivo

    assert caminho.is_file(), f"referencias/{arquivo} sumiu, mas algum agente ainda pede por ele"
