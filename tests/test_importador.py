"""Leitura do export de dados do LinkedIn.

O export é hostil: vem em inglês mesmo em conta em português, muda de nome de
coluna entre versões, e alguns arquivos trazem um preâmbulo de aviso antes do
cabeçalho de verdade. Estes testes fixam o comportamento que absorve essa
bagunça — se ele quebrar, o perfil do usuário entra vazio e todos os agentes
passam a escrever sobre ninguém.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from linkedin_growth.perfil.importador import (
    _linhas_do_csv,
    _mapear_arquivos,
    _normalizar,
    _valor,
)


# ==============================================================================
# Normalização de nomes
# ==============================================================================


@pytest.mark.parametrize(
    ("entrada", "esperado"),
    [
        ("Company Name", "companyname"),
        ("First Name", "firstname"),
        ("  ESPAÇO  ", "espao"),
        ("Formação", "formao"),
        ("já-normalizado", "jnormalizado"),
    ],
)
def test_normalizar_reduz_a_letras_e_numeros_minusculos(entrada: str, esperado: str):
    """Acento some junto: é o que permite casar coluna em pt e em en."""
    assert _normalizar(entrada) == esperado


# ==============================================================================
# Busca de valor por sinônimo de coluna
# ==============================================================================


def test_valor_encontra_a_coluna_pelo_sinonimo():
    linha = {"Company Name": "Acme", "Title": "Dev"}

    assert _valor(linha, "company name") == "Acme"


def test_valor_aceita_grafias_diferentes_do_mesmo_sinonimo():
    """'Company Name', 'companyname' e 'COMPANY  NAME' são a mesma coluna."""
    linha = {"COMPANY  NAME": "Acme"}

    assert _valor(linha, "Company Name") == "Acme"


def test_valor_ignora_celula_vazia_e_devolve_none():
    assert _valor({"Title": "   "}, "title") is None


def test_valor_com_coluna_ausente_devolve_none():
    assert _valor({"Outra": "x"}, "title") is None


def test_valor_usa_o_primeiro_sinonimo_com_conteudo():
    linha = {"Title": "", "Position": "Engenheiro"}

    assert _valor(linha, "title", "position") == "Engenheiro"


# ==============================================================================
# Leitura de CSV
# ==============================================================================


def test_linhas_do_csv_le_cabecalho_na_primeira_linha(tmp_path: Path):
    arquivo = tmp_path / "Positions.csv"
    arquivo.write_text("Company Name,Title\nAcme,Dev\n", encoding="utf-8")

    linhas = _linhas_do_csv(arquivo, ["Company Name"])

    assert linhas == [{"Company Name": "Acme", "Title": "Dev"}]


def test_linhas_do_csv_pula_o_preambulo_de_aviso_do_linkedin(tmp_path: Path):
    """Connections.csv é o caso clássico: três linhas de aviso antes do cabeçalho."""
    arquivo = tmp_path / "Connections.csv"
    arquivo.write_text(
        'Notes:\n"Aviso do LinkedIn sobre os dados"\n\n'
        "First Name,Last Name,Company\nGabriel,Antoniette,Acme\n",
        encoding="utf-8",
    )

    linhas = _linhas_do_csv(arquivo, ["First Name", "Company"])

    assert linhas == [{"First Name": "Gabriel", "Last Name": "Antoniette", "Company": "Acme"}]


def test_linhas_do_csv_descarta_linhas_totalmente_vazias(tmp_path: Path):
    arquivo = tmp_path / "Skills.csv"
    arquivo.write_text("Name\nPython\n\n\nAgno\n", encoding="utf-8")

    linhas = _linhas_do_csv(arquivo, ["Name"])

    assert [linha["Name"] for linha in linhas] == ["Python", "Agno"]


def test_linhas_do_csv_com_arquivo_inexistente_devolve_lista_vazia(tmp_path: Path):
    """Export incompleto é normal — nem todo mundo tem certificação ou projeto."""
    assert _linhas_do_csv(tmp_path / "NaoExiste.csv", ["Name"]) == []


def test_linhas_do_csv_le_arquivo_com_bom(tmp_path: Path):
    """O LinkedIn entrega alguns CSVs em UTF-8 com BOM."""
    arquivo = tmp_path / "Profile.csv"
    arquivo.write_text("﻿First Name,Headline\nGabriel,Engenheiro\n", encoding="utf-8")

    linhas = _linhas_do_csv(arquivo, ["First Name"])

    assert linhas == [{"First Name": "Gabriel", "Headline": "Engenheiro"}]


# ==============================================================================
# Mapeamento de arquivos do export
# ==============================================================================


def test_mapear_arquivos_reconhece_os_csvs_conhecidos(tmp_path: Path):
    for nome in ("Positions.csv", "Education.csv", "Skills.csv"):
        (tmp_path / nome).write_text("a,b\n1,2\n", encoding="utf-8")

    reconhecidos, ignorados = _mapear_arquivos(tmp_path)

    assert set(reconhecidos) == {"experiencias", "formacoes", "skills"}
    assert ignorados == []


def test_mapear_arquivos_manda_desconhecido_para_ignorados(tmp_path: Path):
    (tmp_path / "Connections.csv").write_text("a\n1\n", encoding="utf-8")

    reconhecidos, ignorados = _mapear_arquivos(tmp_path)

    assert reconhecidos == {}
    assert [caminho.name for caminho in ignorados] == ["Connections.csv"]


def test_mapear_arquivos_encontra_csv_em_subpasta(tmp_path: Path):
    sub = tmp_path / "Basic_LinkedInDataExport"
    sub.mkdir()
    (sub / "Positions.csv").write_text("a\n1\n", encoding="utf-8")

    reconhecidos, _ = _mapear_arquivos(tmp_path)

    assert "experiencias" in reconhecidos
