"""Fixtures compartilhadas.

Duas decisões que valem para a suíte inteira:

1. **Nenhum teste chama a API da Anthropic nem a do LinkedIn.** Tudo aqui é
   lógica pura ou I/O em disco temporário. Teste que gasta crédito não é
   rodado, e teste que não é rodado não serve para nada.

2. **As ferramentas dos agentes são decoradas com `@tool` do Agno**, então não
   são chamáveis direto: o objeto é uma `Function`, e o código Python original
   fica em `.entrypoint`. O helper `chamar` centraliza esse detalhe — se o Agno
   mudar a API, muda-se aqui e não em trinta testes.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

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
