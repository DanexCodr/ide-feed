A critical flaw in **Red Hat Quay** allows an attacker who can access a Quay registry to read and overwrite private container images in every repository.

Quay enables anonymous access by default, and while it is enabled, the attacker needs no account. When it is off, anyone with a valid account can still exploit the flaw, Red Hat said yesterday. The company has released fixed builds for eight Quay 3 branches.

The flaw is tracked as **CVE-2026-123710 **(CVSS score: 9.8).

Quay uses keys it trusts to sign the access tokens that allow image pushes and pulls. The flaw lets an attacker add their own key to the keys Quay trusts, with no expiry date. Quay then accepts tokens signed with that key for any repository.

With those tokens, an attacker can retrieve private images and any secrets or credentials stored within them. The attacker can also push or overwrite images, and the change propagates to every system that later pulls those images.

The planted key survives restarts until someone removes it. It can also be used to delete the keys that running Quay instances use, so normal pushes and pulls start failing with authentication errors.

Quay's key server checks that a request to replace a key carries a token signed by a trusted key, with the expected audience and issuer. It does not check whether the token was issued for key rotation. An anonymous token from Quay's /v2/auth endpoint passes: Quay signs it with a trusted key, and the caller chooses its audience.

A second critical flaw, **CVE-2026-110697** (CVSS score: 9.9), was disclosed at the same time. It lets a Quay user who can create a namespace steal other tenants' robot account tokens and use them to read, push, or overwrite those tenants' images.

This flaw is in the code that lists robot accounts. It builds an SQL LIKE pattern from the namespace name without escaping wildcard characters, and in SQL LIKE an underscore matches any single character.

So a namespace with an underscore in the right place can match another tenant's namespace and return its robot accounts, with their decrypted tokens. The attacker needs no elevated privileges, and the victim does not have to do anything.

Deleting the attacker's namespace also deletes the corresponding robot accounts, which can cut off systems that rely on them. Where Quay is the integrated registry for OpenShift, stolen robot credentials can be used to inject malicious images into CI/CD pipelines, the company says.

Red Hat's Dave O'Connor found both flaws. The logic behind CVE-2026-123710 has been in Quay since its first public commit, according to the [bug report](https://bugzilla.redhat.com/show_bug.cgi?id=2568072) for that flaw.

Red Hat lists every version of Quay 3 and Quay 5 as affected by both flaws. For CVE-2026-123710, its guidance names standalone installs, Quay deployed by the Quay Operator on OpenShift, and the mirror registry for Red Hat OpenShift as affected.

Any Quay instance that untrusted clients can reach is exposed, including internal registries, the company says.

When checked today, the [CVE entry](https://access.redhat.com/security/cve/cve-2026-123710) for CVE-2026-123710 still showed every Quay package as affected, with no fix, even though each advisory lists the flaw.

The company recommends these steps:

1. At the proxy or load balancer, block the /keys endpoint for everything except trusted internal components.
2. Search the audit logs for service_key_rotate and service_key_delete events where expiration_date is null.
3. Remove any approved service keys you do not recognize.
4. Install the fixed release. Until it is running, an attacker can add a new key the same way, so deleting one does not last.

"Turning off anonymous access doesn't protect you," the company says in its [key remediation article](https://access.redhat.com/solutions/7149923). A planted key also continues to work after password resets and changes to the robot token.

For CVE-2026-110697, the company's [CVE page](https://access.redhat.com/security/cve/cve-2026-110697) names the same eight releases as fixed, calls updating the only complete fix, and says Quay.io is already fixed. But none of the eight advisories list CVE-2026-110697.

Until an update is in place, the company suggests limiting who can create organizations or namespaces containing an underscore, rotating robot tokens for any namespace that matches an underscore namespace, and watching for pulls or pushes that do not fit normal robot use. These steps reduce the exposure, but the flaw remains.

The [upstream fix](https://github.com/quay/quay/commit/094cfb024f01) adds the missing rotation check, requires keys added through the key server to have an expiry date, and stops callers from choosing a token's audience. The same change fixes the robot account search too.