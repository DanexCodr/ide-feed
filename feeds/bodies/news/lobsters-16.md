In July, we [announced a series of planned updates](https://blog.pypi.org/posts/2026-07-22-ui-updates/) to the PyPI user interface. Shaped by [user research with members of the Python community](https://github.com/pypi/warehouse/issues/20111), the updates aim to improve how we surface security signals and display package details.

We're pleased to share that this work is now complete and live on [PyPI](https://pypi.org/).

## Context[¶](https://blog.pypi.org/posts/2026-11-06-ui-updates-complete/#context)

With the rapid growth of the Python ecosystem, PyPI has become an increasingly attractive target for malicious actors. In response, the PyPI team has [delivered many security features](https://docs.pypi.org/about/security-and-internals/#pypi-security-features) while taking a more active role in helping PyPI users assess and understand package security.

[Digital attestations](https://blog.pypi.org/posts/2024-11-14-pypi-now-supports-digital-attestations/), introduced in 2024, are an example of this effort, providing a verifiable record of a release file's *provenance* (where it came from). However, provenance and attestations are still unfamiliar concepts for many PyPI users, and PyPI's interface did little to communicate their meaning, importance, or limitations.

To address this, PyPI partnered with [Kabu Creative](https://kabucreative.com/) to bring clearer security signals to the PyPI UI, implementing the recommendations developed in the [OpenSSF Attestations Style Guide](https://repos.openssf.org/attestations-style-guide).

Here's a look at what's changed, what it means for you, and what actions you can take.

## The New Security Tab[¶](https://blog.pypi.org/posts/2026-11-06-ui-updates-complete/#the-new-security-tab)

The new **security tab** communicates release provenance states and displays per-file attestations, giving you a dedicated place to verify where the release files came from.

### Provenance States[¶](https://blog.pypi.org/posts/2026-11-06-ui-updates-complete/#provenance-states)

PyPI calculates each release's provenance state by checking whether each release file has an attestation. Typically, a release will be in one of two states:

#### Full Provenance[¶](https://blog.pypi.org/posts/2026-11-06-ui-updates-complete/#full-provenance)

This means that 100% of the release files have attestations, carrying either or both of the supported attestation types:

**[PyPI Publish](https://docs.pypi.org/attestations/publish/v1/) attestations** confirm the file was published by a [PyPI Trusted Publisher](https://docs.pypi.org/trusted-publishers/):

**[SLSA Build Provenance](https://slsa.dev/spec/v1.2/build-provenance) attestations** link the file back to its exact source commit, build platform, and instructions:

You can review attestation metadata directly in the UI, or click on the transparency log link for more information.

#### No Provenance[¶](https://blog.pypi.org/posts/2026-11-06-ui-updates-complete/#no-provenance)

"No provenance" simply means that no file in the release has an attestation. This is typical for older releases or projects that have not yet configured Trusted Publishing. **No provenance does not necessarily indicate that a release or release file is malicious; it instead means that the *file origin cannot be cryptographically verified***.

When there is no provenance, you should rely on surrounding trust signals to assess security, such as maintainer history, release patterns, and repository activity. If you maintain the package, consider using [Trusted Publishing](https://docs.pypi.org/trusted-publishers/) with a [publisher that generates attestations](https://docs.pypi.org/attestations/producing-attestations/) for your next release.

### Provenance Warnings[¶](https://blog.pypi.org/posts/2026-11-06-ui-updates-complete/#provenance-warnings)

Provenance warnings are designed to help you identify when a file may not have come from the project's maintainers, for example, if an attacker has taken over an account or a publishing workflow.

When provenance metadata looks unusual or conflicts with a project's history, PyPI surfaces a prominent warning. Many warnings have legitimate explanations, but each one is worth checking before you install.

This means that some files carry attestations while others do not (e.g., wheels were published via Trusted Publishing, but the source tarball was uploaded using an API token).

Exercise caution if you see this warning. Check release notes for build issues or ask in the project's issue tracker before installing.

This warning indicates that files within the same release originate from different build systems or source repositories.

Check the attestation metadata to confirm whether all files came from sources controlled by the maintainers.

This warning tells you that the release files originated from a different repository or workflow than a previous release. While often legitimate (such as an organization name change or repository migration), it can also indicate a compromised pipeline or account takeover.

If you see this warning, check the project release notes or official channels to confirm that an infrastructure migration was planned.

This means that a project that previously published with attestations has changed to uploading release files without them.

Check whether the maintainers intentionally changed their publishing process, for example by switching back to API tokens, or by changing their publishing configuration so that it no longer generates attestations. If this is unexpected, treat the release with skepticism until verified.

To learn more about provenance and attestations, including provenance warnings, see our [user documentation](https://docs.pypi.org/using-pypi/package-security/provenance/).

## Redesigned Project Detail Page[¶](https://blog.pypi.org/posts/2026-11-06-ui-updates-complete/#redesigned-project-detail-page)

To support these changes, the project detail page has also been updated:

- Provenance warnings now appear at the top of the page, alongside status banners for yanked releases, archived projects, and pre-releases. If a project or release is quarantined, only the quarantine banner is shown, as it takes precedence over all other warnings and banners.
- When a release has full provenance or provenance warnings, its provenance state is displayed in the sidebar, linking through to the security tab for more information.
- Metadata is now ordered by utility and labeled as "PyPI data" or "Data verified by PyPI", replacing the old design where data was grouped and ordered by verification status.

## Release Files and Release History[¶](https://blog.pypi.org/posts/2026-11-06-ui-updates-complete/#release-files-and-release-history)

The redesigned **release files tab** helps you find the right file by searching and filtering long lists. You can also view the provenance state of each file within the table, and quickly identify late files, which are marked with an orange warning icon.

Late file warnings are shown when one or more files were uploaded more than 14 days after the initial release timestamp. These warnings only appear on releases prior to July 2026, when a policy was introduced to [reject new files after 14 days](https://blog.pypi.org/posts/2026-07-22-releases-now-reject-new-files-after-14-days/).

The **release history tab** now also provides more details about each release, exposing file count, provenance state, and release status (i.e., quarantined, yanked, archived, or pre-release).

## Getting Help[¶](https://blog.pypi.org/posts/2026-11-06-ui-updates-complete/#getting-help)

Alongside the interface updates, [PyPI's user documentation](https://docs.pypi.org/) has been extended to help you better navigate package security. Read our [package security guide](https://docs.pypi.org/using-pypi/package-security/introduction/) to learn about:

## Looking Ahead & Acknowledgments[¶](https://blog.pypi.org/posts/2026-11-06-ui-updates-complete/#looking-ahead-acknowledgments)

The new security tab gives PyPI a dedicated home for future attestation types and security notices. To help the wider open source ecosystem benefit from this work, we've also [published a case study in the OpenSSF Attestations Style Guide](https://repos.openssf.org/attestations-style-guide/pypi-case-study) detailing the design patterns and warnings developed during this project.

This initiative was funded by the [Open Source Security Foundation](https://openssf.org/) and implemented by [Kabu Creative](https://kabucreative.com/). We would like to thank [Dustin Ingram](https://github.com/di), [Zach Steindler](https://github.com/steiza), and the members of the [OpenSSF Securing Software Repositories Working Group](https://repos.openssf.org/) for championing this effort. Special thanks to [Mike Fiedler](https://github.com/miketheman), [Jacob Coffee](https://github.com/JacobCoffee), and members of the PyPI team for their thoughtful design feedback and code reviews, [@cofiem](https://github.com/cofiem) for their contributions to the new release files tab, and our [user interview participants](https://github.com/pypi/warehouse/issues/20111) and community testers for helping shape the final design.

Finally, we would like to thank the OpenSSF for its funding and continued partnership in securing the Python packaging ecosystem.