They’re calling the new feature *Adaptive Dark Mode<sup>™</sup>*. I’m learning that other browsers already had a [similar feature](https://help.vivaldi.com/desktop/appearance-customization/browser-appearance-customization-on-desktop/#Website_Appearance). I assumed people relied on add-ons like [Dark Reader](https://addons.mozilla.org/en-US/firefox/addon/darkreader/) (and millions do). Regardless, pushing what is effectively an accessibility option to the forefront goes a long way to help people respect it.

## My dark mode

My site [used to have dark mode](https://dbushell.com/2020/08/05/i-have-only-gone-and-redesigned-my-website-again/#dark-mode) but [I wasn’t happy](https://dbushell.com/2025/03/21/blog-redesign/#dark-mode) with my colour choice and implementation. [I redesigned my site](https://dbushell.com/2026/02/09/big-design-and-bold-ideas/) back in Feb and removed it. Later I experimented with [colour themes](https://dbushell.com/2026/07/16/choose-your-own-dark-mode/) which I’ve since adapted for [alternate blog banners](https://dbushell.com/notes/2026-09-28T05:49Z/).

In that experiment I said:

> Personally I prefer reading with a dark theme for long-form content. Dark is not my brand though and I don’t believe every website needs to support [colour scheme preference](https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/At-rules/@media/prefers-color-scheme) automatically. A good browser has reader mode, I use that all the time.

“Just enable reader mode!”

What a load of rubbish. You have to understand that sometimes I just write stuff and I don’t read it back. This also contradicted my previous statement:

> That said, in [current year] brands with a digital presence — all of them? — should have a colour scheme for both.

That’s probably more true.

Certainly websites must work for forced dark mode. (Any site forcing `light only` itself upon users should go straight to jail.) So either provide a dark mode, or be prepared to test against every adaptive and forced dark mode implementation, or just let your website look broken. Probably easier to design a dark mode then?

So that’s what I did, again.

Maybe you noticed? If not, there’s a toggle button up top. At the risk of weighing in on [the conversation](https://lea.verou.me/blog/2026/dark-mode-toggles/) I’ve opted for a two-state single button. I default to system preference. The mystery button flips between light and dark. Want to return to system default? Tough luck! You shouldn’t have clicked it. Delete [local storage](https://developer.mozilla.org/en-US/docs/Web/API/Window/localStorage) nerd!

## My code

Technically I’m using a [registered custom property](https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/At-rules/@property) with [container style queries](https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/At-rules/@container#container_style_queries) because it looks like fancy modern CSS. Three at-rules!

```
@property --theme {
  syntax: "light | dark";
  initial-value: light;
  inherits: true;
}

@media (prefers-color-scheme: dark) {
  html {
    --theme: dark;
  }
}

@container style(--theme: dark) {
  body {
    /* make it dark */
  }
}
```

Most of my light/dark theming is done by customs properties. The default light colours (A) are set on the root `<html>` element. A style query applies the dark colours (B) on the `<body>` element. For edge cases that don’t follow the A/B rule I can use one of two techniques.

Either a style query inside a specific component:

```
.Component {
  color: var(--theme-A);

  @container style(--theme: dark) {
    color: var(--theme-C);
  }
}
```

Or use the `light-dark()` function:

```
.Component {
  color-scheme: var(--theme);
  color: light-dark(var(--theme-A), var(--theme-C));
}
```

Note that I set `color-scheme` to make `light-dark()` aware of the user’s choice that might override their system preference. I wonder if I can do this once:

```
body {
  color-scheme: var(--theme); /* safe? */
}
```

Is that safe? Let me know!

It’s not safe to do on the root `<html>` element because browsers checks that for adaptive dark mode etc. I’ll stick to the verbose style queries for now until I’m sure.

There’s a sprinkle of JavaScript to use local storage for the toggle button.

```
document.documentElement.style.setProperty("--theme",
  localStorage.getItem("--theme") ??
  (window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light")
);
```

It’d be better to use a cookie and a server-side template. My website is hosted on a [static CDN](https://dbushell.com/2025/04/27/bunny-cdn-edge-storage/) and I’m not adding edge worker latency, so I’ll risk [*Flash of inAccurate coloR Theme* (FART)](https://css-tricks.com/flash-of-inaccurate-color-theme-fart/). My site only risks a FART if a user’s choice doesn’t match their system preference. A week into my [Noscript November](https://dbushell.com/notes/2026-11-01T07:21Z/) experiment I see most websites are prone to a big FART because they rely entirely on JavaScript to enable dark mode.

I’m not happy with my button using a hidden label. Bit of a design failure I need to address later. My original goal was to have multiple themes but I ran out of time.

At the risk of soliciting replies to a question I didn’t ask, I would like your feedback on my choice of dark mode colours! **Do they look nice?** I don’t care whether dark mode makes your eyes bleed (turn it off) or you absolutely must have a 4-dimensional toggle.

## Elsewhere

[Stephanie Eckles](https://thinkdobecreate.com/articles/simplified-dark-mode-with-style-queries/) wrote about the same CSS technique I use. [Dave Rupert](https://daverupert.com/2026/04/inverted-light-dark/) has explored the `light-dark()` with `color-scheme` variations. I saw [Una Kravets](https://una.im/modern-css-theming) is using `contrast-color()` with style queries to do something extra fancy. [Stu Robson](https://www.alwaystwisted.com/articles/dynamic-colour-schemes-with-modern-css) has written in depth on dynamic colour schemes too. [Sara Joy](https://css-tricks.com/come-to-the-light-dark-side/) has a great CSS-Tricks article on the topic.

If you read this entire post in an RSS reader and never clicked through, what a power move!