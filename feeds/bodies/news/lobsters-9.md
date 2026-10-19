For quick and dirty rendering of simple dynamic content, you may not need the complexity of a templating language like Handlebars or a PHP backend.

Let’s use the example phrase, *“Come on, it’s `<currentYear>`”*. It should result in *“Come on, it’s ”* when rendered today.

You can write this directly in HTML—*without IDs, classes, or querySelectors in your JS!* Thanks to the [`document.currentScript`](https://developer.mozilla.org/en-US/docs/Web/API/Document/currentScript) property, we can refer to the *currently running `<script>` element* directly and go from there.

So the dynamic phrase **“Come on, it’s ”** would now be written as:

```
Come on, it’s
<script>
  document.currentScript.replaceWith(new Date().getFullYear())
</script>
```

The script simply replaces itself with its computed value on the spot.

The code’s a bit wordy though, but we can *alias* it to a constant like `$` via `$=(...n)=>document.currentScript.replaceWith(...n)`. Then we’d have something reminiscent of [template literals](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Template_literals) in JS.

```
Come on, it’s <script>$(new Date().getFullYear())</script>
```

The code is pretty readable at a glance without context (after you get past the bit of indirection that is the `$` alias).

This is the `RenderJS` custom element. All it does is replace itself with the result of its contents treated as JavaScript code.

To use it, we must first name the tag. The beloved dollar sign `$` is not allowed, so we use the next best thing—the emoji 💲. Sadly, that’s not enough: Tag names must start with a letter of the alphabet and include a hyphen. As such, we are forced to name it: `j-💲` representing JavaScript.

```
<script>customElements.define('j-💲', RenderJS);</script>
```

### Example usage

```
I overslept by about <j-💲>Math.PI</j-💲> hours this morning.
```

A [`noscript`](https://developer.mozilla.org/en-US/docs/Web/HTML/Element/noscript) fallback would be nice for those that don’t run JS.

```
Come on, it’s
<noscript>current year</noscript>
<script>$(new Date().getFullYear())</script>
```

The resulting script-noscript juxtaposition in the markup looks almost like Angular/Vue’s if-else markup, neat.

## Real world examples

If you thought this technique is only useful for rendering the current year, you’re mostly right! As an example, I’ve used inline scripts to refer to relative dates in my living pages. Because **“ years ago”** sounds more natural than **“2017”**.

```
It was planted
<noscript>in 2017</noscript>
<script>$(new Date().getFullYear()-2017, ' years ago')</script>
but now it has grown tall and strong.
```

### Random greeting

Another example is in my front page, which says a randomly selected greeting on each visit.

```
<span class="intro-line">
  <noscript>Hello!</noscript>
  <script>
    $([
      "Hello!",
      "Hey~~~",
      "What’s up ↑",
      "Hi there →",
      "Hey there →",
    ][Date.now() % 5])
  </script>
</span>
```

### Splitting text for animation

Split text into characters using inline scripts to generate markup per character which can then be controlled or animated! In my case, I used it to render circular text, but a more common use case is text animation like the following.

```
It has been a
<script>document.currentScript.outerHTML=
  "supercalifragilisticexpialidocious"
    .replace(/./g, c => `<strong>${c}</strong>`)
</script>
week.

<style>
  strong {
    display: inline-block;
    animation: wave 0.3s infinite alternate ease-in-out;
    &:nth-child(4n + 1) { animation-delay: -0.6s; }
    &:nth-child(4n + 2) { animation-delay: -0.45s; }
    &:nth-child(4n + 3) { animation-delay: -0.3s; }
    &:nth-child(4n + 4) { animation-delay: -0.15s; }
  }
  @keyframes wave {
    to { transform: translateY(-2px); }
  }
</style>
```

Why import a text splitting library?

### Rendering metadata to reduce duplication

This post’s heading is dynamically derived from the page title metadata. I only have to define this post’s title once, in the `<title>` tag.

```
<blog-header>
  <h1><script>$(document.title)</script></h1>
  <img src="hero.jpg" alt="" loading="lazy"></img>
</blog-header>
```

### Auto-updating footer

How about an auto-updating copyright notice in the footer which may or may not have legal implications? <small>(IANAL)</small>

```
<footer>
  © <script>$(new Date().getFullYear())</script> Mycorp, Ltd.
</footer>
```

For comparison, here’s the StackOverflow/ChatGPT answer:

```
document
  .getElementById("copyright-year")
  .textContent = new Date().getFullYear();
```

```
<footer>
  © <span id="copyright-year"></span> Mycorp, Ltd.
</footer>
```

Why pollute the global ID namespace and separate coupled code if we can avoid it?

At this point you may be asking, is this technique only really useful for rendering the current year? Maybe, but we can do more than just *rendering* text.

Come on, it’s , the web is rich and interactive!

### The ubiquitous counter app example

This is not a simple templating example anymore, but shows the power of `currentScript` in [hydrating](https://en.wikipedia.org/wiki/Hydration_(web_development)) self-contained bits of interactive HTML.

```
<div>
  Count: <span>0</span>
  <button>Increment</button>
  <button>Decrement</button>
  <script>
    const [span, increment, decrement] =
      document.currentScript.parentElement.children;
    let count = 0;
    increment.onclick = () => span.replaceChildren(++count);
    decrement.onclick = () => span.replaceChildren(--count);
  </script>
</div>
```

I used this ‘local script’ pattern all the time in a previous version of this blog. It’s useful when making interactive illustrations in the middle of a long post. You wouldn’t want to put that logic at the very end or start of the file, away from the relevant section! Same goes for styles, now made even better with the [`@scope` rule](https://developer.chrome.com/docs/css-ui/at-scope#prelude-less_scope).

It’s a good way to manage islands of interactivity.

## The catch

There are reasons people gravitate to libraries and frameworks. They’re just too convenient.

If you want to use the alias definition above—the `$` shorthand—then you'd first have to define it at the top of the HTML, **synchronously**. Say you want to use this in multiple pages, so you put this in a common script file and load it via `<script src="$.js"</script>`. This could result in a parser- and render-blocking fetch: potentially very bad for performance!

For my own cases, I don’t use the alias. I straight up just use `document.currentScript​.replaceWith`. Wish it was  [shorter…](https://developer.mozilla.org/en-US/docs/Web/API/Document/write)

<del>Also, you cannot do **data-driven templating** this way, in the sense that you have **templates** to apply **data** onto. Metadata such as date published, post title, and tags that are stored in some posts table or in frontmatter somewhere, cannot be used for inline scripting purposes. You can’t fetch data from inline scripts. Therefore, unless data is somehow pre-injected in the global scope, no luck in pure vanilla JS templating. This is where templating languages like [Liquid](https://shopify.github.io/liquid/) really shine.</del>

## Update: Data-driven templating

I previously said that you cannot do **data-driven templating** this way (see deleted section above). However, a nice reader has found a way to do so (thanks Amier)!

All you need is to save the `currentScript` in a variable, then you can refer to it in any async operation!

Here’s the code for that: [jsfiddle](https://jsfiddle.net/0xh2mg8f/).

```
<ul class="posts">
  <script>
    const script = document.currentScript;
    fetch("/posts.json") 
      .then(response => response.json()) 
      .then(data => data.map(p => (
        `<li><a href="${p.url}">${p.title}</a></li>`
      )).join(""))
      .then(html => script.outerHTML = html);
  </script>
</ul>
```

It incurs an extra HTTP request on the client, though, unlike backend-side templating systems.

For my site, I don’t need a templating system—I use direct patching to data-drive my HTML (in which the source and the output files are the same).

Even if you use a templating framework or a static site generator, inline scripts remain useful!

## Further reading

- Surreal - a library that offers this technique, plus other jQuery-style helpers. Note the synchronous script tag loading issue though!
- currentScript discussion in SvelteKit - this as an alternative to global IDs for self-hydrating things. In the end they went with generated IDs. :|

## Appendix

[`document.write()`](https://developer.mozilla.org/en-US/docs/Web/API/Document/write) used to (?) work like this for inline rendering, but it’s now deprecated because it had inconsistent behaviour.