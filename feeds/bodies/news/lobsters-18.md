A goal one might have when designing a signing algorithm is to prevent signing a message one has not seen.

Signing a message one hasn't seen might sound difficult at first, but [most](https://www.rfc-editor.org/info/rfc8017/#section-8.1) [classical](https://www.rfc-editor.org/info/rfc8017/#section-8.2) [signature](https://en.wikipedia.org/wiki/Digital_Signature_Algorithm) [algorithms](https://en.wikipedia.org/wiki/Elliptic_Curve_Digital_Signature_Algorithm), as commonly used, sign a hash of the message, rather than the message itself. This kind of arrangement is necessitated by the fact that the underlying algorithms are only capable of signing messages of a limited size. You might not have seen the message, but you might have seen the hash of it, or another signature which encodes said hash. In many protocols, this lets you produce a valid signature on a message you've never seen. That's rarely a problem in practice, but it can be surprising, and it's a pitfall for the unsuspecting protocol designer.

More recent algorithms take steps to prevent this:

- Ed25519 signs SHA-512(R || PubK || M) where R is functionally a random curve point, PubK is the public key, M is the message, and || is the concatenation operator
- ML-DSA signs SHAKE-256(SHAKE-256(PubK, 64) || 0x00 || len(ctx) || ctx || m, 64) (where ctx is a 0 to 255 byte context string)

