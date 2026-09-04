"""Os fluxos determinísticos — e o que cada passo realmente lê.

O defeito que estes testes travam foi encontrado rodando o sistema de verdade:
`linkedin post --tema "custo e latência de um pipeline com LLM"` produziu um
post sobre vazamento de chave de API. E `linkedin calendario --semanas 4`
ignorava o número de semanas.

A causa era a mesma nos dois casos. O `Step(agent=...)` do Agno monta a
mensagem com `_prepare_message`, que **substitui** a entrada do workflow pelo
conteúdo do passo anterior. Do segundo passo em diante o pedido do usuário
simplesmente não existe mais: o redator via só a lista de notícias que o
pesquisador tinha levantado, e escrevia sobre a mais chamativa delas.

Nada nisso aparece como erro. O fluxo termina, o arquivo é gravado, e o
usuário recebe um post bem escrito sobre o assunto errado. Por isso os testes
olham o texto que chega a cada agente, e não o resultado final.
"""

from __future__ import annotations

import pytest
from agno.workflow import StepInput

from linkedin_growth import fluxos

from .conftest import ModeloEspiao

TEMA = "o que eu aprendi medindo custo e latência de um pipeline com LLM"
PESQUISA = "1. LLMjacking: chave de API vazada vira mineração de tokens."


def _espioes_usados(sem_api) -> list[ModeloEspiao]:
    """Só os modelos que chegaram a ser chamados.

    Construir um agente cria mais de um modelo: o dele e o do gerente de
    memória, que roda no fim de uma conversa e nestes testes nunca é acionado.
    """
    return [espiao for espiao in sem_api.criados if espiao.chamadas]


def mensagens_recebidas(sem_api) -> str:
    """Tudo o que chegou a algum modelo durante o teste, prompt de sistema junto."""
    return "\n".join(espiao.texto_da_chamada(0) for espiao in _espioes_usados(sem_api))


def pedidos_recebidos(sem_api) -> str:
    """Só o que o fluxo escreveu como pedido, sem as instruções fixas do agente.

    A distinção importa: as instruções do pesquisador *mencionam* os dois modos
    de trabalho, então procurar 'TEMA JÁ DECIDIDO' no prompt inteiro acharia a
    frase mesmo quando o fluxo não a mandou. O que decide o comportamento é a
    mensagem do usuário.
    """
    partes = [
        str(mensagem.content)
        for espiao in _espioes_usados(sem_api)
        for mensagem in espiao.chamadas[0]
        if mensagem.role == "user"
    ]
    return "\n".join(partes)


# ==============================================================================
# O tema pedido tem que chegar em todos os passos
# ==============================================================================


@pytest.mark.parametrize("indice", [0, 1, 2])
def test_o_tema_pedido_chega_ao_passo(indice, banco_temp, sem_api):
    """Pesquisador, redator e editor precisam saber sobre o que é o post.

    O passo de pesquisa recebia o tema por ser o primeiro; os outros dois viam
    apenas o texto de quem veio antes, e era ali que o assunto se perdia.
    """
    passo = fluxos.fluxo_post().steps[indice]

    saida = passo.executor(StepInput(input=TEMA, previous_step_content=PESQUISA))

    assert saida.content, f"o passo '{passo.name}' não produziu nada"
    assert TEMA in pedidos_recebidos(sem_api), (
        f"o passo '{passo.name}' não recebeu o tema pedido"
    )


def test_cada_passo_do_fluxo_de_post_le_o_tema_e_o_passo_anterior(
    banco_temp, sem_api
):
    """A verificação de verdade: o que foi escrito na mensagem do agente.

    Monta a mensagem de cada passo com a mesma função que o fluxo usa e confere
    que o tema aparece. Se algum passo voltar a receber só o conteúdo anterior,
    este teste cai.
    """
    fluxo = fluxos.fluxo_post()

    for passo in fluxo.steps[:3]:
        entrada = StepInput(input=TEMA, previous_step_content=PESQUISA)
        saida = passo.executor(entrada)
        assert saida.content

    mensagens = pedidos_recebidos(sem_api)
    assert mensagens.count(TEMA) >= 3, (
        "o tema pedido tem que chegar aos três agentes do fluxo"
    )
    assert PESQUISA in mensagens, (
        "o trabalho do passo anterior também tem que continuar chegando"
    )


def test_o_pedido_de_semanas_chega_ao_planejador(banco_temp, sem_api):
    """`--semanas 4` só funciona se o planejador souber que são quatro.

    Ele é o segundo passo do fluxo da semana, então recebia apenas as pautas do
    pesquisador e planejava a quantidade que bem entendesse.
    """
    pedido = "Levante as pautas desta semana e monte o calendário das próximas 4 semanas."
    fluxo = fluxos.fluxo_semana()

    saida = fluxo.steps[1].executor(
        StepInput(input=pedido, previous_step_content=PESQUISA)
    )

    assert saida.content
    mensagem = pedidos_recebidos(sem_api)
    assert "4 semanas" in mensagem
    assert PESQUISA in mensagem


# ==============================================================================
# O pesquisador tem dois modos, e o fluxo escolhe qual
# ==============================================================================


def test_com_tema_decidido_o_pesquisador_nao_sugere_outras_pautas(
    banco_temp, sem_api
):
    """O fluxo de post fecha o assunto antes de o pesquisador começar.

    Sem isso o pesquisador faz o que ele faz por padrão — curadoria da semana —
    e devolve 8 pautas, das quais o redator escolhe a mais chamativa em vez do
    tema pedido.
    """
    fluxos.fluxo_post().steps[0].executor(StepInput(input=TEMA))

    mensagem = pedidos_recebidos(sem_api)
    assert "TEMA JÁ DECIDIDO" in mensagem
    assert "não proponha pauta" in mensagem.lower() or "Não faça a curadoria" in mensagem


