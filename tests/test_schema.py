"""Modelo de dados do perfil.

O esquema é o contrato entre o importador e todos os agentes. O que se testa
aqui é o que quebra silenciosamente: campo obrigatório onde o export costuma
vir vazio, e os dois trechos com lógica de verdade.
"""

from __future__ import annotations

from linkedin_growth.perfil.esquema import Experiencia, Perfil


# ==============================================================================
# Tolerância a export incompleto
# ==============================================================================


def test_perfil_vazio_e_valido():
    """Nem todo export tem certificação, projeto ou idioma.

    Se algum campo virar obrigatório, o import quebra para quem não tem aquela
    seção — e o usuário fica sem perfil nenhum.
    """
    perfil = Perfil()

    assert perfil.nome is None
    assert perfil.experiencias == []
    assert perfil.skills == []


def test_perfil_ja_nasce_com_objetivo_e_temas_de_interesse():
    """São o piso do posicionamento: sem eles o agente escreve para ninguém."""
    perfil = Perfil()

    assert "engenharia de IA" in perfil.objetivo
    assert perfil.temas_de_interesse


def test_listas_do_perfil_nao_sao_compartilhadas_entre_instancias():
    """Erro clássico de default mutável: um perfil herdar a lista do outro."""
    primeiro = Perfil()
    segundo = Perfil()

    primeiro.skills.append("Python")

    assert segundo.skills == []


# ==============================================================================
# Lógica
# ==============================================================================


def test_experiencia_sem_data_de_fim_conta_como_atual():
    assert Experiencia(empresa="Acme", inicio="2024").atual is True


def test_experiencia_com_data_de_fim_nao_e_atual():
    assert Experiencia(empresa="Acme", inicio="2020", fim="2023").atual is False


def test_resumo_curto_junta_nome_e_headline():
    perfil = Perfil(nome="Gabriel", headline="Construindo agentes de IA")

    assert perfil.resumo_curto() == "Gabriel — Construindo agentes de IA"


def test_resumo_curto_sem_headline_devolve_so_o_nome():
    assert Perfil(nome="Gabriel").resumo_curto() == "Gabriel"


def test_resumo_curto_sem_nome_avisa_em_vez_de_devolver_vazio():
    """Aparece em log e cabeçalho de artefato: string vazia ali confunde."""
    assert Perfil().resumo_curto() == "(sem nome)"
