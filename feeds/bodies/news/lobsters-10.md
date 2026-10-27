Today I got a strange email that turned into an unsettling phishing experiences.

> // If you’re just here to read about how bad passkeys are, skip to [part 4](https://www.kcoleman.me/2026/10/22/hacked.html#4-the-passkey-was-actually-the-scariest-part)

## It Started With a YouTube Support Ticket

![](https://www.kcoleman.me/images/hacked/phishing-email.png)

I thought someone from Russia created a support ticket with YouTube to take over my gmail account and I needed to click on their link to reject the support ticket. Oops.

## The Google Login Page Looked *almost* Legit

![](https://www.kcoleman.me/images/hacked/phishing-site.png)

But I was already logged into Google in another browser tab. So why was Google asking me to log in again?

I even noticed `sites.google.com` login page, but proceeded anyway thinking that this was just a weird auth flow for a support website (its common for companies to require you to login separately to a support ticket website from your main account)

I copied over Google credentials from my password manager. Then it asked for my two-factor authentication code.

I copied and pasted the correct code. It failed.

I tried again.

Failed again.

## Then the Apple Passkey Prompt

> I really wish I took screenshots of their phishing page for science, but after I reported the phishing page to Google, either the attackers or Google took down the page.

After the two-factor authentication attempts failed, the site switched authentication methods.

It presented what looked like an Apple passkey interface, rendered directly inside the browser window.

*What the hell?*

I don’t use Apple Passkeys. This isn’t how my passkey authentication normally works.

So I hit cancel to step away from this Apple passkey interface.

## They Knew I Used Bitwarden and were ready

After I dismissed the passkey prompt, another modal appeared that looked like the Bitwarden login screen, asking me to add a passkey to the account.

I use a forked copy of Bitwarden that’s been rebranded as [Saigon Safe](https://chromewebstore.google.com/detail/saigon-safe/iplggehdmbbndlednajekcfmcokbnnlj?authuser=1&hl=en), not the Bitwarden branded extension!

> Plug: [Saigon Safe](https://www.kcoleman.me/2026/10/22/2026/06/14/saigon-safe.html) removes ads, adds advanced security measures, and dramatic improvements to the UX. Click the article link to see what Saigon Safe actually looks like.

So the login screen they presented didn’t actually match my password manager, but through the browser extension detection API, attackers new exactly which password managers they should fake. How kind of web browsers to give phishers exactly the right tools to use.

Now they were going for my throat: 650+ passwords ‘securely’ stored in my password manager.

## Then Google Emailed Me: A New Passkey Was Added

![](https://www.kcoleman.me/images/hacked/google-drive.png)

Oh, no. Attackers installed hooks for them to come back in later.

## The Device I Didn’t Recognize

![](https://www.kcoleman.me/images/hacked/devices.png)

Someone had gained access to my account, and the attackers were either smart enough to use a proxy location near me or were physically near me… Scary.

## What to do if this happens to you:

1. Log their device out
2. Remove the new passkey immediately
3. Recover deleted emails Google Email Recovery Tool
4. Review Google Drive
5. Review Gmail forwarding

## My Security Posture: Why This Could Have Been Much Worse

Because while I absolutely fell for part of this phishing attempt, I had also intentionally set things up to limit the damage if something like this ever happened.

### 1. I Don’t Keep 16 Years of Email Sitting in Gmail

I intentionally keep only about five years of email in Gmail.

Anything older gets backed up offline, encrypted, and stored on infrastructure I control. There’s almost no reason for that much historical information to remain continuously available online.

### 2. My Most Sensitive Accounts Use Separate *secret* Email Addresses

For things like banking applications, password managers, and other critical services, I typically use dedicated, nonpublic custom-domain email addresses.

That way, even if someone compromises my primary Gmail account, they don’t automatically get a convenient list of my most sensitive accounts or their login identifiers or ability to trigger password recovery to access them.

### 3. Thinking like a Hacker

One thing that still puzzles me about this attack is how sophisticated the phishing tools were compared to how little the attacker seemed to actually did once they got into my account.

From what I gathered, they:

1. Permanently deleted original phishing email
2. Reviewed 2 Google Sheet documents in my drive

Maybe there is something else they did that I don’t know about though.

They had clearly invested in a convincing phishing setup, but there didn’t seem to be an obvious plan for exploiting the account immediately. Perhaps they used a pre-purchased phishing kit, but were sophisticated enough to quickly do something meaningful with the access.

**Theory 1: They were collecting compromised accounts to sell later.**

Maybe the goal wasn’t to attack me directly. Maybe it was to collect as many compromised Google accounts as possible, register passkeys, and sell access to other criminals.

Those buyers could then use the accounts for targeted phishing, stealing sensitive documents, spreading malware, or even ransomware attacks.

**Theory 2: They planned to come back and exploit the account themselves.**

I doubt the attacker designed the system so they had to sit at the computer waiting for people to fall for that email. These campaigns are probably sent to many people, and the initial compromise may be largely automated.

But something interesting happened in my case. Potentially because I opened the email shortly after I received the email, potentially the attacker was around to do some manual clicking.

![](https://www.kcoleman.me/images/hacked/google-drive.png)

My Google Drive access history shows what they looked at: Financial and Crypto-related documents. Fortunately, while this is private information, its not something they can use to steal money from me.

This suggests there was at least some active exploration of my account.

But there was no evidence of them adding a forwarding address, permanent distructive deleting the drive folder or emails, sending out emails to my contacts list, etc.

### 4. The Passkey Was Actually the Scariest Part

With the recent Hacker News debates about whether [passkeys are a trap](https://news.ycombinator.com/item?id=50048312), I think my experience highlights another risk that deserves more attention.

**Passkeys can replace both your password and your second authentication step.**

They’re designed to be phishing-resistant, which is great. But what happens when an attacker manages to register **their own passkey on your account**?

Once that passkey becomes usable, they may be able to sign in without your password or a fresh 2FA challenge. I verified with a fresh Google account in a private window (but same device and IP address) that Google did not prompt 2fa (either confirm on another device or TOTP or SMS).

Fortunately, Google sent me an email and push notification about a new passkey being added.

![](https://www.kcoleman.me/images/hacked/push.png)

**Without Google’s new passkey email and push, I might have changed my password, assumed my account was secure, and completely missed the attacker’s new way back in.**

Passkey registerations remind me of the GDPR regulation for exporting your account data created unintended consequences of giving an attacker controls to quickly steal EVERYTHING before you have time to file a support ticket to kick them out.

**Passkey UX currently sucks… Attackers exploited the current flow of: “Thanks for logging in via a normal method, lets add a passkey to your account.”**

Passkeys give phishers a backdoor into your system, without needing the regular 2fa verification methods!

I wish there was a way to block passkey use on my account, until the technology matures a bit.

I reported to Google the phishing site. Either the attacker or Google has already taken down the site.