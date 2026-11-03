Tor Browser 16.0 is now available for [Desktop](https://download.torproject.org/tor-browser-for-desktop/) and [Android](https://download.torproject.org/tor-browser-for-android/). This is our first stable release based on Firefox ESR 153, incorporating a year's worth of changes that have been shipped upstream in Firefox. As part of this process, we've also completed our annual ESR transition audit, where we reviewed and addressed [over 270 Bugzilla](https://gitlab.torproject.org/tpo/applications/tor-browser/-/work_items?sort=updated_desc&state=all&search=Review%20Mozilla&milestone_title=Browser%2016.0&label_name%5B%5D=Apps%3A%3AType%3A%3AAudit&first_page_size=100) issues covering changes in Firefox that could negatively affect the privacy and security of Tor Browser users.

The ongoing development of Tor Browser is made possible thanks to the support of our community. Every donation helps power the tools that let people browse freely and privately. Consider [joining thousands of others who have already made a small contribution](https://torproject.org/donate/donate-bp2-yec2026) towards building a better internet for everyone.

## What's new for Desktop?

![](https://blog.torproject.org/new-release-tor-browser-160/160-desktop.png)

### Redesigned Settings

Tor Browser connects millions of people to the Tor network (and by extension, the free and open internet) out of the box. However, for those who need to circumvent advanced censorship, boost their security level, or tailor their browsing experience, clear and easy-to-use Settings are essential. To that end, Tor Browser 16.0 introduces a complete redesign of the Settings experience based on a parallel redesign [shipped in Firefox in June](https://blog.mozilla.org/en/firefox/firefox-settings/). Improvements include a cleaner layout, updated navigation, and clearer labels and descriptions aimed at making settings easier to find, understand, and manage. Other noteworthy changes include:

- The long-standing "General" page has been retired, with its contents distributed across new pages for Appearance, Downloads, Tabs and browsing, Accessibility and Languages.
- Pages and components that are unique to Tor browser like Connection and Security Level have been rebuilt from scratch using Firefox's new components so they look and feel consistent with the rest of Settings.
- Some settings that, if enabled, could compromise your privacy or make your browser easier to fingerprint have either been hidden or feature clear warnings.

Fear not: your existing preferences will remain saved even if the original setting has moved or changed, and you can use the search bar at the top of Settings to find anything you're struggling to track down.

### Generic window titles

Another new addition to Settings is the option to use generic window titles, which can be found under Privacy and security → Protections from third-party applications. Like most browsers, Tor Browser uses the title of the page you're currently viewing for the names of its windows. However, other applications on your computer or your operating system itself can read these titles without special permissions. When enabled, this option simply replaces all window titles with "Tor Browser" — preventing other software from snooping on your browsing history. As always, for more comprehensive protection from third-party applications on your device, we recommend using [Tails](https://tails.net/).

For now, this option is strictly opt-in, as we did not have sufficient time during this release cycle to properly evaluate potential side-effects for users. In particular, we worry that enabling this setting may reduce the browser's usability for those who rely on accessibility tools (e.g. screen-readers) or those with highly customized systems (e.g. less-popular desktop managers, application switchers, etc). If you are one of these users, we would ask that you try using this setting, and report back any bugs or usability issues you find!

📣 Generic window titles have also been upstreamed to Firefox as part of the [Tor Uplift Project](https://wiki.mozilla.org/Security/Tor_Uplift). Advanced Firefox users can enable this feature by opening `about:config` and setting `privacy.exposeContentTitleInWindow` (for normal windows) and `privacy.exposeContentTitleInWindow.pbm` (for private browsing windows) to `false`.

### New user manual

The Tor Browser manual, which can be found by visiting `about:manual` or through the application menu (☰) → Help → Tor Browser manual, has also received a complete revamp. Since the [release of our new Support portal in 2025](https://blog.torproject.org/new-user-support-portal-tor-tails/), the team has had to maintain two sets of documentation: one for the traditional manual that's available to read in Tor Browser, and another for the new Support site. With this release, we've solved that problem by replacing the older material in the Tor Browser manual with our latest and greatest help content from the new Support site. Like the previous iteration of the manual, the new version is bundled with Tor Browser for Desktop so it can be read offline, which comes in particularly handy when troubleshooting issues that prevent you from connecting to the Tor network.

### Linux on ARM

Finally, after a year of testing, Tor Browser 16.0 now features native support for Linux computers with 64-bit ARM (AArch64) processors, such as Raspberry Pis and Apple Silicon Macs running Linux. If you have been relying on Tor Browser Alpha for support for these devices, we recommend switching over to the stable release channel unless you plan to continue testing Alpha releases. Meanwhile, Tor Browser 16.0 follows Firefox in ending support for 32-bit x86 Linux computers. Fortunately, very few people should be affected, as we currently receive around 200 update checks from this platform a day, down from a peak of around 4,000 in 2019. Most remaining 32-bit users should be able to switch to the 64-bit version unless they're running outdated hardware or versions of Linux.

## What's new for Android?

![](https://blog.torproject.org/new-release-tor-browser-160/160-android.png)

Tor Browser for Android has also benefited from Mozilla's ongoing work to modernize Firefox, as seen in the Settings redesign on desktop. Over the past year, Firefox has been gradually transitioning to Jetpack Compose — Google's newest framework for building native Android interfaces. In this release, we've made significant progress applying the same changes to Tor Browser. As a result, large swaths of Tor Browser's user interface has been updated to Material Design 3 — the latest iteration of Google's design language for Android — with more yet to come in future releases.

Google Play limits the size of apps distributed as APKs to 100 MB. Since Firefox for Android continues to grow with each release, keeping Tor Browser within this limit has been an ongoing challenge — for example, this issue has prevented us from bundling Tor Browser's manual on Android so that it can be accessed offline. Nevertheless, we've found various ways to reduce the size of our Android package over the years and stay within the limit. Most recently, this involved carefully and creatively compressing some of the built-in resources Firefox uses to display its interface.

## What's in the works?

Tor Browser users can expect additional improvements over the next few months as we continue to refine the new Settings experience for desktop and Material Design 3 for Android. If you find a bug or have a suggestion for how we could improve this release, [we'd love to hear your feedback](https://support.torproject.org/get-in-touch/bug-or-feedback/).

The team is also working hard on a new and improved circuit display, coming soon to Tor Browser Alpha, which integrates site information directly into the circuit panel and can visualize more complex multi-path circuits. Multi-path circuits use additional relays to split your traffic into two paths that converge on a single exit, improving both connection speed and reliability. These circuits already exist for regular websites (but not onion sites) and are randomly assigned based on network availability. Although Tor Browser's traditional circuit display can only show a single path at a time, you have likely benefited from a multi-path circuit without even knowing it. What's more, this exciting update will mark the debut of the circuit display on Tor Browser for Android, which has been exclusive to desktop until now.

## Contributions <3

Thanks to all of the teams across Tor, and the wider community, who contributed to this release. In particular, we'd like to extend our gratitude to the following volunteers who have contributed their expertise, labor, and time:

If you would like to contribute to a future release, please see our [guide for new contributors](https://gitlab.torproject.org/tpo/applications/wiki/-/wikis/Development-Information/Tor-Browser/Contributing-to-Tor-Browser) to get started.

## Full changelog

The [full changelog](https://gitlab.torproject.org/tpo/applications/tor-browser-build/-/raw/maint-16.0/projects/browser/Bundle-Data/Docs-TBB/ChangeLog.txt) since Tor Browser 15.0.26 is:

- All Platforms
  - Updated NoScript to 13.6.37.1984
  - Updated tor to 0.4.9.15
  - Bug tor-browser#43857: Review in-source TODOs
  - Bug tor-browser#43858: Clean out deprecated or unused methods in TorConnect
  - Bug tor-browser#44118: Decide how to deal with upstream feature gates in a RR world
  - Bug tor-browser#44251: Drop pt_config.json meek-azure migration logic
  - Bug tor-browser#44257: Disable locale-based font rules as a defense-in-depth
  - Bug tor-browser#44280: Test stream isolation
  - Bug tor-browser#44420: Drop "rights" from components.conf
  - Bug tor-browser#44492: Fix python linting warnings in our test files
  - Bug tor-browser#44562: Set the new online Suggest prefs to false
  - Bug tor-browser#44571: Disable restrict_to_adults for potential fingerprintability
  - Bug tor-browser#44580: Registers NoScript to check for updates on first run
  - Bug tor-browser#44619: Add custom logs to Tor logs
  - Bug tor-browser#44621: Move about:torconnect back to browser
  - Bug tor-browser#44647: Clean up patch for SearchEngineSelector.sys.mjs.
  - Bug tor-browser#44663: NoScript behavior on “Safer” security level prevents integrity checks for dynamically loaded javascript
  - Bug tor-browser#44687: Expect javascript.options.asmjs to be false for all security levels
  - Bug tor-browser#44701: Unexpected change to netwerk/url-classifier/components.conf
  - Bug tor-browser#44720: Migrate New Identity commit to Tor Browser
  - Bug tor-browser#44753: Drop TorProvider.isBootstrapDone
  - Bug tor-browser#44755: Trusted Types (Firefox 148 and above) + Web Workers broken on Safer Level
  - Bug tor-browser#44763: Disable WebGPU until audited
  - Bug tor-browser#44764: Hide some AI settings using browser.ai.control.default
  - Bug tor-browser#44767: Safer Level's worker patching throws on new about:blank frames with Trusted Types
  - Bug tor-browser#44778: Safer Level: xray causes patched TrustedTypePolicy instances to be unusable by content.
  - Bug tor-browser#44795: Revert BB 27604 patch as not needed anymore
  - Bug tor-browser#44796: Adjust TorProviderBuilder to report the provider state to consumers
  - Bug tor-browser#44801: Redact onion origins from Location.ancestorOrigins.
  - Bug tor-browser#44811: Remove the lock on pdfjs.disable.
  - Bug tor-browser#44814: Disable trustpanel until our new designs are ready
  - Bug tor-browser#44815: Disable harmful addon URL blocking
  - Bug tor-browser#44828: Remove browser module references from toolkit/modules/ActorManagerParent.sys.mjs
  - Bug tor-browser#44841: TorDomainIsolator proxy filter returns null on exception instead of preserving SOCKS proxy
  - Bug tor-browser#44857: Drop browser.display.use_system_colors from our preference list
  - Bug tor-browser#44865: Block chrome:///locale/ to content
  - Bug tor-browser#44870: Remove legacy branch from gitlab templates
  - Bug tor-browser#44896: Drop privacy.partition.network_state
  - Bug tor-browser#44990: CI failing due to dubious ownership of cached repo
  - Bug tor-browser#45037: Potential runtime errors in the search service when changing JS status
  - Bug tor-browser#45047: Cross-site oracle via worklet rejection error in Safer Mode
  - Bug tor-browser#45072: Disable XSLT already for 16.0
  - Bug tor-browser#45073: Review preference changes between Firefox 141 and 153
  - Bug tor-browser#45080: Keep the Reporting API disabled.
  - Bug tor-browser#45131: Security level is using an unsafe getBoolPref
  - Bug tor-browser#45161: Drop TorProviderBuilder.firstWindowLoaded
  - Bug tor-browser#45333: Disable the fast-path to skip proxy resolution
  - Bug tor-browser#45336: Pass --disable-proxy-direct-failover in our mozconfigs
  - Bug tor-browser#45410: Incomplete Safer Level propagation to nested workers
  - Bug mullvad-browser#483: Add the "No AI" version of DuckDuckGo to available search engines
  - Bug tor-browser-build#41686: Copy more build artifacts to the artifacts directory
  - Bug tor-browser-build#41713: Try to find a component for bugs found with commits in triage spreadsheets
  - Bug tor-browser-build#41780: Create sha256sums-unsigned-build.txt in artifacts/$platform directories
  - Bug tor-browser-build#41846: Sign alpha releases using new gpg subkey
- Windows + macOS + Linux
  - Updated Firefox to 153.6.0esr
  - Bug tor-browser#34319: Remove symlink support from the updater
  - Bug tor-browser#42065: Security exception warning and button for Onion Services with self-signed certificates
  - Bug tor-browser#42664: Use mozilla token sizes in CSS
  - Bug tor-browser#43560: Add "UTC" to the end of the timestamp on tor logs (Desktop)
  - Bug tor-browser#43570: Report errors in about:torconnect when tor daemon crashes (Desktop)
  - Bug tor-browser#43640: Poor screen reader experience when opening preferences and scrolling to element
  - Bug tor-browser#43824: Switch resource:// modules to use moz-src:
  - Bug tor-browser#43939: Update Bridge settings when connection failed
  - Bug tor-browser#44247: Adapt Tor Browser manual to use the new support pages
  - Bug tor-browser#44289: RFPHelper console error when --toolbar-field-color is set to inherit
  - Bug tor-browser#44302: Fix the flags of some about pages
  - Bug tor-browser#44343: Hide the default browser settings again after MozBug 1969949
  - Bug tor-browser#44411: DownloadsTorWarning.sys.mjs fails to load
  - Bug tor-browser#44419: Re-add the moz-toggle title attribute patch
  - Bug tor-browser#44439: Remove translate action from urlbar
  - Bug tor-browser#44458: Fix the "Connect" and ".onion available" button height
  - Bug tor-browser#44459: Letterboxing content alignment setting is missing styling
  - Bug tor-browser#44460: Payment methods and addresses setting headings are visible in settings
  - Bug tor-browser#44511: Make sure new search suggest features are disabled for 16.0
  - Bug tor-browser#44520: Make sure "Firefox labs" is hidden by default
  - Bug tor-browser#44522: Move common changes to about dialog to base-browser
  - Bug tor-browser#44528: Make sure desktop IP Protection is disabled on desktop
  - Bug tor-browser#44535: Letterboxing background colour is no longer used
  - Bug tor-browser#44560: Customize the flags for alternate 'Application Data' directories
  - Bug tor-browser#44629: Add a search suggestion warning in the settings
  - Bug tor-browser#44630: Use settings config to hide settings, rather than data-hidden-from-search or commenting out
  - Bug tor-browser#44682: Wrong pid in the exit log
  - Bug tor-browser#44685: Use border radius for letterboxing
  - Bug tor-browser#44706: creating a new profiles causes crash ENOTTY
  - Bug tor-browser#44709: Hide the AI settings panel
  - Bug tor-browser#44710: Hide about:preferences#translations
  - Bug tor-browser#44765: Restore the limited sidebar description
  - Bug tor-browser#44781: Use a static page title for about:torconnect
  - Bug tor-browser#44793: privacy.spoof_english console error in about:preferences
  - Bug tor-browser#44797: Clean up about:torconnect styling
  - Bug tor-browser#44798: Don't load about:torconnect into iframes
  - Bug tor-browser#44799: Onionize toggle in about:tor uses blue text color
  - Bug tor-browser#44802: Hide the "safe browsing" settings
  - Bug tor-browser#44829: Hide the settings privacy card
  - Bug tor-browser#44830: Migrate our home page adjustments to the settings config
  - Bug tor-browser#44831: Misleading banner in "Search engine suggestions" settings
  - Bug tor-browser#44832: Hide the Firefox mascot in about:neterror
  - Bug tor-browser#44844: Use new urlbar CSS variables
  - Bug tor-browser#44846: about:torconnect redirect doesn't work with the new neterror page
  - Bug tor-browser#44847: Drop letterboxing sidebar rounded corner logic
  - Bug tor-browser#44855: Use ariaNotify for bridge updates
  - Bug tor-browser#44883: Remove urlbar quick action for labs
  - Bug tor-browser#44888: Use --button-opacity-disabled for disabled styling.
  - Bug tor-browser#44902: Error in privacy preference initialisation due to missing dataCollectionViewProfilesMultiProfileBackupWarning
  - Bug tor-browser#44903: Use the support-page instead of tor-manual-page in moz-support-link
  - Bug tor-browser#44904: Use settings config for onion site settings
  - Bug tor-browser#44952: TOR_PROVIDER=none throws an error at launch
  - Bug tor-browser#44955: Use context-fill for about-wordmark.svg
  - Bug tor-browser#44956: Switch colours in letterboxing setting icons to match the tab-alignment icons
  - Bug tor-browser#44959: Integrate the new Tor Browser manual into Tor Browser
  - Bug tor-browser#44991: Improve the no-authentication handling on the control port
  - Bug tor-browser#44998: Remove Firefox branding from about:preferences
  - Bug tor-browser#45005: Rename arrowpanel CSS variable
  - Bug tor-browser#45029: Convert connection status settings to new design and config approach
  - Bug tor-browser#45039: Make it easier to test ProfileDataUpgrader customization
  - Bug tor-browser#45051: Show a separate Tor error prompt for users who do not see about:torconnect (desktop)
  - Bug tor-browser#45055: Rename --color-gray-05 to --color-gray-0
  - Bug tor-browser#45058: Convert bridge settings to new design and config approach
  - Bug tor-browser#45059: Convert advanced connection settings to new design and config approach
  - Bug tor-browser#45079: Move letterboxing to the appearance setting pane
  - Bug tor-browser#45081: Use the new "Acorn" icons on desktop
  - Bug tor-browser#45083: Error in about:preferences due to ipprotection missing
  - Bug tor-browser#45112: Rename border colour tokens
  - Bug tor-browser#45123: Disable profile backup for 16.0
  - Bug tor-browser#45125: Tidy up bridge emoji widget
  - Bug tor-browser#45132: nsAppFileLocationProvider.cpp: use of undeclared identifier 'XRE_EXECUTABLE_FILE'
  - Bug tor-browser#45133: Disable browser.toolbars.share-button.enabled
  - Bug tor-browser#45143: Modify moz-fieldset to allow focusing the heading
  - Bug tor-browser#45156: Remove "Firefox Home" from the appearance settings
  - Bug tor-browser#45157: Grant "access local files" permission to NoScript
  - Bug tor-browser#45168: Hide the history search option, again
  - Bug tor-browser#45169: Cannot open history sidebar in private browsing window
  - Bug tor-browser#45171: Disable split view for 16.0
  - Bug tor-browser#45176: Add "Request English" to the website language config
  - Bug tor-browser#45177: Remove websiteSpoofEnglishControl
  - Bug tor-browser#45178: Change support URLs in new settings
  - Bug tor-browser#45179: Update the feedback URL to point to the new support page.
  - Bug tor-browser#45180: Also show download warning in download settings
  - Bug tor-browser#45185: Disable network also in the Rust implementation of the remote settings client
  - Bug tor-browser#45186: Remove duplicate alert roles in moz-message-bar
  - Bug tor-browser#45187: Disable private browsing "delete downloaded files" feature
  - Bug tor-browser#45190: New circuit urlbar icon button is squished
  - Bug tor-browser#45192: Some URLs trigger The proxy server is refusing connections rather than about:torconnect prior to bootstrap
  - Bug tor-browser#45194: Hard code the "Your bridges" background colour
  - Bug tor-browser#45195: Modify our calls to openPreferences to work with the new settings
  - Bug tor-browser#45196: Replace old connection settings with setting-group widgets
  - Bug tor-browser#45197: Hide password settings by default
  - Bug tor-browser#45200: Include onion authentication in the new password settings
  - Bug tor-browser#45201: Convert security level settings to the new config
  - Bug tor-browser#45208: Switch on the setting redesign
  - Bug tor-browser#45209: Remove mention of "sync" from new settings
  - Bug tor-browser#45211: Add settings for protections from third party applications
  - Bug tor-browser#45214: Keep megalist (contextual password manager) disabled for 16.0
  - Bug tor-browser#45226: Stylelint issues on browser/components/torpreferences/content/torPreferences.css
  - Bug tor-browser#45228: Drop browser.urlbar.update2.engineAliasRefresh
  - Bug tor-browser#45232: Spoof picture-in-picture sizes under RFP
  - Bug tor-browser#45236: Resolve miscellaneous accessibility issues in about:torconnect
  - Bug tor-browser#45249: Remove the duplicate "Verified by" from the old site identity panel
  - Bug tor-browser#45262: Disable reset PBM burn button and related UI migration
  - Bug tor-browser#45277: Change setting icon for About Tor Browser
  - Bug tor-browser#45278: Explicitly disable WebXR
  - Bug tor-browser#45343: Hide verifier and the related error for self-signed onion cert case
  - Bug tor-browser#45360: Port our language preference customization to the new settings design
  - Bug tor-browser#45403: Ensure RemoteSetting dumps are loaded ASAP
  - Bug tor-browser-build#41800: Create a script that adapts the Tor Browser manual HTMLs to work in Tor Browser
- Windows + Linux
  - Bug tor-browser-build#40892: Move torrc-defaults, geoip and geoip6 on Windows and Linux
- Windows + Android
  - Bug tor-browser#44513: Backport Bugzilla 2059471: Do not spoof screen orientation when it is locked
- Windows
  - Bug tor-browser#44461: Window controls are missing on Windows
  - Bug tor-browser#44513: Backport Bugzilla 2059471: Do not spoof screen orientation when it is locked
  - Bug tor-browser#44633: Move D3D11 function from local webrtc changes to tbb webrtc patches
  - Bug tor-browser#44745: Change how we hide SSO setting for windows
  - Bug tor-browser#44862: Fontvis is missing Segoe MDL2 Assets
  - Bug tor-browser#45144: Do not offer to make the browser a PDF viewer when in portable mode
  - Bug tor-browser#45243: Disable taskbar tabs
  - Bug tor-browser#45293: Set widget.windows.tablet_detection_override to -1
- macOS
  - Bug tor-browser#44728: Bundled fonts are broken on macOS when the GPU process is enabled
  - Bug tor-browser#44850: Wrong path for bootstrapped tor daemon on macOS
  - Bug tor-browser#45108: Artifact generation fails due to missing .DS_Store in the branding directories
  - Bug tor-browser#45163: Consistently do not disable app group container support
  - Bug tor-browser-build#41476: Since 13.5-legacy is not longer supported, remove tools/signing/wrappers/sign-rcodesign
- Linux
  - Bug tor-browser#44050: Change the domain in DBus interfaces
  - Bug tor-browser#44410: Use system's size for UI font on Linux
  - Bug tor-browser#44521: Disable widget.wayland.fractional-scale.enabled
  - Bug tor-browser#44887: Drop Linux 32-bit deprecation notice
- Android
  - Updated GeckoView to 153.6.0esr
  - Bug 40627: [Android] "share" selected text only works once [tor-browser]
  - Bug tor-browser#41758: Don't allow PDFs to be opened by 3rd party apps
  - Bug tor-browser#43349: Add user feedback for when Tor connects (Android)
  - Bug tor-browser#43403: Add "UTC" to the end of the timestamp on tor logs (Android)
  - Bug tor-browser#43543: Make the dev icon distinct from the nightly one
  - Bug tor-browser#43571: Implement improved error handling and tor restart flow (Android)
  - Bug tor-browser#43790: Address "Various android workarounds" commit introduced in the 138 rebase
  - Bug tor-browser#43819: Show custom security level on android
  - Bug tor-browser#43820: Use SecurityLevel integration on Android
  - Bug tor-browser#43856: Fix onBackPressed() deprecation
  - Bug tor-browser#44054: Remove "open" button from download snackbar; second line defense for shouldShowAppDownloaderDialog
  - Bug tor-browser#44057: Drop about:torconnect from android
  - Bug tor-browser#44091: Add frequent regions to tor connection assist for Android
  - Bug tor-browser#44155: Always enable LNA on Android as a defense-in-depth
  - Bug tor-browser#44157: Remove secret setting toggle for Tab Management Redesign
  - Bug tor-browser#44175: Remove all default browser functionality (Android)
  - Bug tor-browser#44210: Drop shouldDisableNormalMode setting
  - Bug tor-browser#44211: Disable "Shake it up. Skip the scroll."
  - Bug tor-browser#44226: Disable all link sharing functionality
  - Bug tor-browser#44274: Re-add Screenshot setting
  - Bug tor-browser#44303: Fix extension update job on first launch on Android
  - Bug tor-browser#44323: Audit Android Settings changes from 128 to 140
  - Bug tor-browser#44324: Refactor the NSS no proxy-bypass patch on A-S to avoid -Wunreachable-code
  - Bug tor-browser#44448: Trivialise unused assets rather than delete them
  - Bug tor-browser#44506: Remove more sync
  - Bug tor-browser#44507: Drop the dependency on Sentry
  - Bug tor-browser#44548: Remove "Passwords" UI from Android
  - Bug tor-browser#44581: Cleanup new Android compose tab-strip feature introduced in Firefox 147
  - Bug tor-browser#44582: Fix or remove new settings search functionality on Android
  - Bug tor-browser#44615: Remove ability to "Rate/Review in Google Play" in app
  - Bug tor-browser#44653: Disable "Allow search suggestions in private sessions" prompt presented in RR 148 android
  - Bug tor-browser#44694: Remove new "Tab bar" feature on Android
  - Bug tor-browser#44698: Clean up comments in AccountSettingsFragment.kt. FIXME: Update A-S
  - Bug tor-browser#44700: Untracked change to HomepageHeader.kt
  - Bug tor-browser#44718: Fix splash screen branding and other issues in RR
  - Bug tor-browser#44721: Android build failure in nightlyOssLicensesTask: missing dependencies.json file
  - Bug tor-browser#44751: NoScript (and likely any extension) can be accidentally turned off
  - Bug tor-browser#44752: Remove new expanded toolbar option on Android due to fingerprintability
  - Bug tor-browser#44758: Disable email mask feature
  - Bug tor-browser#44769: TBA crash screen has Firefox asset as well as a "Send crash report" button
  - Bug tor-browser#44788: Extensions are unreachable via 3 dot menu in alpha (android)
  - Bug tor-browser#44789: Icon of "New Circuit" is not centered but lies in top left corner
  - Bug tor-browser#44827: Always enable NoScript for Android
  - Bug tor-browser#44842: Replace instances of SwitchPreference with SwitchPreferenceCompat
  - Bug tor-browser#44848: Do not overwrite Android toolchains on default mozconfigs
  - Bug tor-browser#44881: Remove link sharing setting on Android
  - Bug tor-browser#44913: Fully disable custom download location
  - Bug tor-browser#44917: Disable Ads client for all channels
  - Bug tor-browser#44921: Disable Google Lens feature
  - Bug tor-browser#44935: Remove incorrectly shown "Open in App" notification dot on settings button
  - Bug tor-browser#44936: Search widget icon is too small
  - Bug tor-browser#45031: Disable AI features for Android
  - Bug tor-browser#45045: Remove moz asset in Downloads screen
  - Bug tor-browser#45049: Opening a pdf from outside TBA crashes TBA after bootstrapping it not already bootstrapped
  - Bug tor-browser#45052: Initialise Tor modules on Android in the same order as desktop
  - Bug tor-browser#45085: Disable GooglePlay Integrity
  - Bug tor-browser#45098: Share link button shows in landscape mode on android despite being removed elsewhere
  - Bug tor-browser#45103: Disable broken "tab management"
  - Bug tor-browser#45109: No value passed for parameter 'jsEnabled'
  - Bug tor-browser#45118: Audit and disable Mozilla VPN promo
  - Bug tor-browser#45130: Clean up TorHomePage padding
  - Bug tor-browser#45159: Fix Android Padlock security pane colors
  - Bug tor-browser#45170: Tab Switcher shows Firefox's private browsing mask badge on tab switcher icon
  - Bug tor-browser#45172: Move our "Connect to Tor before opening links" code from the deprecated openToBrowserAndLoad to the recommended loadUrlOrSearch
  - Bug tor-browser#45173: Disable Search Optimizations for Android
  - Bug tor-browser#45221: Remove "Manage downloads with another app" setting from TBA download settings
  - Bug tor-browser#45225: Remove "Share" and "Translate" options from "Settings" -> "Customize" -> "Toolbar shortcut"
  - Bug tor-browser#45227: Remove "Default search engine for Standard Mode"
  - Bug tor-browser#45234: Do not spoof secondary screen orientations if they were requested by a lock
  - Bug tor-browser#45250: Remove "Privacy report" in tabs settings in Android
  - Bug tor-browser#45251: Turn off and hide the remote improvements UI
  - Bug tor-browser#45252: Remove the change wallpaper menu item
  - Bug tor-browser#45261: Add linter check: only MAIN+LAUNCHER components may be exported="true"
  - Bug tor-browser#45269: Completely disable search suggestion feature
  - Bug tor-browser#45275: Drop clearOnShutdown on Android-specific profile
  - Bug tor-browser#45280: about:config broken on Android
  - Bug tor-browser#45281: Fix screen lock to hide Tor Browser tabs feature
  - Bug tor-browser#45363: Disable import bookmarks in Android
  - Bug tor-browser-build#28595: Remove the need to update var/gradle_dependencies_version
- Build System
  - All Platforms
    - Bug tor-browser#43180: Remove translation CI 13.5 legacy extension
    - Bug tor-browser#43951: Include product with the component in triage CSVs
    - Bug tor-browser#44452: Improve tb-dev range-diff and diff-diff
    - Bug tor-browser#44498: Update translations CI to account for 1.0 version gap between alpha and stable
    - Bug tor-browser#45224: Enable Rust linter in CI
    - Bug tor-browser#45334: Update marionette harness to accept multiple tags
    - Bug tor-browser-build#31860: Start using LTO for firefox project
    - Bug tor-browser-build#40903: Make xz multi-threaded
    - Bug tor-browser-build#41445: Better handle bugzilla "Web Compatibility" issues in generate-bugzilla-triage-csv
    - Bug tor-browser-build#41591: Remove support for old mar filenames when 13.5 legacy branch is EOL
    - Bug tor-browser-build#41607: Fix regression from #41373 in tools/count-mar-downloads
    - Bug tor-browser-build#41608: Add per-platform numbers for incrementals in count-mar-downloads
    - Bug tor-browser-build#41647: Add a XZ_DEFAULTS to set_default_env
    - Bug tor-browser-build#41648: Add a mozconfig to projects/geckoview
    - Bug tor-browser-build#41660: Add a Firefox target to build unpatched Firefox in tor-browser-build
    - Bug tor-browser-build#41664: Investigate and fix issue with unexpected build_id changes
    - Bug tor-browser-build#41668: Build mozharness.zip when building dev artifacts
    - Bug tor-browser-build#41671: Update tools/signing/linux-signer-sign-android-apks to check for v3 signatures instead of v1
    - Bug tor-browser-build#41678: use set -u and set -o pipefail
    - Bug tor-browser-build#41685: Add henry to list of taggers in relevant projects.
    - Bug tor-browser-build#41687: Add single make list_toolchain_updates command to list all toolchain updates
    - Bug tor-browser-build#41690: Merge list_toolchain_updates-firefox-* commands into one
    - Bug tor-browser-build#41693: Drop base-browser targets
    - Bug tor-browser-build#41705: Remove unnecessary workaround in projects/go/build
    - Bug tor-browser-build#41707: firefox-l10n fails to build with fetch_locale: 1: set: Illegal option -o pipefail
    - Bug tor-browser-build#41726: Check in list_toolchain_updates that the sha512sum we have for the macOS SDK is the same as Mozilla
    - Bug tor-browser-build#41727: Split the list_toolchain_updates_checks script in two
    - Bug tor-browser-build#41728: Update projects/application-services/list_toolchain_updates_checks to check nss sha256sum
    - Bug tor-browser-build#41753: Allow running custom commands when vendoring Go dependencies
    - Bug tor-browser-build#41766: Use gzip for all platforms for Go vendoring
    - Bug tor-browser-build#41778: Remove base-browser from protected-branches.py
    - Bug tor-browser-build#41780: Create sha256sums-unsigned-build.txt in artifacts/$platform directories
    - Bug tor-browser-build#41786: Add comment to rbm.local.conf.example warning about potential recursive loops in tmp_dir definition
    - Bug tor-browser-build#41806: make list_toolchain_updates should check var/firefox_platform_version
    - Bug tor-browser-build#41807: Incorrectly generated Bugzilla query link in generate-bugzilla-triage-csv.py
    - Bug tor-browser-build#41813: Disable build artifacts in make generate_gradle_dependencies_list-geckoview
    - Bug tor-browser-build#41823: Add versions information to the toolchain list update
    - Bug tor-browser-build#41844: Add scripts to backup/deploy signing keys on signing machines
    - Bug tor-browser-build#41860: Change GCC sources mirror to https://gcc.gnu.org
    - Bug tor-browser-build#41867: Update tails-dev email address in release prep templates
    - Bug tor-browser-build#41896: Update Lyrebird to 0.9.0
    - Bug tor-browser-build#41898: Separate MB and TB toolchain archives in https://nightlies.tbb.torproject.org/nightly-builds/toolchains/
    - Bug rbm#40093: Make it easy to get the sha256sum of an input_files file
    - Bug rbm#40096: container extract is showing confusing error when target directory already exists
    - Bug rbm#40100: The GZIP variable makes set -u fail
    - Bug rbm#40103: Allow having multiple tmp_dir values
    - Bug rbm#40106: Improve error message in case of recursive definition
  - Windows + macOS + Linux
    - Bug tor-browser-build#41427: Drop the openURL property from the update
    - Bug tor-browser-build#41662: Add python-zstandard to desktop containers
    - Bug tor-browser-build#41711: Update our manual machinery for its new home
    - Bug tor-browser-build#41759: Remove references to legacy release in tor-browser-build
  - Windows + Linux + Android
    - Updated Go to 1.26.10
    - Bug tor-browser-build#41770: Update Go to 1.26.x
  - Windows + macOS
    - Bug tor-browser-build#41535: Update macOS and Windows containers to Debian trixie
  - Windows
    - Bug tor-browser#44853: Update target in mozconfig-windows-x86_64 and mozconfig-windows-i686
    - Bug tor-browser-build#41810: Define GetAddrInfoExCancel on mingw
    - Bug tor-browser-build#41877: make list_toolchain_updates is not checking windows-app-sdk
    - Bug tor-browser-build#41878: Update the Windows app SDK and add some additional DLLs
  - macOS
    - Bug tor-browser-build#41665: Update macos signing wrapper for new executable gpu-helper.app
    - Bug tor-browser-build#41773: Change the position of -mindepth when creating the dmg
    - Bug tor-browser-build#41793: Stop copying permissions from .mar in dmg2mar
  - Linux
    - Bug tor-browser#44555: Remove mozconfig-linux-i686
    - Bug tor-browser-build#41601: Upstream dropped Linux i686 support
    - Bug tor-browser-build#41627: Firefox build system needs a more recent version of OpenSSL on Linux
    - Bug tor-browser-build#41632: Ship Linux aarch64 builds in Alpha Release Channel
    - Bug tor-browser-build#41639: Remove linux-arm target
    - Bug tor-browser-build#41640: Clean the GCC config file
  - Android
    - Bug tor-browser#44360: Patch the vendored Gradle Nimbus plugin
    - Bug tor-browser#44370: Always produce target.maven.zip
    - Bug tor-browser#44508: Drop clearkey also on Android
    - Bug tor-browser#44848: Do not overwrite Android toolchains on default mozconfigs
    - Bug tor-browser#45086: Compress omni.ja with xz on Android
    - Bug tor-browser-build#32200: only include required bits of OpenSSL in Android builds
    - Bug tor-browser-build#41485: Retire get_gradle_dependencies_list and create a simple way to update gradle deps
    - Bug tor-browser-build#41573: Remove Android x86 support
    - Bug tor-browser-build#41621: Remove support using older android build tools when signing 14.5 releases in tools/signing/wrappers/sign-apk
    - Bug tor-browser-build#41628: android_ndk_version and revision can be grouped together
    - Bug tor-browser-build#41636: Update the scripts to manage Gradle dependencies
    - Bug tor-browser-build#41666: Normalize the path to tor-expert-bundle.aar
    - Bug tor-browser-build#41684: Use only the NDK as var/compiler on Android
    - Bug tor-browser-build#41699: Delete prefs specific to other architectures in omni.ja
    - Bug tor-browser-build#41702: Replace uglifyjs with terser
    - Bug tor-browser-build#41719: Enable network when var/generate_gradle_dependencies_list is set in geckoview
    - Bug tor-browser-build#41736: Add generate_gradle_dependencies_list-$project makefile targets
    - Bug tor-browser-build#41737: Remove comment from gen-gradle-deps-file.py saying var/gradle_dependencies_version should be updated
    - Bug tor-browser-build#41743: Make an error if gradle-dependencies-list is missing in the input files
    - Bug tor-browser-build#41744: Reduce duplication between projects/geckoview/build and projects/geckoview/build_apk
    - Bug tor-browser-build#41745: Add .sh file extension to included build_* scripts in projects/geckoview
    - Bug tor-browser-build#41751: Fix the NDK path
    - Bug tor-browser-build#41801: Hardlink artifacts in fix_gradle_deps.py
    - Bug tor-browser-build#41830: Update the browser project to change omni.ja.xz
    - Bug tor-browser-build#41843: Remove unused universal apk from geckoview
    - Bug tor-browser-build#41876: Add missing firefox_platform_version.txt file in android artifacts directories

## Comments

We encourage respectful, on-topic comments. Comments that violate our
	  [Code of Conduct](https://community.torproject.org/policies/code_of_conduct)
	  will be deleted. Off-topic comments may be deleted at the discretion of
	  the moderators. Please do not comment as a way to receive support or to
	  report bugs on a post unrelated to a release. If you are looking for
	  support, please see our [FAQ](https://support.torproject.org/),
	  [user support forum](https://forum.torproject.org/) or ways to
	  [get in touch with us](https://www.torproject.org/contact).