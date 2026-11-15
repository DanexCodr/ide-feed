This year the Percona Live conference took place from September 9-11 in Amsterdam. We provide an overview of this year's event. Percona Live is a technical conference focused on open source database technologies, data infrastructure and community collaboration among database engineers, DBAs, operators and architects. The event covers the full spectrum of open source database ecosystems,including MySQL, PostgreSQL, MongoDB, MariaDB, Valkey and columnar/analytical engines like ClickHouse and DuckDB. This year the conference focused on several key subjects: **1\. AI and Vector search in data infrastructure**

  * AI driven operations and autonomous DBAs: Presenters explored the shift toward autonomous database management, such as DBTune's framework for autonomous PostgreSQL and Sixta's AI DBA and examined how AI agents are changing workload patterns, data volume and serverless/ephemeral database requirements.  

  * Vector search across engines: Sessions highlighted native and self hosted vector search capabilities across open source databases (including PostgreSQL, MongoDB, Valkey, MySQL and MariaDB), featured in panels like The Vector Search Quintet and announcements like Percona Search for MongoDB.

**2\. Kubernetes, Cloud Native and private DBaaS**

  * Database operators at scale: Engineers shared real world architecture patterns, trade offs and lessons from operating 40+ production databases per cluster on Kubernetes, including automated operator tuning and memory/swap management under extreme load.  

  * Private DBaaS platforms: Talks evaluated multi database control plane solutions such as Open Everest to manage MySQL, PostgreSQL and MongoDB on Kubernetes as a private DBaaS without vendor lock in.

**3\. Open source governance, sovereignty and licensing**

  * Licensing and Digital Sovereignty: Keynotes addressed changing open source license models, community governance, data sovereignty demands across Europe and building long term trust in open source software.  

  * Upstream first and community contributions: Sessions highlighted the importance of upstream contributions (such as AWS's Upstream First initiatives ), community driven projects like reviving the Percona Toolkit and maintaining corporate open source responsibility.

**4\. Engine innovations and technical tracks**

  * PostgreSQL: Deep dives covered new capabilities in PostgreSQL 19 (including asynchronous I/O improvements, visibility map updates, autovacuum scoring and system observability, performance tuning parameters (random_page_cost, fill factor) and OAuth implementation.  

  * MySQL and extensions: Updates included Oracle's initiative to open MySQL innovation, VillageSQL's extension framework for porting PostgreSQL extensions to MySQL using Rust, ProxySQL ecosystem enhancements and binary log server topology management.  

  * MongoDB, Valkey and MariaDB: Presentations covered agentic era features and zero downtime migrations in MongoDB, Valkey in memory key value operations and Kvrocks on disk compatibility and MariaDB 11.8 protocol security and server plugin extensions.  

  * Columnar engines and benchmarking: Analytics tracks showcased columnstore innovations (ClickHouse, DuckDB and VictoriaMetrics for petabyte scale logs) alongside open source database benchmarking standards using HammerDB.

**5\. Observability, reliability and migrations**

  * Modern Observability: Discussions focused on real time query analytics in Percona Monitoring and Management (PMM), OpenTelemetry integration and proactive failure detection before incidents occur.  

  * Migration case studies: Practical war stories detailed complex, zero downtime migrations,such as moving an 800 TB / 6,000 tenant SaaS platform from Oracle to PostgreSQL and transitioning banking workloads from Hadoop NoSQL to MongoDB.

Would want to be there but missed it? No worries as you can now watch on demand since the sessions are now available online. Because there's a lot of material to go through, we did a bit of digging to suggest the best to watch first. As such, the following three talks provided particularly unique, contrarian, or highly innovative perspectives compared to the rest of the conference program. VIDEO **1\. "SQL injection is a thing of the past…. and other lies we tell ourselves" , Mackenzie Jackson**  
The traditional myth is that SQL injection is an outdated problem that was technically solved in 1998 with prepared statements and parameterization. However despite being "solved," initial security scans show that 10% to 20% of applications still contain active SQL injection vulnerabilities. More critically, Jackson highlights how the rise of AI agents introduces an entirely new threat vector: when AI models generate raw SQL queries dynamically from user prompts, standard parameterization no longer offers protection against prompt injection attacks. **2\. "When 3,951x Is Not a Speedup: Measurement Integrity in Database Benchmarking" , Nima Torabi and Vitalii Akimov**  
If a synthetic benchmark demonstrates a nearly 4,000x performance improvement in dev/test, the optimization will translate to massive gains in production. Torabi and Akimov demonstrate how a 4,000x reported speedup can produce zero actual speedup in production. This measurement illusion happens when test benchmarks warm up on rare parameter values,causing PostgreSQL to generate optimal custom index plans,whereas production queries with uniform or skewed "whale" data fall back to generic sequential scans. **3\. "Tuning PostgreSQL for performance: the role of random_page_cost" , Fernando Cargos**  
On modern SSD and NVMe storage, DBAs should aggressively drop PostgreSQL’s default random_page_cost from 4.0 down to 1.1 or 1.0 to reflect faster random read speeds. Citing empirical tests, Cargos points out that random page access on SSDs remains 15x to 25x more expensive than sequential reads. Blindly lowering random_page_cost to 1.1 deceives the query planner into forcing inefficient index scans over faster sequential scans when fetching large result sets, ultimately leading to significant performance regressions. While these were the most interesting talks, that's not all as there were many other great sessions. So, take your time and delve into the conference by going through its YouTube playlist. In the end, Percona Live Amsterdam 2026 proved to be highly worthwhile, offering database professionals exceptional technical depth, practical real world solutions and valuable community networking across three days.

#### More Information

[Percona Live 2026 Youtube playlist](<https://www.youtube.com/watch?v=UV7khoro3XQ&list=PLOgsvlaOXz2c>)

#### Related Articles

[What happened At PGconf.dev 2026](<https://www.i-programmer.info/news/99-professional/19126-what-happened-at-pgconfdev-2026.html>)  

__ To be informed about new articles on I Programmer, sign up for our [weekly newsletter](<https://www.i-programmer.info/edit-profile.html?layout=form>),[ ](<https://s3.amazonaws.com/com.alexa.toolbar/atbp/hfdfGO/download/index.htm>)subscribe to the [RSS feed](<https://www.i-programmer.info/component/ninjarsssyndicator/?feed_id=3&format=raw>) and follow us on [Facebook](<http://www.facebook.com/pages/iProgrammer/127140977307932#%21/pages/iProgrammer/127140977307932?v=wall>) or [Linkedin](<http://www.linkedin.com/company/i-programmer>). [](<https://amzn.to/4iJFqTH>)