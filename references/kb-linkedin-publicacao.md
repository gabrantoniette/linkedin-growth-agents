---
id: kb-linkedin-publicacao
titulo: "Base de referência — Timing, frequência e formato de publicação no LinkedIn"
versao: 1.0
data_compilacao: 2026-09-12
revalidar_em: 2026-12-12
idioma: pt-BR
escopo:
  - dia_da_semana
  - horario_do_dia
  - frequencia_semanal
  - formato_de_conteudo
  - mecanica_do_algoritmo
  - mercado_brasil
fora_de_escopo:
  - linkedin_ads
  - recrutamento_e_sourcing
  - copywriting_e_hooks
  - social_selling_e_outbound
confianca_global: media
natureza_da_evidencia: observacional
tem_experimento_controlado: false
---

# Base de referência — Publicação no LinkedIn

Compilação de seis estudos primários publicados entre o fim de 2025 e setembro de 2026,
cobrindo mais de 10 milhões de posts. Documento destinado a servir de contexto factual
para agentes que recomendam estratégia de publicação.

---

## 0. Instruções de uso para o agente

Regras de conduta ao usar este documento como fonte:

1. **Nunca apresentar horário como fato consolidado.** Os estudos divergem em ~7 horas.
   Toda recomendação de horário deve vir acompanhada da divergência (§3.2).
2. **Sempre distinguir perfil pessoal de página de empresa.** As populações se comportam
   de forma diferente e a maioria dos estudos mistura as duas sem declarar.
3. **Sempre distinguir métrica por post de métrica por semana.** É o erro analítico mais
   comum do domínio (§4.1).
4. **Dados do próprio usuário superam este documento.** Se o usuário apresentar analytics
   próprio, ele é a autoridade final; esta base vira hipótese inicial.
5. **Horários são sempre no fuso local do público-alvo**, não do publicador. Para
   audiência brasileira, ler tudo como horário de Brasília.
6. **Nenhum estudo aqui tem corte para o Brasil.** Ver §7 antes de aplicar a
   público brasileiro.
7. Ao citar um número, citar também o `source_id` correspondente (§10).
8. Se a pergunta do usuário cair em `fora_de_escopo`, declarar a lacuna em vez de inferir.

---

## 1. Parâmetros canônicos

Bloco parseável com os valores de consenso. Campos `confianca`: `alta` = todos os
estudos concordam; `media` = maioria concorda; `baixa` = divergência aberta.

```json
{
  "dias": {
    "bloco_forte": ["terca", "quarta", "quinta"],
    "bloco_aceitavel": ["segunda"],
    "bloco_fraco": ["sexta"],
    "bloco_evitar": ["sabado", "domingo"],
    "melhor_dia_unico": {"valor": "quarta_ou_terca", "confianca": "media"},
    "confianca": "alta"
  },
  "horarios": {
    "janela_de_sobreposicao_entre_estudos": "10:00-16:00",
    "janela_alternativa_manha": "07:00-09:00",
    "janela_alternativa_tarde": "15:00-20:00",
    "slot_mais_citado": {"valor": "quarta_16h", "confianca": "media"},
    "hora_de_maior_volume_de_publicacao": "09:00",
    "confianca": "baixa",
    "amplitude_da_divergencia_horas": 7
  },
  "frequencia_perfil_pessoal": {
    "piso_sustentavel_semanal": 2,
    "faixa_recomendada_semanal": [3, 5],
    "faixa_aceleracao_semanal": [6, 10],
    "teto_com_penalidade_detectada": null,
    "espacamento_minimo_entre_posts_horas": 24,
    "confianca": "alta"
  },
  "formatos_por_engajamento_desc": [
    "carrossel_pdf",
    "video",
    "imagem",
    "texto",
    "post_com_link_no_corpo"
  ],
  "regra_de_link": "link no primeiro comentário, nunca no corpo do post",
  "hierarquia_de_impacto_desc": ["consistencia", "formato", "frequencia", "horario"]
}
```

---

## 2. Dias da semana

### 2.1 Consenso

Único ponto onde todos os datasets convergem: **o bloco terça–quinta domina e o fim de
semana desaba**. O LinkedIn é acoplado à semana útil de forma que nenhuma outra
plataforma social é. `confianca: alta`

