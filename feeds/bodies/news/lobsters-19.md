LibreOffice does not reject artificial intelligence out of hand, but an office suite used by tens of millions of people – in schools, hospitals, public bodies, law firms and thousands of other organisations – will not add a feature to its default configuration until that feature can be delivered under the conditions defined by the project in accordance with its principles.

**User-controlled execution**. The user must be able to choose where inference takes place: on the local computer, on an infrastructure directly controlled by the user, or on a service chosen independently by the user. A default setting that silently redirects to a single provider is not a choice.

**No content may leave the computer without authorisation**. The content of documents is a user’s asset and, in many implementations, is also legally protected material: medical records, case files, tender documents and student data. Transmission must be the result of a user’s decision and not behaviour carried out in the background by the application.

**No telemetry of any kind**. LibreOffice does not collect usage data, and this must also apply to AI features.

**No dependence on a single provider**. An integration that only works with a single company’s API is a lock-in mechanism, regardless of how it is described in the release notes. Interfaces should be open and implementable by multiple backends.

**No compromises on format**. Generated content must be in ODF format, just like any other content, and must retain its structure, styles and semantics. An assistant that generates documents in a proprietary format perpetuates content lock-in.

**Entirely optional**. It must be installable, removable, and absent from the user interface for those who do not wish to use it, including administrators deploying the software across thousands of workstations who, due to company policy, do not authorise its use.

**Where we stand today**

In light of this list, there is no integration that meets all the requirements and that could be deployed, enabled by default, and supported throughout the entire lifecycle of a release. This is an assessment of the current state of the technology and the solutions based on it, and not a judgement on the value of the sector.

In the meantime, users who wish to use AI features can install one of the available extensions, which can be found either on the LibreOffice extensions website or distributed independently. Most connect to a locally running model via Ollama, LM Studio or another OpenAI-compatible endpoint, which means the document never leaves the computer.

These are third-party extensions at various stages of maturity, developed and maintained by their respective authors rather than by The Document Foundation. Users and administrators should assess them as they would any third-party component, checking whether a cloud endpoint is configured and what the provider does with the data it receives. The extension mechanism offers AI functionality to those who want it, without any consequences for all other users.

**Why our motivations are different**

The reason our position differs from that of the dominant suites has almost nothing to do with the technology.

For a company that sells subscriptions, an AI assistant justifies a price increase and strengthens the case for keeping all documents within its own infrastructure. The functionality and the business model reinforce each other, so integration is not only attractive but almost mandatory.

The Document Foundation is a not-for-profit organisation. There are no subscription tiers to protect, no upsells, no data to monetise. This does not make us wiser than others, but it means we can take the time needed to decide whether something is genuinely useful for our users, as we are not driven by quarterly results.

**What lies ahead**

The criteria we have listed do not amount to a definitive rejection. The AI sector is evolving rapidly; on-premises inference is becoming manageable on standard hardware; and open models are improving much faster than most of us had anticipated. Should an approach emerge that meets all the conditions, we will evaluate it very carefully.

Until then, there will be no AI of any kind in the default installation; extensions will be available for those who wish to integrate AI features, and we will closely monitor where the technology is actually heading.