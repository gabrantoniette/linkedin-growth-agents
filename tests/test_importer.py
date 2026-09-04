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
    _limpar_comentario,
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


# ==============================================================================
# Os dois defeitos que só apareceram com um export de verdade
# ==============================================================================
# Ambos falhavam em silêncio: o import terminava com "sucesso", a tabela de
# arquivos reconhecidos parecia certa, e o estrago só aparecia no texto que os
# agentes leem. É o tipo de bug que teste sintético não pega — este bloco existe
# para que não volte.


def test_arquivo_com_id_do_membro_no_nome_e_reconhecido(tmp_path: Path):
    """`Shares_1109184680.csv` é o nome real; `Shares.csv` não existe no export.

    O LinkedIn sufixa parte dos arquivos com o id numérico da conta. Sem cortar
    o sufixo, os posts antigos são ignorados, o `voz.md` não é gerado, e todo
    agente que escreve passa a usar tom genérico de LLM — sem nenhum aviso de
    que a amostra de voz do usuário ficou de fora.
    """
    (tmp_path / "Shares_1109184680.csv").write_text(
        "Date,ShareCommentary\n2026-01-01,texto\n", encoding="utf-8"
    )

    reconhecidos, ignorados = _mapear_arquivos(tmp_path)

    assert "posts" in reconhecidos
    assert reconhecidos["posts"].name == "Shares_1109184680.csv"
    assert ignorados == []


def test_sufixo_numerico_nao_transforma_arquivo_desconhecido_em_conhecido(
    tmp_path: Path,
):
    """Cortar o sufixo não pode virar um casamento frouxo.

    `Comments_1109184680.csv` continua ignorado — o corte remove o id, não
    aproxima nomes diferentes.
    """
    (tmp_path / "Comments_1109184680.csv").write_text("a,b\n1,2\n", encoding="utf-8")

    reconhecidos, ignorados = _mapear_arquivos(tmp_path)

    assert reconhecidos == {}
    assert [caminho.name for caminho in ignorados] == ["Comments_1109184680.csv"]


def test_campo_multilinha_entre_aspas_chega_inteiro(tmp_path: Path):
    """O 'Sobre', a descrição de cada cargo e o texto dos posts são multilinha.

    Quebrar o arquivo com `splitlines()` antes do `csv.reader` corta dentro do
    campo: cada parágrafo vira uma linha nova do CSV e o texto chega
    embaralhado. O leitor precisa receber o arquivo inteiro.
    """
    (tmp_path / "Positions.csv").write_text(
        'Company Name,Title,Description\n'
        'Acme,Dev,"Primeira linha.\n\nSegunda linha.\n\nTerceira."\n',
        encoding="utf-8",
    )

    linhas = _linhas_do_csv(tmp_path / "Positions.csv", ["Company Name", "Title"])

    assert len(linhas) == 1, "o campo multilinha não pode virar três registros"
    assert linhas[0]["Description"] == "Primeira linha.\n\nSegunda linha.\n\nTerceira."


def test_quebra_de_paragrafo_do_export_vira_paragrafo_de_verdade():
    """No `Shares.csv` cada quebra de parágrafo do post vem como aspas-newline-aspas.

    Sem desfazer, o `voz.md` fica uma parede de aspas — justamente o arquivo
    que deveria ensinar os agentes a escrever como o usuário.
    """
    bruto = 'Três planilhas. Uma pergunta:"\n""Quantos ainda temos?""\n""\n"E ninguém sabe.'

    assert _limpar_comentario(bruto) == (
        "Três planilhas. Uma pergunta:\n\n"
        '"Quantos ainda temos?"\n\n'
        "E ninguém sabe."
    )


def test_aspas_de_verdade_no_meio_da_frase_sobrevivem():
    """O padrão exige a quebra de linha entre as aspas — citação inline fica de pé."""
    assert _limpar_comentario('Ele disse "não" e saiu.') == 'Ele disse "não" e saiu.'