| Estudo | Melhor dia declarado |
|---|---|
| Buffer 2026 | Quarta, depois quinta e sexta |
| Sprout Social 2026 | Terça, quarta, quinta |
| MagicPost 2026 | Terça |
| Hootsuite + Critical Truth | Terça e quarta |
| SocialPilot 2026 | Terça, quarta, quinta |
| Metricool 2026 | Segunda, terça, quarta |

### 2.2 Quantificação do gradiente

MagicPost mediu impressões reais de 831.350 posts de 10.798 criadores e contou em qual
dia cada criador teve seu maior alcance. Índice com terça = 100:

| Dia | Índice de alcance | Criadores |
|---|---|---|
| Segunda | 95 | 1.980 |
| **Terça** | **100** | **2.075** |
| Quarta | 91 | 1.886 |
| Quinta | 92 | 1.900 |
| Sexta | 77 | 1.607 |
| Sábado | 33 | 685 |
| Domingo | 32 | 665 |

**Leitura correta:** segunda a quinta formam um platô estatisticamente próximo (91–100).
A diferença entre "o melhor dia" e "o quarto melhor dia" é pequena. O corte real está
entre semana útil e fim de semana, não entre terça e quarta.

**Divergência a preservar:** o Buffer rankeia segunda e terça como os *piores* dias úteis,
enquanto MagicPost coloca segunda em segundo lugar e Hootsuite coloca terça em primeiro.
Não afirmar ranking interno da semana útil com confiança.

---

## 3. Horários

### 3.1 Ressalva estrutural

Nenhum estudo mede **acessos reais**. LinkedIn e Microsoft não divulgam sessões por
dia/hora. Todos os números abaixo são proxies de três tipos distintos:

- **Engajamento por slot dia×hora** — proxy de audiência ativa. O mais usado.
- **Volume de publicação** — mede oferta (congestionamento do feed), não demanda.
- **Tráfego web agregado** — mensal, sem corte horário.

### 3.2 A divergência (não achatar)

| Estudo | Amostra | Métrica | Veredito |
|---|---|---|---|
| Hootsuite | 1M+ posts, 118 países | Engajamento bruto | 08:00–09:00, ter/qua |
| MagicPost | 2.667.049 posts | Normalizado por autor | 07:00–09:00, dias úteis |
| Metricool | 673.658 posts / 63.108 contas | Engajamento | 09:00–12:00 |
| SocialPilot | 683.000 posts / 47.672 contas | Engajamento | 10:00–12:00 e 13:00–16:00 |
| Sprout Social | ~2 bi interações / 307k perfis | Engajamento bruto | 11:00–17:00 |
| Buffer | 4,8M posts | Engajamento bruto | 15:00–20:00, pico qua 16:00 |

**Amplitude: ~7 horas entre o extremo mais cedo e o mais tarde.**

### 3.3 Por que divergem — causas identificadas

| Causa | Efeito |
|---|---|
| **Métrica** | Engajamento bruto premia horas em que contas grandes publicam. Páginas de empresa rodam em agenda de escritório → puxa o resultado para a tarde. MagicPost normalizou contra a média histórica do próprio autor → resultado migra para a manhã. |
| **População** | Criadores individuais vs. páginas de empresa. Páginas apresentam ~1,7x mais variação entre melhor e pior dia que perfis pessoais (AuthoredUp, 3M+ posts). Misturar os dois soterra o sinal de hora. |
| **Fuso** | Buffer, Sprout e MagicPost normalizam para o horário local do público. Outros não declaram. Comparar tabelas sem checar isso produz erro sistemático. |
| **Janela de coleta** | Sprout coletou 27/11/2025 a 27/02/2026 — inclui feriados do hemisfério norte, onde está a maior parte da amostra. |
| **Viés de carteira** | Cada ferramenta analisa os próprios clientes. Perfis de cliente diferentes produzem horários diferentes. |

**Regra derivada:** se o usuário tem perfil pessoal e publica como pessoa física, priorizar
o achado do MagicPost (manhã cedo). Se opera página de empresa, priorizar Buffer/Sprout
(meio do dia a tarde).

### 3.4 Grade por dia — Buffer (perfis mistos, engajamento bruto)

