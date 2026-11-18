jQuery 4.1.0 has arrived! And it brought a friend. Alongside the first minor release of the 4.x line, we're also releasing jQuery 3.8.0. A word of caution: 3.8.0 exists to release the fixes and improvements that have been pending on the `3.x-stable` branch for the past few years, some of which you may recognize from the jQuery 4.0.0 release. It is a send-off, not a comeback. Going forward, the 3.x branch will only receive critical security and bug fixes. If you haven't yet made the jump to 4.x, we encourage you to do so — we have an [upgrade guide](https://jquery.com/upgrade-guide/4.0/) and the [jQuery Migrate plugin](https://github.com/jquery/jquery-migrate/) ready to help, and most users will be able to upgrade with minimal changes.

As usual, the releases are available on [our CDN](https://jquery.com/download/) and the npm package manager. Other third party CDNs will probably have them available soon as well, but remember that we don't control their release schedules and they will need some time. Here are the highlights.

## In both 4.1.0 and 3.8.0

A few changes landed on both branches, so you get these no matter which version you're on.

### A new API for AJAX transport complete callbacks

Custom AJAX transports have long received a `completeCallback` with positional arguments:

```
function( status, statusText, responses, headers ) {}
```

Transports can now instead invoke the callback with a single object:

```
function( { status, statusText, responses, headers } ) {}
```

This makes it possible for us to add new parameters in the future without relying on their order, and for transports to provide them selectively. In fact, 4.1.0 already takes advantage of it — see `responseURL` below.

### Selector: ReDoS fix in identifier matching

The regular expression jQuery uses to match identifiers in selectors was vulnerable to catastrophic backtracking; a long chain of hex escapes followed by an invalid character — for example, in an attribute selector — could hang the page. The production now explicitly excludes digits & hex characters where the spec says it should, bringing us closer to spec and eliminating the ReDoS.

### Selector: loose document comparisons everywhere

IE & Edge Legacy sometimes throw on strict document comparisons (`===`) but not on loose ones (`==`). We switched most of these comparisons years ago, but a few leftovers remained in the selector code. They've now all been converted, avoiding some rare crashes in those browsers.

## What else is new in 4.1.0

### jqXHR gains responseURL

`jqXHR` objects now expose `responseURL` — the final URL of the request after any redirects followed by the browser. Following the existing `responseText`/`responseXML`/`responseJSON` pattern, it is only set when the transport can report it: modern-browser XHR provides it, while IE 11 and the script & JSONP transports do not.

### Serialize form-associated custom elements

Form-associated custom elements — custom elements registered with `formAssociated = true` — now serialize correctly with `.serialize()` and `.serializeArray()`. Elements that appear in `form.elements` are trusted to be submittable rather than being filtered out by a tag name check.

### CSS methods work in XML documents

In non-XHTML XML documents, such as XSLT-transformed documents, elements created with `document.createElement` land in the XML namespace and have no `style` property, which broke jQuery's CSS support tests. jQuery now uses `createElementNS` with the XHTML namespace internally, so `.css()` and friends behave in these documents.

### querySelectorAll everywhere

jQuery no longer uses `getElementsByTagName` or `getElementsByClassName` internally, relying on `querySelectorAll` instead. In today's browsers, `qSA` is on par with or faster than the old methods, and returns a static list rather than a live collection that we had to snapshot. The switch also fixes some long-standing bugs, including MathML elements not being found by lowercase tag names on cloned nodes in IE 11, selectors with leading combinators not working on document fragments, and selection by tag names containing less common symbols such as dots.

Related selector work makes the quick selection paths stricter about what counts as a simple tag or class selector — with a fallback to regular selection when `qSA` throws — and invalid escape sequences in selectors are now decoded to U+FFFD, the replacement character, as the CSS specification requires.

### Faster uniqueSort

`jQuery.uniqueSort` removes duplicates with a single-pass, two-pointer compaction instead of repeated splices, taking the duplicate removal from O(N²) time and O(N) extra space to O(N) time and constant space. Behavior and ordering are unchanged; large disconnected sets just get there faster.

## What's in 3.8.0

Again, most of what's in 3.8.0 has been sitting on the branch for a while, and much of it will look familiar if you read the [jQuery 4.0.0 release post](https://blog.jquery.com/2026/01/17/jquery-4-0-0/). But there are a few things specific to 3.x.

### Support for hidden="until-found"

The `hidden` attribute used to be a boolean attribute, but it has since gained the `until-found` value. jQuery 3.x normalized boolean attributes in a way that clobbered that value; `.attr( "hidden", "until-found" )` now sets it as-is. jQuery 4.x changed how boolean attributes are handled precisely to avoid this class of problem, so no change was needed there.

### Deprecations to smooth the road to 4.x

Two sets of APIs that were removed in jQuery 4.0.0 are now formally deprecated in 3.x, which means the [jQuery Migrate plugin](https://github.com/jquery/jquery-migrate/) can warn you about them before you upgrade:

- The push, sort & splice Array methods on the jQuery prototype. These were always meant for internal use and jQuery itself hasn't used them since Sizzle was inlined. If you need the same behavior, $elems.push( elem ) can be replaced with [].push.call( $elems, elem ).
- jQuery.expr[ ":" ] and jQuery.expr.filters, which have been documented as deprecated since 3.0.0 but never made their way into the deprecated module. Use jQuery.expr.pseudos instead.

### Backported fixes

3.8.0 also picks up a number of fixes that already shipped in jQuery 4.0.0, including support for self-removing scripts passed to `.html()`, a fix for `jQuery.cleanData` skipping elements during cleanup, correct dimensions for table `<col>` elements, more robust native event handling in `leverageNative`, and support test fixes for pages under CSS zoom and initially hidden iframes.

## Download

You can get the files from the jQuery CDN, or link to them directly:

You can also get this release from npm:

`npm install jquery@4.1.0`

`npm install jquery@3.8.0`

The slim builds are available as well:

Information on all the ways to get jQuery is available at [https://jquery.com/download/](https://jquery.com/download/).

One more time for the folks in the back: jQuery 3.8.0 is the last planned feature release on the 3.x branch. From here on, 3.x will only receive critical fixes. jQuery 4.x is where active development happens, and it's ready for you.

## Thanks

Thank you to all of you who participated in these releases by submitting patches, reporting bugs, or testing, including [ac-mmi](https://github.com/ac-mmi), [Apoorv Darshan](https://github.com/apoorvdarshan), [Richard Gibson](https://github.com/gibson042), [Michał Gołębiowski-Owczarek](https://github.com/mgol), [J.Son](https://github.com/xwxtwd), [Naveed Khan](https://github.com/rootvector2), [metsw24-max](https://github.com/metsw24-max), [neogy-akash](https://github.com/neogy-akash), [orbisai0security](https://github.com/orbisai0security), [Stephen Sigwart](https://github.com/ssigwart), [studystill](https://github.com/studystill), [Timo Tijhof](https://github.com/Krinkle), [TomTensor](https://github.com/tommyhgunz14), [서울민트초코](https://github.com/minirang), and the whole jQuery team.