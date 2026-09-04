"""Importa o export de dados do LinkedIn para um `Perfil` estruturado.

Por que este arquivo é tolerante em vez de direto ao ponto: o LinkedIn **não
documenta publicamente** os nomes das colunas do arquivo de export, e eles mudam
com o tempo e com o idioma da conta. Um parser que exigisse `"Company Name"`
exato quebraria em silêncio.

Então a estratégia é:

1. varrer todo `.csv` da pasta e casar o *arquivo* por nome normalizado;
2. casar cada *coluna* por lista de sinônimos, ignorando caixa e pontuação;
3. pular as linhas de aviso que o LinkedIn coloca antes do cabeçalho real;
4. devolver um relatório do que foi reconhecido e do que foi ignorado.

O `perfil.yaml` gerado é para ser lido e corrigido à mão. Ele, e não o CSV, é a
fonte de verdade dos agentes.
"""

from __future__ import annotations

import csv
import io
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable

import yaml

from linkedin_growth.config import EXPORT_DIR, PERFIL_DIR, PERFIL_YAML, VOZ_MD
from linkedin_growth.perfil.esquema import (
    Certificacao,
    Experiencia,
    Formacao,
    Idioma,
    Perfil,
    PostAntigo,
    Projeto,
)

# Quantos posts antigos guardar como amostra de voz. O suficiente para o modelo
# pegar o tom sem inchar o contexto de todo agente.
MAX_POSTS_VOZ = 25


# ==============================================================================
# Normalização
# ==============================================================================


def _normalizar(texto: str) -> str:
    """'Company Name' -> 'companyname'. Base de toda comparação deste módulo."""
    return re.sub(r"[^a-z0-9]", "", texto.strip().lower())


def _valor(linha: dict[str, str], *sinonimos: str) -> str | None:
    """Primeiro valor não vazio entre as colunas cujo nome casa com um sinônimo."""
    alvos = {_normalizar(s) for s in sinonimos}
    for chave, valor in linha.items():
        if chave is None:
            continue
        if _normalizar(chave) in alvos:
            limpo = (valor or "").strip()
            if limpo:
                return limpo
    return None


# ==============================================================================
# Leitura de CSV
# ==============================================================================


def _linhas_do_csv(caminho: Path, colunas_esperadas: Iterable[str]) -> list[dict[str, str]]:
    """Lê um CSV do export, pulando o preâmbulo que o LinkedIn às vezes insere.

    Alguns arquivos (Connections.csv é o caso clássico) começam com linhas de
    aviso antes do cabeçalho. Procuramos a primeira linha que contenha alguma
    das colunas esperadas e tratamos ela como cabeçalho.

    O texto vai para o `csv.reader` inteiro, dentro de um `StringIO`, e não
    quebrado com `splitlines()`. A diferença importa: o 'Sobre' do perfil, a
    descrição de cada experiência e o texto dos posts são campos multilinha
    entre aspas, e `splitlines()` corta no meio deles — o leitor então
    interpreta cada parágrafo como uma nova linha do CSV e o texto chega
    embaralhado, cheio de aspas soltas e sem os parágrafos originais.
    """
    esperadas = {_normalizar(c) for c in colunas_esperadas}

    try:
        bruto = caminho.read_text(encoding="utf-8-sig", errors="replace")
    except OSError:
        return []

    todas = list(csv.reader(io.StringIO(bruto)))
    if not todas:
        return []

    indice_cabecalho = 0
    for i, linha in enumerate(todas[:10]):
        if any(_normalizar(celula) in esperadas for celula in linha):
            indice_cabecalho = i
            break

    cabecalho = todas[indice_cabecalho]
    registros: list[dict[str, str]] = []
    for linha in todas[indice_cabecalho + 1 :]:
        if not any(celula.strip() for celula in linha):
            continue
        registro = dict(zip(cabecalho, linha))
        registros.append(registro)
    return registros


@dataclass
class Relatorio:
    """O que o importador entendeu do export. Impresso para o usuário conferir."""

    arquivos_encontrados: list[str] = field(default_factory=list)
    arquivos_ignorados: list[str] = field(default_factory=list)
    contagens: dict[str, int] = field(default_factory=dict)
    avisos: list[str] = field(default_factory=list)