| Dia | 1º | 2º | 3º |
|---|---|---|---|
| Segunda | 22:00 | 17:00 | 21:00 |
| Terça | 16:00 | 17:00 | 22:00 |
| Quarta | **16:00** | 15:00 | 17:00 |
| Quinta | 17:00 | 19:00 | 21:00 |
| Sexta | 15:00 | 16:00 | 17:00 |
| Sábado | 09:00 | 18:00 | 22:00 |
| Domingo | 22:00 | 21:00 | 06:00 |

### 3.5 Grade por dia — Sprout Social (engajamento bruto, ~2 bi interações)

| Dia | Janela de pico |
|---|---|
| Segunda | 13:00–14:00 |
| Terça | 11:00–17:00 |
| Quarta | 11:00–16:00 |
| Quinta | 11:00 e 13:00–17:00 |
| Sexta | 11:00 e 13:00–14:00 |
| Sábado / Domingo | sem janela ótima |

### 3.6 Achado transversal: hora da multidão ≠ hora de desempenho

MagicPost separou **quando mais gente publica** de **quando os posts rendem mais**. Não
são a mesma hora, e o padrão se repete em todos os mercados grandes medidos.

| Mercado | Hora da multidão | Score | Melhor hora | Score |
|---|---|---|---|---|
| EUA (Eastern) | 09:00 | 72 | 08:00 | 80 |
| Reino Unido | 09:00 | 73 | 07:00 | 86 |
| França (Paris) | 08:00 | 57 | 07:00 | 70 |
| Índia (IST) | 10:00 | 68 | 08:00 | 81 |
| Global (UTC) | 07:00 | 61 | 06:00 | 66 |

Exemplos de magnitude: nos EUA, 09:00 concentra 69.398 posts de dias úteis; às 08:00 o
volume é ~25% menor e o score sobe. Na França, 08:00 é a maior hora isolada de qualquer
país medido (138.029 posts) e pontua 57; 07:00, com um quinto do volume, pontua 70.

**Regra derivada:** publicar de 1 a 2 horas antes do pico local de publicação. Se a
resposta for "maior fluxo", a resposta literal é 09:00 local — mas fluxo de publicação é
congestionamento, não oportunidade.

---

## 4. Frequência semanal (perfil pessoa física)

### 4.1 O erro analítico central

Métrica **por post** e métrica **por semana** andam em direções opostas conforme a
frequência sobe. Quem monitora engajamento/post conclui que aumentar a cadência está
piorando a performance e recua — conclusão invertida.

MagicPost, faixa 1.000–10.000 seguidores (~15.000 criadores da amostra):

| Ritmo | Likes medianos/post | Likes medianos/semana |
|---|---|---|
| < 2 por mês | 29 | 11 |
| 2–4 por mês | 21 | 21 |
| 1–2 por semana | 18 | 35 |
| 2–4 por semana | 15 | 58 |
| ~diário | 13 | 87 |
| > diário | 8 | 114 |

Quem publica 2–4 vezes por semana acumula ~5x o engajamento semanal de quem publica menos
de duas vezes por mês. No ritmo diário, ~8x.

**Denominador correto: a semana.**

### 4.2 Por faixa de seguidores (likes medianos/semana)

| Ritmo | < 1k | 1k–10k | 10k–50k | 50k+ |
|---|---|---|---|---|
| < 2 por mês | 4 | 11 | 23 | 161 |
| 1–2 por semana | 12 | 35 | 91 | 521 |
| ~diário | 25 | 87 | 235 | 1.156 |

O padrão de "mais frequência, mais total semanal" se mantém em todas as faixas.

### 4.3 Ganho marginal — Buffer (melhor desenho metodológico)

Buffer comparou **a mesma conta** em semanas de alta e baixa frequência, usando Z-score
contra a própria média e regressão de efeitos fixos, sobre 2M+ posts de 94k+ contas.

| Frequência | Ganho vs. 1 post/semana |
|---|---|
| 2–5 por semana | +1.182 impressões/post, +0,23 p.p. de taxa de engajamento |
| 6–10 por semana | +5.001 impressões/post, +0,76 p.p. |
| 11+ por semana | +16.946 impressões/post, ~3x engajamentos, +1,40 p.p. |

