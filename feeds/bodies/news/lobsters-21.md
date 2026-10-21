Unfortunately, accessibility is often an afterthought when designing a website. Maybe you came up with a color palette you’re happy with, but it doesn’t quite jive with the [WCAG 2 success criteria](https://www.w3.org/TR/WCAG21/#contrast-minimum) for contrast, or perhaps the animations on your website got a bit out of hand.

Fortunately, there are some newly supported but underutilized CSS media queries that can be leveraged to improve accessibility without having to scrap the design and starting over—by considering *user preferences*.

The user preferences that can be targeted with media queries control contrast, motion, color schemes and transparency. These can be configured in the accessibility or display settings of the operating system.

## [prefers-contrast](https://fleeb.ee/blog/improving-accessibility-with-css-media-queries/#prefers-contrast)

A good contrast ratio by default is always a nice thing to have, but it can sometimes be difficult to pull off while maintaining the desired aesthetic. By using `prefers-contrast` we can boost the contrast of our content for users who have expressed a preference for that while retaining the original style for the rest.

```
.blue {
  color: rgb(117, 105, 255);

  @media (prefers-contrast: more) {
    color: rgb(44, 0, 255);
  }
}
```

To help identify contrast issues, a color can be clicked in the developer tools to show the contrast ratio between it and its background. The WCAG 2 recommends a minimum contrast ratio of **4.5** for small text and **3.0** for large text such as headers.

There’s no need to do this one by one: Most browsers come with tools that automatically list all contrast issues on a website.

## [prefers-reduced-motion](https://fleeb.ee/blog/improving-accessibility-with-css-media-queries/#prefers-reduced-motion)

Many users experience discomfort because of motion-based or blinking animation. If non-essential animations can be identified, it’s a good idea to disable (or *reduce*) them for people who prefer reduced motion.

One can also choose to obliterate all animation on their page using the following CSS:

```
@media (prefers-reduced-motion: reduce) {
  * {
    animation: none !important;
    transition: none !important;
  }
}
```

It’s worth checking the resulting page for unintended side-effects after employing this method.

## [prefers-color-scheme](https://fleeb.ee/blog/improving-accessibility-with-css-media-queries/#prefers-color-scheme)

If you haven’t been living under a rock, you’re probably familiar with the concept of light and dark modes. Designing two palettes is double the work, but for those who want to go the extra mile, there’s `prefers-color-scheme`:

```
:root {
  --color-text: black;
  --color-background: white;
}

@media (prefers-color-scheme: dark) {
  :root {
    --color-text: white;
    --color-background: black;
  }
}

.theme-aware-element {
  color: var(--color-text);
  background-color: var(--color-background);
}
```

A common pattern is to define CSS variables for your colors, and then use those variables everywhere so you only have to write one `prefers-color-scheme` query for the entire website. Easy.

In fact, as of 2024 you can also use [`color-scheme`](https://developer.mozilla.org/en-US/docs/Web/CSS/color-scheme) and [`light-dark()`](https://developer.mozilla.org/en-US/docs/Web/CSS/color_value/light-dark) to achieve the same result:

```
:root {
  color-scheme: light dark;
  --color-text: light-dark(black, white);
  --color-background: light-dark(white, black);
}

.theme-aware-element {
  color: var(--color-text);
  background-color: var(--color-background);
}
```

`color-scheme` is handy because it helps the browser apply default colors that match the preferred color scheme for scrollbars, selections etc.

## [prefers-reduced-transparency](https://fleeb.ee/blog/improving-accessibility-with-css-media-queries/#prefers-reduced-transparency)

This one is experimental and at the time of writing isn’t supported by Firefox or Safari out of the box. I’d advise to be conservative with translucency as long as that remains the case.

```
.translucent {
  opacity: 0.6;

  @media (prefers-reduced-transparency) {
    opacity: 1;
  } 
}
```

It’s important to recognize that while accessibility preferences are mostly binary on/off settings, the impairments individuals suffer from fall into a wider spectrum. It’s probably a good idea to design reasonably accessible interfaces as a starting point.

These media queries are no silver bullet, but they can come in handy when you need some more flexibility in a pinch.