# Nome normalizado do arquivo -> rótulo interno. O export vem em inglês mesmo
# quando a conta é em português, mas aceitamos as duas grafias por segurança.
ARQUIVOS_CONHECIDOS: dict[str, str] = {
    "profile": "perfil",
    "positions": "experiencias",
    "education": "formacoes",
    "skills": "skills",
    "certifications": "certificacoes",
    "projects": "projetos",
    "languages": "idiomas",
    "shares": "posts",
    "richmediashares": "posts",
}


def _chave_do_arquivo(nome: str) -> str:
    """'Shares_1109184680' -> 'shares'.

    O LinkedIn sufixa parte dos arquivos do export com o id numérico do membro
    (Shares, Comments, Reactions, Votes...). Sem remover o sufixo,
    `Shares_1109184680.csv` não casa com 'shares' e os posts antigos são
    ignorados **em silêncio**: o `voz.md` não é gerado e o sistema inteiro passa
    a escrever com tom genérico de LLM, sem nada indicando o que faltou.

    O corte é feito antes de normalizar porque `_normalizar` come o underscore
    e deixaria 'shares1109184680' — indistinguível de um nome de arquivo real.
    """
    return _normalizar(re.sub(r"_\d{4,}$", "", nome.strip()))


def _mapear_arquivos(pasta: Path) -> tuple[dict[str, Path], list[Path]]:
    """Casa cada CSV da pasta com um rótulo conhecido."""
    reconhecidos: dict[str, Path] = {}
    ignorados: list[Path] = []
    for caminho in sorted(pasta.rglob("*.csv")):
        chave = _chave_do_arquivo(caminho.stem)
        rotulo = ARQUIVOS_CONHECIDOS.get(chave)
        if rotulo and rotulo not in reconhecidos:
            reconhecidos[rotulo] = caminho
        else:
            ignorados.append(caminho)
    return reconhecidos, ignorados


# ==============================================================================
# Extratores, um por seção
# ==============================================================================


def _extrair_identidade(linhas: list[dict[str, str]], perfil: Perfil) -> None:
    if not linhas:
        return
    linha = linhas[0]
    nome = " ".join(
        parte
        for parte in (
            _valor(linha, "First Name", "Nome"),
            _valor(linha, "Last Name", "Sobrenome"),
        )
        if parte
    )
    perfil.nome = nome or None
    perfil.headline = _valor(linha, "Headline", "Titulo", "Título")
    perfil.sobre = _valor(linha, "Summary", "Resumo", "About", "Sobre")
    perfil.setor = _valor(linha, "Industry", "Setor")
    perfil.localizacao = _valor(linha, "Geo Location", "Location", "Localizacao", "Localização")
    sites = _valor(linha, "Websites", "Sites")
    if sites:
        perfil.sites = [s.strip() for s in re.split(r"[,;]", sites) if s.strip()]


def _extrair_experiencias(linhas: list[dict[str, str]]) -> list[Experiencia]:
    return [
        Experiencia(
            empresa=_valor(linha, "Company Name", "Company", "Empresa"),
            cargo=_valor(linha, "Title", "Position", "Cargo"),
            descricao=_valor(linha, "Description", "Descricao", "Descrição"),
            local=_valor(linha, "Location", "Localizacao", "Localização"),
            inicio=_valor(linha, "Started On", "Start Date", "Data de inicio"),
            fim=_valor(linha, "Finished On", "End Date", "Data de termino"),
        )
        for linha in linhas
    ]


def _extrair_formacoes(linhas: list[dict[str, str]]) -> list[Formacao]:
    return [
        Formacao(
            instituicao=_valor(linha, "School Name", "School", "Instituicao", "Instituição"),
            curso=_valor(linha, "Activities", "Field Of Study", "Curso"),
            grau=_valor(linha, "Degree Name", "Degree", "Grau"),
            descricao=_valor(linha, "Notes", "Description", "Descricao", "Descrição"),
            inicio=_valor(linha, "Start Date", "Started On"),
            fim=_valor(linha, "End Date", "Finished On"),
        )
        for linha in linhas
    ]


def _extrair_certificacoes(linhas: list[dict[str, str]]) -> list[Certificacao]:
    return [
        Certificacao(
            nome=_valor(linha, "Name", "Nome"),
            emissor=_valor(linha, "Authority", "Issuer", "Emissor"),
            url=_valor(linha, "Url", "URL"),
            inicio=_valor(linha, "Started On", "Start Date"),
            fim=_valor(linha, "Finished On", "End Date"),
        )
        for linha in linhas
    ]


