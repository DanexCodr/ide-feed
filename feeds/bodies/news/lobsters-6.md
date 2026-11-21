A few weeks ago Kev Quirk asked: [Do you use `:visited` on links?](https://kevquirk.com/do-you-use-visited-on-links) — and I said to myself: No! I don’t use visited links… but why *don’t* I use visited links?

TL;DR: I’ve gone and styled visited links, and they’re purple.

## Blue and purple

I did a cursory five minutes of research and found Wikipedia still styles visited links (blue to purple). [MDN](https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/Selectors/:visited) does too. As does the [GOV.UK design system](https://design-system.service.gov.uk/styles/links/) — they have a special class to opt-out of the visited style. [BBC News](https://www.bbc.co.uk/news) turns black links to grey, how emo.

I decided to style visited links within my `<main>` body copy. Which to be fair is most links but not the big headings on [my blog index](https://dbushell.com/blog/) for example. I was too intimidated to turn those purple. Maybe you can give me the courage to style those too?

It looked a bit weird at first but I like the [colourful additions](https://dbushell.com/2026/11/09/dark-mode/) to my blog.

## Accessibility

WCAG 2.2 guidelines have no requirement to differentiate visited from unvisited links. Regardless, visited links should meet all the same criteria applied to any link.

There is one specific exception ([following this discussion](https://github.com/w3c/wcag/issues/905)). Because web browsers have strict style limitations and technical constraints due to [privacy concerns](https://developer.mozilla.org/en-US/docs/Web/CSS/Guides/Selectors/Privacy_and_:visited):

> Where color alone distinguishes between visited and unvisited links, it does not result in a failure of this Success Criterion, even where the contrast between the two link colors is below 3:1.
>
> [SC 1.4.1 Use of Color (Level A)](https://www.w3.org/WAI/WCAG22/Understanding/use-of-color.html#:~:text=Most%20user%20agents,background%20%28SC%201.4.3%29)

This means that a subtle contrast different in blue vs purple is not considered an accessibility failure under that rule.

Web accessibility is all about ensuring a *comparable* experience for all users. Nothing can be perfectly accessible though. I think this small enhancement is fine, even if not everyone can see the difference. It’s a rare exception though. I’m conscious that too often excuses are made to ignore UX parity. I think any higher contrast or another visual indicator would be off-putting and impede readability. Forgoing any style doesn’t help anyone either. If blue and purple is good enough for those examples mentioned above, I’m on board.

[Bryce Wray commented](https://kevquirk.com/do-you-use-visited-on-links#:~:text=Reply-,Bryce%20Wray) on Kev Quirk’s blog to note that Chromium browsers introduced [`:visited` link partitioning](https://developer.chrome.com/blog/visited-links) in 2025. I had no idea this was a thing!

What do you think, do you care about visited link styles?

## Bubbles

I found Kev Quirk’s blog on [bubbles.town](https://bubbles.town/). Bubbles is a charming social RSS aggregator. It’s doing a great job at supporting small personal blogs and promoting non-toxic topics. Bubbles is far from perfect though. It probably needs a tech filter. It certainly needs more participation in comments and voting. The developer is actively working to improve the site and a community is growing, so that’s cool to see.

I hope Bubbles can thrive and remain human. This is the web we need to bypass the dead web *Google et. al.* are gatekeeping. Let them wall themselves in with their slop!