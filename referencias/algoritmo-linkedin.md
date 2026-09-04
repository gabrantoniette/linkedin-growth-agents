# Heurísticas do algoritmo do LinkedIn (2026)

Adaptado de [sergebulaev/linkedin-skills](https://github.com/sergebulaev/linkedin-skills)
(MIT), skill `linkedin-post-writer` / `references/algorithm-heuristics.md`. São
dados de pesquisa externa (paper 360Brew, arXiv 2501.16450; benchmarks
AuthoredUp 2026; reportagens sobre moderação de pods) — trate como direcional,
não como garantia, e desconfie de número que parecer bom demais.

Isto é referência de **formato e mecânica**, não de conteúdo. As regras de
honestidade, posicionamento e voz continuam em `principios.py` e valem mais
que qualquer heurística de algoritmo daqui.

## Tamanho

- Ponto ideal: 900-1.300 caracteres (~150-220 palavras) — bate com a regra
  já existente de 120-250 palavras.
- Corte do gancho: **~140 caracteres no celular** antes do "ver mais" (no
  desktop são ~210). Escreva o gancho pensando no corte de celular.
- Post longo (1.500-1.900) só funciona com quebra de linha a cada 1-2 frases
  e um payoff narrativo real no fim.

## Hashtags

- **0 a 3 hashtags bem específicas** performam igual ou melhor que 5+ em 2026
  — o ranqueador usa embeddings semânticos, não faz mais correspondência por
  tag.
- **5 ou mais hashtags correlaciona com padrão de conta spam** (sinal
  negativo). Isso substitui qualquer regra antiga de "3 a 5 hashtags".
- Hashtag no fim do post, nunca no meio da frase.

## Link externo

- Link no corpo do post: **queda de ~40-60% no alcance**.
- Link no primeiro comentário: ~2x mais impressões que link no corpo.
- Se o post citar uma fonte externa, escreva "fonte no primeiro comentário" e
  deixe o link lá, não no post.

## Primeiros 60-90 minutos ("janela de momentum")

- Essa janela decide ~80% do alcance total do post.
- Responder a todo comentário dentro dos primeiros 90 minutos é o que
  determina se o post atinge o teto de alcance.
- 3+ comentários substantivos nos primeiros 30 minutos dão um segundo
  impulso de distribuição.

## Sinais de qualidade (não confirmados oficialmente, mas reportados)

- "Salvar" pesa como ~5x uma curtida, ~2x um comentário.
- Comentário em formato de parágrafo pesa ~4x mais que uma reação de uma
  palavra.
- Comentário respondido pelo autor conta como sinal novo a cada resposta.
- Tempo de leitura ideal: 31-60 segundos.
- "Ver mais" seguido de abandono rápido (<3s) é penalizado como clickbait.

## O que é penalizado

- Pedir engajamento de forma genérica ("concorda? comenta aí") é
  ativamente suprimido — isso já é proibido por `O_QUE_NAO_FAZER`, e agora
  também tem penalidade técnica, não só reputacional.
- Padrão de "pod" de engajamento (mesmas contas comentando no mesmo minuto
  todo dia) é detectado e derruba alcance por semanas. Não é um risco real
  para uma conta pessoal orgânica, mas explica por que nunca vale pedir para
  amigos "darem uma força" comentando ao mesmo tempo.
- Pergunta de fechamento genérica ("o que vocês acham?") tem 20-40% menos
  engajamento que uma pergunta específica nomeando o tópico — já era regra
  do projeto, o dado só confirma.

## Checklist antes de publicar

- [ ] Gancho cabe nos ~140 caracteres do corte mobile
- [ ] Sem travessão longo (—) nem meia risca (–) — ver `vocabulario-ia.md`
- [ ] Ao menos um número específico a cada ~100 palavras
- [ ] Ao menos um nome próprio, ferramenta ou projeto concreto
- [ ] Ao menos um detalhe em primeira pessoa (o que você viu, fez, decidiu)
- [ ] Nenhum link no corpo do post — link vai no primeiro comentário
- [ ] 0 a 3 hashtags, específicas, só no final
- [ ] Quebra de linha entre ideias, não a cada frase
- [ ] Fechamento é uma pergunta específica, ou um fechamento limpo — nunca
      "o que vocês acham?"
