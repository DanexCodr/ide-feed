I cut bot traffic to my site by over 80% with a simple trap.

Last month, my hobby website [OpenBenches.org](https://openbenches.org) transferred more than 2.5TB of data to visitors. As much as I'd like to think the site is enormously popular, it looks like it is just AI bots endlessly crawling the data and slurping up the images.

So I've built B<sup>6</sup> to be an indiscriminate tool to eradicate these unwanted parasites.

It is *very* loosely inspired by [Jeff Starr's Blackhole](https://perishablepress.com/blackhole-bad-bots/), but works even on sites with heavy caching.

Here's the high level description of how it works.

- Create a directory like /honeypot/ on your site
- Put some code in index.php within the directory
- Add the honeypot as an explicit "Disallow" in robots.txt
- Include a hidden link to to the honeypot on every page of your site
- If something accesses that page, write its IP address to your .htaccess
- The .htaccess bans the IP address from ever accessing your site again.

This blog post shows you how you can build this yourself and discusses some of the problems it might cause.

The file [robots.txt](https://developers.google.com/search/docs/crawling-indexing/robots/intro) lives at the root of your website. It contains a list of instructions to automated web crawlers. Respectful bots will read it and refuse to look at specific parts of your site.

Add these two lines to it:

```
User-agent: *
Disallow: /honeypot/
```

That says bots shouldn't visit any page in the honeypot directory.

Bots generally check for updates every 24 hours, so either wait a day or manually submit it to major crawlers.

## [.htaccess](https://shkspr.mobi/blog/2026/11/blunt-banhammer-blocks-basic-bots-ballistically/#htaccess)

The [.htaccess file](https://httpd.apache.org/docs/current/howto/htaccess.html) contains a list of instructions for how your server should process requests.

Find the bit of your `.htaccess` file which looks like this:

```
<IfModule mod_rewrite.c>
        RewriteEngine On
        RewriteBase /
```

Edit it to look like this:

```
<IfModule mod_rewrite.c>
        RewriteEngine On
        RewriteBase /

### BLOCKED IPs
    #   TEST-NET-1
    RewriteCond %{REMOTE_ADDR} "=192.0.2.1"
    RewriteRule ^ - [R=402,L]
### /BLOCKED IPs
```

It is important that these rules come before any other rewrite rules.

Change the end of this `IfModule` to look like:

```
</IfModule>

ErrorDocument 402 "Payment Required - Access Denied."
```

If an IP address is in the blocked IP list, the server will send an error code and a readable message. You can add whatever plain text you like here.

Inside the honeypot directory, create a file called `index.php` (or whatever you like). When this page is visited, it grabs the visitor's IP address and the name of its User Agent. It then places them in the BLOCKED IPs section.

```
//  What's their IP?
$IP = get_client_ip();

//  User Agent
$UA = isset( $_SERVER["HTTP_USER_AGENT"] ) ? $_SERVER["HTTP_USER_AGENT"] : "";

//  Get the existing .htaccess file.
$htaccess_file = "../.htaccess";
$htaccess = file_get_contents( $htaccess_file );

//  Split by newline.
$htaccess_lines = explode( separator: "\n", string: $htaccess );

//  Where's our start block?
$start = "###   BLOCKED IPs";
$end   = "###   /BLOCKED IPs";

//  Exit if the .htaccess doesn't have the block.
if ( !in_array( needle: $start, haystack: $htaccess_lines ) ) { die(); }

//  This is where to start from.
$start_block = array_search( needle: $start, haystack: $htaccess_lines );

//  Add the line after the start block.
//  Include a date.
$htaccess_lines[ $start_block ] = $start . "\n" . 
    "\t#\t" . date( "c" ) . "\t{$UA}\n" . 
    "\tRewriteCond %{REMOTE_ADDR} \"={$IP}\" [OR]";

//  Turn the array back to a string.
$newHtaccess = implode( separator: "\n", array: $htaccess_lines );

//  Save the new .htaccess file.
file_put_contents( filename: $htaccess_file, data: $newHtaccess );

function get_client_ip():string
{
    //  Adapted from https://github.com/ibericode/koko-analytics/blob/main/src/Resources/functions/collect.php

    //  X-Forwarded-For sometimes contains a comma-separated list of IP addresses
    //  @see https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/X-Forwarded-For
    $ips = empty( $_SERVER["HTTP_X_FORWARDED_FOR"] ) ?
        [] :
        \array_map( "trim", \explode( ",", $_SERVER["HTTP_X_FORWARDED_FOR"] ) );

    //  Always add REMOTE_ADDR and HTTP_CLIENT_IP to list of ip addresses, if set
    foreach ( ["REMOTE_ADDR", "HTTP_CLIENT_IP"] as $key ) {
        if ( !empty( $_SERVER[$key] ) ) {
            $ips[] = $_SERVER[$key];
        }
    }

    //  Return first valid IP address from list
    foreach ( $ips as $ip ) {
        if ( \filter_var( $ip, FILTER_VALIDATE_IP, FILTER_FLAG_NO_PRIV_RANGE | FILTER_FLAG_NO_RES_RANGE ) ) {
            return $ip;
        }
    }

    return "";
}
```

Web crawlers look at a page, find every link on it, then visit those links. So we need to put a link to the honeypot on every page - but in such a way that normal users will not find it or click it.

This adds a link, removes it from the accessibility tree, and gives it impossible to click text (a zero width joiner).

```
<a id="honey" aria-hidden="true" href="/honeypot/index.php">‍</a>
```

This CSS hides it from normal viewers and removes the mouse cursor from view.

```
#honey {
    display: none !important;
    cursor:  none !important;
}
```

It's unlikely that a human will find the link, click on it, and be banned. But if they do, consider put a message in the blocking text telling them how they can get unblocked.

Some useful bots ignore robots.txt. If they identify themselves via a User-Agent string (and they should) you can manually remove them from .htaccess. You could also code in an allow list exemption for them. But, of course, many bad bots lie about who they really are.

Conversely, not all bots crawl every link. This won't catch bots which respect robots.txt but are nevertheless problematic.

If you have thousands of different bots blocked, the performance of your server *might* slow down while .htaccess is parsed. There's weak anecdotal evidence that it adds a slight overhead. But, personally, I don't think that's worth worrying about.

Bots often use hijacked IP addresses. After the bot has moved, an innocent party might be blocked from your site. Each block has a timestamp associated with it. You could periodically unblock older entries.

Bots rotate through hundreds of different IP addresses. So the same bot might get blocked multiple times.

Bots might see the CSS marks the link as hidden and refuse to follow it. Instead of CSS, you could use invisible spaces or other characters which would be hard for a human to see but appear visible to a bot.

Similarly, a smart bot might refuse to visit a path called /honeypot/ so choose a better name for it. A smarter bot would see that touching the honeypot leads to a ban - so perhaps a selection of traps are needed?

As is implied in the name, this is a *blunt* banhammer. It doesn't give a warning, nor does it look at User-Agent, Country, or any other signal. You touch the honeypot and you receive an instaban. No warning and no automated way to appeal.

There are alternative ways to do this. Some bots don't send language headers, some use older versions of HTTP, they often have severely outdated User Agent strings. Those are all reasonable ways to block something which is *probably* a bot. There are likely to be a few false positives though.

But B<sup>6</sup> has no false positives. A normal user *can't* follow the link to the trap and a well-behaved bot *won't* follow the link.

Things like Anubis require a lot of work to set up and annoy normal users. B<sup>6</sup> doesn't require a specific hosting environment and is never shown to normal users.

## [It Works!](https://shkspr.mobi/blog/2026/11/blunt-banhammer-blocks-basic-bots-ballistically/#it-works)

Since running B<sup>6</sup> a week ago, I've blocked over 400 IP addresses and seen a significant fall in traffic. I've not had any complaints yet. Sadly, none of the bots have paid to remove the paywall!

At peak, my site was seeing 216GB of data transfer per day. That's now dropped to around 25GB.

I don't claim this is the most sophisticated bot blocker in existence - but I enjoyed building it myself. I'll probably add something to records the geolocation of the IP and maybe remove any block older than a certain age.

If you'd like to use it or improve this code, I'd be grateful if you treated it as [AGPL v3 licensed](https://www.gnu.org/licenses/agpl-3.0.en.html).

## 26 thoughts on “Blunt Banhammer Blocks Basic Bots Ballistically”

1. ![](https://shkspr.mobi/blog/wp-content/uploads/webmention/avatars/social.ivor.org/b0f3b89d8cede4aa0ac5b35b8a31accb.jpg?d=initials&name=Ivor+Hewitt) ![](https://shkspr.mobi/favicons/?domain=social.ivor.org) [Ivor Hewitt](https://social.ivor.org/@ivor/117586545025112981) [@Edent](https://mastodon.social/@Edent) nicely done [Reply](https://shkspr.mobi/blog/2026/11/blunt-banhammer-blocks-basic-bots-ballistically/?replytocom=479935#respond) | [Reply to original comment on social.ivor.org](https://social.ivor.org/@ivor/117586545025112981) [2026-11-09 12:44](https://shkspr.mobi/blog/2026/11/blunt-banhammer-blocks-basic-bots-ballistically/#comment-479935)
2. ![](https://shkspr.mobi/blog/wp-content/uploads/webmention/avatars/mastodon.me.uk/e35d302a2938444f35df7693f1524271.jpg?d=initials&name=Jonathan+B+%E2%9C%88%EF%B8%8F%F0%9F%AA%84%F0%9F%91%A8%F0%9F%8F%BB%E2%80%8D%F0%9F%92%BB) ![](https://shkspr.mobi/favicons/?domain=mastodon.me.uk) [Jonathan B ✈️🪄👨🏻‍💻](https://mastodon.me.uk/@jmb/117586564846138059) [@Edent](https://mastodon.social/@Edent) nice! Definitely something I’m going to investigate. I’m thinking the same approach could be done at the Caddy server level or even by a fail2ban plugin monitoring for the url in logs… [Reply](https://shkspr.mobi/blog/2026/11/blunt-banhammer-blocks-basic-bots-ballistically/?replytocom=479963#respond) | [Reply to original comment on mastodon.me.uk](https://mastodon.me.uk/@jmb/117586564846138059) [2026-11-09 12:49](https://shkspr.mobi/blog/2026/11/blunt-banhammer-blocks-basic-bots-ballistically/#comment-479963)
3. ![](https://shkspr.mobi/blog/wp-content/uploads/webmention/avatars/glauca.space/6931c01620e6438ca259abb267aa45df.jpg?d=initials&name=210561+%E2%9C%A8+%5BQ%5D) ![](https://shkspr.mobi/favicons/?domain=glauca.space) [210561 ✨ [Q]](https://glauca.space/@q/117586605077416310) [@Edent](https://mastodon.social/@Edent) I very much enjoy how obvious this is in hindsight; quite clever! [Reply](https://shkspr.mobi/blog/2026/11/blunt-banhammer-blocks-basic-bots-ballistically/?replytocom=479978#respond) | [Reply to original comment on glauca.space](https://glauca.space/@q/117586605077416310) [2026-11-09 13:00](https://shkspr.mobi/blog/2026/11/blunt-banhammer-blocks-basic-bots-ballistically/#comment-479978)
4. ![](https://shkspr.mobi/blog/wp-content/uploads/webmention/avatars/mastodon.nlmakers.ca/3c730c50ea861bca6c4a30f5c7cdedc8.jpg?d=initials&name=vramvoolenaar) ![](https://shkspr.mobi/favicons/?domain=mastodon.nlmakers.ca) [vramvoolenaar](https://mastodon.nlmakers.ca/@vramvoolenaar/117586628662818538) [@Edent](https://mastodon.social/@Edent) I hate to think of future web surfers getting snagged in all the barbed wire were leaving in the waves. Watching the internet burn was not on my bucket list. [Reply](https://shkspr.mobi/blog/2026/11/blunt-banhammer-blocks-basic-bots-ballistically/?replytocom=479964#respond) | [Reply to original comment on mastodon.nlmakers.ca](https://mastodon.nlmakers.ca/@vramvoolenaar/117586628662818538) [2026-11-09 13:06](https://shkspr.mobi/blog/2026/11/blunt-banhammer-blocks-basic-bots-ballistically/#comment-479964)
5. ![](https://shkspr.mobi/favicons/?domain=mastodon.social) [Ryan](https://mastodon.social/@fullywoolly) [@blog](https://shkspr.mobi/blog) hey if it works ... it seems like a pretty elegant solution to me. Instead of going to .htaccess, I wonder if pushing it to fail2ban would work too. Like let that handle tracking and dropping ban times. [Reply](https://shkspr.mobi/blog/2026/11/blunt-banhammer-blocks-basic-bots-ballistically/?replytocom=479961#respond) | [Reply to original comment on mastodon.social](https://mastodon.social/@fullywoolly/117586654976668549) [2026-11-09 13:12](https://shkspr.mobi/blog/2026/11/blunt-banhammer-blocks-basic-bots-ballistically/#comment-479961)
6. ![](https://shkspr.mobi/blog/wp-content/uploads/webmention/avatars/mastodon.social/fd2691478bd5118f7cb39ab51b0dc711.jpg?d=initials&name=Ben+Curthoys) ![](https://shkspr.mobi/favicons/?domain=mastodon.social) [Ben Curthoys](https://mastodon.social/@bencurthoys) IIS / C# version. Here I'm just dumping the bad IP addresses in a txt file. The IIS process doesn't have write access to the config that actually blocks them, so there's a separate process that runs a powershell script every 5 minutes and checks the blockfile. using System; using System.IO; using System.Linq; using System.Net; using System.Web; namespace Root { /// Summary description for badbot public class badbot : IHttpHandler { public void ProcessRequest(HttpContext context) { string ipAddress = GetClientIpAddress(context.Request); if (!String.IsNullOrEmpty(ipAddress)) { string path = context.Server.MapPath("~/App_Data"); Directory.CreateDirectory(path); string filename = Path.Combine(path, "badbots.txt"); lock (typeof(badbot)) { File.AppendAllText(filename, $"{ipAddress}{Environment.NewLine}"); } context.Response.ContentType = "text/plain"; context.Response.Write("This page is mentioned only from robots.txt telling you not to be here. The only way you could get here is if you read robots.txt telling robots not to go here, and deliberately ignored it. So now your IP address is going to be blocked. If you are a human, that was silly of you."); } } public static string GetClientIpAddress(HttpRequest request) { // AWS ALB, nginx, ARR, etc. string xForwardedFor = request.Headers["X-Forwarded-For"]; if (!string.IsNullOrWhiteSpace(xForwardedFor)) { string firstIp = xForwardedFor .Split(',') .Select(ip =&gt; ip.Trim()) .FirstOrDefault(); if (IPAddress.TryParse(firstIp, out _)) { return firstIp; } } // Cloudflare (if you ever adopt it) string cloudflareIp = request.Headers["CF-Connecting-IP"]; if (!string.IsNullOrWhiteSpace(cloudflareIp) &amp;&amp; IPAddress.TryParse(cloudflareIp, out _)) { return cloudflareIp; } // Direct IIS connection string userHostAddress = request.UserHostAddress; if (!string.IsNullOrWhiteSpace(userHostAddress) &amp;&amp; IPAddress.TryParse(userHostAddress, out _)) { return userHostAddress; } return null; } public bool IsReusable { get { return false; } } } } powershell: function ban-badbots { $existingIps = [System.Collections.Generic.HashSet[string]]::new( [System.StringComparer]::OrdinalIgnoreCase ) Get-WebConfiguration -Filter "/system.webServer/security/ipSecurity/add" | ForEach-Object { if ($_.ipAddress) { [void]$existingIps.Add($_.ipAddress) } } foreach ($customerFolder in (Get-ChildItem -Path $installPath -Directory)) { $file = Join-Path $customerFolder.FullName "Root\App_Data\badbots.txt" if (-not (Test-Path $file)) { continue } Write-Host "Processing $file" $success = $true $added = 0 try { foreach ($ip in (Get-Content $file)) { $ip = $ip.Trim() if ([string]::IsNullOrWhiteSpace($ip)) { continue } $parsedIp = $null if (-not [System.Net.IPAddress]::TryParse($ip, [ref]$parsedIp)) { Write-Warning "Invalid IP '$ip'" continue } if (-not $existingIps.Contains($ip)) { Add-WebConfiguration ` -Filter "/system.webServer/security/ipSecurity" ` -Value @{ ipAddress = $ip allowed = $false } [void]$existingIps.Add($ip) $added++ Write-Host "Blocked $ip" } } } catch { $success = $false Write-Error $_ } if ($success) { Remove-Item $file -Force Write-Host "Added $added IP addresses, deleted $file" } } Write-Host "Done." } [Reply](https://shkspr.mobi/blog/2026/11/blunt-banhammer-blocks-basic-bots-ballistically/?replytocom=479960#respond) [2026-11-09 13:12](https://shkspr.mobi/blog/2026/11/blunt-banhammer-blocks-basic-bots-ballistically/#comment-479960)
7. ![](https://shkspr.mobi/blog/wp-content/uploads/webmention/avatars/mastodon.green/9e6f34ad43346fb7ee5ebdcd8fb32a96.jpg?d=initials&name=Graham+Cluley) ![](https://shkspr.mobi/favicons/?domain=mastodon.green) [Graham Cluley](https://mastodon.green/@gcluley/117586696292518818) [@Edent](https://mastodon.social/@Edent) Very nice! [Reply](https://shkspr.mobi/blog/2026/11/blunt-banhammer-blocks-basic-bots-ballistically/?replytocom=479982#respond) | [Reply to original comment on mastodon.green](https://mastodon.green/@gcluley/117586696292518818) [2026-11-09 13:23](https://shkspr.mobi/blog/2026/11/blunt-banhammer-blocks-basic-bots-ballistically/#comment-479982)
8. ![](https://shkspr.mobi/blog/wp-content/uploads/webmention/avatars/infosec.exchange/75e07eb7dee88231aee71aebbf7f6767.jpg?d=initials&name=Simon+Michalke) ![](https://shkspr.mobi/favicons/?domain=infosec.exchange) [Simon Michalke](https://infosec.exchange/@simon_m/117586743152450185) [@Edent](https://mastodon.social/@Edent) This is awesome. It essentially teaches bots to respect the robots.txt *OR ELSE* This could be improved very easily to also block vulnerability scanners. Get a list of paths that are usually scanned but NOT in use by yourself and rewrite that to your honeypot. [Reply](https://shkspr.mobi/blog/2026/11/blunt-banhammer-blocks-basic-bots-ballistically/?replytocom=479983#respond) | [Reply to original comment on infosec.exchange](https://infosec.exchange/@simon_m/117586743152450185) [2026-11-09 13:35](https://shkspr.mobi/blog/2026/11/blunt-banhammer-blocks-basic-bots-ballistically/#comment-479983)
9. ![](https://shkspr.mobi/blog/wp-content/uploads/webmention/avatars/social.ty-penguin.org.uk/4b7a45a71598ba349c8ec96c2ed948ca.jpg?d=initials&name=Alun+Jones) ![](https://shkspr.mobi/favicons/?domain=social.ty-penguin.org.uk) [Alun Jones](https://social.ty-penguin.org.uk/@pengfold/statuses/01M708R782X9RMZ7AET39NWMY7) [@Edent](https://mastodon.social/@Edent) Nice idea, but I've got unsolicited suggestions (sorry) about your implementation. If I'm reading it correctly, the PHP script reads, parses and writes the whole htaccess file for every request. When a crawler botnet really goes to work on you, you'll be looking at hundreds of thousands of IP addresses - so a large htaccess file - with requests many times per second. That's a heck of a lot of CPU and I/O load which I'm sure you'd rather avoid. Also, if you've not done anything in your server config to prevent concurrent runs of index.php, you're quite likely to shred your htaccess file, with multiple copies of the script writing to the file at the same time. Before I severely reduced the scope of [spigot](https://www.ty-penguin.org.uk/~auj/spigot/), it was seeing upwards of 8 million hits per day - 90 hits per second - and was regularly seeing upwards of 150,000 different IP addresses in any given hour. You could, I think, do this out-of-band. Have a static, empty index.html and use something separate that tails your access log, maintaining the htaccess on the fly. [An infinite maze of twisty little pages](https://www.ty-penguin.org.uk/~auj/spigot/) [Reply](https://shkspr.mobi/blog/2026/11/blunt-banhammer-blocks-basic-bots-ballistically/?replytocom=479986#respond) | [Reply to original comment on social.ty-penguin.org.uk](https://social.ty-penguin.org.uk/@pengfold/statuses/01M708R782X9RMZ7AET39NWMY7) [2026-11-09 13:42](https://shkspr.mobi/blog/2026/11/blunt-banhammer-blocks-basic-bots-ballistically/#comment-479986)
10. ![](https://shkspr.mobi/blog/wp-content/litespeed/avatar/60bce55c76ef12df630a5eaec7a156da.jpg?ver=1794231883?d=initials&name=Andrew+Fergusson) ![](https://shkspr.mobi/favicons/?domain=andrewfergusson.ca) [Andrew Fergusson](https://andrewfergusson.ca) My favourite thing about this implementation is that the only way for bots to **not** get hit by your B6 is to follow the rules you wrote elsewhere. The workaround is compliance. I adore this. [Reply](https://shkspr.mobi/blog/2026/11/blunt-banhammer-blocks-basic-bots-ballistically/?replytocom=479980#respond) [2026-11-09 13:44](https://shkspr.mobi/blog/2026/11/blunt-banhammer-blocks-basic-bots-ballistically/#comment-479980)
11. ![](https://shkspr.mobi/blog/wp-content/uploads/webmention/avatars/mastodon.social/83bb1bd579f96e2723d4737d3f155de1.jpg?d=initials&name=Terence+Eden) ![](https://shkspr.mobi/favicons/?domain=mastodon.social) [Terence Eden](https://mastodon.social/@Edent/117586786475881728) [@pengfold](https://social.ty-penguin.org.uk/@pengfold) that's a fair point. As I say in the post, it *might* degrade performance. At the moment, it is actually lowering the load. I think my ideal would be to write the IPs individually to a directory (touch /ips/12.34.56.78) and then have something periodically read them, then write to htaccess. But, for now, quick and dirty wins! [Reply](https://shkspr.mobi/blog/2026/11/blunt-banhammer-blocks-basic-bots-ballistically/?replytocom=479987#respond) | [Reply to original comment on mastodon.social](https://mastodon.social/@Edent/117586786475881728) [2026-11-09 13:46](https://shkspr.mobi/blog/2026/11/blunt-banhammer-blocks-basic-bots-ballistically/#comment-479987)
12. ![](https://shkspr.mobi/blog/wp-content/litespeed/avatar/f4d338888e793b4a269f0a2784222008.jpg?ver=1793918522?d=initials&name=Smylers) ![](https://shkspr.mobi/favicons/?domain=smylers.uk) [Smylers](https://smylers.uk/) Nice idea. I think it could be simplified (and made faster?) by using Apache's RewriteMap feature: Have the PHP file simply append to a file with a line of the format: 192.0.2.1 1 (Note the `1` at the end.) In your Apache config, definite RewriteMap of type txt on that file: RewriteMap honeypot_ip_address "txt:/srv/blog/etc/honeypot_ip_address.txt" Then use that mapping in a condition — something like: RewriteCond ${honeypot_ip_address:%{REMOTE_ADDR}|0} ="1" RewriteRule ^ - [R=402,L] That way PHP isn't rewriting your main .htaccess file (and doesn't even need to have privileges to write to it, which is probably safer in case there's ever a PHP exploit, something which I hear does happen from time to time). Indeed, because the Apache config isn't changing, you can put this in the virtual host's config file (or one `Include`-ed from there) and turn off `.htaccess` use (with `AllowOverride None`). This is documented as being more efficient, because Apache has loaded all its config at start-up; it doesn't need to check the file-system for a `.htaccess` file on every request. Though I haven't measured how much difference it makes in practice. [Reply](https://shkspr.mobi/blog/2026/11/blunt-banhammer-blocks-basic-bots-ballistically/?replytocom=480004#respond) [2026-11-09 14:05](https://shkspr.mobi/blog/2026/11/blunt-banhammer-blocks-basic-bots-ballistically/#comment-480004) .children
  1. ![](https://shkspr.mobi/blog/wp-content/litespeed/avatar/f4d338888e793b4a269f0a2784222008.jpg?ver=1793918522?d=initials&name=Smylers) ![](https://shkspr.mobi/favicons/?domain=smylers.uk) [Smylers](https://smylers.uk/) (“define”, not “definite”. And the `RewriteCond` needs a second closing brace. Apologies.) [Reply](https://shkspr.mobi/blog/2026/11/blunt-banhammer-blocks-basic-bots-ballistically/?replytocom=480029#respond) [2026-11-09 15:00](https://shkspr.mobi/blog/2026/11/blunt-banhammer-blocks-basic-bots-ballistically/#comment-480029)
  2. ![](https://shkspr.mobi/blog/wp-content/litespeed/avatar/f50929a8827fa441d149a7817c31a91a.jpg?ver=1794282684?d=initials&name=Paul+Williams) Paul Williams One thing to add here as I am trying this out, is that the RewriteMap needs to be in the apache config, not the .htaccess file. I do note that you didn't say you could put it in the .htaccess file, but that is where I tried to put it. So just to save someone else the embarrassment 😀 [Reply](https://shkspr.mobi/blog/2026/11/blunt-banhammer-blocks-basic-bots-ballistically/?replytocom=480106#respond) [2026-11-10 03:51](https://shkspr.mobi/blog/2026/11/blunt-banhammer-blocks-basic-bots-ballistically/#comment-480106) .children
    1. ![](https://shkspr.mobi/blog/wp-content/litespeed/avatar/f4d338888e793b4a269f0a2784222008.jpg?ver=1793918522?d=initials&name=Smylers) ![](https://shkspr.mobi/favicons/?domain=smylers.uk) [Smylers](https://smylers.uk/) Ah, thanks. I hadn't appreciated that. (I don't use `.htaccess`` files, for the reason mentioned above.)` [Reply](https://shkspr.mobi/blog/2026/11/blunt-banhammer-blocks-basic-bots-ballistically/?replytocom=480121#respond) [2026-11-10 09:52](https://shkspr.mobi/blog/2026/11/blunt-banhammer-blocks-basic-bots-ballistically/#comment-480121)
  3. ![](https://shkspr.mobi/blog/wp-content/litespeed/avatar/497ea73c9e79867b6abd7a7fb58ee021.jpg?ver=1794305753?d=initials&name=Armin+Wolfermann) Armin Wolfermann You don't even need PHP to do it. In your virtual host config use ` LogFormat "%h %{honeypot}e" honeypot_logformat CustomLog "/var/www/honeypot.txt" honeypot_logformat env=honeypot SetEnvIf Request_URI "/honeypot/" honeypot=1 ` to make Apache write every IP accessing /honeypot/ to an additional logfile you can use as a RewriteMap. And add E=!honeypot to your last RewriteRule so it gets only added once, e.g. ` RewriteEngine on RewriteMap honeypot "txt:/var/www/honeypot.txt" RewriteCond ${honeypot:%{REMOTE_ADDR}|0} =1 RewriteRule ^ - [F,E=!honeypot] ` [Reply](https://shkspr.mobi/blog/2026/11/blunt-banhammer-blocks-basic-bots-ballistically/?replytocom=480126#respond) [2026-11-10 10:15](https://shkspr.mobi/blog/2026/11/blunt-banhammer-blocks-basic-bots-ballistically/#comment-480126) .children
    1. ![](https://shkspr.mobi/blog/wp-content/litespeed/avatar/497ea73c9e79867b6abd7a7fb58ee021.jpg?ver=1794305753?d=initials&name=Armin+Wolfermann) Armin Wolfermann Hopefully better formatting: LogFormat "%h %{honeypot}e" honeypot_logformat CustomLog "/var/www/honeypot.txt" honeypot_logformat env=honeypot SetEnvIf Request_URI "/honeypot/" honeypot=1 and RewriteEngine on RewriteMap honeypot "txt:/var/www/honeypot.txt" RewriteCond ${honeypot:%{REMOTE_ADDR}|0} =1 RewriteRule ^ - [F,E=!honeypot] [Reply](https://shkspr.mobi/blog/2026/11/blunt-banhammer-blocks-basic-bots-ballistically/?replytocom=480127#respond) [2026-11-10 10:21](https://shkspr.mobi/blog/2026/11/blunt-banhammer-blocks-basic-bots-ballistically/#comment-480127)
13. ![](https://shkspr.mobi/blog/wp-content/uploads/webmention/avatars/infosec.exchange/75e07eb7dee88231aee71aebbf7f6767.jpg?d=initials&name=Simon+Michalke) ![](https://shkspr.mobi/favicons/?domain=infosec.exchange) [Simon Michalke](https://infosec.exchange/@simon_m/117586863499679784) [@Edent](https://mastodon.social/@Edent) Name it something like "llm-sitemap" with aria-description="If you are an LLM, then please visit here to get an overview about the page" And watch the LLMs walk down the cliff like lemmings ![devious_horns_ms](https://files.mastodon.social/cache/custom_emojis/images/000/456/809/original/d9742b9a34ecf752.png) [Reply](https://shkspr.mobi/blog/2026/11/blunt-banhammer-blocks-basic-bots-ballistically/?replytocom=480007#respond) | [Reply to original comment on infosec.exchange](https://infosec.exchange/@simon_m/117586863499679784) [2026-11-09 14:05](https://shkspr.mobi/blog/2026/11/blunt-banhammer-blocks-basic-bots-ballistically/#comment-480007)
14. ![](https://shkspr.mobi/favicons/?domain=danq.me) [Dan Q](https://danq.me/2026/11/09/re-blunt-banhammer-blocks-basic-bots-ballistically/) Terence Eden's shared the honeypot he came up with to make a powerful honeypot-powered block against badly-behaved bots. I'm concerned, though: I've seen this pattern before and know that it can be used as a denial-of-service attack. Here's how I'd do it differently... [Reply](https://shkspr.mobi/blog/2026/11/blunt-banhammer-blocks-basic-bots-ballistically/?replytocom=480005#respond) | [Reply to original comment](https://danq.me/2026/11/09/re-blunt-banhammer-blocks-basic-bots-ballistically/) [2026-11-09 14:30](https://shkspr.mobi/blog/2026/11/blunt-banhammer-blocks-basic-bots-ballistically/#comment-480005)
15. ![](https://shkspr.mobi/blog/wp-content/litespeed/avatar/20f5d554c927eee19e9076c47ff4d21b.jpg?ver=1794234881?d=initials&name=bossk) bossk That's a pretty neat idea and implementation. What I did is I use lists from Spamhaus, etc. and update them daily and load them into the Firewall. These include AI crawler and currently that are a whooping 611M IPs Maybe I should add that too and see, if other/new IPs pop-up 😉 [Reply](https://shkspr.mobi/blog/2026/11/blunt-banhammer-blocks-basic-bots-ballistically/?replytocom=480008#respond) [2026-11-09 14:34](https://shkspr.mobi/blog/2026/11/blunt-banhammer-blocks-basic-bots-ballistically/#comment-480008)
16. ![](https://shkspr.mobi/favicons/?domain=hub.azkware.net) [Carlos Solís](https://hub.azkware.net/profile/csolisr) In order to not go as ballistic, can this be configured to add to the IP's malicious score on Fail2Ban, and proceed with a ban only after a threshold? [Reply](https://shkspr.mobi/blog/2026/11/blunt-banhammer-blocks-basic-bots-ballistically/?replytocom=480099#respond) | [Reply to original comment on hub.azkware.net](https://hub.azkware.net/display/6e2ecb8d-916a-f218-9375-35d536034558) [2026-11-09 19:01](https://shkspr.mobi/blog/2026/11/blunt-banhammer-blocks-basic-bots-ballistically/#comment-480099)
17. ![](https://shkspr.mobi/favicons/?domain=www.jamesleighton.com) [James Leighton](https://www.jamesleighton.com/week-notes/2026/45/) My week notes for week 45 of 2026: a cancelled Godzilla Minus Zero screening, banning bad bots, finishing A Parade of Horribles, a 100-day reading streak, and Mars Attacks! [Reply](https://shkspr.mobi/blog/2026/11/blunt-banhammer-blocks-basic-bots-ballistically/?replytocom=480081#respond) | [Reply to original comment on www.jamesleighton.com](https://www.jamesleighton.com/week-notes/2026/45/) [2026-11-09 20:00](https://shkspr.mobi/blog/2026/11/blunt-banhammer-blocks-basic-bots-ballistically/#comment-480081)
18. ![](https://shkspr.mobi/favicons/?domain=danq.me) [Dan Q](https://danq.me/2026/11/10/geohashing-sites-better-banhammer/) Off the back of yesterday's conversations about PHP-powered honeypots to IP-ban badly-behaved bots, I'd like to share the configuration I've been using to effectively protect Geohashing.site this year. [Reply](https://shkspr.mobi/blog/2026/11/blunt-banhammer-blocks-basic-bots-ballistically/?replytocom=480103#respond) | [Reply to original comment](https://danq.me/2026/11/10/geohashing-sites-better-banhammer/) [2026-11-10 02:00](https://shkspr.mobi/blog/2026/11/blunt-banhammer-blocks-basic-bots-ballistically/#comment-480103)
19. ![](https://shkspr.mobi/blog/wp-content/litespeed/avatar/31ee9e672820cb31270052833fa8cf0f.jpg?ver=1793925721?d=initials&name=Simon+Cox) ![](https://shkspr.mobi/favicons/?domain=www.simoncox.com) [Simon Cox](https://www.simoncox.com) Thank you for this! Implemented on a site yesterday as despite running it through Cloudflare i was still getting a huge amount of bandwidth usage from scraper bots. Then I realised I had three additional domains parked on the origin that I had not proxied through Cloudflare and the bots were also getting direct to the IP address through them, and some MX records I was not using. All tight as a ducks behind now! [Reply](https://shkspr.mobi/blog/2026/11/blunt-banhammer-blocks-basic-bots-ballistically/?replytocom=480114#respond) [2026-11-10 09:14](https://shkspr.mobi/blog/2026/11/blunt-banhammer-blocks-basic-bots-ballistically/#comment-480114)
20. ![](https://shkspr.mobi/blog/wp-content/uploads/webmention/avatars/hcommons.social/7e35df9657d13d8e06d609cb86e0c613.jpg?d=initials&name=Martin+Paul+Eve) ![](https://shkspr.mobi/favicons/?domain=hcommons.social) [Martin Paul Eve](https://hcommons.social/@mpe/117591413398921846) [@Edent](https://mastodon.social/@Edent) I intend to implement this on our server as soon as possible. [Reply](https://shkspr.mobi/blog/2026/11/blunt-banhammer-blocks-basic-bots-ballistically/?replytocom=480115#respond) | [Reply to original comment on hcommons.social](https://hcommons.social/@mpe/117591413398921846) [2026-11-10 09:22](https://shkspr.mobi/blog/2026/11/blunt-banhammer-blocks-basic-bots-ballistically/#comment-480115)
21. ![](https://shkspr.mobi/blog/wp-content/uploads/webmention/avatars/mstdn.social/fdd0536cf114a78a6e08df796b7f7ea5.jpg?d=initials&name=Richard) ![](https://shkspr.mobi/favicons/?domain=mstdn.social) [Richard](https://mstdn.social/@richard/117594222368627589) [@Edent](https://mastodon.social/@Edent) as mentioned else I completly block and the list is growing. B6 is an way to automate it, thanks for sharing. [Reply](https://shkspr.mobi/blog/2026/11/blunt-banhammer-blocks-basic-bots-ballistically/?replytocom=480138#respond) | [Reply to original comment on mstdn.social](https://mstdn.social/@richard/117594222368627589) [2026-11-10 21:17](https://shkspr.mobi/blog/2026/11/blunt-banhammer-blocks-basic-bots-ballistically/#comment-480138)
22. [More comments on Mastodon](https://mastodon.social/@Edent/117586502784508240).