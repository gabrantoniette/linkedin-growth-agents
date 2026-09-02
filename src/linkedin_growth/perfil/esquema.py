"""Modelo de dados do perfil.

Este é o contrato entre o importador (que lê os CSVs do LinkedIn) e todos os
agentes (que leem o perfil já estruturado). Tudo é opcional porque o export do
LinkedIn varia — nem todo mundo tem certificações, projetos ou idiomas.
"""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class Experiencia(BaseModel):
    empresa: Optional[str] = None
    cargo: Optional[str] = None
    descricao: Optional[str] = None
    local: Optional[str] = None
    inicio: Optional[str] = None
    fim: Optional[str] = None

    @property
    def atual(self) -> bool:
        return not self.fim


class Formacao(BaseModel):
    instituicao: Optional[str] = None
    curso: Optional[str] = None
    grau: Optional[str] = None
    descricao: Optional[str] = None
    inicio: Optional[str] = None
    fim: Optional[str] = None


class Certificacao(BaseModel):
    nome: Optional[str] = None
    emissor: Optional[str] = None
    url: Optional[str] = None
    inicio: Optional[str] = None
    fim: Optional[str] = None


class Projeto(BaseModel):
    titulo: Optional[str] = None
    descricao: Optional[str] = None
    url: Optional[str] = None
    inicio: Optional[str] = None
    fim: Optional[str] = None


class Idioma(BaseModel):
    nome: Optional[str] = None
    proficiencia: Optional[str] = None


class PostAntigo(BaseModel):
    """Post publicado no passado. Serve para o sistema aprender a voz do usuário."""

    data: Optional[str] = None
    texto: Optional[str] = None
    link: Optional[str] = None


class Perfil(BaseModel):
    """Retrato completo do usuário. Fonte de verdade de todos os agentes."""

    # --- identidade -----------------------------------------------------------
    nome: Optional[str] = None
    headline: Optional[str] = None
    sobre: Optional[str] = None
    setor: Optional[str] = None
    localizacao: Optional[str] = None
    sites: list[str] = Field(default_factory=list)

    # --- histórico ------------------------------------------------------------
    experiencias: list[Experiencia] = Field(default_factory=list)
    formacoes: list[Formacao] = Field(default_factory=list)
    certificacoes: list[Certificacao] = Field(default_factory=list)
    projetos: list[Projeto] = Field(default_factory=list)
    idiomas: list[Idioma] = Field(default_factory=list)
    skills: list[str] = Field(default_factory=list)

    # --- histórico de conteúdo ------------------------------------------------
    posts_antigos: list[PostAntigo] = Field(default_factory=list)

    # --- objetivo (preenchido à mão no YAML, não vem do export) ---------------
    objetivo: str = Field(
        default=(
            "Migrar para engenharia de IA. Sem experiência profissional na área "
            "ainda; estou aprendendo e construindo projetos em público."
        ),
        description="Para onde você quer ir. Editável à mão no perfil.yaml.",
    )
    temas_de_interesse: list[str] = Field(
        default_factory=lambda: [
            "agentes de IA",
            "LLMs",
            "RAG",
            "Python",
            "engenharia de prompt",
        ]
    )

    def resumo_curto(self) -> str:
        """Uma linha para logs e cabeçalhos de artefato."""
        partes = [self.nome or "(sem nome)"]
        if self.headline:
            partes.append(self.headline)
        return " — ".join(partes)
