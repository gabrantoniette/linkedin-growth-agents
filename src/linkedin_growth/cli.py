"""Interface de linha de comando.

Cada comando é um passo do ciclo:

    importar -> diagnosticar -> perfil -> estrategia -> calendario
             -> post -> publicar -> metricas -> (volta para estrategia)

Rode `uv run linkedin --help` para ver tudo.
"""

from __future__ import annotations

import csv
import re
from datetime import date
from pathlib import Path
from typing import Annotated, Optional

import typer
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Confirm, Prompt
from rich.table import Table

from linkedin_growth.config import (
    CONTEUDO_DIR,
    EXPORT_DIR,
    MAX_TOKENS,
    METRICAS_CSV,
    PERFIL_YAML,
    POSTS_DIR,
    SESSAO_PADRAO,
    ConfiguracaoAusente,
    garantir_diretorios,
)

app = typer.Typer(
    add_completion=False,
    no_args_is_help=True,
    help="Sistema de relevância no LinkedIn para engenharia de IA.",
)
console = Console()


# ==============================================================================
# Utilidades
# ==============================================================================


def _erro(mensagem: str) -> None:
    console.print(Panel(mensagem, title="Erro", border_style="red"))
    raise typer.Exit(code=1)


def _avisar_se_truncou(saida) -> None:
    """Avisa quando a resposta bateu no teto de `max_tokens`.

    Isto já custou caro uma vez: o agente escreveu o relatório inteiro, a
    resposta foi cortada exatamente no limite, a chamada de `salvar_artefato`
    nunca aconteceu — e o texto na tela terminava com "salvei o relatório".
    Nada indicava a falha. O teto foi aumentado em `config.MAX_TOKENS`, mas o
    modo de falhar continua existindo, e ele é invisível por natureza: o
    usuário só descobre quando vai procurar o arquivo.

    O Agno não expõe o `stop_reason` do provedor, então o sinal usado é o
    consumo da última mensagem batendo no teto.
    """
    ultima = next(
        (
            mensagem
            for mensagem in reversed(saida.messages or [])
            if mensagem.role == "assistant"
        ),
        None,
    )
    gastos = getattr(ultima, "metrics", None)
    if not gastos or (gastos.output_tokens or 0) < MAX_TOKENS:
        return

    console.print(
        Panel(
            "A resposta foi cortada no limite de tokens, então o final se "
            "perdeu — inclusive uma possível gravação de arquivo.\n\n"
            "Confira se o artefato foi criado. Para dar mais espaço, aumente "
            "no .env:\n"
            f"    MAX_TOKENS={MAX_TOKENS * 2}",
            title="Resposta truncada",
            border_style="yellow",
        )
    )


def _executar_agente(construtor, pergunta: str, titulo: str) -> None:
    """Roda um agente com saída em streaming e trata pausas de aprovação."""
    garantir_diretorios()
    try:
        agente = construtor()
    except ConfiguracaoAusente as erro:
        _erro(str(erro))

    console.rule(f"[bold]{titulo}")
    saida = agente.run(pergunta)

    while saida.is_paused:
        for ferramenta in saida.tools_requiring_confirmation:
            console.print(
                Panel(
                    f"[bold]{ferramenta.tool_name}[/bold]\n\n{ferramenta.tool_args}",
                    title="Aprovação necessária",
                    border_style="yellow",
                )
            )
            ferramenta.confirmed = Confirm.ask("Executar?", default=False)
        saida = agente.continue_run(run_response=saida)

    if saida.content:
        console.print(Markdown(str(saida.content)))
    _avisar_se_truncou(saida)


def _extrair_secao(texto: str, idioma: str) -> Optional[str]:
    """Pega o corpo do post sob o cabeçalho da versão pedida.

    O cabeçalho vem de `principios.CABECALHO_POST`, que é a mesma constante que
    o Editor recebe na instrução — as duas pontas do contrato saem da mesma
    fonte, senão elas divergem em silêncio e o `publicar` quebra só na hora H.

    O regex é tolerante de propósito no que não importa: o arquivo é gerado por
    um modelo, então aceitamos um a três '#', variação de espaço e o sufixo de
    país opcional. A parada é no próximo cabeçalho de qualquer nível.
    """
    from linkedin_growth.agentes.principios import CABECALHO_POST

    cabecalho = CABECALHO_POST.get(idioma)
    if not cabecalho:
        return None

    rotulo = re.escape(cabecalho.lstrip("# ").strip())
    # 'Post (pt-BR)' -> 'Post \( pt (-BR)? \)', para aceitar '(pt)' e '(pt-BR)'.
    rotulo = rotulo.replace(r"\-BR", r"(?:\-BR)?").replace(r"\(en\)", r"\(en(?:\-US)?\)")
    achado = re.search(
        rf"^#{{1,3}}\s*{rotulo}\s*$\n(.*?)(?=^#{{1,3}}\s|\Z)",
        texto,
        re.DOTALL | re.IGNORECASE | re.MULTILINE,
    )
    return achado.group(1).strip() if achado else None


