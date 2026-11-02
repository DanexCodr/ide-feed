**TL;DR**: LaTeX in Org mode now go **whoosh**, all pretty like.  Install the development branch of Org mode to use it.

After grumbling about the inadequacy of LaTeX previews in Emacs – and specifically Org mode – for over a decade, [Tecosaur](https://tecosaur.net/) and I decided to take the leap and rewrite the feature from the ground up.  The result is a preview system for LaTeX math that can provide near-WYSIWYG feedback but retains the properties we expect in the Emacs environment: text-first, extensible and composable.

It’s not much code, but it contains many moving pieces and makes contact with several corners of Emacs.  Now that the feature is part of Org mode, I thought I would take this opportunity to document how it works from the ground up, and use it as a launchpad to explain relevant aspects of Emacs’ event loop and its unofficial package API
<small>
Emacs doesn’t really have a “package API”, since you build Emacs packages from the same elements as Emacs itself.
</small>
.

This article is not an exhaustive demo of all the shiny new features, although there are a few videos peppered throughout.  It’s also not the user manual (not yet updated on orgmode.org) or a tutorial (see Tecosaur’s [This Month in Org](https://blog.tecosaur.net/tmio/2026-11-01-preview.html) writeup).

Instead, it aims to provide an overview of the goals and design of the library, along with some explainers of relevant aspects of the Emacs API and tips to write your own features.  This write-up is for you if you are interested in

- a broad understanding of LaTeX preview generation (how and why),
- learning about Emacs’ event loop, subprocess interaction, overlay-based display and UI, or
- a case study on building a non-trivial Emacs “application” from scratch.

## What is `org-latex-preview`?

This is a feature included with Org mode to preview LaTeX math snippets as images in Emacs buffers.  The contents of LaTeX fragments and environments in Org mode are replaced with rendered images.

It has existed for decades at this point, but in a form that I consider barely usable; this rewrite overhauls the code base and adds a number of quality-of-life features.  There is a 13 minute demo that can give you a good idea of the new capabilities of Org mode:

The bullet points, if you prefer:

- Preview generation is fully asynchronous <small> Or as asynchronous as Emacs in its current form allows. </small> , with images placed continuously as they are generated
- Bulk generation: Preview 200 to 800 snippets per second
- Previews blend in correctly with surrounding colors
- Automatically match the current Emacs theme (even through theme changes)
- Previews are aligned with and scaled to match the font baseline and size
- Previews auto-generate for newly inserted LaTeX
- Previews auto-update as you change the underlying LaTeX
- Preview as you type: Live-previews of LaTeX fragments
- Consistent (correct) equation numbering across the document
- LaTeX compilation error reporting for previews

And a couple more quick demos:

The rest of this article is mostly about how it works, and briefly why.  As such, it has a “fractal” level of detail.  There is information intended

- to give the casual reader a bird’s eye view of LaTeX preview generation,
- to give the motivated reader a detailed look at its many pieces,
- for the potential new Emacs package author looking for pointers on aspects of Emacs’ API,
- for folks wanting to develop a similar feature for applications other than Emacs,
- and information that is of no use whatsoever except to the future maintainers of the org-latex-preview library.

To that end, many details are tucked away in blocks like the following.  You can safely ignore them in favor of the top-level headings, images and video demos.

Blocks like this describe the concrete implementation of aspects of the code.

This is probably only interesting if you are looking to dive into the code itself, or if you are looking to write a similar package.

Blocks like this are for additional notes on aspects of Emacs’ API, including the odd code snippets.

Warning: Here be idiosyncratic takes.

Blocks like this describe other Org features relevant to LaTeX preview generation.

Blocks like this describe CLI commands associated with this process, or their output.

## Isn’t this a narrow feature to spend so much time on?

Indeed, this feature

- requires a LaTeX distribution installed,
- works only with Org mode (for now),
- and is glued together from several processes and grossly inefficient in the larger scheme of things.
- It’s also finicky, as all hyper-configurable software is.

LaTeX was not built with the aim of minimizing latency.  Having to start multiple new processes even for a one-character change places a hard cap on what’s possible in terms of real-time feedback.  Implementing an equivalent preview feature for a system designed for modern computers, like Typst, is trivial in comparison.

Moreover, as popular as Org mode is, it’s a small player in the space of markup languages.  The fraction of Org and LaTeX users who would prefer to use Org mode to write LaTeX is smaller still.  And while Org attempts to integrate well with LaTeX, navigating the mishmash of Org and LaTeX syntax presents an extra learning curve on top of learning to use the two markup languages individually.

But it also has a few things going for it.

First, LaTeX is ubiquitous, and Org mode is a far more convenient format for writing than raw LaTeX.  There is significantly less visual noise (think Markdown vs HTML), and Org provides an escape hatch for adding LaTeX verbatim.  Org’s simple interface for shuffling text around, monitoring task progress and executing code blocks makes it easy for eventual LaTeX documents to begin as Org files.  Since everything in Emacs composes with everything else, your system for (say) [fast LaTeX input](https://karthinks.com/software/latex-input-for-impatient-scholars/) transfers over to Org mode seamlessly.

Second, the fact that Org is versatile as a publishing tool implies that some benefits of better LaTeX support transfer over to other formats too, like equations in HTML or ODT exports.

There is a wide swath of applications built on Org mode that benefit from LaTeX math input, such as Org Roam and Org Noter.  For these applications converting Org documents to LaTeX is not the goal, as they are not primarily publication tools: they stick around as private digital archives, and better LaTeX support is a bonus to the user’s expressivity.

Real-time feedback when editing LaTeX snippets is a categorical improvement to the user’s experience.  I did not realize this when I started work on `org-latex-preview`, but now I wouldn’t want to LaTeX without it.
<small>
It baffles me that web LaTeX editors (Overleaf etc) don’t provide this out of the box, especially as they target novice LaTeX users.
</small>
.

Finally, we *can* keep Org mode out of the picture: `org-latex-preview` can technically work anywhere in Emacs, and in every major-mode. it’s just not there yet
<small>
(See [below](https://karthinks.com/software/understanding-org-latex-preview/#latex-previews-everywhere-in-emacs))
</small>
.

But perhaps the most germane reason is that Emacs users don’t shy away from settling comfortably into tiny, cramped and poorly insulated niches.  Comes with the territory!

## The Objectives

### Never Block Emacs

Emacs users are closely acquainted with its frequent unresponsiveness.  You’re never more than one minor-mode or mode line indicator away from causing Emacs to block or lag.  While it’s not a big ask to wait a second for the result of an action *you* initiate, the unresponsiveness often manifests as short random freezes, which is unacceptable.  But there’s more.  Beyond the annoyance and inconvenience, poor responsiveness denies us an entire class of uses: real-time feedback is everything for interactive applications.

Owing to both its design and age, Emacs is not very well suited for asynchronous applications.  Certain patterns of asynchronous usage are viable (see below), but concurrency support is limited and parallelism is absent: no worker threads, channels, async-io, or anything of the like.

I lied.  In addition to Elisp threads, there exist prototype libraries for async-io ([Chris Wellons](https://nullprogram.com/blog/2019/03/10/)) and channels/CSP ([Andrey Listopadov](https://andreyorst.gitlab.io/posts/2023-02-01-ad-hoc-async-in-emacs-lisp-via-generators/)) based on Emacs’ [generators library](https://www.gnu.org/software/emacs/manual/html_node/elisp/Generators.html), which in turn is implemented using continuation passing.  But generators as provided by this library do not have anywhere near the level of robustness or support you need to build actual applications: no introspection, error handling or debugging support, poor performance, and just overall jankiness.  I’ve tried and lived to regret it – [Elfeed Tube](https://github.com/karthink/elfeed-tube) is a real mess.

The [Futur](https://elpa.gnu.org/packages/futur.html) package is another promising swing at an async-io style interface, but it’s new and I haven’t been able to try it yet.

In any event, a more responsive `org-latex-preview` would require parallelism and not just concurrency.  There is John Wiegley’s [async library](https://github.com/jwiegley/emacs-async) (and packages inspired by it, like [session-async](https://codeberg.org/FelipeLema/session-async.el)) that spawn a child Emacs that runs in parallel, but communication is limited and the overhead is sizeable, so this is a bit of a bludgeon.

The upshot is this: we want `org-latex-preview` to be as asynchronous as possible within Emacs’ effectively single-threaded event loop model.  The goal is to minimize how long the user has to wait, in terms of both the overall run time and the fraction of that for which Emacs is unresponsive.  We end up having to trade these off against each other.

### Go Fast (relative to LaTeX and Emacs)

A close second concern is preview generation speed.  This is desirable both in the large and the small.  Previewing upwards of a hundred LaTeX math fragments in a math-heavy Org document used to be an exercise in patience.  Now it takes about one second, and can be much faster with some trade-offs.

| LaTeX Fragments | Old preview system (s) | `org-latex-preview` (s) | Speed up |
| --- | --- | --- | --- |
| 35 | 12.96 | 0.43 | 30x |
| 70 | 22.59 | 0.51 | 44x |
| 160 | 33.99 | 0.68 | 50x |
| 330 | 84.95 | 1.32 | 64x |
| 660 | 139.73 | 1.96 | 71x |
| 1000 | 194.16 | 3.24 | 60x |

### Provide Real-Time Feedback

Speeding up bulk generation is at most a boost in convenience.  You don’t regenerate a large buffer’s worth of previews more than once every few sessions, and the resulting images are cached anyway.  The more interesting aspect is that speed enables a close to real-time feedback loop that wasn’t available before.  This is especially useful when you’re deep inside a messy structure like an array:

No more counting field separators.  No more exiting, regenerating and re-examining snippets.  It’s the best parts of WYSIWYG and visible markup, together.

### Look Pretty

Even in the niche of academic types who use Org mode with LaTeX, there are very different orientations.  There’s Org the transient format, where an Org document starts out as a rough sketch, a thought bubble translated to the screen, and soon transitions into a TeX file that becomes the source of truth.  There’s Org the intermediate publication format, where the document lives as an Org file, but its value is in the web page or PDF document it eventually becomes.  For the adherents of this style the appearance of the Org document is irrelevant.

Finally, there’s the class of uses described [above](https://karthinks.com/software/understanding-org-latex-preview/#isn-t-this-a-narrow-feature-to-spend-so-much-time-on), where the desired output is the Org document itself, or a cross-linked collection of them.  These are folks who care about the aesthetics of Org documents and often suffer a thousand cuts in trying to make Emacs look “modern”.

One of the objectives of `org-latex-preview` is to ease their self-imposed burden somewhat: LaTeX previews should blend in perfectly with the surrounding text.  This means

- preview image sizing that is consistent with surrounding text,
- with perfect baseline alignment at any font size,
- and Emacs theme-aware colors that change automatically with the theme.

Getting the fonts to match is possible too, but requires some degree of compromise on the part of the user
<small>
You could start by using the variable-pitch Latin Modern font in your Org documents.
</small>
.

Each of these is a long-standing issue with LaTeX previews in Org, and Stack Overflow and the usual haunts have decades of discussions on how to fix them, with band-aid after band-aid proposed as solutions.  We took an elephant gun to this problem, starting by throwing out the giant mess that was Org’s accreted LaTeX preview code of the past two decades.

Here’s a demo of theme-aware LaTeX preview colors:

### Windfalls: Consistent numbering, error reporting

Finally, there are a few features we picked up along the way because they came free.

Recording compilation errors was a simple matter since we scan the LaTeX output anyway.

Consistent equation numbering was expensive in the past because numbering changes can propagate across the document, and parsing the Org document and LaTeX fragment compilation were both slow.  Recent changes to Org have made the former a non-issue (see the [parsing section below](https://karthinks.com/software/understanding-org-latex-preview/#parsing)), and the [performance scaling](https://karthinks.com/software/understanding-org-latex-preview/#figure--timing-chart-svg-only) of our bulk LaTeX runs has fixed the latter.

There are several more minor features along for the ride, such as improvements to editing LaTeX with `org-edit-special` (`C-c '`).

## The Emacs API: An Overview

As mentioned in the introduction, the LaTeX preview system draws on a few different facets of the Emacs API: mainly async process interaction (the “backend”) and overlays (the UI or “frontend”).  The live-updating behavior leans heavily on hooks and timers, and we join these pieces together with very simple Lispy data structures, like alists and plists.

We also (naturally) use a few Org mode specific APIs, including ones developed by us for this purpose.  We cover these further below as we encounter them.

### The Substrate: Emacs’ Event Loop

If you are designing an Emacs application that interacts with the outside world, it helps to start with a mental picture of Emacs’ event loop.  To a first approximation, the main loop does only four things:

![](https://karthinks.com/img/emacs-event-loop-simple.png)

- Read input events: This includes keyboard, mouse and touchscreen events, but also some OS signals. This is the user’s interface to Emacs.
- Evaluate commands and redisplay: This is the heart of the Lisp evaluator, and Emacs’ interface to the user.

Together these two connect the user and Emacs.  If the main loop did only these two things Emacs would still qualify for the title of “Lisp evaluator masquerading as a text editor”, but it wouldn’t be nearly as useful.  For that we need it to

- Read subprocess output: This includes output from “regular” processes like shell commands or LaTeX, but also network requests. This connects Emacs to the world <small> (your computer and the network) </small> , and vice-versa. Command shells, LaTeX previews, LLM clients and most IDE features work because of this.

The last event loop function combines the above three, but across time:

- Run timers: Schedule code for the future and run them when timers are ripe. Somewhat tentatively, I’m including garbage collection here.

This design explains why timers in Emacs are not reliable in the absolute sense.  The timer runs not when it’s ripe, but when it’s ripe *and* when the main loop gets around to it.  Nevertheless, scheduling code provides a much-needed degree of flexibility to a rigidly ordered task list.

The way these four tasks are actually organized in the main loop code is less pleasing:

![](https://karthinks.com/img/emacs-event-loop-detailed.png)

Also, Emacs is obviously doing things outside of the event loop as well.  Font caches are compacted, Emacs is responding to the compositor and some OS signals, interacting with dynamic modules, and so on.  In the currently experimental MPS branch, some garbage collection activities also occur in the background.   These are invisible to the Lisp evaluator and thus out of scope when learning to build an Elisp package.

### The Backend: Subprocess Interaction

![](https://karthinks.com/img/async-interaction-via-processes.png)

This design suggests that *Emacs can only do one thing at a time*
<small>
As of Emacs 31
</small>
, so that designing a responsive application is a steep ask.   But the situation is more nuanced:

1. Yes, the Lisp evaluator holds a global interpreter lock. At any point in time Emacs is doing exactly one of the following: painting the screen (redisplay), updating syntax highlighting (fontification), running hook functions or timers, responding to window changes, handling keyboard input, and – crucially for us – interacting with subprocesses. Every action is thus blocking.
2. The only asynchronous interaction possible is by starting an OS-level subprocess <small> Another lie, since we have [dynamic modules, covered below](https://karthinks.com/software/understanding-org-latex-preview/#org-target--org-latex-preview-dynamic-modules). </small> . Emacs continues to run independently from the subprocess, but it still has to handle its `STDOUT` and `STDERR` streams and respond to process signals. When it is doing this, it cannot pay attention to your input or anything else. Again, Emacs can only do one thing at a time. ![](https://karthinks.com/img/emacs-icon.png) Starting asynchronous subprocesses There are multiple commands to start an asynchronous subprocess from Emacs (see `M-x shortdoc` `process`), but `start-process` covers most common use cases. ` (setq my-process-object (start-process "name" "buffer-name" "program" "--arg1" "--arg2" "...")) `Processes are (optionally) associated with a buffer where process output is inserted. To send a subprocess some input, there’s `process-send-string` and `process-send-region`. Responding to process output and signals is the responsibility of process filters and sentinels ([next block](https://karthinks.com/software/understanding-org-latex-preview/#org-target--org-latex-preview-process-filters-sentinels)). `kill-process` does what you’d expect. All of these functions take the process object that `start-process` returns as an argument. Except for some [fiddly details](https://karthinks.com/software/understanding-org-latex-preview/#org-target--org-latex-preview-fiddly-details), that’s essentially all there is to the process interaction API. There are several variants of `start-process` available – the synchronous `call-process`, the shell versions `start-process-shell-command` and `call-process-shell-command`, and so on. The only one that does something different is the primitive `make-process`, which is a more extensive version that can (additionally) create network processes, send data through TCP or Unix sockets and so on.
3. Emacs will try to prioritize user input events. To do this it can delay tasks like reading from subprcesses if necessary. [Idle timers](https://www.gnu.org/software/emacs/manual/html_node/elisp/Idle-Timers.html) are another example of this. Some actions are thus delayable, but they block Emacs when they (eventually) run. There might be a penalty to pay afterwards, for instance when there’s more subprocess output to process as a result of delaying the task. ![](https://karthinks.com/img/emacs-icon.png) Process filters and sentinels: Handling process output By default, Emacs inserts the output from a subprocess into the process buffer, or ignores it if there is no process buffer. (Crucially, it still has to read the output from the process pipe.) This is good enough for simple tasks. To use or transform subprocess output in more specialized ways, you can write an elisp function that is used as a *process filter*. It is called whenever Emacs reads new process output. In the language of shell commands, I think of process filters like this: ` $ start-process "some-process" 2>&1 | process-filter `Process filters can be tricky to write if you want to parse structured process output, because the amount of data that Emacs reads from the pipe can be arbitrary. Unless latency is a concern, it’s often preferable to work with *process sentinels* for this reason. Sentinels are the second tool Emacs makes available for reacting to processes. A process sentinel is an elisp function (callback) called whenever the process changes state or raises a signal, including when it terminates. Practically speaking, I think of them like this: ` $ start-process "some-process" 2>&1 > process-buffer && \ process-sentinel < process-buffer `They are typically used for cleaning up after the process, and updating Emacs’ state depending on how the subprocess ends. But you can use them to access the process buffer containing all the process output, and thus do whatever you would in the filter. Filters and sentinels can be attached to a subprocess object created with `start-process` using `set-process-filter` and `set-process-sentinel` respectively.
4. Many blocking operations can be interrupted by signaling a `quit`: this is what pressing `C-g` does, with some variations, in most contexts. Crucially for us, however, quitting is suppressed when Emacs is handling subprocess output or signals <small> This is to keep your `C-g` from doing something unpredictable to “background” code that you didn’t initiate. </small> . If Emacs is blocked because it’s reading a large data dump… well, tough luck.

`keyboard-quit` (`C-g`) is a *specific* input that interrupts *any* code, with a few exceptions.

The obverse of this is to wrap code in a `while-no-input` clause – now *any* input will interrupt the processing of *this* specific block.  This can be used to do background processing in small chunks without making Emacs unresponsive, but there are subtleties involved that I’m not familiar with.

Despite these carveouts, a package that interacts heavily with external processes faces a latency-throughput tradeoff.  The more time Emacs spends starting processes and managing their output, the less attention it can pay to your input.  Designing Org’s LaTeX preview thus involves finding an acceptable balance.

It is *significantly* easier to write a large Emacs library than an equally versatile plugin for most plugin systems built around multi-threaded GUI applications.  I say this as a non-programmer who has only succeeded at the former.  We lean on the interpreter lock in many ways, choosing [simple data structures](https://karthinks.com/software/understanding-org-latex-preview/#how-it-works-data-flow) and [control flow](https://karthinks.com/software/understanding-org-latex-preview/#how-it-works-control-flow) that wouldn’t work if Emacs was multi-threaded.  But most of Emacs wouldn’t work if Emacs was multi-threaded, anyway.  In for a penny…

### The Frontend: Displaying images over text

[Overlays](https://www.gnu.org/software/emacs/manual/html_node/elisp/Overlays.html) are a way to alter the appearance or behavior of regions of buffer text without modifying the text itself.  Displaying images is one of their most common uses: LaTeX preview images are overlaid on top of the source fragments.

![](https://karthinks.com/img/olp-before-and-after-2.png)

Once you have the preview images in hand, placing them in overlays and managing their state is essentially all the LaTeX preview code does.

In fact, overlays account for much of the display trickery in Emacs:  Images over text?  Overlays. “Virtual text” like in `whitespace-mode`?  Overlays.  [Inline results](https://github.com/xiongtx/eros) of code evaluation: overlays. [Multiple cursors](https://github.com/magnars/multiple-cursors.el)? Those are overlays.  Emacs has only one cursor.

For a quick look into the overlay API, run `M-x shortdoc` `overlay`.

The even shorter version: We can create an overlay `ov` from buffer position `BEG` to `END` with

```emacs-lisp
(setq ov (make-overlay BEG END))
```

and move it around with

```emacs-lisp
(move-overlay ov NEW-BEG NEW-END)
```

To avoid creating garbage, it is preferable to reuse overlays when possible instead of throwing them away with `(delete-overlay ov)` and starting over. `move-overlay` can move them to other buffers too.

The only other tricky question is what happens to the overlay when text is inserted at its left or right boundaries.  Does it expand to contain the text?  This is left as an exercise for the reader.

These alterations are specified by adding or modifying the overlay’s “properties”.  Like [symbol properties](https://www.gnu.org/software/emacs/manual/html_node/elisp/Symbol-Properties.html), overlay properties are a way to store arbitrary information along with the overlay, and `org-latex-preview` uses them to keep track of state, such as whether the preview image is out of date because the LaTeX fragment has been edited, and to store LaTeX compilation errors for the corresponding fragment.

To set and retrieve overlay properties, we can use

```emacs-lisp
(overlay-put ov prop value)
(overlay-get ov prop)
```

where the property `prop` is any elisp symbol.  There is also an `overlay-properties` function to access the full list.  Once again, `M-x shortdoc` `overlay` has us covered.

![](https://karthinks.com/img/olp-phi-overlaid.png)

Some properties have special meanings as interpreted by Emacs’ display engine.  `display`, the most common property, changes how the overlay region appears on screen, and this is typically set to the image we want to see in place of the text.

But several more interesting modifications are possible with overlays, such as changing the face (font+style) of the underlying text, making it invisible, making it intangible to the cursor, or specifying keymaps that are activated when the cursor is within the bounds of the overlay.

The only other detail we need is the [list of overlay properties](https://www.gnu.org/software/emacs/manual/html_node/elisp/Overlay-Properties.html) that Emacs considers special.  The `display` property can be used to show an image instead of the text “below” (or “under”) the overlay, for example:

```emacs-lisp
(let ((img (create-image "/path/to/image.png")))
  (overlay-put ov 'display img))
```

The `face` property can change the display of the text.  Here we dim the text the overlay covers:

```emacs-lisp
(overlay-put ov 'face 'shadow)
```

Here are a few more interesting uses of other special overlay properties.

Send a message if the text under the overlay changes:

```emacs-lisp
(defun notify-on-ov-change (ov after-p beg end &optional _)
   (when after-p
     (message "Text changed: %s"
              (buffer-substring-no-properties beg end))))

(overlay-put ov 'modification-hooks (list #'notify-on-ov-change))
```

You can use this to set up a “watcher” – perhaps run a process when a region inside a buffer changes
<small>
If you want to set up a watcher on the contents of the entire buffer as opposed to a piece of it, you should avoid overlays and look at the hook `after-change-functions` instead.  Be warned: it’s easy to slow down Emacs to a crawl this way if you’re not careful.
</small>
!  This is not hypothetical: `preview-latex` does this to [re-dump the LaTeX preamble](https://karthinks.com/software/understanding-org-latex-preview/#precompilation) of TeX files (in the background) as you edit them.

Add a highlight and tooltip (“hover text”) when the mouse is on the overlay:

```emacs-lisp
(overlay-put ov 'mouse-face 'highlight)
(overlay-put ov 'help-echo "You're on an overlay, pal.")
```

Open the displayed image externally when pressing `RET` with the cursor on it:

```emacs-lisp
(overlay-put
 ov 'keymap
 (define-keymap "RET"
   (lambda () (interactive)
     (when-let* ((img (get-char-property (point) 'display))
                 ((imagep img))
                 (file (image-property img :file)))
       (start-process "view-image" nil
                      "xdg-open" file)))))
```

This works by defining a `keymap` overlay property with the required function.  (On non-Linux systems, you will want to change `"xdg-open"` to an equivalent command-line utility.)

Center an image in a window:

```emacs-lisp
(let* ((img (image-create "/path/to/image.png"))
       (spacing (propertize
                 " " 'face 'default
                 'display
                 `(space :align-to (- center (0.5 . ,img))))))
  (overlay-put ov 'display img)
  (overlay-put ov 'before-string spacing))
```

This image stays centered as you resize the window:

This one needs a little explanation:  The `before-string` overlay property displays an object before the overlay itself.  The object we choose to display is some propertized text with a `display` *text-property*.  The `display` text-property provides the means to [insert spaces of specified widths](https://www.gnu.org/software/emacs/manual/html_node/elisp/Pixel-Specification.html), and a symbolic way to refer to the text margins, window center and horizontal window boundary positions.  Combining the two gives us (consistently) centered images in Emacs.

### The Reactive UI: Hooks and Timers

In its basic form, the LaTeX preview feature involves no reactive behavior: there is one command to overlay preview images on LaTeX fragments, another to clear those overlays, and nothing else.

But this is a far cry from our goal of real-time feedback.  For LaTeX previews to be automatically generated and updated as we type, we need both timers and *hooks*.

Hooks are variables provided by Emacs where we can register code to run at certain points.  In this case, we want to react primarily to two kinds of user inputs:

- Cursor motion, so that entering a previewed LaTeX fragment reveals its source and leaving it re-displays the image.
- Buffer changes, so that a preview generation subprocess automatically fires when a new LaTeX fragment is typed in or an existing one is edited.

In turn, `org-latex-preview` exposes hooks of its own for consumers to run additional processing.  These fire when LaTeX subprocesses finish, when overlays are created, and so on.

Timers are complementary to hooks, used to space out or limit the consequences of hooks firing.  They are used

- to keep these hooks from firing all the time, which would create redundant subprocesses with each edit, locking up the main loop. They provide the means to implement throttling and debouncing.
- to delay clean-up tasks like deleting intermediate LaTeX output until Emacs is idle.

## The structure of `org-latex-preview`

Besides basic Elisp data structures, that’s everything we need from Emacs to implement non-blocking, fast LaTeX previews.  Assuming you have a handle on what `org-latex-preview` does, we can start peering into the how.

### How it works: control flow

Here is a high-level overview of the control flow of LaTeX preview generation:

This is a rough picture of how LaTeX previews are generated in Org mode, subdivided into tasks
<small>
The made-up term “task” corresponds to a handful of functions devoted, in our heads, to one purpose.
</small>
.  Each action belongs to one of three categories:

- Blocking tasks: These must run synchronously and thus require the user to wait while Emacs is unresponsive. We want this to be minimal and/or done ahead of time.
- Delayable tasks: These tasks can be delayed if more immediate actions – such as accepting user input – are pending. However, once such a task is started it runs synchronously and we’re locked in. We want this work to be chunked into small independent pieces.
- Asynchronous tasks: These are subprocesses spawned by Emacs and managed by the OS. Emacs monitors the process status and handles process output in a delayable fashion, but is otherwise unencumbered by them.

When a LaTeX preview command is issued, the first chunk of processing (the PREPARE block)

1. sets up overlays in the buffer that “cover” the fragments, with the intent to add preview images to them at the end,
2. creates a TeX file containing the relevant LaTeX fragments from the Org buffer, along with a preamble. This preamble is optionally precompiled, which can speed up processing considerably.

It then starts a two step process chain (the RUN block) that runs asynchronously.  The end result of a successful run is a preview image or series of images.

The PROCESS FILTERS block: From this point on until either process ends, Emacs checks in periodically through the associated process filter, acting on the `STDOUT` to capture various bits of preview metadata.  It also keeps track of images that have finished processing, and (synchronously) caches them and adds them to the overlays in the buffer for these fragments.  This continuous update is doubly useful:

- Previews start appearing in the buffer much faster, with the window viewport being updated first.
- This processing happens in small chunks instead of all at once at the end, so Emacs stays more (even if not fully) responsive to input.

The POSTPROCESS block: After the subprocesses have finished, Emacs runs their process sentinels, which clean up the detritus of this process chain, or reset the buffer if the preview run failed.

And speaking of detritus…

### How it works: file I/O

![](https://karthinks.com/img/olp-files-flowchart.svg)

This figure shows the same process but with an emphasis on disk I/O.  The primary chain is TeX file → DVI/PDF output file → SVG/PNG preview images.

Of the file categories involved in the process, we care about two: the “format dump file” produced by precompilation, and the preview images.  Both are cached and persisted across Emacs sessions.  All other produced files are deleted by the POSTPROCESS block.

### How it works: data flow

Displaying previews that are color-, alignment- and size-aware, along with associated information like errors, requires a considerable amount of bookkeeping.  Since this information arrives piecemeal and processing happens asynchronously in chunks, we also need some way of storing and passing along this context.  There are perhaps clever ways to do this, but we use a straightforward solution – a (dynamic) global plist that associates each active process chain with its data (see [org-async](https://karthinks.com/software/understanding-org-latex-preview/#org-target--org-latex-preview-org-async-explainer) below).

![](https://karthinks.com/img/olp-data-extended-info.svg)

All of the data generated and required for the many tasks in our process chain are captured in a single mutable container, referred to here – for convenience – as “Extended Info” (`extended-info`).  This data includes

- User preferences for the preview run, such as the LaTeX compiler in use,
- Input LaTeX strings to be rendered,
- Input file paths, output image paths and image cache details,
- Emacs’ context like the current buffer – which is important since we need to restore it before we can run asynchronous callbacks,
- Overlay positions and properties,
- Compilation errors,
- Computed preview geometry and fontsize for alignment,

and more besides.

“Extended Info” is implemented as a plist (property list).  Actually, almost every compound data structure `org-latex-preview` uses is either an alist or a plist, which is just a linked-list under the hood.  `extended-info` is also a tree since a few of its members are plists themselves ([see below](https://karthinks.com/software/understanding-org-latex-preview/#org0ce9534)).

We used property lists at first since they’re mutable and schema-less, and the design of the library was very fluid.  Unfortunately we are now well past the point where we could switch to something more structured like `cl-defstruct`, so plists it is.

If it’s any consolation, most of Org works with large property lists too.  Org’s export system passes around a big `plist` bucket for communication in much the same way we do here.  Access can get expensive as they grow, but at least passing them around is cheap.  It’s… not much of a consolation.

plists have one other coincidental(?) advantage: You can splice them in as arguments to a `cl-defun`.

Consider:

```emacs-lisp
(cl-defun foo (&key (buf (current-buffer)) (valid-p t) (pred #'ignore)
                    &allow-other-keys)
  ;; body of foo
  )
```

This function has the signature

```emacs-lisp
(foo :buf some-buffer :valid-p t :pred #'always)
```

which is just a list with the name of the function followed by… a plist.  So we can build up the plist programmatically and use it directly as `foo`’s argument list:

```emacs-lisp
(let ((arglist `(:buf ,some-buffer :valid-p t :pred ,#'always :unknown-key nil)))
  (apply #'foo arglist))
```

’tis a silly thing but oh, so satisfying.  In fact, this is a convenient way to feed a job spec to `org-async` ([see below](https://karthinks.com/software/understanding-org-latex-preview/#org-target--org-latex-preview-org-async-explainer)).

#### How `extended-info` is populated

The setup functions in the PREPARE block initialize this bucket with data from parsing the buffer – i.e., LaTeX fragment locations, equation numbers, etc.  From then on, each task updates `extended-info` with progressively more information.  The structure of `extended-info` and this flow of information into it is visualized in this “data flow” diagram:

![](https://karthinks.com/img/olp-in-data-flowchart.svg)

Contained in “Extended Info”: “Processing Info” contains information about and relevant to the external process (LaTeX and the image converter).  “Fragment” is a list of metadata for fragments to be previewed, including the overlays that will eventually display the preview images.  All of this preview metadata is obtained from the outputs of the latex and image converter runs via the process filters.

Note that Emacs’ interpreter lock precludes data races and other concurrency issues, since only one function modifies `extended-info` at a time.

#### How `extended-info` is accessed

The above chart only captures the flow of data in one direction: from the sources of computation into the `extended-info` container.  Tasks that don’t modify `extended-info` still need to read it  to do their jobs.  For example,

- Clean up temporary files needs the paths to the temporary files.
- Cache images and metadata needs the generated image paths, as well as all the geometry metadata.

Most functions in the process chain are passed `extended-info`, or a subset thereof, as an argument.

![](https://karthinks.com/img/olp-out-data-flowchart.svg)

Once again, we get away with it because there are no concurrency problems when there is no concurrency.  This design pattern of passing around a single heap-allocated container across setup functions and callbacks works for all kinds of applications in Emacs.  This is exactly how Org’s (synchronous) export system manages information as well.

## `org-latex-preview` Pieces and the Org API

This is where we get into the weeds.  If you’re here for the bird’s eye view, you can skip ahead to [Live previews](https://karthinks.com/software/understanding-org-latex-preview/#live-previews-hooks-galore) now.

### Parsing

This is the Collect LaTeX Fragments task in the [control flow diagram](https://karthinks.com/software/understanding-org-latex-preview/#figure--org-latex-preview-process-chart).

Org’s syntax is [extensive](https://orgmode.org/worg/org-syntax.html#LaTeX_Fragments), and parsing Org files used to involve a giant mess of regular expressions.  Thankfully the mess is now handled by the `org-element` library, which provides a simple and powerful API for querying or acting on Org’s AST.  A fair amount of work has gone into making it perform well under the constraints of Emacs’ single-threaded event loop
<small>
Besides caching its state, it uses [timers](https://karthinks.com/software/understanding-org-latex-preview/#the-reactive-ui-hooks-and-timers) to schedule parsing work outside of the times the user is interacting with Emacs.
</small>
.

Crucially for us, Org has first-class support for LaTeX environments and fragments, and this greatly simplifies parsing and metadata handling.  This support is what makes using LaTeX in Org a pleasant experience in the first place.

Added in late 2021, the `org-element` library greatly simplifies the process of working with Org documents.

I have a minimal working knowledge of the library, so this block covers only the aspects of `org-element` that we use in `org-latex-preview`.

Org’s syntax distinguishes between “elements” and “objects”, where anything “larger” than a paragraph is an element, and any syntax that could be contained within a paragraph is an object
<small>
Incidentally, the default `mark-paragraph` binding runs `org-mark-element` in Org mode, which selects the smallest logical element is at point instead.  Try `M-h` at different locations in an Org buffer to see what element you’re on!
</small>
.

This distinction matters to us because LaTeX text to be previewed can be either.  As you might expect, inline math (`$...$` or `\(...\)`) is an object, and LaTeX environments (`\begin{foo}...\end{foo}`) are elements, and they differ in the way we must display the preview images.

Every node in the AST as parsed by `org-element` is made available as a plist whose keys are properties of the element.  These properties include the start and end positions of the element and its contents (`:begin`, `:end` and `:contents`), as well as metadata like properties and keywords.  For example, every element can be named with a `#+name:` keyword.

These are the only things we need from `org-element` as far as parsing goes.

The objective of the parsing step is to find the bounds of LaTeX fragments in the buffer (or in some region).  In principle, we could do this with `org-element`:

```emacs-lisp
(org-element-map
    (org-element-parse-buffer)
    '(latex-environment latex-fragment)
  #'identity)
```

But this would be too slow, and would allocate far more memory than we need.  Instead, we use a simple regexp scan of the buffer to find the bounds of LaTeX fragments and environments, and `org-element` only to gather specific metadata about these elements.

### Preamble generation

This is the Create preamble task in the [control flow diagram](https://karthinks.com/software/understanding-org-latex-preview/#figure--org-latex-preview-process-chart).

Many editor plugins (and web apps) implement LaTeX previews, usually via [MathJax](https://www.mathjax.org/) or [KaTeX](https://katex.org/).  KaTeX is fast, and both function well for web pages with limited needs.  But they implement ersatz support for a limited number of LaTeX packages, and cannot consume an actual “full-fat” LaTeX preamble of the kind you might use when writing a research paper.  There is no `\usepackage{}` macro or TikZ support, for example.

By comparison, `org-latex-preview` is backed by a full LaTeX engine and LaTeX distribution, so nothing is off the table.  Of course, this means we need a way to construct the preamble and feed it to the LaTeX engine.

In addition to Emacs-wide settings (like `org-latex-preview-preamble` and `org-latex-packages-alist`), document-specific LaTeX headers can be specified with the `#+latex_header:` directive:

```org
#+latex_header: \newcommand{\sOmega}{{\scriptstyle \Omega}}
#+latex_header: \DeclareMathOperator{\diag}{diag}
#+latex_header: \DeclareMathOperator{\toep}{toep}
#+latex_header: \usepackage{calc,cancel}
#+latex_header: \usepackage{rotating}
#+latex_header: \usepackage{tikz}
```

The combined preamble must be constructed when exporting the Org document to LaTeX, and this machinery lives in the `ox-latex` library.  `org-latex-preview` simply calls into it for the preamble.  Among other benefits, this means the preamble used for the preview run is identical to the one used for LaTeX exports
<small>
unless you *want* them to differ, because of course Org provides ways to do that
</small>
, so these truly are *previews*.

The `ox` library and its children, like `ox-latex` provide an interface to convert Org documents to any other format, like Pandoc does.

While the specifics (like collating a LaTeX preamble) are output-format dependent, the basic method is uniform and simple.  An exporter maps each Org syntax [element and object](https://karthinks.com/software/understanding-org-latex-preview/#org76ac7ab) to a function that creates the equivalent in the output format, like image links to HTML `img` tags, or `#+begin_quote ... #+end_quote` blocks to HTML blockquotes elements.  The fact that the Org syntax supports LaTeX environments natively helps with LaTeX exports.

Of course, when a clean mapping like this is not possible, you can work on the buffer directly and rip out and replace raw text.  Emacs, huh.

This does make `ox-latex` one of the few dependencies of `org-latex-preview`, which is regrettable given the larger aim of [providing LaTeX previews across Emacs](https://karthinks.com/software/understanding-org-latex-preview/#latex-previews-everywhere-in-emacs).

### Precompilation

This is the Precompile LaTeX preamble task in the [control flow diagram](https://karthinks.com/software/understanding-org-latex-preview/#figure--org-latex-preview-process-chart).

To process a preamble, the LaTeX engine needs to tokenize and execute tens of thousands of lines of macro source.  For a complex preamble, the kind you would use for a book, this can take several seconds on a modern processor.

Since `org-latex-preview` aims to provide close to real-time feedback as you type, we resort to a trick from the 1990s: we serialize the entire engine state – the string pool, macro bodies as token lists, font data, engine execution parameters and so on – into a single binary memory image.  This process, called *format dumping* or *precompilation*, was automated for document preambles by David Carlisle’s `mylatex.ltx`, modernized as the `mylatexformat` package by Florent Chervet.

The upshot is that precompilation saves a significant amount of LaTeX startup time, reducing and (almost) flattening it across all preamble sizes.

Precompilation relies on a number of hacks and only works because pdftex has changed little for decades.  Unfortunately, precompilation is not supported at all by xelatex and only partially by lualatex
<small>
preambles that load OpenType fonts or Lua code are unsupported
</small>
, so `org-latex-preview` is slow with the Unicode engines.

Under a [different LaTeX preview architecture](https://karthinks.com/software/understanding-org-latex-preview/#how-a-modern-latex-preview-system-should-work), none of this would be needed.  But it’s what we have so far: a very 90s solution for a very 90s editor.

### Creating the TeX file

And speaking of being stuck with an old architecture, depending on pdflatex implies that we have to create and feed it a TeX file for each batch of previews
<small>
pdflatex and friends do accept input via STDIN, but this did not work out for finicky reasons.
</small>
.

This is the Create TeX file task in the [control flow diagram](https://karthinks.com/software/understanding-org-latex-preview/#figure--org-latex-preview-process-chart).

As you might expect, the generated TeX file contains a reference to the precompiled dump file and a listing of all the LaTeX fragments to be previewed.  Instead of placing them into the document separated by something like `\pagebreak`, we place them inside `\begin{preview}` and `\end{preview}` blocks provided by the [preview.sty](https://www.ctan.org/pkg/preview) CTAN package.

`preview.sty` is authored by David Kastrup, who also wrote the Emacs-side `preview.el` package that’s part of AUCTeX.  `preview.el` was the inspiration for `org-latex-preview` – it was clear at least that previews in Org mode could be much, much faster.

`preview.sty` does three critical things for us:

1. It places each preview snippet (enclosed within \begin{preview} and \end{preview} blocks) on a separate page in the LaTeX output;
2. it finds the boundaries of the generated text and crops the page down to them;
3. and it reports the font size, image size and baseline position in the LaTeX process’ output stream.

These modifications were technically doable through a combination of other packages (Org’s old implementation used the tightpage option of the preview machinery), but in cumbersome and error-prone ways.

This makes `preview.sty` an external dependency of `org-latex-preview`.  Fortunately this package is included by default even with minimal installs of all common LaTeX distributions.

### The process runner

The pipeline from the LaTeX fragment text in the TeX file to images suitable for preview consists of two steps.  A LaTeX engine (pdflatex, xelatex or lualatex) produces DVI, XDV or PDF output, which is fed to an image converter (dvisvgm, dvipng or imagemagick) to produce PNG or SVG images.  This is the RUN block of the [control flow diagram](https://karthinks.com/software/understanding-org-latex-preview/#figure--org-latex-preview-process-chart).

This involves a fair bit of bookkeeping, and Emacs’ callback-based async process management (via “process sentinels” and “process filters”) isn’t the most ergonomic tool for this.  In the absence of reliable async-io support, we use `org-async`, a declarative process chain manager now bundled with Org mode.

Because we need to run a chain of processes with different callback behaviors depending on the exit statuses, `org-latex-preview` uses `org-async`, a process queue manager that wraps Emacs’ `start-process`, process filter and process sentinel API.  It handles a lot of the bookkeeping for us, providing for

- declarative specification of a tree of processes that branch on the exit status of a process,
- including the ability to register multiple callbacks as required,
- keeping track of the context (the extended-info bucket in our case) and passing it to the filter and sentinel,
- and limiting the pool of concurrent subprocesses and handling timeouts.

The global variable that keeps track of the context data between async calls is managed by `org-async`.

The following code might be out of date, please refer to the Org manual.

An example of an `org-async` job spec might look like the following (simplified for clarity):

```emacs-lisp
(setq task-spec
      (list 'org-async-task             ; <-- LaTeX compilation task
            '("latex" "-interaction" "nonstopmode" "texfile.tex")
            :buffer t
            :info extended-info
            :filter #'latex-preview-filter
            :failure #'latex-failure-callback
            :success (list 'org-async-task ; <-- Image conversion task
                           '("dvisvgm" "--page=1-" "-o out-%p.svg" "texfile.dvi")
                           :buffer t
                           :info extended-info
                           :filter #'dvisvgm-place-previews-filter
                           :failure (list #'dvisvgm-failure-callback
                                          #'log-errors-callback
                                          #'cleanup-callback)
                           :success (list #'check-fragments
                                          #'cleanup-callabck))))
```

Starting this process chain is simple:

```emacs-lisp
(org-async-call task-spec)
```

`org-async-call` also provides other conveniences like timeouts, retries and concurrent subprocess limits.

### Tracking with process filters

On the other side of the process invocation are the “process filters”, which are callbacks [called by the event loop](https://karthinks.com/software/understanding-org-latex-preview/#figure--emacs-event-loop-simple) whenever Emacs reads chunks of subprocess output.  This is the PROCESS FILTERS block in the [control flow diagram](https://karthinks.com/software/understanding-org-latex-preview/#figure--org-latex-preview-process-chart).

Following the [shell metaphor for process filters](https://karthinks.com/software/understanding-org-latex-preview/#org-target--org-latex-preview-process-filters-sentinels), a simple way to think of a process filter for an Emacs subprocess is as a sink at the end of a Unix pipe:

```sh
some-process 2>&1 | process-filter
```

In the LaTeX preview case, the picture is a little more complex as there are multiple processes:

```sh
latex -interaction nonstopmode -output-directory /tmp preview-file.tex | latex-process-filter; \
dvisvgm --page=1- --bbox=preview -o image-file.svg preview-file.dvi | image-converter-process-filter
```

The analogy is different for each of the image converters.  Since [dvipng runs in parallel with LaTeX](https://karthinks.com/software/understanding-org-latex-preview/#org-target--org-latex-preview-dvipng-parallel-path), for example:

```sh
{ latex -interaction nonstopmode -output-directory /tmp preview-file.tex | latex-process-filter; } & \
{ dvipng --follow -T tight --depth --height -o image-%09d.png preview-file.dvi | image-converter-process-filter; }
```

In `org-latex-preview`’s process filters we look for the output (DVI or image) file paths, but also a variety of metadata that preview.sty and dvisvgm emit.  This includes geometry information like the width, height and baseline alignment of the image, and any compilation errors.

```text
Preview: Fontsize 10pt
! Preview: Snippet 1 started.
<-><->

l.9 \begin{preview}

Preview: Tightpage -32891 -32891 32891 32891
! Preview: Snippet 1 ended.(973936+0x22609920).
<-><->

l.14 \end{preview}
```

The printed information is cryptic.  Here’s what the numbers mean.

- The “tightpage” line reports margins around the rendered equation: ` Margins: left bottom right top Preview: Tightpage -32891 -32891 32891 32891 `The unit is “Base pts”, which is 1:65536 of a pt. (There is an additional factor of 72:72.27 on top relating a Base pt to a scaled point.)
- The next line reports the width, depth (below baseline) and height (from baseline) of the image. ` height depth width ! Preview: Snippet 1 ended.(973936 + 0 x 22609920). `
- Finally, any compilation errors reported for each preview in the above output (none here) are captured as well.
  - Errors are reported on lines starting with “lN”, where N is the line number.
  - Messages are reported (as above) on lines starting with “!”.

The [preview.sty manual](https://www.ctan.org/pkg/preview) provides more details and documents other options.

```text
pre-processing DVI file (format version 2)
processing page 1
  applying bounding box set by preview package (version 13.1)
  width=346.003754pt, height=15.362961pt, depth=.501877pt
  graphic size: 346.003754pt x 15.864838pt (121.606411mm x 5.575853mm)
  output written to /tmp/org-tex-ang3Se-000000001.svg
1 of 1 page converted in 0.16035 seconds
```

```text
[1 (preview-latex version 13.1) (preview-latex tightpage option detected, will use its bounding box) depth=1 height=29]
```

> “Whenever Emacs reads chunks of subprocess output…”

This phrasing omits some important but fiddly details about how often and how much output is read at a time, in much the same way as the Unix pipe `|` symbol does.

While the event loop is switching between [its four main tasks](https://karthinks.com/software/understanding-org-latex-preview/#figure--emacs-event-loop-simple) continuously, there  are (only) a couple of knobs available at the Elisp level to manage how Emacs reads subprocess output.

- read-process-output-max limits how much it reads in one event loop turn. Setting it to a high value means output from chatty processes will be read sooner, but at the expense of blocking user input. This is, essentially, Emacs’ latency vs throughput curse in a nutshell.
- process-adaptive-read-buffering tries to delay reading from subprocesses that produce very small chunks of data at a time, as this is inefficient. In practice turning this on has tended to make things worse instead of better when running most subprocesses.

Trying to optimize this for `org-latex-preview` has proved to be… difficult.  The rates and sizes of output emitted varies significantly between different LaTeX engines and image converters:

They differ even between different versions of the same program across Texlive versions:

`org-latex-preview` settles for a broadly acceptable set of defaults in this regard.

But the main reason we use process filters here is that we can place images in the buffer as they are generated (and read in from the process STDOUT by the event loop), and don’t have to wait for the LaTeX or image converter processes to end.

### Cleaning up with process sentinels

The unfortunate result of being forced to do file I/O at each step of the pipeline is that we are left with a trail of intermediate files that need to be swept away
<small>
Instead of, say, a block of shared memory that can simply be freed.
</small>
.  This is the POSTPROCESS block in the [control flow diagram](https://karthinks.com/software/understanding-org-latex-preview/#figure--org-latex-preview-process-chart), accomplished in the “process sentinels”.

A process sentinel is a callback invoked by the event loop when the process changes status.  In principle this includes any status change (exit, signal, stop/continue), but in practice we only care about it after the process exits.

Clearing the intermediate detritus of the compilation is not an urgent task, so `org-latex-preview`’s process sentinels actually schedule this on an idle timer.  Their other major function in this design is to diagnose process failures and restart the job when the cause looks transient.

### Caching

This is the Cache images and metadata task in the [control flow diagram](https://karthinks.com/software/understanding-org-latex-preview/#figure--org-latex-preview-process-chart).

LaTeX preview generation is an order of magnitude (or two) faster than what Org did before, so caching preview images might seem like a secondary concern.  But `org-latex-preview` still caches images, for a few reasons:

- The same state may be encountered dozens of times when editing a fragment with live previews.
- We would like to avoid rerunning LaTeX in contexts where the Org document itself is the final output, such as in-Emacs slideshow programs.
- When exporting to other formats (HTML or ODT), org-latex-preview is responsible for generating the images to be bundled with the web page or document.

In addition to the text of the LaTeX fragment itself, preview images are specific to the LaTeX preview pipeline configuration, the preamble, the Emacs theme and even the fragment’s position in the buffer when equation numbering is turned on.  To cache previews reproducibly, all of these inputs are hashed together as the key to the cached image.

While you can specify where the preview images should be cached relative to the document, `org-latex-preview` defaults to using `org-persist`, a general-purpose caching library that is part of Org mode.  `org-persist` is used for various caching duties by Org mode, such as resources fetched from the Internet and the partial syntax trees of parsed Org buffers.

Caching LaTeX preview images actually involves more than copying a file somewhere and serializing a hash table to disk.  We also need to store, as Elisp data, the image display geometry information, including the baseline alignment height.  The `org-persist` API supports caching different container kinds for exactly this purpose.

Finally, with sufficient time (or a large enough corpus) the cache of LaTeX images can grow to gigabytes in size, so cache entries are set to expire after a month, another function served by `org-persist`’s built-in garbage collection.

### Displaying images and overlay management

This covers the in-buffer UI and affordances of `org-latex-preview`, indicated by the Create overlays and Place LaTeX previews blocks in the [control flow diagram](https://karthinks.com/software/understanding-org-latex-preview/#figure--org-latex-preview-process-chart).

Beyond what is covered in [displaying images over text](https://karthinks.com/software/understanding-org-latex-preview/#the-frontend-displaying-images-over-text), displaying the image itself is simple: the image just needs to be resized and aligned according to the recorded geometry.  The overlays themselves are set up before starting the LaTeX run, and a series of overlay properties are set or unset over the course of the process.

- If an existing image is being updated, the overlay optionally gets a “face” property indicating that the preview is out of date.
- If this is a fresh preview, an overlay property marks it as “processing”, displayed in the fringe.
- If any compilation errors are captured, they’re placed as tooltip text via an overlay property. Via the SVG’s currentColor attribute, we also color the overlay image red to indicate that there was an error.

These are basic but (hopefully) intuitive indicators of the state of the preview.

## Live previews: Hooks galore

The breakdown provided so far does not explain the claims we made in the objectives section, like real-time (or at least fast) feedback as you type.  As seen in the demos above, there is one more element to making the previews appear “live” and reactive to cursor movement or buffer edits.

For the seamless hide/show behavior:

- Moving the cursor into the region covered by the overlay should “open” the overlay, reveal the underlying text and move the image next to or below the LaTeX fragment.
- Moving the cursor out of the region should do the reverse, and “close up” the overlay.

For real-time feedback:

- Editing a fragment with a visible preview marks the preview out of date, so the image should either disappear or be updated.
- If editing displaymath and the numbering changes, all other numbered environments in the buffer should be updated as well.
- Editing a previewed fragment in another buffer (with org-edit-special, C-c ') should cause the preview to be updated as you type.
- When typing or pasting text, LaTeX environments need to be detected and parsed, and the preview pipeline started in real time.

All of these are achieved using hooks, which is ultimately the only mechanism we have to trigger reactive behavior in Emacs.  The hide/show behavior involves tracking the cursor position via `pre-command-hook` and `post-command-hook` (made buffer-local).  Buffer edits are tracked via `after-change-functions`, but with several fast-fail heuristics to avoid slowing down Emacs
<small>
The difficulty of identifying, in real time, `$` and `$$` as LaTeX delimiter starts, delimiter ends, or as actual dollar signs is why live previews require the unambiguous `\(...\)` and `\[...\]` delimiters, even though the dollars are supported in non-live usage.
</small>
.  The list goes on, since we need to track Org’s folding states, as well as changes in other buffers when using `org-edit-special`.

The other strategy we’re forced to employ, given the event loop’s limitations, is to throttle and debounce pipeline calls, batching edits and avoiding race conditions between in-flight LaTeX runs – the interpreter lock protects Elisp state, but independent subprocesses will happily interleave and clobber each other’s output.

Finally, this feature is the source of dozens of edge cases, such as editing fragments inside folded regions (during global text replacement, say), or the many invalid intermediate states of a LaTeX fragment causing the preview to fail repeatedly.  Knocking down these bugs while keeping this path fast was a substantial portion of the effort over the years this library was developed
<small>
Now that it’s part of Org mode and seeing more widespread use, there are no doubt several more edge cases waiting to be reported!
</small>
.

## LaTeX previews everywhere in Emacs

A proof of concept: the design of `org-latex-preview` makes it possible to preview LaTeX outside of Org mode.  Here’s an example previewing LaTeX-formatted comments in a prog buffer (Clojure, here):

In fact, you can use the same code to preview LaTeX fragments literally anywhere in Emacs, including, delightfully, the Emacs calculator.  This (18 minute) demo runs through a bunch of contexts outside of Org mode showcasing live LaTeX previews:

While this feature exists only as a prototype, it’s simple to implement and extend.  To see why, let’s look again at the [preview process breakdown](https://karthinks.com/software/understanding-org-latex-preview/#figure--org-latex-preview-process-chart).  All tasks here are agnostic of Org mode save for two:

![](https://karthinks.com/img/olp-non-org-flowchart.svg)

- Collect LaTeX fragments: currently handled by org-element,
- Create preamble: currently assembled by the org-export (ox-latex) library.

To use LaTeX previews outside of Org mode, we only need providers for these two tasks:

- A parser that can identify the boundaries of LaTeX fragments in the buffer <small> Technically you could reuse `org-element` in non-Org buffers for this, but there will be many false negatives and occasional false positives. </small> . This does not need to be a full-fledged parser – just a regexp scan of the buffer looking for `\begin{` or `\[` can suffice. This is how the above demos were created.
- A LaTeX preamble generator appropriate for the buffer. This can just be a constant string (instead of a function) that includes a reasonable set of LaTeX packages. I used Org’s default LaTeX preamble string everywhere in the above demos.

This description might be out of date, please refer to the Org manual.

`org-latex-preview` tries to separate these independent concerns by providing the function `org-latex-preview-place`, that generates previews anywhere in Emacs given the above information.  Previewing LaTeX fragments is as simple as:

```emacs-lisp
(require 'org-latex-preview)

(org-latex-preview-place 'dvisvgm entries nil preamble)
```

where `entries` encodes the start and end positions of the fragments, and `preamble` is the LaTeX preamble to use.

```emacs-lisp
;; entries is a list of lists
;; Each entry is (start end),
;; or (start end contents)
((1342 1388)
 (1911 2104)
 (2273 2295 "\\( \\epsilon + 3 \\)"))
```

```emacs-lisp
;; preamble is a preamble string
;; See `org-latex-preview-preamble'
"\\documentclass{article}
 [DEFAULT-PACKAGES]
 [PACKAGES]
 \\usepackage{xcolor}"
```

The positions in `entries` would be obtained from your parser for the major mode.  For `preamble` you can just reuse or tweak `org-latex-preview-preamble` in a pinch.  See the function documentation for more details.

Requiring the `org-latex-preview` library will in turn load a few Org libraries (`org-element`, `org-persist`, `ox` and `org-macs`), but it does *not* load all of Org.  We tried hard to keep from loading the 16,000-line behemoth that is `org.el`.

As of late 2026, abstracting the library from its major-mode adapters remains on the TODO list.

## How a modern LaTeX preview system *should* work

When we started `org-latex-preview` in 2021, live-updating previews were not available anywhere except one LaTeX formula-editing website and, to a lesser degree, [LyX](https://www.lyx.org/).  We often wondered why, since `preview.sty` did most of the work for you and the editor side was pretty simple to implement.  If `org-latex-preview` were a thrown-together external Emacs package providing many of the same features (sans polish), it could have been written over a couple of weekends.  I know this because [I wrote it](https://github.com/karthink/org-preview).  [Twice](https://github.com/karthink/org-auctex).

Over the years, however, this feature has grown in ubiquity and there are plugins for most note-taking (Obsidian) and editing software (Neovim, VS Code) that provide this.  Emacs itself has at least four active implementations of live LaTeX previews now, and a frontier LLM can probably implement a basic version for your preferred platform with one prompt.

Even so, Emacs remains the oldest platform to implement this feature, and does so in the most complete and mature form
<small>
As of 2026.
</small>
.  Considering I spent a lot of this write-up complaining about the limitations of the Elisp runtime, this is remarkable.

But creating temporary files after every buffer change and spawning separate LaTeX processes remains a terrible way to do real-time updates.  Precompilation is another hack, unsupported by LaTeX engines besides pdflatex.  While `org-latex-preview` is a massive improvement over the previous LaTeX preview implementation for Org mode, it’s still the Elisp equivalent of a Bash script that got out of hand.  Quite simply, this is the wrong level at which to address the problem.  A better way to implement continuous previews would be to talk to a managed process over a pipe or socket.  The right approach here is to work at the level of the TeX engine, as [TeXPresso](https://github.com/let-def/texpresso) does.

But it would be even better to avoid inter-process communication entirely and use an [Emacs dynamic module](https://www.phimulambda.org/blog/emacs-dynamic-module.html), linking with a modern LaTeX library that does incremental (instead of batch) compilation.  “Lightweight” alternatives like KaTeX or MathJaX don’t cut it, since we need a full-fat LaTeX compiler, macros and all.  One possible candidate for this is [realtime-tex](https://github.com/HenryXiaoYang/realtime-tex), the `rtex` library, which embeds LuaLaTeX (the most modern of the LaTeX engines) and compiles incrementally and effectively instantaneously
<small>
Although I would be inclined to wait for the project to mature.
</small>
.  This would be a quality improvement almost as drastic as the one `org-latex-preview` makes over its predecessor.

Of course, a dynamic module linking an incremental compiler is a completely different architecture from what we have now, and would share at most the image display and UI layer.  So projects like this and the inevitable official Typst preview package for Org are tabled for another day.  Maybe you’ll be the one to implement them?