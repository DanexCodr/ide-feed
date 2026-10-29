We've open-sourced our [Accessible Components Library](https://tetralogical.com/resources/accessible-components-library/), and, as you might expect, this includes the HTML, CSS, and JavaScript code. But, we thought, "Why stop there?" So, we've also published our documentation, including the accessibility requirements, test scenarios, and even the working automated tests which validate each one.

Here's what we've released, how it works, and why automated tests are worth the effort. One caveat: these components are opinionated and built for our needs. Feel free to reuse or adapt them, but test them in your product before relying on them. They're not a production-ready design system.

## What we've released

As part of our efforts to provide useful [resources](https://tetralogical.com/resources) to the accessibility community, we've released version 1.0.0, which includes eight components. We will be releasing more in the future, but for now you can check out:

Each component ships with working examples, the HTML, CSS, and JavaScript behind it, and documentation which explains:

- What problem it solves
- When to use it
- When not to use it
- Where to use it
- Accessibility requirements
  - Test scenarios
  - Assistive technology compatibility

The accessibility requirements are the part which we think separates what we're doing from other component libraries. For every component, we've documented the applicable success criteria from the [Web Content Accessibility Guidelines (WCAG) 2.2](https://www.w3.org/TR/WCAG22/), at levels A, AA, and AAA. We've also added our own recommendations for things WCAG doesn't cover, such as usability when using high contrast themes.

Because WCAG can be challenging to navigate, we've grouped the requirements into ten themes, including:

- Adaptability
- Animation and movement
- Assistive technologies and semantics
- Colour and contrast
- Consistency and predictability
- Images and media
- Input assistance
- Keyboard
- Navigation
- Pointer and touch

This should make it easier to quickly understand how a component meets the needs of the people who use it.

Because there's always some technical jargon and caveats, we've also published our:

- Glossary, in case you come across some terms which are confusing
- Assistive technology compatibility notes, which document some browser and tooling quirks we've run into

## Turning requirements into automated tests

Documenting requirements is useful, but a document can't tell you whether a component actually meets them all. So, we converted each requirement into a test scenario using [Gherkin](https://cucumber.io/docs/gherkin/reference/) syntax, and we wrote working [Cucumber](https://cucumber.io/) tests which validate them.

Gherkin is great because it describes complicated automated tests in plain language, using `Given`, `When`, and `Then` to describe each step. This makes it easier for non-developers to understand what the test is doing, and even help write tests. We've written about Gherkin before, and why it helps to [annotate designs using common language](https://tetralogical.com/blog/2025/09/23/annotating-designs-using-common-language/).

Each of our Gherkin scenarios includes the following:

- Tags: used to run a subset of tests. For example, you might only want to run level A and AA tests, and ignore any recommendations
- Rule: the WCAG success criterion it relates to, or whether it's a recommendation
- Scenario: a description of what the test is checking for
- Test steps: the Given, When, and Then steps which describe exactly how it's tested

For example, here's our scenario for 1.4.10 Reflow on the [breadcrumbs](https://tetralogical.com/resources/accessible-components-library/breadcrumbs) component:

```gherkin
@1.4.10 @aa @automatic
Rule: 1.4.10 Reflow, Level AA
  Scenario: Content reflows without horizontal scrolling at 320px wide
    Given I load the sample "https://tetralogical.com/resources/accessible-components-library/breadcrumbs/examples/default.html"
    When I view the rendered '.tl-breadcrumbs'
    And I set the viewport to 320px wide
    Then it should reflow without requiring horizontal scrolling
```

This matters because you don't need to be able to read all the complex JavaScript code to understand what the test is doing. A designer, a tester, a product manager and a developer can all read the same scenario, and all agree on what it means to pass or fail. And, even if you don't use JavaScript on your project, because Cucumber is available in most mainstream programming languages, you can still use the Gherkin feature files and write your own tests to validate them.

All of our test scenarios are written from a collection of shared steps, which was a lot of work at the beginning, because we had to write the underlying code to validate each one. But, each step is reusable, so scaling is easy.

We've published a [full list of our test steps](https://tetralogical.com/resources/accessible-components-library/test-steps/) which work out of the box. This list is generated from the actual step definitions we use in the repository, so it's kept in sync automatically. This means any time we add a new one, you'll also get it for free.

## What the automated tests check

Behind each test step is JavaScript code that controls a real browser using [Playwright](https://playwright.dev/). The tests load the sample from a URL, and then interact with it the same way a real person would, by clicking things or focusing them using a keyboard. Then, they pull information from the browser, like the states and properties of the elements, and verify whether the things that were supposed to happen actually happened.

This is where our tests go much further than off-the-shelf accessibility checkers. A lot of these tools are valuable, and we do recommend using them, but they mostly inspect static markup. They often tell you about things like a button having no accessible name, but they don't often tell you about more complicated scenarios, like whether a focus indicator is hidden behind another element.

## Things which can't be automated

*Most* of our tests are automated, which has taken a bit of creativity at times. But, not everything can be reliably automated, and we'd be a bit suspicious of any tool that claims it can be. For example, an automated test can easily confirm whether a form field has an associated label. However, it's a lot more difficult to assess whether the label actually makes sense to the person reading it, because that relies on context. Arguably, we could capture screenshots and code snippets, and throw them over a wall to a large language model to assess whether something is readable. But, we think that it's ok to have some things reviewed by a human, because it's *for* humans.

In version 1.0.0, 97% of our scenarios are fully automated. For the remaining 3%, rather than just skipping them, we've added functionality which gathers the information a reviewer needs from the browser, and creates a list of what needs to be checked manually. Every test run produces a JSON report of what passed and failed in the automated tests, plus a Markdown checklist of what still needs verifying by a human.

Finally, all the assistive technology testing on each component is manual. Even if a component passes all the automated and manual tests and is technically compliant, it doesn't guarantee that there won't be any quirks with a particular screen reader or browser. So, we manually check each component, and if something is broken, we fix it.

## Why automated testing matters

In [our strategy work with large organisations](https://tetralogical.com/blog/2026/09/14/sustainable-accessibility-compliance-capability-culture/), we often find they struggle with [sustainable accessibility](https://tetralogical.com/blog/2021/01/07/sustainable-accessibility/). It's common for organisations to pay for an assessment, and then fix the issues. But, a few releases later, everything has quietly regressed, and nobody notices until a customer complains, or they pay for another accessibility assessment, which can get expensive.

Having automated tests breaks this cycle. You can plug them into your continuous integration (CI) pipeline, and have the tests run against every pull request, so you find out quickly when something is broken.

Here's why we think automated tests are so valuable:

- **Immediate feedback**: a developer can run all the tests on their own device in about 30 seconds, and know straight away if they've broken something
- **Regression protection**: every pull request runs all the tests as part of CI, so anybody reviewing your code can quickly check for regressions
- **Shared language**: the scenarios are written in plain English, so accessibility requirements stop being technical, and become acceptance criteria the whole team can read
- **Traceability**: Each scenario is tagged with a success criterion and conformance level, so it's easy to run a subset of tests, or search to see what's covered
- **Coding standards**: Linting rules and CI checks are built in, so regardless of who writes the code, it should always feel familiar
- **More time to spend on usability**: Because the mechanical checks are automated, people can spend more time on real-world testing, rather than inspecting the Document Object Model (DOM) for the hundredth time to see if a button is labelled

## How the library is maintained

We've published the [Accessible Components Library](https://tetralogical.com/resources/accessible-components-library/) in its own repository on GitHub, and in the [resources](https://tetralogical.com/resources) section on our website.

However, the cool part is that our website pulls all the documentation and tests directly from GitHub, so there's a single source of truth. The two can't drift apart or end up out of sync. So, if we want to add a new component to our website, we have to publish it to the repository first. This means you get it too, along with any tests and documentation that go with it.

We'll be releasing more components in the coming months. We've released a small set for now, so we can gather feedback and iron out any teething problems. So, make sure to star the repository to get any updates when they land.

## Try it yourself

We've released the library under the [ISC licence](https://github.com/TetraLogical/accessible-components-library/blob/main/LICENSE), so you're free to use, copy, modify, or share any of the code and documentation, as long as you don't remove the copyright notice.

If you want to run the tests, the [README](https://github.com/TetraLogical/accessible-components-library/tree/main) in the repository explains how to install and run the tests.

If you want to fork it and expand it yourself, the [development guide](https://github.com/TetraLogical/accessible-components-library/blob/main/DEVELOPMENT.md) explains how the repository is put together, and how you can add your own components and tests.

If you spot a bug, or have ideas and opinions, please [open an issue on GitHub](https://github.com/TetraLogical/accessible-components-library/issues).

We're not accepting pull requests at the moment, as each component needs a full set of requirements, tests, and assistive technology checks, which we need to keep in sync with the code. And, because these are the components we use in our own work, we're keeping things opinionated and in-house, at least for now.

## Thank you

It might come as no surprise that this is a lot of work. And, while my name is on this blog post, and on the deployment commit of version 1.0.0, this project has been a labour of love for several TetraLogical colleagues, both past and present including:

## Next steps

Browse the [Accessible Components Library](https://tetralogical.com/resources/accessible-components-library/), or find out how our [Consultancy](https://tetralogical.com/services/consultancy/) and [Training](https://tetralogical.com/services/training/) services can help your team build accessibility testing into the way you work.