Dois achados:
- O efeito é **independente do tamanho da conta**. Contas de algumas centenas de
  seguidores tiveram o mesmo ganho relativo ao sair de 1 para 2–5 posts que contas com
  dezenas de milhares.
- **Retorno marginal decrescente.** O salto de 1 → 2–5 é maior que o salto de 6–10 → 11+.

### 4.4 Benchmark de comportamento real

- Ritmo mais comum na faixa 1k–10k seguidores: **1–2 posts por semana** (~25% dos criadores).
- Publicantes diários são minoria nessa faixa; acima de 1x/dia é menos de 2%.
- Média Metricool: perfis pessoais 3,05 posts/semana; páginas de empresa 2,34.
- Recomendação oficial do LinkedIn: 1 a 5 por semana — 1 a 3 posts curtos semanais e
  1 a 2 artigos longos por mês.
- Apenas ~3% dos membros do LinkedIn publicam mais de uma vez por semana. Publicar com
  qualquer regularidade já coloca o perfil numa minoria estreita.

### 4.5 Tese da canibalização — status: não sustentada

Circula amplamente que publicar demais faz os posts competirem entre si e o algoritmo
suprimir o alcance. Existem guias afirmando que acima de 1 post/dia o alcance por post cai
porque o algoritmo evita mostrar dois posts do mesmo autor ao mesmo usuário em janela curta.

**Nenhum dos dois estudos com dados primários encontrou esse penhasco.** Nem Buffer nem
MagicPost identificaram qualquer nível de frequência em que o total semanal começasse a
cair, inclusive acima de dois posts por dia.

Tratar a canibalização como afirmação sem dataset público por trás. Não repetir como fato.

---

## 5. Formato de conteúdo

Move mais o resultado do que subir um slot na cadência semanal. Engajamento mediano,
dados Buffer:

| Formato | Performance relativa |
|---|---|
| **Carrossel (PDF nativo)** | ~278% acima de vídeo, ~303% acima de imagem, ~600% acima de texto |
| Vídeo | ~84% acima de texto |
| Imagem | ~72% acima de texto |
| Texto puro | Piso de engajamento, mas é o formato que sustenta o hábito |
| Post com link no corpo | Pior taxa de todas — tira o usuário da plataforma |

**Regras derivadas:**
- Link sempre no primeiro comentário, nunca no corpo.
- Conteúdo técnico e didático (arquitetura, comparação de abordagens, passo a passo,
  troubleshooting) é naturalmente sequencial e converte melhor como carrossel do que
  como bloco de texto.
- Começar pelos formatos que sustentam consistência (texto, imagem) e adicionar
  carrossel e vídeo depois que o ritmo existir.

---

## 6. Mecânica do algoritmo (estado em 2026)

### 6.1 O que mudou

O LinkedIn passou a distribuir conteúdo por **relevância** em vez de somente recência.
Consequência operacional: um post pode reentrar em distribuição dias após a publicação,
o que reduz o peso do horário exato.

### 6.2 Golden hour — status: conceito, não regra confirmada

A janela de 60–90 minutos pós-publicação é amplamente citada, mas **o LinkedIn nunca
confirmou oficialmente uma janela de 60 ou 90 minutos**. Tratar como heurística, não como
mecanismo documentado.

### 6.3 O sinal que realmente escala

Análise da AuthoredUp sobre 3M+ posts: publicações que ganham **salvamentos e comentários
substantivos entre 24 e 72 horas** após a publicação performam de **4 a 6 vezes melhor**
nos feeds sugeridos do que publicações que só tiveram engajamento rápido e raso no início.

Isso favorece conteúdo com meia-vida longa e reduz a pressão por volume e por horário.

### 6.4 Comentários como canal paralelo

O LinkedIn passou a contar impressões para comentários, o que efetivamente transforma
comentário em micro-post com alcance fora da rede do autor.

**Regra derivada:** em semanas de baixa capacidade, 2–3 posts + 10–15 minutos diários de
comentários com ponto de vista entregam visibilidade comparável a uma cadência maior.
Comentário genérico ("excelente conteúdo!") não conta.

---

## 7. Contexto Brasil

### 7.1 Dimensão do mercado

