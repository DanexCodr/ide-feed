MongoDB engineers juggling many implementations of many specs.

At MongoDB, we develop a dozen client libraries (“drivers”) in a dozen programming languages. A few wrap shared cores written in C or Java, but mostly they’re rewrites in their target languages: the JavaScript Driver is pure JavaScript, the Rust Driver is pure Rust, and so on. Building the drivers this way is a big commitment. Lots of database companies just write their client in C and make thin wrappers in various languages. Our way is harder but, in my opinion, better. Our drivers are easier to install, their APIs are more idiomatic in each language, and they participate normally in each language’s runtime: its threading model or async loop, its garbage collection, etc. This is only possible because we keep developing *native* drivers in each language.

But then, how do we ensure all our drivers’ behaviors and APIs are consistent? Or, that they’re *appropriately* consistent or inconsistent, according to the conventions of their target languages? Obviously, Python methods are snake_cased and Java methods are camelCased, but MongoDB drivers should have the same basic API in all languages, spelling aside. Node concurrency is async and C concurrency uses threads, but the meaning of [causal consistency](https://emptysqua.re/blog/how-to-use-mongodb-causal-consistency/) should be the same in all drivers.

# In Search of a Tolerable Test Language

[#](https://emptysqua.re/blog/polyglots-dilemma/#in-search-of-a-tolerable-test-language)

I joined MongoDB as a Python driver engineer in November 2011. Looking back through my emails, I see that we were intensely debating how to standardize our drivers from the moment I arrived. Some engineers were writing Java Driver tests in Cucumber, a “behavior-driven development” syntax, like this:

```cucumber
Scenario: Exclude a field from query results
  Given collection "users" contains documents
    """
    {"_id": 1, "name": "alice", "password": "hunter2"}
    {"_id": 2, "name": "bob",   "password": "swordfish"}
    """
  When find documents by
    """
    {"name": "alice"}
    """
  And return fields
    """
    {"password": false}
    """
  Then the result should be
    """
    {"_id": 1, "name": "alice"}
    """
```

My very first task at MongoDB was researching whether we could write test-runners for these Cucumber tests in Python, Ruby, and our other languages. I instantly learned that my second task was dealing with my colleagues’ revulsion to Cucumber’s syntax. One engineer wrote that if we replaced his handwritten tests with Cucumber, he’d “have no part in doing it or supporting the resulting disaster.” (I clarified that we weren’t going to replace tests, only complement them.) Our founder Eliot Horowitz encouraged us to make a shared test suite, but he thought Cucumber specifically was “hilarious.”

We gave up on Cucumber. A few years later, I was involved in a new feature, [specifying how drivers measure and respond to network latency](https://specifications.readthedocs.io/en/latest/server-selection/server-selection/#localthresholdms). I observed that the English spec of the feature could be misunderstood, and some drivers implemented it differently. Once again, Eliot proposed a shared test suite. This time, we avoided Cucumber. We started to develop a custom test language on top of YAML instead. For details, see [my conference talk or blog post about YAML tests](https://emptysqua.re/blog/cat-herds-crook/), with Samantha Ritter.

# The Unreasonable Effectiveness of YAML

[#](https://emptysqua.re/blog/polyglots-dilemma/#the-unreasonable-effectiveness-of-yaml)

Testing drivers with YAML is one of the most successful projects I’ve ever been part of. In the 11 years (nearly 12 now) since we started writing YAML tests, the MongoDB drivers have all converged to a shared API and shared set of behaviors. They’re as similar as they should be, with consciously-chosen variations to fit each language’s idioms and conventions. [I left the Drivers team a while ago](https://emptysqua.re/blog/choosing-the-adventurous-route-video/), but the specification and YAML testing process is going stronger than ever. They now have a Unified Test Format, built on YAML, that can test drivers’ conformance to a dozen different specs. The specs cover how drivers read and write documents, how they retry failed commands, how they start and end transactions, how they encrypt private fields client-side, and lots of other intricate behaviors. Nearly 1,500 YAML files ensure that all these independent code bases implement the same protocols.

Here’s an example of a modern Unified Test Format file. It tests that a driver [auto-retries](https://emptysqua.re/blog/driver-features-for-mongodb-3-6/#retryable-writes) the `update` command after a network error:

```yaml
schemaVersion: "1.4"
runOnRequirements:
  - {minServerVersion: "4.4", topologies: [replicaset]}
createEntities:
  - client:
      id: &client client0
      observeEvents:
        - commandStartedEvent
        - poolClearedEvent
        - serverDescriptionChangedEvent
  - database:
      id: &db db0
      client: *client
      databaseName: &dbName mydb
  - collection:
      id: &coll coll0
      database: *db
      collectionName: &collName mycoll
initialData:
  - collectionName: *collName
    databaseName: *dbName
    documents: [{_id: 1, x: 1}]
tests:
  - description: "updateOne retries after network error,
                  exactly-once execution"
    operations:
      - name: failPoint
        object: testRunner
        arguments:
          client: *client
          failPoint:
            configureFailPoint: failCommand
            mode: {times: 1}
            data:
              failCommands: [update]
              closeConnection: true
      - name: updateOne
        object: *coll
        arguments:
          filter: {_id: 1}
          update: {$inc: {x: 1}}
        expectResult:
          matchedCount: 1
          modifiedCount: 1
          upsertedCount: 0
      - name: waitForEvent
        object: testRunner
        arguments:
          client: *client
          event:
            serverDescriptionChangedEvent:
              newDescription: {type: Unknown}
          count: 1
    expectEvents:
      - client: *client
        eventType: command
        events:
          - commandStartedEvent: {commandName: update}
          - commandStartedEvent: {commandName: update}
      - client: *client
        eventType: cmap
        events: [{poolClearedEvent: {}}]
    outcome:
      - collectionName: *collName
        databaseName: *dbName
        documents: [{_id: 1, x: 2}] # x incremented once
```

For each of our drivers, we implement a *test runner* which can interpret this syntax and call APIs on the driver being tested. The test runner creates two MongoClient objects: the MongoClient under test, and an “internal” MongoClient for sending side-channel commands to the server (see the `failPoint` below).

`schemaVersion` tells the test runner which features the file uses, so an old runner can skip a file it wouldn’t understand instead of failing it. We use JSON Schema to check each YAML test has the proper syntax for its version of the Unified Test Format.

`runOnRequirements` tells the test runner to skip the file unless the MongoDB server deployment matches—here, a replica set running MongoDB 4.4 or later.

`createEntities` builds an *entity map*: a client, a database, and a collection, named with YAML anchors (`&client`) so later operations can refer to them by alias (`*client`). This not only avoids repetition, it means YAML test runners can store and retrieve objects in the entity map, like assigning objects to variables in a real programming language.

`initialData` puts one document in the collection before the test starts. Then the operations run in order:

- failPoint tells the server to close the connection the next time it receives an update. The test runner uses the internal MongoClient for this so it doesn’t touch the MongoClient under test.
- updateOne tells the test runner to call the updateOne API on the MongoClient under test. In Python this is spelled update_one, in C it’s mongoc_collection_update_one, etc. Each driver’s test runner knows how to translate YAML into the driver’s API. The expectResult field asserts what the call returns. In this test, the driver tries to update a doc, it gets a network error from the fail point, it reconnects and retries, and succeeds, returning modifiedCount: 1.
- waitForEvent blocks until the driver has noticed the server closed the connection. (In this test, that happens earlier during updateOne, so the test runner won’t actually block on this line.) The driver handles the network error by marking the server’s type as Unknown, meaning the driver has to figure out the server’s status once it reconnects.
- expectEvents checks that the driver sent two update commands on the wire, meaning it retried the write exactly once, plus there was a poolClearedEvent showing the driver discarded all its connections after the network error.
- outcome reads the collection back to confirm x was incremented exactly once—the retry didn’t apply the update again.

This example shows lots of exciting features! The Unified Test Format lets all the drivers share a test suite. We can prove they all act the same by publishing tests they must all pass. We can update a spec, and force all the drivers to comply with the change, by publishing changes to the shared tests and watching all outdated drivers fail.

Additionally, this test is checking *hidden* behaviors that ordinary integration tests couldn’t observe. We use `failPoint` to make the server close the connection, so we can exercise the driver’s auto-retry logic. From the API surface, retries are invisible—that’s the point. But this YAML test triggers a retry and tests three hidden behaviors: the driver retries exactly once, it marks the server type `Unknown`, and it clears its connection pool. We could assert the entire contents of the two `update` commands the driver sends on the wire, if we wanted to.

# Results

[#](https://emptysqua.re/blog/polyglots-dilemma/#results)

The Unified Test Format has saved us tens of thousands of lines of code over the years, and it’s probably saved us from scores of awful bugs. It enforces spec conformance so when you use MongoDB from several programming languages, you get a consistent API and predictable behavior.

Here are some numbers, starting with code savings. When we created the unified format in 2020, we generalized the YAML test format used by lots of different specs into one format to rule them all. Seven drivers replaced their per-spec test runners with a single Unified Test Format runner, and every one of these came out smaller. We cut 22,000 lines total. The Java Driver alone deleted 6,000 lines of test-runner code.

Meanwhile, we added more and more conformance tests. The Unified Test Format corpus went from about a thousand lines in 2021 to 124,000 today. The biggest jumps are when we mechanically ported tests from per-spec YAML formats into the unified format.

Do the tests actually prevent bugs? We identified a natural experiment: Five drivers implemented the CRUD spec years *before* they adopted its YAML tests, which gives us a before and after to compare. We used Claude to classify every resolved ticket in those drivers—6,836 of them—and counted the ones that were genuine violations of the CRUD Spec. Four of the five drivers had a lower bug rate after adopting YAML tests.

Node.js is the embarrassing one: its bug rate went *up*. Years after it adopted the YAML tests we discovered that its `BulkWriteResult` and `BulkWriteError` classes were inconsistent with the specs and the other drivers. Its test runner hadn’t asserted their contents rigorously enough. The Driver Team filed a bunch of bugs and changed the field names over two major releases.

The IEEE International Symposium on Software Reliability Engineering (ISSRE) just accepted my paper about YAML testing, “The Polyglot’s Dilemma: Conformance Testing a Dozen Specs in as Many Languages.” Driver engineers Jeremy Mikola and Jeff Yemin are my coauthors. The paper has more detail about the history of our YAML tests, and it has plenty of stats and lessons. [Check it out, it’s only 6 pages](https://arxiv.org/abs/2608.18039).