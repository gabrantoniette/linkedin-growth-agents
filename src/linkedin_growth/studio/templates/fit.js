async () => {
  // Runs inside the page after load. Waits for the real fonts, shrinks type
  // that does not fit (never below each element's data-min), and reports what
  // still overflows. The report is what the render turns into errors: a slide
  // whose text is clipped must never be written out as finished.
  await document.fonts.ready;

  const images = [...document.images];
  await Promise.all(
    images.map((img) =>
      img.complete ? null : new Promise((done) => { img.onload = img.onerror = done; })
    )
  );

  const fontsOk = [
    '400 40px "Inter"',
    '800 40px "Inter"',
    '500 24px "JetBrains Mono"',
    'italic 400 40px "Instrument Serif"',
  ].every((face) => document.fonts.check(face));
  const broken = images.filter((img) => !img.naturalWidth).map((img) => img.getAttribute('src'));

  const size = (el) => parseFloat(getComputedStyle(el).fontSize);
  const slides = [];

  for (const slide of document.querySelectorAll('.slide')) {
    const box = slide.querySelector('[data-box]');
    const stack = box.querySelector('.stack');
    const overflow = () => Math.max(
      0,
      Math.ceil(stack.scrollHeight - box.clientHeight),
      Math.ceil(stack.getBoundingClientRect().height - box.getBoundingClientRect().height)
    );

    // Width first: code and big numbers lose a pixel at a time until the
    // widest line fits the frame. An element can name an inner [data-measure]
    // sized to its content, which is how a code window measures its widest
    // line without counting its own padding.
    const tooWide = (el) => {
      const measure = el.querySelector('[data-measure]');
      if (!measure) return el.scrollWidth > el.clientWidth + 1;
      const style = getComputedStyle(el);
      const room = el.clientWidth - parseFloat(style.paddingLeft) - parseFloat(style.paddingRight);
      return measure.getBoundingClientRect().width > room + 1;
    };
    for (const el of slide.querySelectorAll('[data-fit-x]')) {
      const min = parseFloat(el.dataset.min || '20');
      let px = size(el);
      while (tooWide(el) && px > min) {
        px -= 1;
        el.style.fontSize = px + 'px';
      }
    }

    // Then height: every fitted element shrinks by the same factor, so the
    // hierarchy between headline and body survives the squeeze.
    const targets = [...slide.querySelectorAll('[data-fit]')];
    const base = targets.map(size);
    const floor = targets.map((el, i) => Math.min(base[i], parseFloat(el.dataset.min || String(base[i] * 0.75))));
    const apply = (factor) => targets.forEach((el, i) => {
      el.style.fontSize = Math.max(floor[i], base[i] * factor) + 'px';
    });

    if (overflow() > 0) {
      let low = 0.3;
      let high = 1;
      for (let step = 0; step < 16; step++) {
        const middle = (low + high) / 2;
        apply(middle);
        if (overflow() > 0) high = middle; else low = middle;
      }
      apply(low);
    }

    const shrunk = targets.length ? Math.min(...targets.map((el, i) => size(el) / base[i])) : 1;
    const wide = [...slide.querySelectorAll('[data-fit-x]')].filter(tooWide).length;

    slides.push({
      index: Number(slide.dataset.index),
      layout: slide.dataset.layout,
      overflow: overflow(),
      shrunk: Math.round(shrunk * 1000) / 1000,
      wide,
    });
  }

  return { fontsOk, broken, slides };
}
