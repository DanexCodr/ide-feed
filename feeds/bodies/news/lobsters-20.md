> The CSS Working Group just discussed [css-forms-1] Cursors for base appearance, and agreed to the following:
>
> - RESOLVED: Adopt cursor rules in the last comment.
> - SUMMARY: Pointer = “click this thing”, text cursor says “prepare to enter text”, grabbing hand says “drag this”.

One of the rules from the “last comment” mentioned there is

```
select, option, input[type=checkbox], input[type=radio],
button, input[type=button], input[type=submit], input[type=reset], input[type=color], input[type=image], ::file-selector-button {
	cursor: pointer;
}
```

Or, if we were to remove all non-button selectors,

```
button {
	cursor: pointer;
}
```

That is, of course, not a change to the default styles in the browser — this is a rule for elements that will have an `appearance: base-…`.

Also note that, this user agent style will be very much overrideable — no `!important`.

Anyone who does not like `cursor: pointer` on buttons and other similar elements, are free to override it to `default` (or anything else) in their stylesheets.

The rest of us can, I guess, celebrate? I was always on the side of this decision. I published my [“Correct Cursor on Active Elements”](https://kizu.dev/cursor-pointer/) article in 2013. In 2017, I opened my first CSSWG issue — [“Change the pointer cursor to indicate any interactive element”](https://github.com/w3c/csswg-drafts/issues/1936), which led to a change in a non-normative part of the spec.

Since then, I did not see any new arguments in this debate. I will not repeat everything that I argued about, but one of the most common counter-arguments that I read today is “OS does not do it”.

Did you see that “OS”? When was the last time your OS innovated anything in the UI? Did it become easier to use over years?

Many of people with this argument ask, thinking that this will be a good question, something like “What next — change the cursor in the OS?!”.

I mean… Yes? I would be happy with that. When I look at like half of the (non-native) apps in my desktop OS, they have `cursor: pointer` on interactive elements.

Cinny, Discord, Signal, Slack, Steam, VS Code — some of the apps that I have before me.

When I use apps that *do not* change the cursor to anything other than `default`, I cringe.

Default cursor does not communicate anything. It does one job well — point at a specific pixel. It could do more.

In the issue, many people came with dislikes and their arguments against `cursor: pointer`. I want to aknowledge one argument that I fully agree with — it would be great if buttons and links would have different cursors. And also, regular links should have cursors different from the links that are opened in new tabs.

We need more cursors.

But if we were to look at those three things:

- Blank space on the page.
- Buttons.
- Links.

And then had only two cursors to assign to all of them, I know which ones I will assign to which.

And I will never understand anyone thinking that buttons have more in common with blank space than with links.