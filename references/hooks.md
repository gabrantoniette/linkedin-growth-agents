# Hook formulas

Adapted from [sergebulaev/linkedin-skills](https://github.com/sergebulaev/linkedin-skills)
(MIT), the `linkedin-post-writer` skill. The original carries 20 formulas
validated against high-performing posts; here they are trimmed to the essentials
(without the engagement numbers from the original corpus, which do not apply to
this user's account) and mapped onto this project's five pillars: **Built,
Broke, Understood, Read, Compared** (see `principles.py`).

Use them as a starting point, not as a template to fill in without thinking. The
Writer is already instructed to draft three hooks and throw away the most
obvious one; this list exists so the second and third hook are not variations of
the first.

**F6 (Comment Bait) is marked forbidden in this project.** Asking people to
"comment X" is one of the things explicitly vetoed in `DO_NOT`. It stays listed
here only so you recognize the pattern and do not write something like it
without noticing.

The templates keep their Portuguese example phrases, because the posts they
produce are in Portuguese.

---

## F1: Platform-risk anaphora

```
{Platform/situation} can {restrict|hurt} you {when}.
{Another situation} can {bad thing} because of {reason}.
[2-3 more lines in the same pattern, increasing specificity]
You do not control {X}. You do not control {Y}. You are only passing through.
[concrete anecdote with a real number]
What most people miss: {reframe}.
So I changed what I do:
- {tactic 1}
- {tactic 2}
[a self-assessment question for the reader]
```
**Why:** stacked loss aversion plus an identity threat.
**Pillar:** Broke, Understood.

## F2: Category obituary

```
Obituary for {old approach/tool}.
Cause of death: {specific mechanism + numbers}.
[concrete evidence, 2-3 paragraphs]
I defended {the old thing} until {the event that changed it}.
It worked. Until {date/trigger}.
What changed under the hood:
1. {change 1}
...
The winner now is not {old profile}. It is {new profile}.
```
**Why:** replaces the shame of "I was out of date" with curiosity.
**Pillar:** Compared, Understood.

## F3: Year-over-year turn

```
In {last year}, I {humble milestone}.
In {this year}, I {transformative goal}.
Here is what actually changed.
[a vulnerable truth plus specific numbers]
The change was not a tool, it was an identity.
[mirror close: "what was your turn from X to Y this year?"]
```
**Why:** the two-line hook carries nearly all the weight; the mirror question
pulls comments.
**Pillar:** Understood, Built.

## F4: Time-anchored confession

```
{N} {days|months} ago, I stopped {behaviour}.
Here is what happened.
[context for why the old behaviour made sense, with numbers]
[the silent cost it carried]
So I stopped. [new behaviour, 2-3 lines]
{Metric} dropped N%. I expected worse.
What surprised me: {counterintuitive gain}.
[mirror question: "what did you stop doing that quietly improved your work?"]
```
**Why:** the confession earns attention; the numbers kill the hand-waving. This
is the formula most aligned with HONESTY, so only use it with real numbers.
**Pillar:** Broke, Understood.

## F5: Meta-proof (self-verifying)

```
Most technical posts die in the first few minutes.
Not because of {the common reason}. Because of {the real one}.
So here is the test.
Over the next 24h I will {specific, verifiable commitment}.
You do two things:
1. {simple action}
2. {verification action}
If the thesis is right, {expected result}. If it is wrong, I come back here and
say so.
```
**Why:** the claim is validated by the reader's action. Only use it if you will
actually keep the commitment. It fits HONESTY, and breaks it if it becomes an
empty promise.
**Pillar:** Built.

## F6: Comment bait — **FORBIDDEN IN THIS PROJECT**

Asks people to "comment X to get Y". `DO_NOT` already vetoes asking for
engagement ("comment ABC", "tag a friend") because it burns credibility with a
technical audience. Do not use it, not even in disguise.

## F7: Odd-precision ledger

```
{An odd, specific number: "R$ 47,32", "3h42min"}
[one line of context for what the number covers]
Here is every line item, unrounded:
- {item 1}: {value}
- {item 2}: {value}
...
[what that total replaces or represents]
[what surprised you: what broke, what worked]
```
**Why:** unrounded numbers signal a real record rather than an estimate. It gets
screenshotted.
**Pillar:** Built, Compared.

## F8: Paid-becomes-free reversal

```
{Context: something that would normally cost a lot or take real effort}.
Today I am giving it away.
Below is the exact process I use before {decision}. I call it
{FRAMEWORK-NAME}.
[a suggested time box for anyone applying it]
1. {step 1}: [actionable instruction with a number or ratio]
...
Run it today. Most people find 2-3 fixes in the first 20 minutes.
```
**Why:** a named framework signals original thinking rather than generic advice;
a checklist earns more saves than likes.
**Pillar:** Built, Understood.

## F9: Curiosity-gap teaser

```
Yesterday, {system/code} did something.
Something I did not expect.
[a sensory anchor: where you were, what you were doing]
[a specific reveal, not a cliché]
[what it means, one paragraph]
[philosophical close naming a feeling, ending in a question]
```
**Why:** an incomplete first line plus a second line that deepens the gap keeps
the reader from scrolling. The sensory detail keeps it from sounding generated.
**Pillar:** Broke, Understood.

## F10: Contrarian with historical evidence

```
{Established idea} has been "dying" since {year}.
{Month/year}: {event}. "{death prediction}."
[6-9 dated entries, 1-2 lines each]
Every quarter, the same obituary.
Here is the counterargument.
[a hard statistic, with a source]
What actually died was not {X}. It was {a specific subset}.
What is working: {the opposite subset, with detail}.
If you are still {losing behaviour}, you already lost.
If you are {winning behaviour}, you already won.
[provocative question]
```
**Why:** the evidence list holds attention; the binary close forces people to
take a position in the comments.
**Pillar:** Compared, Read.

## F11: In medias res emotional open

```
{One short line, dropped straight into the emotional peak of a real story: the
moment of breaking, loss or maximum difficulty. No setup.}
[narrative in scene, 3-6 short sensory lines]
[the turn: what changed, what it cost]
[one line of meaning, without turning into a moral]
```
**Why:** starting at the emotional peak skips the warm-up that scrolling
punishes.
**Warning:** only use it for a real story. Inventing drama for engagement
violates HONESTY. Do not write the first line in ALL CAPS.
**Pillar:** Broke.

## F12: Permission slip

```
I do not know who needs to hear this today, but {a reassuring truth for an
anonymous reader}.
[2-4 specific, earned lines, not a motivational cliché]
[one small concrete permission: "you are allowed to {X}"]
[a soft close inviting the reader to see themselves in it]
```
**Why:** second-person reassurance makes readers tag themselves in the comments.
**Warning:** this is the most engineered format on the list, and it collides with
`DO_NOT` ("do not write self-help or motivational posts"). Use it rarely, and
only for something you genuinely believe, never as a default move.
**Pillar:** none. Avoid unless the situation is exceptional.

## F13: Bad-news reversal

```
That is it. I am no longer {common practice or beloved habit}.
I am also cutting {second thing}.
[a pause for suspense: let the reader assume bad news]
[the turn: it is actually an upgrade. What replaced it and why.]
[what the change really represents]
```
**Why:** false bad news triggers loss aversion; the positive turn releases the
tension.
**Warning:** it only works if the turn is genuinely positive.
**Pillar:** Understood, Compared.

## F14: Named gratitude

```
To {Name}, {Name} and {Name}: thank you for {what each one did, specifically}.
[2-4 lines naming what each person did. Specific, not generic praise]
[why it mattered to you or to the work]
[a close that honours them, not you]
```
**Why:** naming real people invites their network to repost.
**Warning:** only name real people, for a real reason.
**Pillar:** any, as an occasional post. It is not a technical content pillar.

## F15: Explaining it plainly

```
{Technical term}, explained simply.
{emoji} {TERM}: what does each part mean?
{emoji} {part 1} = {plain-language explanation}
{emoji} {part 2} = {plain-language explanation}
[continue the glossary, scannable]
[one-line close: "now you will not forget it again"]
```
**Why:** a correct simplification of something dense gets saved and shared as a
reference.
**Warning:** the simplification has to be right. Getting your own field wrong
destroys credibility.
**Pillar:** Understood.

## F16: Status-stripping humility

```
Out there, they call me {title/label}.
At home, none of that survives {the moment that disarms it}.
[the scene that strips the status: a real detail, a quiet failure]
[what the contrast taught, one or two lines]
```
**Why:** trading prestige for relatability converts authority into closeness.
**Warning:** it must not become a humblebrag.
**Pillar:** occasional use, outside the five technical pillars.

## F17: Controlled A/B anecdote

```
{Action A} -> {result A}.
{The same action, one variable changed} -> {opposite result B}.
Same {constant 1}. Same {constant 2}. The only variable was {the one thing}.
[what you thought it meant, one line]
[the reframe: what the comparison actually reveals]
[an operational question that makes the reader test their own variable]
```
**Why:** a controlled comparison reads as evidence, not opinion.
**Warning:** the two situations have to differ in exactly one variable, for
real, not constructed to look more impressive.
**Pillar:** Broke, Compared. This is almost the definition of the "Compared"
pillar.

## F18: Dissolving a false binary

```
Everyone falls back on one of two answers to {problem}.
{Option A}? {one line that kills it}.
{Option B}? {one line that kills it}.
Both fail for the same reason: {the shared flaw}.
So I tried a third: {the synthesis}.
[how it works, 2-3 concrete lines]
[the principle that makes the third option obviously better]
[question: how do you handle {problem} today, A, B, or something else?]
```
**Why:** naming and knocking down the two obvious options earns the right to the
third.
**Warning:** the two options have to be the ones the reader would actually
consider. A straw binary reads as manipulation.
**Pillar:** Compared, Understood.

## F19: Anecdote-to-evidence bridge

```
[something small and personal you noticed: one or two concrete lines]
I thought I had found something. Turns out it was already known:
-> {evidence 1, with a number}
-> {evidence 2, with a number}
[the line that names the real pattern]
[what you did about it: the decision, not the theory]
[operational question]
```
**Why:** the personal observation wins attention; the stack of evidence wins
credit.
**Warning:** real numbers only. With no real source, use F4 instead.
**Pillar:** Read, Understood.

## F20: Diverging-curves close

```
[two things that look alike today]
{Approach A}: {what it does over time: grows/decays/weighs}.
{Approach B}: {the opposite over time}.
[anchor it to a timeline: "month 1, X. month 6, Y."]
{One-line maxim contrasting the two trajectories.}
```
**Why:** two opposite trajectories on a timeline make an idea feel inevitable;
the maxim is the repost trigger.
**Warning:** the curves have to genuinely diverge.
**Pillar:** Compared. It usually works well as the close of a post that already
used F17 or F18.

---

## Split by engagement goal

| Goal | Won by | Formulas |
|---|---|---|
| **Comments** | a question, a contrary position, vulnerability, a controlled comparison | F4, F10, F17, F18 |
| **Reposts** | a quotable maxim, a clear distinction, diverging curves | F2, F18, F20 |
| **Likes** | a real emotional story, a status contrast | F11, F16 |
| **Saves** | simplification, a step-by-step, a stack of evidence | F7, F8, F15, F19 |

## Hook micro-rules

- **"How I did it" beats "How to".** First-person experience outperforms generic
  instruction.
- **A specific number in the first sentence** raises the "see more" rate.
  R$ 47,32 beats "a reasonable amount". 40,000 beats "many".
- **A real failure in the first 3 lines** beats a polished framing. Start with
  what broke.

## Never

- Mix two formulas in the same post (it dilutes both).
- Use F5 (meta-proof) if you will not actually keep the commitment.
- Use F6. It is forbidden in this project.
- Combine F7 (the ledger) with an invented number. Readers notice, and it
  violates HONESTY.
- Use F1 to imply that LinkedIn is an inferior platform.
