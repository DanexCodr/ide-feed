pg-java is a modern pre-release PostgreSQL database driver specifically designed for Java 21+ and the JVM. Developed primarily by AI with strict human architectural oversight, the project prioritizes PostgreSQL wire protocol efficiency and virtual thread friendly blocking I/O over legacy JDBC constraints. As such, the development of the driver was guided by several core design goals aimed at addressing the structural limitations of older drivers:

  * **PostgreSQL first native API** : The driver is designed directly around PostgreSQL’s native wire protocol and feature set rather than lowest common denominator database constraints. Its native API directly exposes PostgreSQL idioms (such as $1 positional parameters and 1-based column indexing) without relying on java.sql abstractions.
  * **JDBC as a layer, not a foundation** : Full JDBC compliance is supported via a java.sql.* layer that sits on top of the native API rather than serving as its core foundation. This ensures that historical JDBC limitations and assumptions do not dictate or corrupt the execution core. A full java.sql.* implementation module (postgresql-client-jdbc) provides standard Connection, PreparedStatement, ResultSet, DataSource and XADataSource support built directly on top of the native engine.
  * **Modern java & virtual thread friendliness**: Built for Java 21+, the driver employs straightforward, blocking style code designed specifically not to pin carrier threads (e.g., using ReentrantLock instead of synchronized monitors around I/O). This allows applications to scale to thousands of concurrent connections using virtual threads without requiring asynchronous frameworks or event loops.
  * **Pull-first streaming by default** : The fundamental query primitive is a pull cursor (PgResultStream) that reads row by row off the wire and never buffers the entire result set in memory. Memory overhead is bounded by individual row size rather than result set size, and collection helpers (forEach, map, collect) are adapters layered over this streaming cursor.
  * **Full Postgresql feature set with external lifecycle primitives** : Over time, the driver aims to support the full range of PostgreSQL capabilities (including extended protocol features, COPY, LISTEN/NOTIFY, SCRAM authentication with channel binding and pipelining). Rather than embedding its own connection pool, it provides the essential connection lifecycle primitives needed by external poolers and the JDBC DataSource.

Reading behind the lines, what does the driver offer to developers? The pg-java driver provides a modern, PostgreSQL specific feature set for JVM developers across multiple core areas. What is really powerful is the high performance batching & execution modes. The driver automatically rewrites bulk INSERT statements into an INSERT INTO ... SELECT * FROM unnest(?::type1[], ?::type2[]) form. This keeps the SQL text constant regardless of batch size, uses only one array parameter per column (bypassing PostgreSQL's 65,535 scalar parameter cap without chunking), reuses prepared statement plans and executes in a single round trip. Batch mode continued, there's also Multi Row VALUES batch rewrites. That is, it supports multi row VALUES (?,?), (?,?) batch rewrites chunked at power of two sizes under a single Sync section (rewriteBatchUsingMultipleValues) to reproduce pgjdbc's exact reWriteBatchedInserts behavior and plan cache profile. Other welcome features are

  * Native pipelining API: Lets developers queue multiple arbitrary SQL queries across a single network write window and execute them under explicit sync() error boundaries, cutting network round trip overhead.
  * GraalVM Native image support: Ships with pre-configured GraalVM native image metadata (reflect-config.json, proxy-config.json, resource-config.json) for ahead of time compilation into native binaries.
  * Java record & Enum support: Supports mapping PostgreSQL composite row types directly into Java 21 records and custom database enums into Java enum constants.
  * JSON / JSONB binding: Includes a pgjson wrapper type to carry and bind JSON parameters with proper OID typing, avoiding lossy string parameter typing or mandatory SQL typecasts.

Great! How do you install it? Because pg-java is currently in pre-release and not yet published to Maven Central, you install it by cloning the repository and building it locally using Apache Maven. By way of requirments you need:

  * Java: JDK 21 or newer.
  * Build Tool: Apache Maven (a Maven Wrapper ./mvnw is included in the project, so installing Maven separately is optional).
  * Docker (optional): Only required if you want to run the full integration test suite against real PostgreSQL and PgBouncer containers.

Run the following commands in your terminal to build the driver and install the artifacts into your local Maven repository (~/.m2/repository):

    git clone <https://github.com/pgjdbc/pg-java.git>  
    cd pg-java  
    ./mvnw clean install

If you have Docker running and want to run integration tests against real database instances:

    ./mvnw verify -Pintegration-tests

Once built locally, you can declare dependencies in your application's pom.xml using the org.postgresql groupId For the PostgreSQL-Native API:

    <dependency>  
    <groupId>org.postgresql</groupId>  
    <artifactId>postgresql-client</artifactId>  
    <version>0.1.0-SNAPSHOT</version>  
    </dependency>

For standard JDBC support (jdbc:pg://):

    <dependency>  
    <groupId>org.postgresql</groupId>  
    <artifactId>postgresql-client-jdbc</artifactId>  
    <version>0.1.0-SNAPSHOT</version>  
    </dependency>

For legacy pgjdbc migration / drop-in compatibility:

    <dependency>  
    <groupId>org.postgresql</groupId>  
    <artifactId>postgresql-client-pgjdbc-compat</artifactId>  
    <version>0.1.0-SNAPSHOT</version>  
    </dependency>

To verify the installation in your Java application, connect using the canonical jdbc:pg:// URL scheme:

    String url = "jdbc:pg://localhost:5432/appdb?user=app&sslmode=verify-full";  
    try (Connection connection = DriverManager.getConnection(url, "app", password)) {  
    System.out.println("Connected successfully!");  
    }

Ultimately, pg-java is a welcome newcomer providing a modern, PostgreSQL native JVM client optimized for Java 21+ virtual threads, delivering lower memory overhead through pull-first streaming, faster bulk operations via array-parameter rewrites, and native protocol pipelining without the performance limitations of legacy JDBC.

#### More Information

[Introducing pg-java](<https://launchbylunch.com/posts/2026/Jul/29/introducing-pg-java/>) [pg-java on Github](<https://github.com/pgjdbc/pg-java>)

#### Related Articles

[Polygres: Advanced Search On PostgreSQL](<https://www.i-programmer.info/news/84-database/19138-polygres-advanced-search-on-postgresql.html>) __ To be informed about new articles on I Programmer, sign up for our [weekly newsletter](<https://www.i-programmer.info/edit-profile.html?layout=form>),[ ](<https://s3.amazonaws.com/com.alexa.toolbar/atbp/hfdfGO/download/index.htm>)subscribe to the [RSS feed](<https://www.i-programmer.info/component/ninjarsssyndicator/?feed_id=3&format=raw>) and follow us on [Facebook](<http://www.facebook.com/pages/iProgrammer/127140977307932#%21/pages/iProgrammer/127140977307932?v=wall>) or [Linkedin](<http://www.linkedin.com/company/i-programmer>). [](<https://amzn.to/4iJFqTH>)