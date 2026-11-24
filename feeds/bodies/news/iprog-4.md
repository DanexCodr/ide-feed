pg_pinecone is an open source PostgreSQL extension that integrates vector search directly into PostgreSQL by building on the data types and query patterns developers already use. pg_pinecone is an extension that offers specialized solutions for vector search and document retrieval directly within PostgreSQL, addressing the severe performance bottlenecks and tuning complexities commonly encountered with traditional bolt on options like pgvector. It allows PostgreSQL to remain the authoritative system of record while replacing or augmenting standard vector indexing architectures. While pgvector is a foundational PostgreSQL extension that introduces vector data types and standard vector index types (HNSW and IVFFlat), pg_pinecone is an extension that builds on top of pgvector to provide alternative, highly optimized vector search engines and integrated cloud features. In fact, pg_pinecone requires pgvector to be installed on the server because it operates directly on pgvector's existing vector columns. pg_pinecone then, adds integrating vector search directly the following way: **1\. Seamless pgvector compatibility and standard SQL  
**  
Existing vector columns: pg_pinecone operates directly on existing pgvector columns (vector or halfvec), meaning existing tables and schemas do not need to be restructured. Standard SQL syntax: Applications connect to Postgres as usual and execute standard vector similarity queries using native distance operators (such as ORDER BY embedding <=> $1 LIMIT 10 for cosine distance or <-> for L2 distance). No custom client libraries or external query endpoints are required for basic operations. **2\. "One Column, Three Engines" Architecture  
**  
pg_pinecone provides an index abstraction that allows tables to switch between three underlying search engines using pinecone.set_engine() without altering the application's SQL queries:

  * native (default engine)/fully in database: Runs entirely inside PostgreSQL processes without requiring a Pinecone account, an API key, or any external network calls.
  * remote (Pinecone managed Cloud engine): Designed for tables that outgrow a single PostgreSQL server's RAM or CPU limits.
  * pgvector engine: Directs search execution to pgvector’s standard HNSW or IVFFlat indexes if existing setups are preferred.

**3\. Native in search and multi tenant filtering** Standard graph based approaches in Postgres often perform post filtering (searching neighbors first, then evaluating the WHERE clause), which can discard matching candidates and severely degrade recall or return fewer rows than requested on selective queries. pg_pinecone solves this by integrating filters directly into the index search with selective filtering by storing filter column values alongside vector codes in index pages and namespace partitioning. For multi tenant databases, declaring a partition_column isolates tenant data into dedicated namespaces in the remote engine or enforces targeted partition scans inside Postgres. **4.Integrated inference and hybrid document search** pg_pinecone also brings Pinecone's inference and document tools directly into SQL functions with server side embeddings which allow developers to populate embeddings inside SQL statements without external embedding pipelines and with hybrid and full text search which allows Postgres tables to execute BM25 keyword searches, dense semantic searches and combined hybrid searches with metadata filtering directly via SQL. Finally with pinecone.rerank, candidate results can be reprioritized using dedicated neural reranking models in a single query. **An example in action;** setting up hybrid search and integrated (server side) embedding in PostgreSQL with pg_pinecone requires no custom machine learning pipelines or manual vector wiring. pg_pinecone syncs your standard text columns directly to a Pinecone document index that automatically handles full text (BM25) tokenization and hosted model inference (such as Google's gemini-embedding-2). The example uses the managed Cloud version but it can also be self hosted since the extension is open source. **Step 1: Prerequisites and API key configuration  
**  
PostgreSQL (17 or 18) with pg_pinecone and pgvector installed is needed. Ensure pg_pinecone is listed under shared_preload_libraries in postgresql.conf so background sync workers can run. Hosted models like gemini-embedding-2 require a Pinecone Builder, Standard, or Enterprise plan (they are not available on the Starter plan). Set the API key in PostgreSQL so the background sync worker can authenticate: SELECT pinecone.set_api_key('pcsk_your_api_key'); **Step 2: Create a standard Postgres table  
**  
Create your table with standard relational columns (no vector column is necessary when using integrated embedding): CREATE TABLE articles (  
id bigint PRIMARY KEY,  
title text,  
body text,  
category text  
); INSERT INTO articles (id, title, body, category) VALUES  
(1, 'PostgreSQL Guide', 'PostgreSQL is an extensible relational database system.', 'database'),  
(2, 'Pinecone Overview', 'Pinecone provides cloud-native vector search and retrieval.', 'database'),  
(3, 'Search Algorithms', 'BM25 ranks documents by keyword overlap; semantic search uses vectors.', 'search'); **Step 3: Register the table with pinecone.track_docs  
**  
Call pinecone.track_docs and declare the embed configuration on the text column: SELECT pinecone.track_docs('articles',  
text_columns => '{  
"title": {"language": "en"},  
"body": {"language": "en", "embed": {"model": "gemini-embedding-2"}}  
}',  
metadata_columns => ARRAY['category']  
); track_docs creates a Pinecone document index where body is indexed for both BM25 full-text search and hosted gemini-embedding-2 vector embeddings. Statement level triggers record future INSERT, UPDATE and DELETE operations into an outbox. A background worker batches and streams rows asynchronously to Pinecone, where the embedding model runs server side. **Step 4: Execute hybrid and semantic searches  
**  
pg_pinecone provides two complementary ways to run hybrid search depending on your retrieval strategy. Here's the approach of semantic search with exact hard filters which ranks by conceptual meaning using the hosted embedding model, but restricts candidates to an exact metadata match: SELECT a.id, a.title, a.body, s.score  
FROM pinecone.search_docs(  
'articles',  
'information retrieval and machine learning',  
mode => 'embed',  
filter => '{"category": {"$eq": "search"}}',  
k => 10  
) s  
JOIN articles a ON a.id = s.id::bigint  
ORDER BY s.rank; All in all, pg_pinecone is a valuable addition to the Postgres ecosystem, because it delivers fast, accurate vector search with integrated metadata filtering and a fraction of the memory footprint directly inside PostgreSQL.

#### More Information

[Pinecone for Postgres: one pgvector column, three engines](<https://github.com/pinecone-io/pg_pinecone>)

#### Related Articles

[pg-java Is The Modern JDBC Driver For PostgreSQL](<https://www.i-programmer.info/news/80-java/19216-pg-java-is-the-modern-jdbc-driver-for-postgresql.html>) __ To be informed about new articles on I Programmer, sign up for our [weekly newsletter](<https://www.i-programmer.info/edit-profile.html?layout=form>),[ ](<https://s3.amazonaws.com/com.alexa.toolbar/atbp/hfdfGO/download/index.htm>)subscribe to the [RSS feed](<https://www.i-programmer.info/component/ninjarsssyndicator/?feed_id=3&format=raw>) and follow us on [Facebook](<http://www.facebook.com/pages/iProgrammer/127140977307932#%21/pages/iProgrammer/127140977307932?v=wall>) or [Linkedin](<http://www.linkedin.com/company/i-programmer>). [](<https://amzn.to/4iJFqTH>)