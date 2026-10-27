This release was triggered by the
[eMudhra](https://emudhra.we-have-a-problem.com) CA debacle and getting
informed that Gram is vulnerable due to shipping the `rustls-webpki` and
`webpki-roots` packages. Thus, I recommend everyone to upgrade to 3.4.0 as soon
as possible. If you want to stay on an older version you should rebuild from
source with updated webpki packages.

Although the release was ultimately due to that, it was getting time to tag a
new release anyway. There have been a lot of fixes and some really great new
features implemented, and I want to give a huge thank you to everyone who have
been contributing and helping with the editor. One of the reasons why I have
been holding off on the release is just that I have been so busy this week and
haven't had time to highlight all the improvements as much as I would like to.

Here is a very incomplete list of highlights with this release. More complete
changelog below..

- Side by side view for Git diffs, contributed by @iskrant_x.
- Ability to wrap the tab bar instead of scrolling horizontally, by @kbilkis.
- Helix "Amp Jump" (gw) feature backported by @yilmazer.
- Git commit history view accessible from the git panel (big thank you to @nicoco for working on this as well).
- If a server binary is not found, suggest a command to install it (#485) by @xmort

...OK, it's already too many things, I'm getting lost. Check out the changelog for more!

One thing that has changed that isn't entirely positive is that I have found and
patched a lot more cases where the editor would download stuff behind our backs
without consent. I am determined to close all of these gaps over time, but a
consequence of this is that the editor is a bit more annoying to use now. The UI
for allowing downloads or discovering why a language server isn't running is not
good. I know. I am working on something better. A couple of us have also been
experimenting with replacing or supplanting the Zed extension system with
something more light-weight which would make installing and managing extensions
better. I guess another reason why I didn't tag a release sooner is because I
was hoping to fix some of these usability issues. It'll just have to wait until
the next release. My apologies for any inconvenience caused by these changes.

Again a massive thank you to everyone who are contributing, hanging out in the
XMPP chat channel or just using the editor.

Downloads will as usual be available on
[Codeberg](https://codeberg.org/GramEditor/gram/releases/tag/3.4.0).

Cheers,

*@krig*

## [3.4.0] - 2026-10-23

## Added

- Add 'open current file' button (#583) by @nicoco
- Add 'refresh git history' button (#575) by @nicoco
- Add Helix "Amp Jump" (g w) feature (zed#43733) (#659) by @yilmazer
- Add Repology notes in docs (#470) by @koru
- Add completion_menu_item_kind option to display text icons for completion items. (#623) by @CubeOfShame
- Add code outline support for diff files (#524) by @jqslr
- Add generate shell completions via cli by @ycna07
- Add refs information to commit history views
- Add setting to show pinned tabs in a separate row (zed#46573) (#633) by @kbilkis
- Add setting to wrap tabs onto multiple rows (#643) by @kbilkis
- Add settings-alias support (#581) by @nitbook
- Add side-by-side Git diff view (#565) by @iskrant_x
- Add smart sort for project panel: mod.rs sorts first (#541) by @patchunwrap
- Add support for C23 keyword 'constexpr' (#522) by @mgrave
- Add toggle to enable/disable git hooks + fix running commit-msg hook (#594) by @nicoco
- Add tombi as an LSP and formatter for TOML (#626) (#616) by @psy-q
- Allow disabling 'auto focus on paste' (#487) by @rockisch
- Bundle OpenMoji as emoji fallback (#478)
- Configure debug adapter permissions in language server config view
- Generate color for each commit author
- Handle '#' links in Markdown preview (#514) by @rockisch
- Highlight TODO/NOTE/WARN: comments in builtin languages (#534) by @nitbook
- If a server binary is not found, suggest a command to install it (#485) by @xmort
- Implement clipboard file and image copy for MacOS (#487) by @rockisch
- Language support for Typst via tinymist (#517) by @theDoctor
- Refresh file history view on repository change
- Rework show_tab_bar_buttons setting to allow always showing (#637) by @sir_nacnud