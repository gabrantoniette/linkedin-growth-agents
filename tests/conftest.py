"""Fixtures compartilhadas.

Três decisões que valem para a suíte inteira:

1. **Nenhum teste chama a API da Anthropic nem a do LinkedIn.** Tudo aqui é
   lógica pura ou I/O em disco temporário. Teste que gasta crédito não é
   rodado, e teste que não é rodado não serve para nada.

2. **As ferramentas dos agentes são decoradas com `@tool` do Agno**, então não
   são chamáveis direto: o objeto é uma `Function`, e o código Python original
   fica em `.entrypoint`. O helper `chamar` centraliza esse detalhe — se o Agno
   mudar a API, muda-se aqui e não em trinta testes.

3. **Os testes de memória executam agentes de verdade**, com um `ModeloEspiao`
   no lugar do `Claude` e um banco descartável. É a única forma de responder
   "o agente lembra?": a resposta está nas mensagens que chegam ao modelo, e
   só executando dá para vê-las.
"""

from __future__ import annotations

import json
import sqlite3
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest
from agno.models.anthropic import Claude
from agno.models.message import Message
from agno.models.response import ModelResponse

from linkedin_growth import config, times
from linkedin_growth.agentes import (
    diagnostico,
    editor,
    estrategista,
    perfil_writer,
    pesquisador,
    planejador,
    publicador,
    redator,
)
from linkedin_growth.ferramentas import artefatos, referencias


def chamar(ferramenta: Any, *args: Any, **kwargs: Any) -> Any:
    """Executa uma ferramenta `@tool` do Agno como função Python comum."""
    return ferramenta.entrypoint(*args, **kwargs)