# ==============================================================================
# Comandos
# ==============================================================================


@app.command()
def importar() -> None:
    """Lê o export de dados do LinkedIn e monta perfil/perfil.yaml."""
    from linkedin_growth.perfil import importador

    garantir_diretorios()
    console.rule("[bold]Importando o export do LinkedIn")
    console.print(f"Lendo de: [cyan]{EXPORT_DIR}[/cyan]\n")

    perfil, relatorio = importador.importar()

    if relatorio.arquivos_encontrados:
        tabela = Table("Arquivo reconhecido", "Itens")
        for arquivo in relatorio.arquivos_encontrados:
            rotulo = arquivo.split("(")[-1].rstrip(")")
            tabela.add_row(arquivo, str(relatorio.contagens.get(rotulo, "-")))
        console.print(tabela)

    if relatorio.arquivos_ignorados:
        console.print(
            f"\n[dim]Ignorados ({len(relatorio.arquivos_ignorados)}): "
            f"{', '.join(relatorio.arquivos_ignorados[:12])}"
            f"{' ...' if len(relatorio.arquivos_ignorados) > 12 else ''}[/dim]"
        )

    for aviso in relatorio.avisos:
        console.print(f"\n[yellow]Atenção:[/yellow] {aviso}")

    if not relatorio.arquivos_encontrados:
        console.print(
            Panel(
                "Nenhum CSV conhecido foi encontrado.\n\n"
                "1. No LinkedIn: Configurações > Privacidade de dados > "
                "Obter uma cópia dos seus dados\n"
                "2. Peça o arquivo completo e aguarde o e-mail\n"
                f"3. Descompacte o .zip dentro de:\n   {EXPORT_DIR}\n"
                "4. Rode este comando de novo",
                title="Como obter o export",
                border_style="yellow",
            )
        )
        raise typer.Exit(code=1)

    caminho = importador.salvar(perfil)
    voz = importador.salvar_voz(perfil)

    console.print(f"\n[green]Perfil gravado em[/green] {caminho}")
    if voz:
        console.print(
            f"[green]Amostras de escrita em[/green] {voz} "
            f"({len(perfil.posts_antigos)} posts)"
        )
    console.print(
        "\n[bold]Agora abra o perfil.yaml e revise.[/bold] Corrija o que o "
        "importador não pegou e preencha 'objetivo' com as suas palavras — "
        "é o que todos os agentes vão ler."
    )


@app.command()
def diagnosticar() -> None:
    """Audita seu perfil contra vagas reais de engenharia de IA."""
    from linkedin_growth.agentes import diagnostico

    _executar_agente(
        diagnostico.construir,
        "Faça o diagnóstico completo do meu perfil do LinkedIn para uma "
        "transição para engenharia de IA. Pesquise vagas reais primeiro.",
        "Diagnóstico de perfil",
    )


@app.command()
def perfil() -> None:
    """Gera headline, Sobre, experiências e projetos prontos para colar."""
    from linkedin_growth.agentes import perfil_writer

    _executar_agente(
        perfil_writer.construir,
        "Escreva a versão otimizada do meu perfil do LinkedIn: headline, "
        "Sobre, experiências, projetos e skills. Português e inglês.",
        "Textos do perfil",
    )


@app.command()
def estrategia() -> None:
    """Define posicionamento, pilares de conteúdo e cadência."""
    from linkedin_growth.agentes import estrategista

    _executar_agente(
        estrategista.construir,
        "Monte a minha estratégia de conteúdo no LinkedIn para os próximos "
        "seis meses, com foco em ser notado por recrutadores de engenharia "
        "de IA.",
        "Estratégia de conteúdo",
    )


@app.command()
def calendario(
    semanas: Annotated[int, typer.Option(help="Quantas semanas planejar.")] = 2,
) -> None:
    """Monta o calendário editorial das próximas semanas."""
    from linkedin_growth import fluxos

    garantir_diretorios()
    console.rule("[bold]Calendário editorial")
    try:
        fluxo = fluxos.fluxo_semana()
    except ConfiguracaoAusente as erro:
        _erro(str(erro))

    saida = fluxo.run(
        f"Levante as pautas de engenharia de IA desta semana e monte o "
        f"calendário editorial das próximas {semanas} semanas."
    )
    console.print(Markdown(str(saida.content or "")))


