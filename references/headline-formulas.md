# Headline formulas

Adapted from [sergebulaev/linkedin-skills](https://github.com/sergebulaev/linkedin-skills)
(MIT), the `linkedin-profile-optimizer` skill. The original targets founders and
B2B ("I help X companies reach Y"); this version is adapted for someone moving
into AI engineering with no professional experience in the field. See
POSITIONING in `principles.py`. Use it as a structure; do not copy the founder
examples from the original repository.

**Limit:** 220 characters. Use most of it. A headline that is too short wastes
search space.

**The examples are in Portuguese** because that is the language of the profile
this system writes for.

## The formula

```
[What you build / are learning] | [Verifiable proof or direction]
```

Two halves, separated by `|`:

- **What you build**: the concrete action, not the status. "estudando IA" is not
  an action; "construindo agentes em Python" is.
- **Verifiable proof or direction**: something checkable. Specific technologies,
  what you are looking for, a named project.

This is the same logic as the POSITIONING already defined in the project: the
headline does not announce a job title, it announces a direction and the
evidence for it.

## Rules

1. **Lead with what is verifiable, not with the title.** Someone with no job in
   the field has no title to lead with, and that is fine, because proof counts
   for more than a title even for people who have one.
2. **Be specific about the direction.** "Buscando oportunidades em IA" is weak.
   "Buscando minha primeira posição como engenheiro de IA: RAG, agentes, LLMs"
   is strong, because it names exactly what to search for you by.
3. **Include the keywords a technical recruiter searches.** Tool and concept
   names (RAG, agentes, LLMs, Python, Agno) increase search appearances, but
   they only go in if they are true. Never for SEO.
4. **No filler adjectives.** Cut "apaixonado", "dedicado", "orientado a
   resultados". They carry no information.
5. **Capitalize proper nouns**: products, companies, frameworks (Python, Agno,
   LangChain).

## Before and after

An example fitted to this project's audience (career change, no formal AI
experience):

- Weak: "Estudando Inteligência Artificial"
- Weak: "Aspiring AI Engineer | Apaixonado por tecnologia"
- Strong: "Construindo agentes de IA em Python: LLMs, RAG, Agno | Buscando minha
  primeira posição em engenharia de IA"

The difference is not tone, it is verifiability. The weak version is an identity
claim; the strong one points at something that exists and can be checked on the
profile.

## Antipatterns (automatic fail)

- "Apaixonado", "dedicado(a)", "orientado(a) a resultados": empty signal.
- "Estudando X há N anos": nobody searches for that.
- A headline in all caps.
- A run of decorative emoji: it reads as low effort.
- A generic "aberto a oportunidades" in the headline itself. That is what
  LinkedIn's "Open to Work" badge is for; it should not eat headline space.

## What LinkedIn search indexes

LinkedIn search weighs the headline heavily. To show up in recruiter searches:

- include the target role ("Engenheiro de IA", "AI Engineer")
- include the concrete specialty ("RAG", "agentes", "LLMs em produção")
- avoid terms so generic they filter nothing ("tecnologia", "inovação")
