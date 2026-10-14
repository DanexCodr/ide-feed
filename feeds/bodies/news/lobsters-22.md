Back in August I mentioned the new [curl performance tests](https://daniel.haxx.se/blog/2026/08/14/curl-performance-2/) we have running. I figured it could be apt to return to this topic just to mention some of the initial outcomes.

When the team gets a new set of charts, graphs and plots that visualize something, like performance, they offer an excellent opportunity for us to try to make them look better. This new setup is no exception.

The performance tests have only been running for just a little over two months but they have already made us improve curl performance in several areas. Of course, for most transfers these changes won’t make many visible differences to users. This is more in the vein that every little bit counts and that nothing should run slower than it has to.

This is a list of some improvements that are included in the curl 8.23.0 release, to be shipped tomorrow on October 14.

## faster base64 encoding and decoding

With a few different changes, the internal base64 encoding function is more than twice as fast, while base64 decoding is 40% faster.

## faster URL encoding and decoding

Meaning percent encoding the octets that are not safe to use in URLs. The decoding function now runs more than twice as fast compare to before, while the encoding function is around four times as fast.

## faster date parsing

Converting a date provided in plain ASCII text, as is used in for example cookie headers, to the epoch – number of seconds since Jan 1st 1970, is now more than twice as fast as before. Mostly thanks to completely replaced functions for week day, month name and time zone name lookups.

## faster URL parsing

Parsing a full URL to split it up into separate components as well as confirming its validity is a core component of curl, and libcurl exposes this functionality in its API.

In a test with several hundred different URLs, the new version executes 20-30% faster than before – with an improved ability to return precisely what the problem was when the URL is considered invalid.

## faster printf() calls

For portability and now historical reasons, libcurl has its own printf() implementation. This ensures that it always works identically on all platforms but it also makes it our job to make sure it executes as fast as possible.

Most printf() calls now run slightly faster (5-15%) because it handles “chunks” instead of single byte-by-byte at a time.

## faster number parsing

We have a generic internal function in curl that converts a number provided in ascii to its binary version (for decimal, hexadecimal and octal). It handles 64 bit values, has overflow detection and supports a maximum. This parser now runs almost twice as fast as before thanks to a simple trick to avoid the boundary check for most loops.

## smaller structs

The *easy handle* was 4256 bytes large two months ago, it is now 3064 bytes. About 28% trimmed off. One of these structs is allocated for every concurrent transfer done with libcurl.

There is also one *multi handle* allocated for each set of transfer. This struct shrunk from 900 bytes to 656: 27%.

The *connectdata struct* that is allocated once per connection libcurl handles, went down from 824 to 656 bytes: slightly over 20%.

## fewer and smaller allocations

For the test case where we count all allocations necessary for the curl tool to download a single 512MB file over clear text HTTP://, it went down from 100 to 96 used allocations. Not too exciting perhaps but it is now really hard to squeeze this further!

Mostly thanks to the decreased struct sizes mentioned above, this use case of a single HTTP download now only use 126,875 bytes allocated at peak. Down from 130,622 bytes two months ago. Also quite difficult to trim further.

It should be noted that the download buffer is 102,400 bytes of this amount. If we exclude that buffer from the count, curl is using 15% less memory.

## Easy to check

If you think you can speed up any of these functions, it is now very easy to check: the tests are there in the git repository, ready to be invoked by anyone!

1. ![](https://secure.gravatar.com/avatar/3f96dcc15163444bfde7626f54c56ff1037b6b45a262c52c6e1dc6d39dc70285?s=68&d=monsterid&r=g) **Jeremy Robst** says: .comment-author [October 13, 2026 at 14:07](https://daniel.haxx.se/blog/2026/10/13/a-slightly-faster-slimmer-curl/#comment-27558) .comment-metadata .comment-meta Sorry, very pedantic but I don’t understand some of the percentages for the smaller structs 4256 bytes to 3064; that’s 1192 bytes saved or 28% of 4256. 900 bytes to 656 is 27% saved 824 to 656 bytes is just over 20% saved. .comment-content [Reply](https://daniel.haxx.se/blog/2026/10/13/a-slightly-faster-slimmer-curl/?replytocom=27558#respond) .comment-body .children
  1. ![](https://secure.gravatar.com/avatar/69fdca87edd17cee21ca2e79fc2ff671d644603c3dc27167430f3cd3dbab7ba8?s=68&d=monsterid&r=g) **[Daniel Stenberg](https://daniel.haxx.se/)** says: .comment-author [October 13, 2026 at 14:11](https://daniel.haxx.se/blog/2026/10/13/a-slightly-faster-slimmer-curl/#comment-27559) .comment-metadata .comment-meta I clearly failed at math here… Thanks, the post has been corrected. .comment-content [Reply](https://daniel.haxx.se/blog/2026/10/13/a-slightly-faster-slimmer-curl/?replytocom=27559#respond) .comment-body