@app.command()
def post(
    tema: Annotated[str, typer.Option(help="Tema do post.")],
) -> None:
    """Pesquisa, escreve (pt + en), revisa e salva um post."""
    from linkedin_growth import fluxos

    garantir_diretorios()
    console.rule(f"[bold]Produzindo post: {tema}")
    try:
        fluxo = fluxos.fluxo_post()
    except ConfiguracaoAusente as erro:
        _erro(str(erro))

    saida = fluxo.run(tema)
    console.print(Markdown(str(saida.content or "")))


@app.command()
def publicar(
    arquivo: Annotated[Path, typer.Argument(help="Arquivo do post em conteudo/posts/.")],
    idioma: Annotated[str, typer.Option(help="Qual versão publicar: pt ou en.")] = "pt",
    dry_run: Annotated[
        bool, typer.Option("--dry-run", help="Mostra o que seria enviado, sem enviar.")
    ] = False,
) -> None:
    """Publica um post no LinkedIn pela API oficial."""
    from linkedin_growth.ferramentas import linkedin as li

    caminho = arquivo if arquivo.is_absolute() else (Path.cwd() / arquivo)
    if not caminho.exists():
        caminho = POSTS_DIR / arquivo.name
    if not caminho.exists():
        _erro(f"Arquivo não encontrado: {arquivo}")

    texto_bruto = caminho.read_text(encoding="utf-8")

    # O Editor reprova um post que afirme experiência que o usuário não teve, e
    # quando faz isso ele omite de propósito os títulos publicáveis, para o
    # recorte não achar texto. Sem esta checagem o usuário receberia "não
    # encontrei a seção do idioma 'pt'" e iria caçar um bug de formato que não
    # existe — a resposta certa é que o post foi reprovado, e por quê.
    if re.search(r"^status:\s*reprovado\s*$", texto_bruto, re.MULTILINE):
        _erro(
            f"{caminho.name} foi reprovado pelo Editor e não pode ser publicado.\n\n"
            "O motivo está no próprio arquivo, na seção 'Avaliação' — em geral "
            "o post afirma algo que os seus dados reais não sustentam.\n\n"
            "Resolva as pendências listadas lá e gere de novo com\n"
            '    uv run linkedin post --tema "..."'
        )

    corpo = _extrair_secao(texto_bruto, idioma)
    if not corpo:
        from linkedin_growth.agentes.principios import CABECALHO_POST

        _erro(
            f"Não encontrei a seção do idioma '{idioma}' em {caminho.name}.\n"
            f"O arquivo precisa ter um cabeçalho '{CABECALHO_POST['pt']}' ou "
            f"'{CABECALHO_POST['en']}'.\n"
            "Se o post foi gerado por uma versão antiga, rode "
            "`uv run linkedin post --tema \"...\"` de novo."
        )

    if "[PREENCHER" in corpo:
        _erro(
            "O post ainda tem marcadores [PREENCHER]. Complete o texto antes "
            "de publicar."
        )

    console.print(
        Panel(corpo, title=f"{caminho.name} — {idioma} ({len(corpo)} caracteres)")
    )

    if dry_run:
        console.rule("[bold]Simulação (nada foi enviado)")
        try:
            console.print(li.previa(corpo))
        except ConfiguracaoAusente as erro:
            _erro(str(erro))
        return

    if not Confirm.ask(
        "\n[bold red]Publicar isto no seu LinkedIn agora?[/bold red]", default=False
    ):
        console.print("Cancelado.")
        return

    try:
        resultado = li.publicar(corpo)
    except ConfiguracaoAusente as erro:
        _erro(str(erro))
    except Exception as erro:  # noqa: BLE001 — a falha precisa chegar ao usuário
        _erro(f"Falha ao publicar: {erro}")

    if resultado.get("ok"):
        console.print(f"\n[green]Publicado.[/green] {resultado['url']}")
        console.print(f"[dim]via {resultado['endpoint']}[/dim]")
        console.print(
            "\nDaqui a alguns dias, anote as métricas com "
            "[cyan]uv run linkedin metricas[/cyan]."
        )
    else:
        _erro(
            f"O LinkedIn recusou (HTTP {resultado.get('status')}):\n"
            f"{resultado.get('erro')}"
        )


