**I tested eight popular SVG sanitizers and bypassed six of them. In this post, I'll show you how a response header can run JavaScript in Firefox even when the response body is completely harmless XML. I'll also show you how to get Safari to import a GIF as SVG and execute JavaScript from it. **

SVG is an image format that can contain scripts, event handlers, links, animations and even embedded HTML, so applications that accept SVG uploads usually run them through a sanitizer first. To see how well those sanitizers hold up, I tested the most popular SVG libraries according to ChatGPT:

- [https://github.com/darylldoyle/svg-sanitizer](https://github.com/darylldoyle/svg-sanitizer)
- [https://github.com/cloudflare/svg-hush](https://github.com/cloudflare/svg-hush)
- [https://github.com/cure53/DOMPurify](https://github.com/cure53/DOMPurify)
- [https://github.com/Borewit/svg-sanitizer](https://github.com/Borewit/svg-sanitizer)
- [https://github.com/bgalek/safe-svg](https://github.com/bgalek/safe-svg)
- [https://github.com/mattkrick/sanitize-svg](https://github.com/mattkrick/sanitize-svg)
- [https://github.com/alnorris/SVG-Sanitizer](https://github.com/alnorris/SVG-Sanitizer)
- [https://github.com/jams2/py-svg-hush](https://github.com/jams2/py-svg-hush)

**Library affected: mattkrick/sanitize-svg**

This library has so many bypasses that I'll only cover the interesting ones.

My first finding was that you don't need `<foreignObject>` to get HTML into an SVG. Switch the XML namespace on a single element to XHTML and the browser renders it as HTML directly inside the SVG. A `<frame>` with a JavaScript URL is all it takes:

The same namespace trick works with iframes, which gives you srcdoc to play with:

The library could also be bypassed with a plain old `<foreignObject>`. It renders the SVG, which converts the element name to its camel-case form, foreignObject. It then hunts for the element with `querySelectorAll('foreignobject')`, which finds nothing, so the payload goes straight through:

Even a nested SVG with an onload handler got through:

**Library affected: Borewit/svg-sanitizer
**

This one didn't take much effort. The library let `<animate>` tags through untouched, so you could animate a link's href into a JavaScript URL:

I bypassed the same library a second way using 
[Kevin Mizu's](https://x.com/kevin_mizu)
[trick](https://mizu.re/post/dompurify-bypass-smil-animatetransform-safari), which uses <animateTransform> to set a JavaScript URL in Safari:

**Libraries affected: bgalek/safe-svg, mattkrick/sanitize-svg, alnorris/SVG-Sanitizer**

Now things get more interesting. This is a pretty epic technique: you can get JavaScript execution from an XSLT stylesheet without needing a separate file. I was desperate to blog this one, because unfortunately the feature is deprecated and due for removal November 2026.

The trick is to point an xml-stylesheet processing instruction at a data URL. Base64 is the most elegant way to encode the stylesheet, but URL encoding works too:

Here's the stylesheet that gets base64 encoded:

It matches the root of the document and outputs an HTML page containing a script that alerts document.domain, proving the code runs in the document's origin rather than a null origin. Put it all together and you get this:

In the back of my mind was a trick 
[Paulos Yibelo](https://x.com/PaulosYibelo) once told me about: Firefox lets you load external CSS files using a Link response header. I figured out that data URLs work there too, which got me thinking: if it works for CSS, could it work for XSLT too? You're damn right it can.

First, I needed a version of the stylesheet that fits in a URL. This one has two layers. The outer stylesheet is URL encoded into a data URL. Inside it, XSLT's `document()` function loads a second data URL, URL encoded again, containing an XHTML `<img>` with an `onerror` handler. The stylesheet copies that into a `<foreignObject>`, where it fires.

As a processing instruction, it looks like this:

Here's the payload before encoding. I've left the Hackvertor tags in so you can see where each layer of URL encoding is applied:

You can load and 
[edit the full payload in Hackvertor](https://hackvertor.co.uk/#PD94bWwgdmVyc2lvbj0iMS4wIiBlbmNvZGluZz0iVVRGLTgiPz4KPD94bWwtc3R5bGVzaGVldCB0eXBlPSJ0ZXh0L3hzbCIgaHJlZj0iZGF0YTphcHBsaWNhdGlvbi94bWwsPEBlbmNvZGUodXJsKT48eHNsOnN0eWxlc2hlZXQgdmVyc2lvbj0iMS4wIiB4bWxuczp4c2w9Imh0dHA6Ly93d3cudzMub3JnLzE5OTkvWFNML1RyYW5zZm9ybSI+PHhzbDp0ZW1wbGF0ZSBtYXRjaD0iLyI+PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSI0MDAiIGhlaWdodD0iMjAwIj48Zm9yZWlnbk9iamVjdCB3aWR0aD0iNDAwIiBoZWlnaHQ9IjIwMCI+PHhzbDpjb3B5LW9mIHNlbGVjdD0iZG9jdW1lbnQoJ2RhdGE6YXBwbGljYXRpb24veG1sLDxAZW5jb2RlKHVybCk+PGRpdiB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMTk5OS94aHRtbCI+PGltZyBzcmM9IjEiIG9uZXJyb3I9ImFsZXJ0KGRvY3VtZW50LmRvbWFpbikiIC8+PC9kaXY+PC9AZW5jb2RlPicpLyoiLz48L2ZvcmVpZ25PYmplY3Q+PC9zdmc+PC94c2w6dGVtcGxhdGU+PC94c2w6c3R5bGVzaGVldD48L0BlbmNvZGU+Ij8+CjxzdmcgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48L3N2Zz4=).

With the stylesheet ready, all that's left is to move it out of the document and into a Link header:

The response body is a completely harmless bit of XML, yet 
[this executes in Firefox!](https://02.rs/crazy-firefox-behaviour-jdhwieo292/)

**Libraries affected: cloudflare/svg-hush, jams2/py-svg-hush, bgalek/safe-svg
**

To end this piece of research, here's another epic behaviour, this time in Safari. Firefox and Safari both let you use the <use> element to reference same-origin files, but Safari goes a step further: it lets you import image files as SVG!

index.svg:

test.png:

Alas, you can't make a true SVG/image polyglot because SVG is a little too strict. However, if you can upload a GIF that contains the payload, it won't render when you open it in the browser, but it can still be imported with a `<use>` element!

That's all it takes to bypass all three libraries:

I hope you enjoyed this post. I also exploited two popular applications that I can't name yet, but I'll update the post once I can. Both DOMPurify and darylldoyle/svg-sanitizer held up against everything in this post, which is quite impressive.