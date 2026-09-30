I have always liked the idea of having one program to do everything on my computer.
Also, I have always been a fan of text-based interfaces.
These two preferences of mine scream Emacs user, but I have never really used it seriously.

My experience with Emacs has only been installing it every once in a while, opening it up,
failing to understand how it works, and then uninstalling it again.

So why switch to Emacs now?

## What I Was Missing in Neovim

I have successfully been using Neovim for quite some time and was very happy with it.
The thing is, Neovim is meant to be used as a text editor, and to be frank: it excels at that.
I love everything about Neovim: the ergonomic keybinds, the package system, the customizability, everything.
I have been using it for software development and have had zero issues.

One concept I was always fascinated by was text-based browsers like [lynx](https://lynx.invisible-island.net/).
Just being able to access all the information the web has to offer from my terminal felt like a great idea.
In practice, of course, many modern web pages do not accomodate for browsers without javascript support,
but that is besides my point.

Another idea that sparked interest in me was reading emails from the terminal.
Or having a calendar in the terminal.
Or chatting on IRC channels from the terminal.

Basically, I love the terminal.

So what ended up happening was that I had all of these different programs to do different things.
That was fine and it worked well, but each program had their own keybinds and conventions and things to be aware of.

Neovim was just that: one of the many programs I used. I just used it to edit text files.

I would have **loved** to have a program like Emacs that would compile all of these utilities into one large piece of software
(I am aware that much of the functionality I mentioned is achieved through packages in Emacs, but I am mainly referring to having one
large ecosystem to do all of those things rather than one literal codebase that does it).

## Why I Went With Doom Emacs

When it comes to Emacs, I am very much a beginner.
I am not a fan of using premade configurations for whatever software you use - whether we are talking about a window manager like i3 or Hyprland,
or a text editor like Neovim.

In fact, my Neovim config is written by me and has exactly what I need. Another nice bonus of doing this is that I know how everything works.
This means that, should something break, I would be able to fix it.
Or, if I need to add something to my config, I would know where to look.

Now, if I look back at my Neovim journey, I have also experimented with prebuilt configurations for Neovim.
If anybody knows about them, I have tried LunarVim (which I used for quite a while) and NvChad.

Eventually, once I got comfortable with Neovim and figured out what I used frequently, what was left unused, and what I needed,
I proceeded to write my own config.

It’s not like I did not try to use vanilla Emacs, but I just could not do it. I got some basic things working but it
was taking such a long time that, at this pace, it would have taken me literal **months** of work to get to a point that would allow
me to completely switch over from Neovim to Emacs even for my job.

This is the reason why I decided to go with Doom Emacs. On top of all the reasons mentioned above, in my research it seemed to be the case
that Doom Emacs is ideal for people coming from Neovim, like me, since it uses Vim keybinds for everything.
I can definitely confirm that Doom Emacs has eased the transition significantly and I could get up and running fairly quickly.

## Some Things I Like About Emacs

Since the built-in package manager has been introduced in Neovim, this is not as true anymore, but when I first started using Neovim,
this very much did apply: with Emacs, installing new packages is incredibly easy.

As long as you stick to the built-in repositories for Emacs packages (which are rather extensive), you can just do `M-x package-install` and
install a new package. Everything is done automatically. This felt so great to me. It was a breath of fresh air compared to what I was used to.

Also, the setup required to get language servers working (especially before the introduction of the built-in lsp integration that modern Neovim ships with)
is minimal compared to Neovim. Language servers and syntax highlighting have become a central part of my workflow when programming,
and I believe that every serious editor that strives to gain traction should support TreeSitter and LSPs easily and (ideally) natively.

Also, another thing I thoroughly enjoyed in emacs is the extensive documentation. The documentation emacs has is not even comparable to the
Neovim help pages. With emacs, you can easily figure out what a certain key combination does, or what key combination you need to press to
trigger a certain command. You can easily search what commands there are via keywords. It is just so great.

With vanilla emacs you could even press `C-h m` and it would open a list of all the possible actions one can take in that particular scenario
(for those familiar with emacs, with “scenario” I mean major mode).

With Doom Emacs, `C-h m` becomes less useful since all actions are shadowed by the Doom keybinds, but that is completely fine since most
commands start with space anyway, and when you press space and wait a second it opens this convenient little popup that shows you all possible
ways of continuing this keyboard combination. It feels like searching through a menu rather than memorizing keybinds.
With time you naturally get faster at executing the different keybinds you use often and this becomes second nature,
but for newcomers like me this is a very convenient feature.

To be frank, there were plugins in Neovim that did this as well. But that is kind of the point: you had to know how to install plugins before you
could get access to these kinds of features.

And even then - as I said above - I did not find the Neovim help pages to be nearly as useful as the Emacs documentation pages (on top of Emacs having
much better documentation navigation features).

## What I Plan To Do With Emacs

Ideally, as much as possible.

At the moment I am still setting everything up and getting used to it. This blog article, for example, is written entirely in Emacs.

*(By the way, the out-of-the-box Markdown support of Doom Emacs is extraordinary.)*

In the coming days I would like to setup my emails properly (I have tried using Gnus, but will probably switch to Mu4e since it seems simpler),
get to know org-mode much better and figure out how to use Git with Emacs (via Magit).

I might write some guides about these things, here on my blog.

## Conclusion

I just wanted to report on my first-impression when it comes to Emacs as a Neovim user.
If you are thinking about switching, I cannot recommend Doom Emacs enough.
It makes the transition much more seamless and I quite frankly hate the default Emacs keybindigs, so Doom Emacs makes everything
much more usable and ergonomic. I use the Dvorak keyboard layout, so maybe Qwerty keybindings feel better, I am not sure.

Thank you for reading. As always, for questions or suggestions you can reach me at my email [info@eliasebner.com](mailto:info@eliasebner.com).