@app.command()
def conexao() -> None:
    """Confere se o token do LinkedIn está válido."""
    from linkedin_growth.ferramentas import linkedin as li

    try:
        dados = li.perfil_do_token()
    except ConfiguracaoAusente as erro:
        _erro(str(erro))
    except Exception as erro:  # noqa: BLE001
        _erro(
            f"Não consegui falar com o LinkedIn: {erro}\n\n"
            "Tokens duram 60 dias. Gere outro em\n"
            "https://www.linkedin.com/developers/tools/oauth/token-generator"
        )

    console.print(
        Panel(
            f"Conectado como [bold]{dados.get('name')}[/bold]\n"
            f"urn:li:person:{dados.get('sub')}",
            title="LinkedIn",
            border_style="green",
        )
    )


@app.command()
def metricas() -> None:
    """Registra as métricas de um post publicado.

    O LinkedIn não libera métricas de post por API self-serve, então este
    número entra à mão. É o que fecha o ciclo: o estrategista lê este arquivo
    para saber que tipo de post funciona para você.
    """
    garantir_diretorios()
    colunas = [
        "data",
        "arquivo",
        "pilar",
        "impressoes",
        "reacoes",
        "comentarios",
        "visualizacoes_perfil",
        "contatos_recrutador",
        "observacao",
    ]

    novo = not METRICAS_CSV.exists()
    console.rule("[bold]Registrar métricas de um post")

    linha = {
        "data": Prompt.ask("Data do post", default=date.today().isoformat()),
        "arquivo": Prompt.ask("Arquivo do post", default=""),
        "pilar": Prompt.ask("Pilar (construi/quebrou/entendi/li/comparei)", default=""),
        "impressoes": Prompt.ask("Impressões", default="0"),
        "reacoes": Prompt.ask("Reações", default="0"),
        "comentarios": Prompt.ask("Comentários", default="0"),
        "visualizacoes_perfil": Prompt.ask("Visualizações de perfil na semana", default="0"),
        "contatos_recrutador": Prompt.ask("Contatos de recrutador", default="0"),
        "observacao": Prompt.ask("Observação", default=""),
    }

    with METRICAS_CSV.open("a", encoding="utf-8", newline="") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=colunas)
        if novo:
            escritor.writeheader()
        escritor.writerow(linha)

    console.print(f"\n[green]Registrado em[/green] {METRICAS_CSV}")


@app.command()
def chat(
    sessao: Annotated[
        str,
        typer.Option(help="Qual conversa continuar. Sessões diferentes não se misturam."),
    ] = SESSAO_PADRAO,
) -> None:
    """Conversa com o time no terminal, continuando de onde parou."""
    from linkedin_growth import times

    garantir_diretorios()
    try:
        time = times.construir(sessao)
    except ConfiguracaoAusente as erro:
        _erro(str(erro))

    console.rule("[bold]Time de Presença no LinkedIn")
    console.print(
        f"[dim]Conversa '[cyan]{sessao}[/cyan]'. Digite 'sair' para encerrar.[/dim]\n"
    )

    while True:
        try:
            pergunta = Prompt.ask("[bold cyan]você[/bold cyan]")
        except (KeyboardInterrupt, EOFError):
            break
        if pergunta.strip().lower() in {"sair", "exit", "quit"}:
            break
        if not pergunta.strip():
            continue

        saida = time.run(pergunta)

        # Publicação e outras ações sensíveis pausam a execução esperando o ok.
        while saida.is_paused:
            for requisito in saida.active_requirements:
                if not requisito.needs_confirmation:
                    continue
                execucao = requisito.tool_execution
                console.print(
                    Panel(
                        f"[bold]{execucao.tool_name}[/bold]\n\n{execucao.tool_args}",
                        title="Aprovação necessária",
                        border_style="yellow",
                    )
                )
                if Confirm.ask("Executar?", default=False):
                    requisito.confirm()
                else:
                    requisito.reject("O usuário recusou.")
            saida = time.continue_run(run_response=saida)

        console.print(Markdown(str(saida.content or "")))
        console.print()