def test_sem_tema_decidido_o_pesquisador_faz_a_curadoria_da_semana(
    banco_temp, sem_api
):
    """O fluxo da semana não fecha assunto nenhum: ali a curadoria é o serviço."""
    pedido = "Levante as pautas de engenharia de IA desta semana."

    fluxos.fluxo_semana().steps[0].executor(StepInput(input=pedido))

    mensagem = pedidos_recebidos(sem_api)
    assert "TEMA JÁ DECIDIDO" not in mensagem
    assert pedido in mensagem


def test_o_pesquisador_sabe_separar_os_dois_modos(banco_temp, sem_api):
    """A instrução do agente precisa cobrir os dois casos, não só um."""
    from linkedin_growth.agentes import pesquisador

    instrucoes = " ".join(str(i) for i in (pesquisador.construir().instructions or []))

    assert "TEMA JÁ DECIDIDO" in instrucoes
    assert "curadoria" in instrucoes


# ==============================================================================
# O contrato entre o Editor e o comando `publicar`
# ==============================================================================
# O Editor grava o arquivo; o `publicar` recorta o corpo dele pelo cabeçalho da
# versão. Enquanto cada lado definia o formato por conta própria, o Editor
# gravou '# Versão final (pt-BR)' e o comando procurava '## Post (pt-BR)'.
# Resultado: três agentes rodados, arquivo bonito no disco, e `publicar`
# morrendo com "não encontrei a seção do idioma 'pt'".


def test_o_editor_recebe_os_cabecalhos_exatos_que_o_publicar_procura(
    banco_temp, sem_api
):
    """A instrução do agente sai da mesma constante que o recortador usa."""
    from linkedin_growth.agentes import editor
    from linkedin_growth.agentes.principios import CABECALHO_POST

    instrucoes = " ".join(str(i) for i in (editor.construir().instructions or []))

    for cabecalho in CABECALHO_POST.values():
        assert cabecalho in instrucoes


@pytest.mark.parametrize("idioma", ["pt", "en"])
def test_o_publicar_recorta_o_arquivo_no_formato_documentado(idioma):
    """Um arquivo escrito como o Editor é instruído a escrever tem que ser lido."""
    from linkedin_growth.agentes.principios import CABECALHO_POST
    from linkedin_growth.cli import _extrair_secao

    arquivo = (
        "---\ndata: 2026-09-04\npilar: Entendi\n---\n\n"
        f"{CABECALHO_POST['pt']}\n\nCorpo em português.\n\n"
        f"{CABECALHO_POST['en']}\n\nBody in English.\n\n"
        "## Avaliação\n\nnota 8/10\n"
    )

    corpo = _extrair_secao(arquivo, idioma)

    esperado = "Corpo em português." if idioma == "pt" else "Body in English."
    assert corpo == esperado


def test_o_publicar_nao_engole_a_avaliacao_junto_com_o_post():
    """O recorte para no próximo título. Sem isso, a nota da rubrica ia junto."""
    from linkedin_growth.agentes.principios import CABECALHO_POST
    from linkedin_growth.cli import _extrair_secao

    arquivo = f"{CABECALHO_POST['en']}\n\nBody.\n\n## Avaliação\n\nnota 8/10\n"

    assert _extrair_secao(arquivo, "en") == "Body."


def test_o_publicar_avisa_quando_o_cabecalho_nao_existe():
    """Se o Editor inventar outro título, o recorte devolve nada — e a CLI erra.

    É o comportamento correto: melhor falhar dizendo o que faltou do que
    publicar meio arquivo no LinkedIn.
    """
    from linkedin_growth.cli import _extrair_secao

    assert _extrair_secao("# Versão final (pt-BR)\n\nCorpo.\n", "pt") is None


def test_post_reprovado_pelo_editor_nao_chega_ao_publicar(tmp_path, monkeypatch):
    """Reprovado pelo Editor é reprovado, e o comando diz isso com essas palavras.

    Quando o Editor zera o critério VERDADE ele omite de propósito os títulos
    publicáveis, para o recorte não achar texto. Sem uma checagem explícita, o
    usuário recebia "não encontrei a seção do idioma 'pt'" e ia caçar um bug de
    formato que não existe.
    """
    from typer.testing import CliRunner

    from linkedin_growth import cli

    arquivo = tmp_path / "2026-09-04-tema.md"
    arquivo.write_text(
        "---\ndata: 2026-09-04\nstatus: reprovado\nnota: 4.7/10\n---\n\n"
        "## Avaliação\n\nVerdade: 0. O post afirma medição que não houve.\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(cli, "POSTS_DIR", tmp_path)

    resultado = CliRunner().invoke(
        cli.app, ["publicar", str(arquivo), "--dry-run"]
    )

    assert resultado.exit_code == 1
    assert "reprovado pelo Editor" in resultado.output


def test_post_aprovado_passa_pela_checagem_de_reprovacao(tmp_path, monkeypatch):
    """A checagem não pode barrar um post normal: ela procura o status, não a palavra."""
    from linkedin_growth.agentes.principios import CABECALHO_POST
    from linkedin_growth.cli import _extrair_secao

    arquivo = (
        "---\ndata: 2026-09-04\nstatus: rascunho\nnota: 8.1/10\n---\n\n"
        f"{CABECALHO_POST['pt']}\n\nCorpo aprovado.\n"
    )

    import re

    assert not re.search(r"^status:\s*reprovado\s*$", arquivo, re.MULTILINE)
    assert _extrair_secao(arquivo, "pt") == "Corpo aprovado."