| Métrica | Valor | Data |
|---|---|---|
| Usuários no Brasil | 100 milhões | jun/2026 |
| Posição global | 3º maior mercado (atrás de EUA e Índia) | jun/2026 |
| Penetração na população economicamente ativa (~108M) | ~90% | jun/2026 |
| Novos perfis por dia | 8.000 a 12.000 | jun/2026 |
| Conteúdos originais publicados no trimestre | 11+ milhões | trim. ant. a jun/2026 |
| Interações geradas no trimestre | ~400 milhões | trim. ant. a jun/2026 |

### 7.2 Lacuna crítica

**Nenhum dos seis estudos publica corte para o Brasil.** O MagicPost, único com recorte
por país em horário local, cobre nove mercados (EUA, Reino Unido, França, Alemanha, Índia,
Holanda, Paquistão, Austrália, Canadá) e o Brasil não está entre eles.

Todas as grades horárias deste documento são médias globais dominadas por EUA, Índia,
Reino Unido e França. Aplicá-las ao Brasil é extrapolação, não medição.

O agente **deve declarar essa lacuna** ao recomendar horários para público brasileiro.

### 7.3 Grade de partida para público brasileiro (horário de Brasília)

Construída pela convergência entre estudos. **Status: hipótese a testar, não achado.**

| | Seg | Ter | Qua | Qui | Sex |
|---|---|---|---|---|---|
| Slot manhã | — | 08:00 | 08:00 | 08:00 | — |
| Slot miolo | 13:00 | 11:00–12:00 | 11:00–12:00 | 11:00–12:00 | 11:00 |
| Slot tarde | — | 16:00 | **16:00** | 16:00 | 15:00 |

Quarta às 16:00 é o único slot que aparece com força em múltiplos estudos independentes.

---

## 8. Protocolo de mensuração própria

Dado que os estudos divergem em 7 horas e nenhum cobre o Brasil, medir é a única saída.

### 8.1 Coleta

- Exportar CSV do LinkedIn Analytics (Página → Analytics → Conteúdo → Exportar).
- **Limitação conhecida:** o analytics nativo não preserva timestamp exato de publicação
  após o fato — mostra apenas tempo relativo ("3h", "2d"). É necessário registrar a hora
  de publicação em paralelo, ou publicar via ferramenta que grave isso.

### 8.2 Modelagem

Grão: `post_id × dia_semana × hora × formato`

Métricas: impressões, engajamento, cliques, salvamentos, comentários.

### 8.3 Normalização obrigatória

Normalizar cada post contra a **média móvel de 90 dias do próprio perfil**. Sem isso, o
crescimento da base de seguidores contamina a série temporal e produz a conclusão falsa
de que "os horários melhoraram" quando apenas a audiência cresceu.

### 8.4 Volume mínimo

Não concluir com menos de **10 a 15 posts por slot testado**. Abaixo disso, um único post
viral desloca a média inteira.

### 8.5 Janela de teste

Manter a grade fixa por **2 a 4 semanas** antes de ajustar. Trocar de horário toda semana
impede acumular volume estatístico.

---

## 9. Anti-padrões — afirmações que o agente não deve emitir

| Não afirmar | Motivo |
|---|---|
| "O melhor horário para postar é X" (sem qualificação) | Divergência de ~7h entre estudos com dados primários |
| "Postar demais canibaliza seu alcance" | Não sustentado pelos dois datasets que mediram |
| "O algoritmo julga seu post nos primeiros 60 minutos" | LinkedIn nunca confirmou a janela; distribuição virou contínua |
| "Esses são os melhores horários no Brasil" | Nenhum estudo tem corte para o Brasil |
| "Quarta é o melhor dia" (como fato) | Buffer diz quarta, MagicPost e Hootsuite dizem terça |
| "Seu engajamento por post caiu, reduza a frequência" | Denominador errado; medir por semana |
| "Poste todo dia para crescer" | Verdadeiro no agregado, mas cadência abandonada é pior que cadência menor mantida |

### 9.1 Limitação metodológica a declarar quando relevante

Nenhum estudo aqui é experimento controlado.

- **MagicPost** é correlacional e declara o próprio viés: a amostra vem de perfis
  rastreados pela ferramenta, enviesada para quem leva o LinkedIn a sério. Parte do ganho
  atribuído à frequência pode ser investimento em qualidade, não frequência.