def _extrair_projetos(linhas: list[dict[str, str]]) -> list[Projeto]:
    return [
        Projeto(
            titulo=_valor(linha, "Title", "Name", "Titulo", "Título"),
            descricao=_valor(linha, "Description", "Descricao", "Descrição"),
            url=_valor(linha, "Url", "URL"),
            inicio=_valor(linha, "Started On", "Start Date"),
            fim=_valor(linha, "Finished On", "End Date"),
        )
        for linha in linhas
    ]


def _extrair_idiomas(linhas: list[dict[str, str]]) -> list[Idioma]:
    return [
        Idioma(
            nome=_valor(linha, "Name", "Language", "Idioma"),
            proficiencia=_valor(linha, "Proficiency", "Proficiencia", "Proficiência"),
        )
        for linha in linhas
    ]


def _extrair_skills(linhas: list[dict[str, str]]) -> list[str]:
    vistas: list[str] = []
    for linha in linhas:
        nome = _valor(linha, "Name", "Skill", "Nome")
        if nome and nome not in vistas:
            vistas.append(nome)
    return vistas


def _limpar_comentario(texto: str) -> str:
    """Desfaz a codificação de quebra de linha do export do LinkedIn.

    No `Shares.csv` cada quebra de parágrafo do post vira aspas + newline +
    aspas. Depois que o leitor de CSV faz o trabalho dele, o texto chega assim:

        ...à mesma pergunta:"\\n""Quantos ainda temos disso?""\\n""\\n"Provavelmente...

    Sem desfazer isso, o `voz.md` fica ilegível e os agentes leem a amostra de
    voz do usuário como uma parede de aspas — que é justamente o arquivo que
    deveria ensiná-los a escrever como ele.

    O padrão exige a quebra de linha entre as aspas, então aspas de verdade
    (uma citação dentro do post) continuam de pé.
    """
    limpo = re.sub(r'"[ \t]*\n[ \t]*"', "\n\n", texto)
    limpo = re.sub(r"\n{3,}", "\n\n", limpo)
    return limpo.strip().strip('"').strip()


def _extrair_posts(linhas: list[dict[str, str]]) -> list[PostAntigo]:
    posts: list[PostAntigo] = []
    for linha in linhas:
        texto = _valor(linha, "ShareCommentary", "Commentary", "Texto")
        if not texto:
            continue
        posts.append(
            PostAntigo(
                data=_valor(linha, "Date", "Data"),
                texto=_limpar_comentario(texto),
                link=_valor(linha, "ShareLink", "Link"),
            )
        )
    # Mais recentes primeiro: o export vem em ordem cronológica crescente.
    posts.reverse()
    return posts[:MAX_POSTS_VOZ]


# ==============================================================================
# Ponto de entrada
# ==============================================================================


