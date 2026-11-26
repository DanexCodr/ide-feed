Easily plan and execute SQL Server migrations to Azure with the help of AI. New plugins package focused guidance for supported coding agents and development environments.  Choosing the right Azure SQL migration path requires following an "Evidence first. Recommendation second" approach. Rather than guessing a target, destination selection and migration methods are determined by systematically evaluating evidence across four core dimensions:

  * Assessability: Before evaluating readiness, verify that you have sufficient inventory coverage, up to date assessment data, and no critical confidence gaps.
  * Compatibility: Assess whether your database workload can run on a given Azure target without blockers. This identifies feature support, breaking changes, migration risks, and necessary remediation steps.
  * Sizing: Evaluate actual workload demand,including CPU, memory, storage capacity, and I/O performance, to ensure the target tier provides appropriate performance headroom.
  * Pricing and licensing: Factor in estimated monthly compute and storage costs based on service tier assumptions, deployment region, and licensing benefits such as Azure Hybrid Benefit.

With the Microsoft SQL Migration agent skills (microsoft-sql-migration), you can easily navigate this process through a structured sequence:

  * Pre-assessment and recommendation: Run recommend-migration-path to receive a preliminary disposition and identify the appropriate assessment route.
  * Readiness assessment: For on-premises/local SQL Server instances, execute an offline assessment using az-datamigration via evaluate-offline-migration-readiness. For Azure Arc–enabled instances, use evaluate-azure-migration-assessment or pull existing assessment data via get-migration-assessment.
  * Performance sizing: Use recommend-sku-sizing to analyze collected performance metrics and calculate target SKU recommendations.
  * Prerequisite planning: Use generate-migration-prerequisite-plan to build a scenario-specific checklist tailored to your selected target.
  * Execution and validation: Execute the migration method (BACPAC, LRS, or backup/restore) and run validate-post-migration-data to confirm schema and data integrity after cutover.

The SQL Migration agent skills are packaged as the microsoft-sql-migration plugin within the microsoft/microsoft-sql marketplace. You do not need to clone the repository unless your client lacks marketplace support. The installation coordinate is microsoft-sql-migration@microsoft-sql>, and the installation steps vary depending on your coding agent or development environment. For GitHub Copilot CLI for instance run the following commands in your terminal to register the marketplace and install the plugin: copilot plugin marketplace add microsoft/microsoft-sql  
copilot plugin install microsoft-sql-migration @microsoft-sql Similarly for Claude Code, inside an interactive Claude Code session run: /plugin marketplace add microsoft/microsoft-sql  
/plugin install microsoft-sql-migration @microsoft-sql Ultimately, these skills turn migration expertise into reusable, AI-powered capabilities directly inside your coding environment, transforming a fragmented migration into a connected, context-aware journey, to minimize manual effort and maximize confidence. [ ](<mailto:microsoft-sql-migration@microsoft-sql</a>) [Microsoft SQL agent skills](<https://github.com/microsoft/microsoft-sql>)

#### Related Articles

[AI-901: Introduction to AI in Azure](<https://www.i-programmer.info/news/150-training-a-education/19179-ai-901-introduction-to-ai-in-azure.html>) __ To be informed about new articles on I Programmer, sign up for our [weekly newsletter](<https://www.i-programmer.info/edit-profile.html?layout=form>),[ ](<https://s3.amazonaws.com/com.alexa.toolbar/atbp/hfdfGO/download/index.htm>)subscribe to the [RSS feed](<https://www.i-programmer.info/component/ninjarsssyndicator/?feed_id=3&format=raw>) and follow us on [Facebook](<http://www.facebook.com/pages/iProgrammer/127140977307932#%21/pages/iProgrammer/127140977307932?v=wall>) or [Linkedin](<http://www.linkedin.com/company/i-programmer>). [](<https://amzn.to/4iJFqTH>)