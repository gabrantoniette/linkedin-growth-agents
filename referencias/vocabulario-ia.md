# Vocabulário e tiques que denunciam texto gerado por IA

Adaptado de [sergebulaev/linkedin-skills](https://github.com/sergebulaev/linkedin-skills)
(MIT), skills `linkedin-humanizer` e `linkedin-comment-drafter`. Isto detalha —
com exemplos concretos — o critério **VOZ** da rubrica do Editor
(`principios.py`, `RUBRICA`). Consulte antes de revisar um rascunho, não só
depois de desconfiar dele.

## Regra dura: sem travessão longo nem meia risca

Nunca use `—` (travessão longo) ou `–` (meia risca), nem `--` como
substituto. É o maior tique de texto gerado por IA em 2026 — mais reconhecível
que qualquer palavra da lista abaixo. Troque por ponto, vírgula, ou reescreva
a frase em duas.

## Vocabulário proibido

Nunca use estas palavras e expressões:

- leverage/alavancar (no sentido de "usar"), utilizar (em vez de "usar"),
  facilitar, streamline/otimizar de forma vaga, robusto, seamless/perfeito
  (no sentido de "integrado"), delve/aprofundar-se, navegar (no sentido
  metafórico), destravar, harness/aproveitar, cultivar, fomentar
- fundamentalmente, essencialmente, em última análise, crucialmente,
  notavelmente
- cenário, ecossistema, paradigma, universo (no sentido metafórico), jornada
  (fora do sentido literal)
- "não se trata apenas de X, mas de Y"
- "no mundo acelerado de hoje" / "na era digital atual"
- "game changer", "mergulho profundo" ("deep dive"), "no fim das contas"

Isto substitui e amplia a lista curta que já existe em `O_QUE_NAO_FAZER`
("sinergia", "disruptivo", "game changer", "mindset") — mantenha as duas em
mente, esta é só mais detalhada.

## Estrutura que soa mais humana

- Parágrafos de uma a três linhas — já é regra do projeto.
- Uma frase que faça sentido sozinha, fora de contexto, como se fosse
  capturada em print.
- Pelo menos um número concreto ou nome próprio a cada bloco de texto.
- Nunca termine com "o que vocês acham?" — é a assinatura de quem não sabia
  como fechar.

## Padrões a evitar (sinal de IA, não só de clichê)

- Retomar a tese do próprio post no fechamento ("no fim, isso mostra que...").
- Elogio genérico sem informação nova.
- Aberturas batidas: "Isso.", "100%", "Não poderia concordar mais".
- Regra de três decorativa ("mais rápido, mais barato, melhor") quando os
  três itens não carregam informação real cada um.
- Voz passiva em excesso — se mais de 1 em cada 10 frases estiver na
  passiva, reescreva ativa.
- Simetria excessiva: adjetivos sempre em pares, transições arrumadas demais,
  frases-espelho. Isto já está na `RUBRICA` do Editor — esta lista só dá
  exemplos concretos do que procurar.

## Antes de aprovar um rascunho, pergunte

O texto introduz pelo menos um substantivo ou conceito concreto que não
seria óbvio sem ter vivido a situação? Se a resposta for não, o texto
provavelmente poderia ter sido escrito por qualquer pessoa a partir da
documentação — e isso já reprova o critério ESPECIFICIDADE da rubrica.

## Sobre detectores automáticos de IA (GPTZero, Originality.ai, etc.)

Não use como critério de aprovação. São publicamente pouco confiáveis: a
OpenAI desligou seu próprio classificador em 2023 citando 26% de acurácia, e
detectores de terceiros têm viés documentado contra escrita técnica densa e
contra não-nativos de inglês (Liang et al., 2023, *Patterns*). O critério que
vale é a rubrica do Editor, lida por um humano — não uma pontuação de API.