- **Buffer** resolve o viés de seleção *entre* contas com efeitos fixos, mas não o
  confundidor de nível semana: uma semana com 6 publicações provavelmente também foi uma
  semana com mais tempo, energia e material melhor. A direção da recomendação é segura;
  a magnitude não.

---

## 10. Registro de fontes

| source_id | Organização | Amostra | Período | Métrica | Viés declarado |
|---|---|---|---|---|---|
| `buffer-timing-2026` | Buffer | 4,8M posts | pub. set/2026 | Engajamento bruto | Contas que publicam via Buffer |
| `buffer-freq-2026` | Buffer | 2M+ posts / 94k+ contas | 2025–2026 | Impressões, engajamento, taxa (Z-score + efeitos fixos) | Idem |
| `sprout-2026` | Sprout Social | ~2 bi interações / 307k perfis | nov/2025–fev/2026 | Engajamento bruto | Carteira Sprout; 6 redes |
| `magicpost-timing-2026` | MagicPost | 2.667.049 posts | até mai/2026 | Score normalizado por autor, por país | Criadores individuais que usam a ferramenta |
| `magicpost-dia-2026` | MagicPost | 831.350 posts / 10.798 criadores | mai/2026 | Impressões reais | Idem |
| `magicpost-freq-2026` | MagicPost | 26.428 criadores | 12 meses até jun/2026 | Mediana de likes por post e por semana | Idem |
| `metricool-2026` | Metricool | 673.658 posts / 63.108 contas | 2026 | Engajamento | Carteira Metricool |
| `hootsuite-critical-truth` | Hootsuite + Critical Truth | 1M+ posts / 118 países | 2025 | Engajamento | Carteira Hootsuite |
| `socialpilot-2026` | SocialPilot | 683.000 posts / 47.672 contas | 2026 | Engajamento | Carteira SocialPilot |
| `authoredup-3m` | AuthoredUp | 3M+ posts | 2026 | Distribuição em feeds sugeridos | Não declarado |
| `linkedin-br-2026` | LinkedIn (anúncio oficial) | — | jun/2026 | Contagem de usuários | Fonte primária da plataforma |

### 10.1 Contexto global de plataforma

| Métrica | Valor | Fonte |
|---|---|---|
| Membros registrados | ~1,3 bilhão | LinkedIn / DataReportal |
| Usuários ativos mensais | ~310 milhões (~28% dos registrados) | Microsoft, resultados Q2 FY2026 |
| Visitas mensais ao site | ~1,9–2,0 bilhões | Similarweb, mar–mai/2026 |
| Taxa de acesso diário | 16,2% | DataReportal |
| Taxa de acesso mensal | 48,5% | DataReportal |
| Usuários que interagem com conteúdo de marca ao menos 1x/semana | ~70% | Sprout Social, 2026 Content Strategy Report |
| Membros que publicam mais de 1x/semana | ~3% | LinkedIn DSA / análises agregadas |

---

## 11. Hierarquia de decisão

Ordem de impacto sobre o resultado, do maior para o menor. Um agente que precise
priorizar recomendações deve seguir esta ordem:

1. **Consistência** — cadência mantida por 90+ dias
2. **Formato** — carrossel > vídeo > imagem > texto; link fora do corpo
3. **Frequência** — 3 a 5 por semana como alvo, 2 como piso
4. **Horário** — desempate, não alavanca

Justificativa: a diferença entre o melhor slot horário e o platô ordinário é real e
mensurável, mas menor que a diferença entre formatos e muito menor que a diferença entre
publicar e não publicar. O maior salto de todo o dataset é entre silêncio e qualquer ritmo.

---

## 12. Changelog

| Versão | Data | Alteração |
|---|---|---|
| 1.0 | 2026-09-12 | Compilação inicial. Seis estudos primários + contexto Brasil. |

### Gatilhos de revalidação

Revisar este documento quando ocorrer qualquer um dos eventos abaixo:

- Buffer, Sprout, Metricool, Hootsuite, SocialPilot ou MagicPost publicarem refresh anual
- LinkedIn anunciar mudança de algoritmo de distribuição
- Qualquer estudo publicar corte específico para o Brasil (fecharia a lacuna do §7.2)
- Surgir experimento controlado sobre frequência (mudaria o status do §4.5 e §9.1)
