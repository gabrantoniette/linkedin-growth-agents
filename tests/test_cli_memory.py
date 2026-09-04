"""O comando `linkedin memoria` — a janela do usuário para o que o sistema guarda.

Memória que não dá para inspecionar não dá para confiar. Se um agente começar a
repetir uma bobagem, é por este comando que se descobre de onde veio e é por
ele que se apaga; então ele precisa funcionar mesmo nos casos chatos: banco
vazio, id abreviado, prefixo ambíguo, id que não existe.
"""

from __future__ import annotations

import pytest
from agno.db.schemas.memory import UserMemory
from typer.testing import CliRunner

from linkedin_growth import config
from linkedin_growth.cli import app


@pytest.fixture
def executar(banco_temp, sem_api):
    """Roda um comando da CLI e devolve o resultado."""
    runner = CliRunner()

    def rodar(*argumentos: str, resposta: str = ""):
        return runner.invoke(app, ["memoria", *argumentos], input=resposta)

    return rodar


def texto(resultado) -> str:
    """A saída com o espaçamento normalizado.

    A tabela do Rich quebra linha para caber em 80 colunas, então comparar com
    a frase original falharia por causa da moldura, não do conteúdo.
    """
    return " ".join(resultado.output.split())


def gravar(*lembrancas: str, ids: list[str] | None = None) -> list[str]:
    """Planta memórias no banco de teste e devolve os ids."""
    gerente = config.memoria()
    return [
        gerente.add_user_memory(
            UserMemory(
                memory=lembranca,
                topics=["voz"],
                memory_id=ids[indice] if ids else None,
            ),
            user_id=config.USUARIO_ID,
        )
        for indice, lembranca in enumerate(lembrancas)
    ]


def test_banco_vazio_explica_como_encher(executar):
    """O primeiro dia de uso é este: nada guardado, e o comando ensina o caminho."""
    resultado = executar()

    assert resultado.exit_code == 0
    assert "ainda não lembra de nada" in resultado.output
    assert "linkedin chat" in resultado.output


def test_lista_o_que_o_sistema_lembra(executar):
    # Frase curta de propósito: numa tabela de quatro colunas em 80 caracteres,
    # uma lembrança longa quebra em duas linhas e a moldura entra no meio dela.
    # O que se testa aqui é que a linha aparece, não como o Rich a distribui.
    (identificador,) = gravar("odeia a palavra jornada")

    resultado = executar()

    assert resultado.exit_code == 0
    assert "odeia a palavra jornada" in texto(resultado)
    assert identificador[:8] in texto(resultado), "o id abreviado é o que se copia"
    assert "voz" in texto(resultado)


def test_esquecer_aceita_o_id_abreviado_que_a_tabela_mostra(executar):
    """A tabela corta o id em oito caracteres; o comando tem que aceitar isso.

    Sem isto o usuário copiaria o que vê na tela e receberia "não existe" —
    a pior forma de uma ferramenta falhar.
    """
    (identificador,) = gravar("Gabriel odeia a palavra jornada")

    resultado = executar("--esquecer", identificador[:8])

    assert resultado.exit_code == 0
    assert "Esquecido" in resultado.output
    assert config.memoria().get_user_memories(user_id=config.USUARIO_ID) == []


def test_prefixo_ambiguo_nao_apaga_nada(executar):
    """Na dúvida entre duas memórias, o comando para em vez de escolher."""
    gravar("primeira lembrança", "segunda lembrança", ids=["abc-1", "abc-2"])

    resultado = executar("--esquecer", "abc")

    assert resultado.exit_code == 1
    assert "Use mais caracteres" in resultado.output
    assert len(config.memoria().get_user_memories(user_id=config.USUARIO_ID)) == 2


def test_id_inexistente_avisa_em_vez_de_falhar_calado(executar):
    gravar("uma lembrança qualquer")

    resultado = executar("--esquecer", "nao-existe")

    assert resultado.exit_code == 1
    assert "Não existe memória" in resultado.output
    assert len(config.memoria().get_user_memories(user_id=config.USUARIO_ID)) == 1


def test_limpar_exige_confirmacao_e_recusa_apaga_nada(executar):
    """Apagar tudo é irreversível: o padrão do prompt é 'não'."""
    gravar("uma lembrança qualquer")

    resultado = executar("--limpar", resposta="n\n")

    assert resultado.exit_code == 0
    assert "Cancelado" in resultado.output
    assert len(config.memoria().get_user_memories(user_id=config.USUARIO_ID)) == 1
