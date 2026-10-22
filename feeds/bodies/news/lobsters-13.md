Earlier this morning, Railway detected anomalous activity involving systems that store customer environment variables. After further investigation, our investigation to date indicates that an unauthorized third party may have accessed encrypted environment variables and, for some of them, obtained the decrypted contents. Environment variables may contain secrets such as API keys or database and registry credentials.

We believe this is part of a series of attacks recently targeting platform companies with the aim of compromising AI inference providers. We have notified these upstream providers to revoke all keys proactively, as we take these kinds of events extremely seriously.

While our initial analysis suggests the impact may be limited to a subset of users, we are nevertheless recommending that all users take the actions described below as a precaution to protect your systems while we complete our review.

**What you should do:** As such, we strongly recommend that you immediately roll all environment variables, including any API keys, stored in Railway, as well as any private registry credentials, and review logs for those services for unusual activity.

All deployments are paused while we investigate. Until builds are restored, you will not be able to roll out new versions. We apologize for this inconvenience. Follow [this](https://status.railway.com/incident/QH8L8B3E) incident to be notified when builds resume.

As we confirm which accounts were affected, we will contact those customers directly by email with additional details.

We will provide new updates on this announcement, and on [status.railway.com](http://status.railway.com) as we narrow the scope of impact.