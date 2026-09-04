"""Leitura e estruturação dos dados reais do usuário."""

from linkedin_growth.perfil.contexto import carregar_perfil, contexto_do_perfil
from linkedin_growth.perfil.esquema import Perfil

__all__ = ["Perfil", "carregar_perfil", "contexto_do_perfil"]