@app.command()
def memoria(
    esquecer: Annotated[
        Optional[str],
        typer.Option(help="Apaga uma memória pelo id mostrado na listagem."),
    ] = None,
    limpar: Annotated[
        bool, typer.Option("--limpar", help="Apaga tudo o que o sistema lembra.")
    ] = False,
) -> None:
    """Mostra o que o sistema aprendeu sobre você nas conversas.

    Memória que não dá para inspecionar não dá para confiar: se um agente
    passar a repetir uma bobagem, é aqui que se descobre de onde veio, e é aqui
    que se apaga.
    """
    from linkedin_growth.config import USUARIO_ID, memoria as gerente_de_memoria

    garantir_diretorios()
    try:
        gerente = gerente_de_memoria()
    except ConfiguracaoAusente as erro:
        _erro(str(erro))

    if limpar:
        if not Confirm.ask(
            "\n[bold red]Apagar TUDO o que o sistema lembra de você?[/bold red]",
            default=False,
        ):
            console.print("Cancelado.")
            return
        gerente.clear_user_memories(user_id=USUARIO_ID)
        console.print("[green]Memória apagada.[/green]")
        return

    lembrancas = gerente.get_user_memories(user_id=USUARIO_ID) or []

    if esquecer:
        # A tabela mostra o id abreviado, então o comando aceita o prefixo.
        achados = [
            lembranca
            for lembranca in lembrancas
            if (lembranca.memory_id or "").startswith(esquecer)
        ]
        if not achados:
            _erro(f"Não existe memória começando por '{esquecer}'.")
        if len(achados) > 1:
            _erro(
                f"'{esquecer}' casa com {len(achados)} memórias. "
                "Use mais caracteres do id."
            )
        gerente.delete_user_memory(
            memory_id=achados[0].memory_id, user_id=USUARIO_ID
        )
        console.print(f"[green]Esquecido:[/green] {achados[0].memory}")
        return

    if not lembrancas:
        console.print(
            Panel(
                "O sistema ainda não lembra de nada.\n\n"
                "A memória é escrita durante a conversa com o time:\n"
                "  [cyan]uv run linkedin chat[/cyan]\n\n"
                "Conte o que você prefere, o que construiu e o que funcionou. "
                "O que valer a pena guardar aparece aqui.",
                title="Memória vazia",
                border_style="yellow",
            )
        )
        return

    tabela = Table("id", "o que o sistema lembra", "temas", "quando")
    for lembranca in lembrancas:
        quando = lembranca.updated_at or lembranca.created_at
        tabela.add_row(
            (lembranca.memory_id or "")[:8],
            lembranca.memory,
            ", ".join(lembranca.topics or []),
            date.fromtimestamp(quando).isoformat() if quando else "",
        )
    console.print(tabela)
    console.print(
        "\n[dim]Para apagar uma: "
        "uv run linkedin memoria --esquecer <id>[/dim]"
    )


@app.command()
def serve(
    porta: Annotated[int, typer.Option(help="Porta do servidor.")] = 7777,
    host: Annotated[str, typer.Option(help="Host do servidor.")] = "localhost",
) -> None:
    """Sobe o AgentOS para a interface web em agent_ui/."""
    try:
        from linkedin_growth.agentos import agent_os, app as fastapi_app
    except ConfiguracaoAusente as erro:
        _erro(str(erro))

    console.print(
        Panel(
            f"Servidor em [cyan]http://{host}:{porta}[/cyan]\n\n"
            "Em outro terminal, suba a interface:\n"
            "  [cyan]cd agent_ui && pnpm dev[/cyan]\n"
            "e abra [cyan]http://localhost:3000[/cyan] no modo [bold]Team[/bold].",
            title="LinkedIn Growth OS",
            border_style="green",
        )
    )
    agent_os.serve(app=fastapi_app, host=host, port=porta)


@app.command()
def status() -> None:
    """Mostra o que já existe e qual é o próximo passo."""
    garantir_diretorios()

    etapas = [
        ("perfil importado", PERFIL_YAML, "linkedin importar"),
        ("diagnóstico", CONTEUDO_DIR / "diagnostico.md", "linkedin diagnosticar"),
        ("textos do perfil", CONTEUDO_DIR / "perfil_otimizado.md", "linkedin perfil"),
        ("estratégia", CONTEUDO_DIR / "estrategia.md", "linkedin estrategia"),
    ]

    tabela = Table("Etapa", "Status", "Comando")
    for nome, caminho, comando in etapas:
        existe = caminho.exists()
        tabela.add_row(
            nome,
            "[green]pronto[/green]" if existe else "[yellow]pendente[/yellow]",
            "" if existe else f"uv run {comando}",
        )

    posts = list(POSTS_DIR.glob("*.md"))
    calendarios = list((CONTEUDO_DIR / "calendario").glob("*.md"))
    tabela.add_row("calendários", f"{len(calendarios)}", "uv run linkedin calendario")
    tabela.add_row("posts escritos", f"{len(posts)}", 'uv run linkedin post --tema "..."')

    console.print(tabela)


if __name__ == "__main__":
    app()
