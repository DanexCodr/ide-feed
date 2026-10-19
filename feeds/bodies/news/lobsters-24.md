There are some things I do on a regular basis, and of course I try to automate as much as possible so that I don’t need to remember them. One of these things is a weekly review. A part of my weekly review is checking how much time I’d spent on various things during the past week. Of course, I use Org-mode [clock tables](https://www.gnu.org/software/emacs/manual/html_node/org/The-clock-table.html) for that. I have this piece of Elisp

```
(org-dblock-update '(4))
```

which updates all clock tables in the current buffer, and I run it in the Org file before I start my review.

However, this takes some time (slightly less than a minute, but still). My usual procedure is that I evaluate that form some time after I get up on Sundays (I do my review on Sunday morning), then I go to the bathroom or something, and when I’m back, my clock tables are updated.

I thought that it would be cool if Emacs did it itself when I open my laptop on Sunday morning. Emacs has the concept of [idle timers](https://www.gnu.org/software/emacs/manual/html_node/elisp/Idle-Timers.html) which run after it is “idle” for some time (meaning the user didn’t do anything). My idea is that if Emacs is idle for, say, a minute, it’s probable that I am away from keyboard, so I may not come back within another minute. It is then relatively safe to run something which could take a bit longer.

Of course, I definitely do not want Emacs to update my clock tables every time I don’t do anything in it for one (or even ten) minutes – that would be wasteful and potentially annoying. I only want to do this on Sundays, and only once per Sunday.

This means that I need my idle timer to be set up only on Sunday mornings. This means that I need a [regular timer](https://www.gnu.org/software/emacs/manual/html_node/elisp/Timers.html) to set up an idle timer.

Now, I can just set up a repeating timer with a period of one week, aimed at, say, 3am on Sundays. I don’t turn my laptop off (usually), just put it to sleep, so Emacs is basically open all the time. This means that my “regular” timer would run as soon as I open my laptop, say on Sunday at about 5:30am (which is when I usually sit down to my weekly review). This would break if I actually *turned my laptop off* on Saturday evening and turned it back on on Sunday, since the timer set up for 3am would be skipped. If I were worried about such a case, I could add a check in `init.el` to make sure that the idle timer is set up when I turn my laptop on on Sunday morning. (In fact, I could even update the clock tables *in my `init.el`* – since I start Emacs once every few days at most, I don’t really care about longer startup times.) I don’t expect to turn my laptop off on Saturday evening, though, so let’s concentrate on the initial idea of an idle timer.

Note that I don’t need to write any code to find when 3am next Sunday falls – Emacs can already do that using the excellent `org-read-date` function: `(org-read-date t t "Sun 3:00")`. Of course, in order to be able to do that, I need to `(require 'org)` first.

```
(require 'org)

(defun mbork/update-clock-tables-for-weekly-review ()
  "Update clock tables for the weekly review."
  (message "Updating clock tables in personal.org...")
  (let ((inhibit-message t))
    (with-current-buffer "personal.org"
      (org-dblock-update '(4))))
  (message "Updating clock tables in personal.org...done"))

(defun mbork/set-up-clock-tables-update ()
  "Set up updating clock tables with an idle timer."
  (run-with-idle-timer
   60 nil
   #'mbork/update-clock-tables-for-weekly-review))

(run-at-time
 (org-read-date t t "Sun 3:00")
 (* 60 60 24 7)
 #'mbork/set-up-clock-tables-update)
```

As is often the case, after writing this code I learned that it doesn’t work as I expected. The problem is simple. When `mbork/set-up-clock-tables-update` is run after I open my laptop, the time it was asleep is also counted as idle time, so the clock tables are updated *as soon as I open my laptop* – definitely not what I want.

At first I thought that I could attach `mbork/set-up-clock-tables-update` to `post-command-hook` in my `run-with-timer` invocation, and make that function remove itself from that hook. It is definitely not an elegant way, but at least it could work. However, it dawned on me that there might be a better way. If only I could find a way to *reset* the idle timer (without the user doing anything), I could add such a reset to `mbork/set-up-clock-tables-update`. I couldn’t find anything about resetting the idle timer in the Elisp manual, and grepping the sources didn’t give any obvious hints. I asked an LLM how to do that, and it suggested `(setq unread-command-events '(t))` – however, it was not able to explain why I should use `(t)`. I tried reading [the docs](https://www.gnu.org/software/emacs/manual/html_node/elisp/Event-Input-Misc.html), and it seemed to me that the `(t)` was a typical hallucination. (I also asked another LLM, and the answer was a hilarious back-and-forth of “do it this way… no, wait, that doesn’t exist, this way is the right one… no, it doesn’t exist, either”, ended by a suggestion of using `(discard-input)`. After some experiments, I arrived at something that seemed better to me, that is, `(setq unread-command-events nil)`.

I ended up [asking on the Emacs mailing list](https://lists.gnu.org/archive/html/help-gnu-emacs/2026-02/msg00156.html), and after a [false start due to my poor wording](https://lists.gnu.org/archive/html/help-gnu-emacs/2026-03/msg00000.html) of the question, I’ve received a few very interesting answers. (Protip: if you want to ask a question on one of the GNU mailing lists, and you expect a need to link to the ensuing thread, don’t ask near the end of a month, since apparently there is no way to have a single link to a thread spanning more than one month.) First of all, Eli Zaretskii told me that the `(setq unread-command-events nil)` is rather fragile. I didn’t understand why, but it’s Eli, so it’s safe to assume that he does know what he’s talking about. The solution he suggested was very clever – a bit tricky but clearly robust. His idea was to set up a “normal” timer which would then set up an idle timer for 60 seconds. This means that when I wake up my laptop on Sunday morning, this is what will happen. The “Sunday 3:00am” timer will fire and set up another timer. That timer will fire in 60 seconds and set up yet another timer, set up to fire after 60 seconds of idleness. So, if I just open my laptop and do nothing else, the idle time from the whole night will accumulate (so to speak) and the idle timer will run as soon as it is set up, that is, a minute after the laptop was opened. On the other hand, if I do anything in Emacs during that 60 seconds after opening my laptop, my action will reset the idle time, and the idle timer will properly wait until 60 seconds of idleness. Phew! I admit that stacking three timers *is* a bit convoluted (as you can see from my slightly awkward attempts to explain the whole idea in English), but I can see no reason for this contraption to fail. So, let’s get coding!

```
(require 'org)

(defun mbork/update-clock-tables-for-weekly-review ()
  "Update clock tables for the weekly review."
  (message "Updating clock tables in personal.org...")
  (let ((inhibit-message t))
    (with-current-buffer "personal.org"
      (org-dblock-update '(4))))
  (message "Updating clock tables in personal.org...done"))

(defun mbork/set-up-clock-tables-update-after-60-seconds-idleness ()
  "Set up an idle timer to update clock tables."
  (run-with-idle-timer
   60 nil
   #'mbork/update-clock-tables-for-weekly-review))

(defun mbork/set-up-clock-tables-update-in-60-seconds ()
  "In 60 seconds, set up an idle timer to update clock tables."
  (run-with-timer
   60 nil
   #'mbork/set-up-clock-tables-update-after-60-seconds-idleness))

(run-at-time
 (- (org-read-date t t "Sun 3:00")
    (float-time))
 (* 60 60 24 7)
 #'mbork/set-up-clock-tables-update-in-60-seconds)
```

And from now on, every Sunday on 3am (in reality, as soon as I open my laptop) Emacs will update the clock tables *when I leave it for a minute or more*. This way, I can open my laptop on Sunday morning, do things like [capture my weight](https://mbork.pl/2023-05-13_Dieting_with_Org_mode), then go to the bathroom – and assuming I spend at least about two minutes there, come back to updated clock tables. Yay for automation!

One final remark is that one of the answers on the mailing list prompted me to update my Emacs. It turned out that after I blogged about some [cool new things on the master branch](https://mbork.pl/2025-12-08_Some_new_additions_to_Emacs) last December, some *new* cool things landed! One of them is a new built-in package called [system-sleep](https://cgit.git.savannah.gnu.org/cgit/emacs.git/tree/lisp/system-sleep.el?h=master). One of its features is that it allows to attach Elisp functions to `pre-sleep` and `post-wake` events. Note that the `pre-sleep` event is potentially fragile because of reasons outside Emacs – this is what the manual says:  
*Handling ‘pre-sleep’ events should be done as fast as possible and avoid user prompting. Systems often grant a very short pre-sleep processing interval, typically ranging between 2 and 5 seconds. The system may sleep even if your processing is not complete, so be sure you do as little as possible. For example, your function could close active connections or serial ports.*

I don’t think these will be useful in my case – checking if it’s Sunday morning *and* whether the clock tables were updated today or not every time I open my laptop is certainly possible but even more complex than what I have above. Still, it’s good to know that `system-sleep` exists, since it might come in handy some day. As you can see, contrary to some opinions, Emacs is far from dead and new useful things are being implemented all the time!