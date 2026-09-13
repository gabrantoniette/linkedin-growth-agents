# Review checklist

Look at the contact sheet first, because that is roughly how the deck looks in
a feed. Then inspect the cover and the densest slide at full size.

## At thumbnail size, on the contact sheet

- [ ] The cover headline reads without zooming, and nothing else on the cover
      competes with it.
- [ ] Every slide has one obvious first thing to read.
- [ ] No slide looks like a page of text.
- [ ] The deck reads as one system: the same theme throughout, the headlines
      starting at the same height.
- [ ] The slide that carries the main evidence is visibly the strongest slide,
      not buried in the middle of three similar ones.
- [ ] No slide is thin. Two short items, or one sentence with a line of support,
      usually belongs merged into the slide next to it when both make the same
      point.

## At full size, with inspect_slides

- [ ] No headline ends on a lonely short word, and no word is broken across
      lines.
- [ ] Code: the highlighted lines are the ones the headline talks about, the
      listing is not shrunk below comfortable reading, and the report did not
      mask something that should not have been in the code at all.
- [ ] Screenshots: the part that proves the point is visible, not cropped away,
      and the source is on the slide.
- [ ] Screenshots: the text that proves the point reads at full slide size, and
      no line is cut at the edge of the capture. If not, capture a narrower
      window or an element, or replace it with a `quote` slide
      (`proof-screenshots` skill).
- [ ] Metrics: the number appears in the post, and the source line says where
      it comes from.
- [ ] At most one emphasis mark per slide, and none in a headline.
- [ ] The closing slide asks the same question as the post.

## The text

- [ ] It sounds like the user (the VOICE rules), not like a slide template:
      no "Contexto", "Principais aprendizados", "Conclusão".
- [ ] No claim on a slide that the post does not make.
- [ ] Portuguese conventions: decimal comma, `R$ 47,32`, quotes as “ ”.

## When something fails

Fix the spec, not the render. Cut words, split a slide in two, pick another
layout, crop the screenshot with a selector. The studio already shrinks type as
far as it can be read; if that is not enough, the slide has too much on it.
