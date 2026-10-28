# Are you tired of your screenshares looking like this?

## Don't you think they should look like this instead?

*OBS*

## You need WHIP.

Did you know OBS or FFmpeg can go directly into a video conference? You configure everything,
           so you control exactly the quality you are going to get. WHIP support means these tools
           now speak the protocol of video conferencing.

## Help! My video conferencing provider doesn't support WHIP. What can I do?

Send them an angry email. Tell them you don't want their crappy
          proprietary client. You want open standards that let you bring the tools
          you prefer.

## FAQ

[WHIP](https://www.rfc-editor.org/rfc/rfc9725.html) is an open standard for sending live video to a service using WebRTC.
              Your provider gives you a server URL and a stream key, called a bearer token. Before to join a conference
              call each client had to run custom code. That means FFmpeg/OBS would never be able to join.

A lack of control. Your browser is picking a bitrate, codec or resolution that doesn't match what you need.

OBS and FFmpeg let you choose your resolution, frame rate, bitrate, and codec.
              You can tune those settings for the content you're sharing and the hardware and connection you have.

OBS Virtual Camera sends your OBS scene to the conferencing app as a webcam.
              You can pick the layout of your stream, but the conferencing app still handles encoding.