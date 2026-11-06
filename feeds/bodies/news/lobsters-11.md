Have you ever encountered such a glaring UI bug, that you ask how it is possible no one has fixed it yet?

GitHub thinks I have two unread notifications.
I really wish I had only two.

As of today, I have `2,240` and counting. The Inbox badge says `2`. Further down the same sidebar, a single repository shows `1,680`.

| ![GitHub Notifications sidebar showing an Inbox count of 2](https://nlopes.dev/images/github-notifications/inbox-count.png) | ![GitHub Notifications sidebar showing repositories unread count](https://nlopes.dev/images/github-notifications/repo-list-unread-count.png) |
| --- | --- |

*Yes, I have too many unread notifications. We can have that conversation another day.*

I see this bug **every day** and I had some time to kill this morning so, armed with [OpenAI Codex](https://openai.com/codex/), I went exploring.

GitHub sent both of these in the same response:

```html
<!-- Mobile Inbox -->
<span class="count text-normal">2,240 </span>

<!-- Desktop Inbox -->
<span title="2" data-view-component="true" class="Counter">2</span>
```

The incorrect value was already in the HTML before the browser ran any scripts or laid out the page.

As you can see above, the Mobile Inbox html shows `2,240` and the repository counts also added up to `2,240`. I also validated with my phone per below<sup>[[1](https://nlopes.dev/writing/i-need-the-missing-digits-github#_footnotedef_1)]</sup>.

Retrieving through the [notifications API’s](https://docs.github.com/en/rest/activity/notifications#list-notifications-for-the-authenticated-user) pretty much confirms the total of 2k+ notifications as well.

Codex, sifted through the [javascript code](https://github.githubassets.com/assets/notifications-v2-5d23a751104dc877-35f2e97a2e7f3b71.js.map) because we can just this nowadays (and even though we already knew that the html returned was wrong).
When I told Codex to use its fetch helper directly, we still go the same mismatch.

After all this, and knowing that GitHub uses ruby, my best guess is that a `.to_i` is messing things up.
In Ruby, `"2240".to_i` returns `2240`, while `"2,240".to_i` returns `2`.
I can’t see the server code that produces the badge, so can’t quite be 100% but this would be a simple explanation to why this is happening.

Quite frankly, someone introducing this bug is, well, fine. Bugs exist everywhere.

What bothers me is that this bug has been present for years, and it’s still *right* there.
The badge with the number should give me a sense of how many unread notifications I have, at a glance.
Instead, I’ve learnt to ignore it.

Who at GitHub is actually using the product and paying attention to the UI?

GitHub, I’d quite like the rest of my digits back.
If any GitHub engineer reads this, I beg you, either help us fix this, or write an amazing technical blog post explaining why this is harder to fix than it looks.