def importar(pasta: Path | None = None) -> tuple[Perfil, Relatorio]:
    """Lê o export e devolve o perfil montado mais o relatório do que foi lido."""
    pasta = pasta or EXPORT_DIR
    relatorio = Relatorio()
    perfil = Perfil()

    if not pasta.exists():
        relatorio.avisos.append(f"A pasta {pasta} não existe.")
        return perfil, relatorio

    reconhecidos, ignorados = _mapear_arquivos(pasta)
    relatorio.arquivos_ignorados = [p.name for p in ignorados]

    if not reconhecidos:
        relatorio.avisos.append(
            f"Nenhum CSV conhecido em {pasta}. Descompacte o arquivo do export "
            "do LinkedIn dentro dessa pasta."
        )
        return perfil, relatorio

    leitores: dict[str, tuple[list[str], Any]] = {
        "perfil": (["First Name", "Headline", "Summary"], None),
        "experiencias": (["Company Name", "Title"], None),
        "formacoes": (["School Name", "Degree Name"], None),
        "certificacoes": (["Name", "Authority"], None),
        "projetos": (["Title", "Description"], None),
        "idiomas": (["Name", "Proficiency"], None),
        "skills": (["Name"], None),
        "posts": (["ShareCommentary", "Date"], None),
    }

    for rotulo, caminho in reconhecidos.items():
        colunas, _ = leitores.get(rotulo, ([], None))
        linhas = _linhas_do_csv(caminho, colunas)
        relatorio.arquivos_encontrados.append(f"{caminho.name} ({rotulo})")

        # A chave da contagem é sempre o rótulo, para o relatório conseguir
        # cruzar arquivo -> quantidade sem tradução no meio.
        if rotulo == "perfil":
            _extrair_identidade(linhas, perfil)
            relatorio.contagens["perfil"] = 1 if perfil.nome else 0
        elif rotulo == "experiencias":
            perfil.experiencias = _extrair_experiencias(linhas)
            relatorio.contagens["experiencias"] = len(perfil.experiencias)
        elif rotulo == "formacoes":
            perfil.formacoes = _extrair_formacoes(linhas)
            relatorio.contagens["formacoes"] = len(perfil.formacoes)
        elif rotulo == "certificacoes":
            perfil.certificacoes = _extrair_certificacoes(linhas)
            relatorio.contagens["certificacoes"] = len(perfil.certificacoes)
        elif rotulo == "projetos":
            perfil.projetos = _extrair_projetos(linhas)
            relatorio.contagens["projetos"] = len(perfil.projetos)
        elif rotulo == "idiomas":
            perfil.idiomas = _extrair_idiomas(linhas)
            relatorio.contagens["idiomas"] = len(perfil.idiomas)
        elif rotulo == "skills":
            perfil.skills = _extrair_skills(linhas)
            relatorio.contagens["skills"] = len(perfil.skills)
        elif rotulo == "posts":
            perfil.posts_antigos = _extrair_posts(linhas)
            relatorio.contagens["posts"] = len(perfil.posts_antigos)

    if not perfil.nome:
        relatorio.avisos.append(
            "Não consegui ler seu nome do Profile.csv. Preencha à mão no perfil.yaml."
        )
    if not perfil.experiencias:
        relatorio.avisos.append(
            "Nenhuma experiência importada. Se você tem histórico profissional, "
            "confira se Positions.csv veio no export."
        )

    return perfil, relatorio


def salvar(perfil: Perfil, *, preservar_edicoes: bool = True) -> Path:
    """Grava o perfil em `perfil/perfil.yaml`.

    Se já existir um YAML editado à mão, os campos que o export não fornece
    (`objetivo`, `temas_de_interesse`) são preservados — eles são a parte que o
    usuário escreve, e reimportar não pode apagá-la.
    """
    PERFIL_DIR.mkdir(parents=True, exist_ok=True)

    if preservar_edicoes and PERFIL_YAML.exists():
        try:
            anterior = yaml.safe_load(PERFIL_YAML.read_text(encoding="utf-8")) or {}
            if isinstance(anterior, dict):
                if anterior.get("objetivo"):
                    perfil.objetivo = anterior["objetivo"]
                if anterior.get("temas_de_interesse"):
                    perfil.temas_de_interesse = anterior["temas_de_interesse"]
        except yaml.YAMLError:
            pass  # YAML corrompido não pode impedir a reimportação

    dados = perfil.model_dump(mode="json", exclude={"posts_antigos"})
    cabecalho = (
        "# Perfil gerado a partir do export do LinkedIn.\n"
        "# Este arquivo é a FONTE DE VERDADE dos agentes — leia e corrija à mão.\n"
        "# 'objetivo' e 'temas_de_interesse' são seus: reimportar não os apaga.\n\n"
    )
    PERFIL_YAML.write_text(
        cabecalho + yaml.safe_dump(dados, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )
    return PERFIL_YAML


def salvar_voz(perfil: Perfil) -> Path | None:
    """Grava as amostras de escrita em `perfil/voz.md`.

    Os agentes leem este arquivo para escrever com o tom do usuário em vez do
    tom genérico de LLM. Sem posts antigos, o arquivo não é criado.
    """
    if not perfil.posts_antigos:
        return None

    PERFIL_DIR.mkdir(parents=True, exist_ok=True)
    partes = [
        "# Amostras da minha escrita",
        "",
        "Posts que eu já publiquei, extraídos do export do LinkedIn.",
        "Servem de referência de tom — não de conteúdo.",
        "",
    ]
    for post in perfil.posts_antigos:
        if post.data:
            partes.append(f"## {post.data}")
        partes.append("")
        partes.append(post.texto or "")
        partes.append("")
        partes.append("---")
        partes.append("")

    VOZ_MD.write_text("\n".join(partes), encoding="utf-8")
    return VOZ_MD
