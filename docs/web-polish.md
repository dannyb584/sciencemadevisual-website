# Web polish notes

Reusable patterns and a vetted library shortlist for making Danny's static sites (SMV, PCCE) feel more alive without adding a build step.

## What the SMV site uses now (no dependencies)

Everything lives in `index.html`, in the CSS block and script section both labelled **ENGAGEMENT LAYER**.

| Pattern | How it works |
|---|---|
| Motion opt-in | A tiny inline script in `<head>` adds `.motion` to `<html>` only when `prefers-reduced-motion` is not set. All hiding and animation is scoped under `.motion`, so content is always visible without JS and for reduced-motion users. |
| Scroll reveal | `IntersectionObserver` adds `data-reveal` and `--i` (stagger index) to elements, then `.in` when they enter view. The CSS fades and slides them up with `transition-delay: calc(var(--i) * 70ms)`. After revealing, `data-reveal` is removed so card hover transitions go back to normal. |
| Filter pills | Built from the `TOPICS` keyword map in the script. Each episode's drug class comes from its title, so new `SERIES` entries need no extra field. Buttons use `aria-pressed`, and an `aria-live` line announces "Showing X of Y". |
| Category chips | `.chip` / `.chip-accent`: topic and episode number on each video card, "3D printed" / "STL file" badges on shop cards. |
| Pill nav | An absolutely positioned `.nav-pill` slides (`transform` + `width`) to whichever nav link's section is in view. Uses `IntersectionObserver` with `rootMargin: -45% 0px -50% 0px`. |
| Scroll progress | CSS-only, `animation-timeline: scroll(root)` inside `@supports`. Browsers without support simply don't show it. |
| Marquee | The list is duplicated once in JS (copy marked `aria-hidden`), then animated with `translateX(calc(-50% - gap/2))` for a seamless loop. Pauses on hover/focus; with reduced motion it becomes a static wrapped row. |
| Counter | `requestAnimationFrame` with ease-out-cubic counts up to the total number of `SERIES` episodes. |
| Spotlight hover | `pointermove` sets `--mx/--my` on the card, and a `::after` radial gradient follows the cursor. |

### Snippet: reveal on scroll (drop-in)

```html
<script>if (matchMedia('(prefers-reduced-motion: no-preference)').matches) document.documentElement.classList.add('motion');</script>
<style>
  .motion [data-reveal] { opacity: 0; transform: translateY(24px); transition: opacity .7s cubic-bezier(.2,.8,.2,1), transform .7s cubic-bezier(.2,.8,.2,1); transition-delay: calc(var(--i,0) * 70ms); }
  .motion [data-reveal].in { opacity: 1; transform: none; }
</style>
<script>
  const io = new IntersectionObserver(es => es.forEach(e => { if (e.isIntersecting) { e.target.classList.add('in'); io.unobserve(e.target); } }), { threshold: .12 });
  document.querySelectorAll('[data-reveal]').forEach((el, i) => { el.style.setProperty('--i', i % 6); io.observe(el); });
</script>
```

### Rules of thumb
- Animate only `transform` and `opacity` (GPU-cheap). Never animate `width`/`top` on scroll.
- Keep durations between 0.2s (hover) and 0.8s (reveal). Use one easing everywhere: `cubic-bezier(.2,.8,.2,1)`.
- One accent colour: Electric Lime `#C6FF3D` is either text on graphite (15:1+) or a fill with `#0A0A0C` text (16:1). Never lime text on white.
- Always check mobile with `document.documentElement.scrollWidth === innerWidth`. Unwrapped flex rows are the usual cause of overflow.

## Library shortlist (licences checked on GitHub, 30 Oct 2026)

| Library | Licence | Good for | Verdict |
|---|---|---|---|
| [Motion](https://github.com/motiondivision/motion) (motiondivision/motion) | MIT | `animate()`, `inView()`, `scroll()` and springs in about 3–5 kB of vanilla JS from a CDN | **First choice** if we outgrow hand-rolled CSS. |
| [GSAP](https://github.com/greensock/GSAP) | Standard "no charge" licence (free, including commercial use and all plugins since the Webflow deal). **Not OSI/MIT.** | Timelines, ScrollTrigger pinning, SplitText headline reveals | Best-in-class power. Fine to *use* via CDN, but can't be copied into an open-source repo as MIT code. |
| [Lenis](https://github.com/darkroomengineering/lenis) | MIT | Buttery smooth scrolling, pairs with GSAP/Motion | Nice-to-have. Test with embedded iframes first. |
| [AOS](https://github.com/michalsnik/aos) | MIT | `data-aos="fade-up"` attribute reveals, zero JS knowledge needed | Simple, but unmaintained since 2024. Our observer does the same in 20 lines. |
| [AutoAnimate](https://github.com/formkit/auto-animate) | MIT | One-line animated add/remove/reorder of list items | **Great fit** for the filter grid if we want cards to glide into new positions. |
| [anime.js](https://github.com/juliangarnier/anime) | MIT | Lightweight timelines, SVG line-drawing, stagger helpers | Good for animated molecule/receptor SVGs. |
| [Open Props](https://github.com/argyleink/open-props) | MIT | CSS custom-property tokens: easings, shadows, keyframes | **Borrow the easing and animation tokens.** Pure CSS, no build. |
| [Uiverse](https://github.com/uiverse-io/galaxy) | MIT | 3,000+ copy-paste HTML/CSS buttons, toggles, loaders and cards | Mine for one-off micro-interactions. Credit the author in a comment. |
| [Magic UI](https://github.com/magicuidesign/magicui) | MIT | Marquee, number ticker, shimmer button, bento grid (React/Tailwind) | Inspiration and recipes. Port ideas to vanilla. |
| [Animata](https://github.com/codse/animata) | MIT | Hand-picked animated components (React/Tailwind) | Same as Magic UI. |
| Aceternity UI (ui.aceternity.com) | No public repo or licence found | Spotlight cards, beams, 3D card effects | **Inspiration only.** Don't copy code. |

**Attribution rule:** when borrowing MIT code, keep the copyright line in a comment next to it, e.g. `/* Adapted from Uiverse.io by @author (MIT) */`.

## Possible next steps
1. Add AutoAnimate (`https://cdn.jsdelivr.net/npm/@formkit/auto-animate@0.8.2/index.min.js`) to the medications grid for gliding filter transitions.
2. Use anime.js SVG line-drawing for a small animated receptor or channel motif in the hero.
3. Bring the reveal and pill patterns to PCCE once Danny is happy with SMV.