This can complicate your signing code, particularly when dealing with HSMs or smart cards, [but it doesn't require majorly reworking](https://keymaterial.net/2024/11/05/hashml-dsa-considered-harmful/) your signing process. Unfortunately, on the verification side things are less rosy.

## The challenge

As a general rule of thumb, we should avoid touching the body of a signed message until we've verified the signature. Also as a general rule of thumb, cryptographic protocols where there are multiple signers put the signer's identity within said body (X.509, most JWT and CWT usages, SAML, I'm looking at all of you, but you're not the only ones).

This means the verification process ends up being

1. Gingerly parse the message
2. Dig through as much message as necessary to identify the signing key
3. Actually verify the message
4. Actually consume the message

Often (JWT, CWT and SAML again), there's either no key identifier present in the signed message, or it's permitted for multiple signing keys to share a key identifier<sup>†</sup>. This means that, if the issuer has multiple keys, you may have to do multiple trial-verifications to work out if the message is actually valid.

One nice property that all of these protocols have (except XML Digital Signatures, but *nobody* thinks XML Digital Signatures were a good idea) is that they carry the signing method in a header. So, with a traditional signing algorithm, you have the option of

1. Parsing the header
2. Identify algorithm and hence the hash algorithm
3. Hash the message
4. Gingerly parse the message
5. Dig through as much message as necessary to identify the signing key
6. Actually verify the message
7. Actually consume the message

This comes with two advantages:

1. After step 3, you can throw away the raw message, reducing memory usage
2. In step 6, you pay for the cost of verifying a signature for every attempted key rather than also the cost of re-hashing the message. In most cases messages are small and this cost is also small, but every little helps.

Unfortunately, it has the slight flaw that it doesn't work with either Ed25519 or ML-DSA as defined.

For ML-DSA, it would have been quite easy to re-arrange matters. If we instead computed `SHAKE-256(0x00 || len(ctx) || ctx || m || SHAKE-256(PubK, 64), 64)` (i.e. we put the public key hash in *at the end*), then we can hold our SHAKE-256 context around and copy it for each trial verification. We'd end up keeping just over 200 bytes of SHAKE-256 context around (instead of 64 bytes of output), but that's not too bad. Unfortunately, that's not the choice that was made and we'll just have to deal with it.

Ed25519 is slightly more challenging. If we reversed the hash computation to be `SHA-512(M || R || PubK)` instead, it would be vulnerable to length extension attacks (for any `SHA-512(X)` you can extend it into `SHA-512(X || some predictable garbage || Y)` for any arbitrary Y).

Fixing that when Ed25519 was published in 2011 would be somewhat tricky, though the easiest option without truncating the hash is just to sign `SHA-512(SHA-512("ed25519 domain separation" || M || R || PubK))`.

Since we don't have a time machine, it's all a bit academic. In 2026 you can just avoid the problem by using SHA-3, BLAKE2, a truncated SHA-2 variant, or any other modern hash function which isn't vulnerable to length extension attacks.

In the meantime I'll just sigh and hope we can reduce the number of signatures we pass around, given they're really becoming rather large and expensive.

† You may be thinking it somewhat defeats the purpose of having a key identifier if they aren't unique. I don't disagree!

## Comments

[@erincandescent](https://akko.erincandescent.net/users/erincandescent) /me looks at URL  
> "Mu Annoys Me"  
What did [@wohali](https://timeloop.cafe/@wohali)'s cat do to you :(?

(Cool article, will take me several passes to understand it tho)

[@erincandescent](https://akko.erincandescent.net/users/erincandescent) hashes ur public key first

[@Lunaphied](https://provably.online/@Lunaphied) nooo!

| Likes | [![Huubje](https://ftp.ieji.de/accounts/avatars/111/427/922/353/181/682/original/d2f6815edffcefd9.png)](https://ieji.de/@Huubje)[![William D. Jones](https://files.mastodon.social/accounts/avatars/000/011/500/original/7eb522416c373a06.jpg)](https://mastodon.social/@cr1901)[![Tris](https://assets.chaos.social/accounts/avatars/114/631/355/525/605/024/original/b3d9a7b56c1712ef.png)](https://chaos.social/@tris)[![Fiona](https://woem.men/files/49ecc1bf-5913-411e-9c7b-eb1cd9589cc2)](https://woem.men/@airtower)[![Kanbaru 🌟 (one hikari of too many)](https://cdn.bsky.app/img/avatar/plain/did:plc:cocuumty5bs4zbiltpmp37f5/bafkreibb5i3f7xz7sqeku4unyator3vi5ufybg2udoduynbn2p2kh2xiou)](https://bsky.app/profile/hikari.noyu.me)[![Oblomov](https://snowfan.it/system/accounts/avatars/117/342/193/979/745/312/original/ca9ec961a255db56.png)](https://snowfan.it/@oblomov)[![Bart Coppens](https://files.mastodon.social/accounts/avatars/000/038/881/original/cdae76dfce3a1122.jpg)](https://mastodon.social/@bartcopp)[![Lunaphied](https://provably.online/system/accounts/avatars/114/458/103/977/672/839/original/941b57352d1b66d1.jpeg)](https://provably.online/@Lunaphied)[![Tired Bunny :comf:](https://media.akko.wtf/32ac9c197b839b0030d7110a59a3e2c3a60d062bc8e51aee80c9ac3fbef880da.png)](https://akko.wtf/users/tiredbun) |
| --- | --- |
| Reposts | [![Huubje](https://ftp.ieji.de/accounts/avatars/111/427/922/353/181/682/original/d2f6815edffcefd9.png)](https://ieji.de/@Huubje)[![Tris](https://assets.chaos.social/accounts/avatars/114/631/355/525/605/024/original/b3d9a7b56c1712ef.png)](https://chaos.social/@tris)[![⎔ erincandescent](https://cdn.bsky.app/img/avatar/plain/did:plc:l6rr5satovz254j4ndjuqzcd/bafkreifcjjzt6glrfbz3mjltrd5zazdfhqgbu3bf6xjr4vv2rwu6e2eyam)](https://bsky.app/profile/erincandescent.net)[![erincandescent 💜](https://erincandescent.catgirldelivery.network/2eb59444c0d502d090d44564ee6929afd74b0ac9783edaddf055e7b9061f3f47.png)](https://akko.erincandescent.net/users/erincandescent) |