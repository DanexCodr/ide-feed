There are some programs that I like to call anthropomorphic software. These
programs have copy in the first person that is personified. A distinction I
would like to make is that LLMs and other conversational AI do not count. I
will, however, talk about them at the end.

A familiar example is Git. Have you ever tried to create a commit on a freshly installed system? You might have encountered this error:

```
*** Please tell me who you are.

    Run

      git config --global user.email "you@example.com"
      git config --global user.name "Your Name"
```

Quite personal for a tool whose primary use is to track mistakes.

Start a rebase while Git finds an existing rebase in progress. It also says
"run me again" and "I am stopping."

```
I wonder if you are in the middle of another rebase.
```

In an interactive terminal, mark a revision during bisect before starting the bisect.

```
Do you want me to do it for you [Y/n]?
```

My favourite. During `git bisect`, skip enough commits that Git cannot narrow
the answer further.

```
We cannot bisect more!
```

Adjacently, Git changelogs too are personified:

> "git fsck" learned to catch NUL byte in a commit object as potential error and warn.
>
> CI test was taught to build documentation pages.

The patch command in --verbose mode:

```
Hmm...  I can't seem to find a patch in there anywhere.
```

```
Looks like a unified diff to me...
```

GNU tar command:

```
Cowardly refusing to create an empty archive
```

The Elm programming language is an extreme example.

```
webpack 5.69.1 compiled with 1 error in 55 ms
Detected problems in 1 module.
-- EXTRA COMMA ----------------------------------------------------- src/App.elm

I am partway through parsing a record, but I got stuck here:

16|         { init = \_ -> init
17|         , view = view
18|         , update = update,,
                              ^

I am seeing two commas in a row. This is the second one!

Just delete one of the commas and you should be all set!

Note: If you are trying to define a record across multiple lines, I recommend
using this format:

    { name = "Alice"
    , age = 42
    , height = 1.75
    }
```

I like this effect when used sparingly, unlike Elm.

With this option enabled, sudo will insult you if you enter an incorrect
password:

```
team@itsfoss:~$ sudo apt update
[sudo] password for team:
When you're walking home tonight, and some homicidal maniac comes after you with a bunch of loganberries, don't come crying to me!
[sudo] password for team:
I'm very sorry, but I'm not allowed to argue unless you've paid.
[sudo] password for team:
sudo: 3 incorrect password attempts
team@itsfoss:~$ sudo apt update
[sudo] password for team:
You'll starve!
[sudo] password for team:
You can't get the wood, you know.
[sudo] password for team:
sudo: 3 incorrect password attempts
team@itsfoss:~$
```

If you have ever attempted Linux From Scratch, you will know that Bash can say
"I have no name!" in the prompt.

On September 1, running Nmap with -v makes it wish itself happy birthday.

For 2026, the message expands to:

```
Happy 29th Birthday to Nmap, may it live to be 129!
```

It also wishes users a merry Christmas on December 25.

If you are aware of any more examples, I would be glad to list them here.

LLM agents are the ultimate version of anthropomorphic software. But agents do
not have to sound human. I force my agents to not speak like humans for my own
sanity. Agents might become the default paradigm of computer user interface in
the future. I will miss anthropomorphic software then.

Most usage of this effect is purely for whimsy and isn't intended to improve
the user experience. Apple's user interface guidelines prescribe avoiding error
messages that contain "uh-oh!"s and "oops"es.