@pytest.fixture
def conteudo_temp(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Aponta `conteudo/` para uma pasta descartável.

    Sem isto, um teste de escrita sujaria a pasta real do usuário — e um teste
    de path traversal poderia gravar fora dela de verdade.
    """
    raiz = tmp_path / "conteudo"
    raiz.mkdir()
    monkeypatch.setattr(artefatos, "CONTEUDO_DIR", raiz)
    return raiz


@pytest.fixture
def referencias_temp(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Aponta `referencias/` para uma pasta descartável."""
    raiz = tmp_path / "referencias"
    raiz.mkdir()
    monkeypatch.setattr(referencias, "REFERENCIAS_DIR", raiz)
    return raiz


# ==============================================================================
# Infraestrutura para testar memória
# ==============================================================================
# Os testes de memória precisam de duas coisas que os outros não precisam:
# um modelo que não chame a API e um banco descartável. Ambos ficam aqui.


class ModeloEspiao(Claude):
    """Um `Claude` que não fala com a Anthropic e guarda o que recebeu.

    A pergunta "o agente lembra?" só se responde olhando as mensagens que
    chegam ao modelo — é ali que história, memórias e resumos aparecem, ou não.
    Este espião grava cada lista de mensagens em `chamadas` e devolve sempre a
    mesma resposta, sem tool call, para que a execução seja determinística.

    Herda de `Claude` de propósito: assim o objeto passa por todas as checagens
    que o Agno faz no modelo real (formatação de ferramentas, flags de
    structured output), e o que estamos testando continua sendo o caminho de
    verdade, não uma maquete dele.
    """

    def __init__(
        self,
        resposta: str = "resposta do espião",
        id_modelo: str | None = None,
        **kwargs: Any,
    ) -> None:
        # O id do modelo é preservado porque o sistema escolhe modelos
        # diferentes para trabalhos diferentes (Opus julga, Sonnet destila), e
        # há teste que verifica essa escolha.
        super().__init__(
            id=id_modelo or config.MODELO_PRINCIPAL,
            api_key="chave-de-teste",
            **kwargs,
        )
        self.resposta = resposta
        self.chamadas: list[list[Message]] = []

    # -- o único ponto de rede do modelo, substituído ---------------------
    def invoke(  # type: ignore[override]
        self, messages: list[Message], assistant_message: Message, **kwargs: Any
    ) -> ModelResponse:
        self.chamadas.append(list(messages))
        assistant_message.metrics.start_timer()
        assistant_message.metrics.stop_timer()
        return ModelResponse(role="assistant", content=self.resposta)

    # Nenhum teste usa async nem streaming. Se algum passar por aqui, é bug do
    # teste, e é melhor estourar do que tentar falar com a API de verdade.
    async def ainvoke(self, *args: Any, **kwargs: Any) -> ModelResponse:
        raise AssertionError("teste tentou chamar o modelo em modo async")

    def invoke_stream(self, *args: Any, **kwargs: Any) -> Any:
        raise AssertionError("teste tentou chamar o modelo em streaming")

    async def ainvoke_stream(self, *args: Any, **kwargs: Any) -> Any:
        raise AssertionError("teste tentou chamar o modelo em streaming")

    # -- leitura das mensagens capturadas ---------------------------------
    def texto_da_chamada(self, indice: int = -1) -> str:
        """Todas as mensagens de uma chamada concatenadas, para busca simples."""
        return "\n".join(str(m.content) for m in self.chamadas[indice])

    def papeis_da_chamada(self, indice: int = -1) -> list[str]:
        return [str(m.role) for m in self.chamadas[indice]]


class ModeloQueAnota(ModeloEspiao):
    """Um espião que, na primeira chamada, pede para gravar uma memória.

    O `MemoryManager` do Agno não escreve memória a partir de texto: ele dá ao
    modelo a ferramenta `add_memory` e grava o que o modelo mandar gravar. Para
    testar a escrita de ponta a ponta — e não só a leitura — o falso modelo
    precisa devolver essa chamada de ferramenta.

    Da segunda chamada em diante devolve texto, senão o laço de ferramentas do
    Agno nunca terminaria.

    Aviso para quem for estender: o Agno copia o modelo ao montar a execução,
    então `chamadas` deste objeto pode ficar vazio mesmo tendo funcionado. A
    verificação confiável é o banco.
    """

    def __init__(self, lembranca: str, topicos: list[str] | None = None) -> None:
        super().__init__()
        self.lembranca = lembranca
        self.topicos = topicos or []
        self.pedidos = 0

    def invoke(  # type: ignore[override]
        self, messages: list[Message], assistant_message: Message, **kwargs: Any
    ) -> ModelResponse:
        self.chamadas.append(list(messages))
        assistant_message.metrics.start_timer()
        assistant_message.metrics.stop_timer()
        self.pedidos += 1
        if self.pedidos > 1:
            return ModelResponse(role="assistant", content="pronto")
        return ModelResponse(
            role="assistant",
            tool_calls=[
                {
                    "id": "chamada-1",
                    "type": "function",
                    "function": {
                        "name": "add_memory",
                        "arguments": json.dumps(
                            {"memory": self.lembranca, "topics": self.topicos}
                        ),
                    },
                }
            ],
        )


def sessoes_gravadas(arquivo_db: Path) -> list[tuple]:
    """Lê `agno_sessions` direto no SQLite, sem passar pelo Agno.

    De propósito: se o teste perguntasse ao próprio Agno o que ele gravou,
    estaria confiando na peça que está sob teste.
    """
    conexao = sqlite3.connect(arquivo_db)
    try:
        return conexao.execute(
            "SELECT session_id, session_type, user_id FROM agno_sessions"
        ).fetchall()
    except sqlite3.OperationalError:
        return []
    finally:
        conexao.close()


def memorias_gravadas(arquivo_db: Path) -> list[tuple]:
    """Lê `agno_memories` direto no SQLite. Tabela ausente conta como vazia."""
    conexao = sqlite3.connect(arquivo_db)
    try:
        return conexao.execute(
            "SELECT memory, user_id FROM agno_memories"
        ).fetchall()
    except sqlite3.OperationalError:
        return []
    finally:
        conexao.close()


@pytest.fixture
def banco_temp(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Aponta o banco do sistema para um arquivo descartável.

    Sem isto, rodar a suíte poluiria o histórico real do usuário em
    `tmp/linkedin_growth.db` — e o teste passaria a depender do que já estava lá.
    """
    arquivo = tmp_path / "memoria_teste.db"
    monkeypatch.setattr(config, "TMP_DIR", tmp_path)
    monkeypatch.setattr(config, "DB_FILE", arquivo)
    monkeypatch.setattr(config, "_db", None)
    # O gerente de memória também é cacheado, e guarda uma referência ao banco.
    # Sem zerar, o segundo teste da sessão escreveria no banco do primeiro.
    monkeypatch.setattr(config, "_memoria", None)
    return arquivo


@pytest.fixture
def sem_api(monkeypatch: pytest.MonkeyPatch) -> Callable[..., ModeloEspiao]:
    """Troca o modelo real pelo espião em todos os módulos que constroem agentes.

    Os módulos fazem `from ...config import modelo`, então a função já está no
    namespace de cada um: não adianta trocar só em `config`.

    Devolve uma fábrica que também registra cada espião criado, para o teste
    poder inspecionar qualquer um deles.
    """
    criados: list[ModeloEspiao] = []

    def fabrica(id_modelo: str | None = None) -> ModeloEspiao:
        espiao = ModeloEspiao(id_modelo=id_modelo)
        criados.append(espiao)
        return espiao

    fabrica.criados = criados  # type: ignore[attr-defined]

    monkeypatch.setattr(config, "modelo", fabrica)
    monkeypatch.setattr(times, "modelo", fabrica)
    for modulo in (
        diagnostico,
        editor,
        estrategista,
        perfil_writer,
        pesquisador,
        planejador,
        publicador,
        redator,
    ):
        monkeypatch.setattr(modulo, "modelo", fabrica)

    return fabrica
