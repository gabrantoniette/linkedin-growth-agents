"""A estratégia codificada.

`principios.py` não é código de apoio, é o produto: o comportamento do sistema
inteiro sai daqui. Estes testes protegem invariantes — não a redação exata das
regras, que deve mesmo evoluir, mas o fato de que certas regras continuam
chegando a todo agente.
"""

from __future__ import annotations

from linkedin_growth.agentes.principios import (
    HONESTIDADE,
    O_QUE_NAO_FAZER,
    PILARES,
    REGRAS_DE_ESCRITA,
    RUBRICA,
    instrucoes_base,
    instrucoes_de_conteudo,
)


# ==============================================================================
# O que todo agente recebe
# ==============================================================================


def test_instrucoes_base_carregam_todas_as_regras_de_honestidade():
    """A regra que nenhum agente pode quebrar tem que chegar a todos eles."""
    base = "\n".join(instrucoes_base())

    for regra in HONESTIDADE:
        assert regra in base


def test_instrucoes_base_pedem_resposta_em_portugues():
    assert any("português" in instrucao.lower() for instrucao in instrucoes_base())


def test_instrucoes_base_avisam_que_nao_ha_api_para_editar_o_perfil():
    """Sem isto o agente promete ao usuário uma automação que não existe."""
    base = "\n".join(instrucoes_base())

    assert "Não existe API para editar o perfil" in base


def test_instrucoes_de_conteudo_trazem_os_cinco_pilares():
    conteudo = "\n".join(instrucoes_de_conteudo())

    assert len(PILARES) == 5
    for pilar in PILARES:
        assert pilar in conteudo


def test_instrucoes_nao_vem_vazias():
    assert len(instrucoes_base()) > 5
    assert len(instrucoes_de_conteudo()) > 5


# ==============================================================================
# Regressões de regras específicas
# ==============================================================================
# Cada uma destas regras foi decidida com um motivo. O teste existe para que
# ninguém as reverta sem perceber.


def test_regra_de_hashtag_permite_no_maximo_tres():
    """Dado de 2026: 5+ hashtags é sinal de conta spam, não de alcance.

    A regra antiga pedia 'de 3 a 5'. Se voltar, este teste falha.
    """
    escrita = "\n".join(REGRAS_DE_ESCRITA)

    assert "0 a 3 hashtags" in escrita
    assert "3 a 5 hashtags" not in escrita


def test_existe_proibicao_explicita_de_travessao_longo():
    """É o tique mais reconhecível de texto gerado por IA."""
    escrita = "\n".join(REGRAS_DE_ESCRITA)

    assert "—" in escrita and "NUNCA use travessão" in escrita


def test_existe_regra_de_link_no_primeiro_comentario():
    escrita = "\n".join(REGRAS_DE_ESCRITA)

    assert "primeiro comentário" in escrita


def test_pedir_engajamento_continua_proibido():
    """Queima reputação com público técnico, e o LinkedIn suprime."""
    proibido = "\n".join(O_QUE_NAO_FAZER)

    assert "Não peça engajamento" in proibido


# ==============================================================================
# Rubrica do editor
# ==============================================================================


def test_rubrica_tem_os_sete_criterios():
    for criterio in (
        "GANCHO",
        "VERDADE",
        "PROVA",
        "ESPECIFICIDADE",
        "LEGIBILIDADE",
        "VOZ",
        "FECHAMENTO",
    ):
        assert criterio in RUBRICA


def test_rubrica_reprova_o_post_inteiro_quando_verdade_e_zero():
    """A honestidade é eliminatória, não um critério que se compensa com nota alta."""
    assert "isto reprova o post inteiro" in RUBRICA
    assert "Se VERDADE for 0, não entregue versão final" in RUBRICA
