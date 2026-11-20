Spring AI is an application framework that brings familiar the Spring design principles of portability, modular design, and auto configuration into the world of Artificial Intelligence. While Python tools like LangChain and LlamaIndex popularized generative AI development, Spring AI was built specifically for the Java and enterprise ecosystem, aiming to connect your internal data, APIs and business logic to AI models without unnecessary complexity. Spring AI does that by providing a unified API across major AI providers (OpenAI, Anthropic, Google GenAI, Amazon Bedrock, Ollama, Mistral and others). Because the underlying mechanics are abstracted behind interfaces like ChatModel, EmbeddingModel and ImageModel, you can switch providers simply by changing a dependency starter in your build file and configuring properties, without rewriting business logic. Back in 2023, we witnessed Spring AIs humble beginnings with version Alpha 0.7.0-SNAPSHOT. Since then the project has grown so much that come 2026 and past week we reached version 2.1.0-RC1 and 2.0.2. So what's new? **1\. Spring AI 2.1.0-RC1 (preview / release candidate)**  
Version 2.1.0-RC1 introduces several foundational features and architectural modernizations:

  * In addition to the OpenAI Responses API, major chat models,including OpenAI (Chat Completions), Anthropic, Google GenAI, Amazon Bedrock Converse, Ollama, Mistral AI and DeepSeek, now produce and consume content natively as ordered MessagePart entries.
  * Preserves reasoning blocks (e.g., Anthropic thinking signatures, Gemini thought signatures) and tool calls in their proper execution order without losing metadata.
  * Configurable replaying of reasoning_content (via spring.ai.openai.chat.replay-reasoning-content) accommodates providers with varying requirements (e.g., DeepSeek requires it, whereas Groq rejects it).
  * Replaces flat message history by introducing Session Memory, ported from the community project.
  * Records conversation history as an append only event log (SessionEvent).
  * Includes repository implementations such as InMemorySessionRepository and JdbcSessionRepository (supporting PostgreSQL, MySQL, MariaDB and H2).
  * Tool call confirmation. Adds interactive confirmation workflows directly to tool calling, allowing human in the loop or programmatic approval before tool execution proceeds.
  * New engine support. Integrates the pure JVM inference engine jinfer, adding dedicated ChatModel, EmbeddingModel, DocumentPostProcessor, TextToSpeechModel and TranscriptionModel implementations.
  * Decision models API. Introduces the DecisionModel abstraction (org.springframework.ai.decision) to choose among predefined categorical outcomes (e.g., yes/no or classification scales) with model reported confidence.

Together with those there was also ETL and Vector store enhancements, as well as audio and multimodal updates. **2\. Spring AI 2.0.2 (Maintenance / stable release)**  
As a patch release for the 2.0.x line, 2.0.2 provides stability, bug fixes and targeted enhancements (which are also rolled into 2.1.0-RC1):

  * Extends Micrometer observations (gen_ai.client.operation) to OpenAI text to speech and transcription, ElevenLabs text to speech and Stability AI image models.
  * Provides metric series and traces for audio generation and transcription pipelines.
  * Corrects the Neo4j chat memory repository schema by establishing updated property indexes (session_id_index and message_idx_index).
  * Fixes PDF readers to properly close underlying resource streams.
  * Addresses token and usage parsing quirks, filter edge cases in vector stores (such as date normalization and numeric boundaries) and non PNG image handling in OpenAI Responses.

How to set it up Setting up Spring AI follows the standard Spring Boot conventions. You can set it up either by starting a fresh project or by adding the necessary dependencies and configurations to an existing project. The quickest way by far is via Spring Initializr:

  1. Go to start.spring.io.
  2. Choose your Project build tool (Maven or Gradle), language (Java) and a compatible Spring Boot version.
  3. Under Dependencies, search for and select your AI provider starter (e.g., OpenAI, Anthropic, or Ollama) and any required storage such as a vector database (e.g., PGvector, Redis, Chroma).
  4. Click Generate, unzip the project and open it in your IDE.

That's it! In the end Spring AI is a good option when dealing with Java, because it brings the portable, modular and auto configured architecture of the Spring ecosystem to generative AI, enabling enterprise Java developers to seamlessly connect internal data, APIs and business logic to foundation models without vendor lock in.

#### More Information

[Spring AI 2.1.0-RC1 and 2.0.2 Available Now](<https://spring.io/blog/2026/10/23/spring-ai-2-1-0-RC1-available-now>)

#### Related Articles

[Introducing Spring AI](<https://www.i-programmer.info/news/105-artificial-intelligence/16702-introducing-spring-ai.html>) __ To be informed about new articles on I Programmer, sign up for our [weekly newsletter](<https://www.i-programmer.info/edit-profile.html?layout=form>),[ ](<https://s3.amazonaws.com/com.alexa.toolbar/atbp/hfdfGO/download/index.htm>)subscribe to the [RSS feed](<https://www.i-programmer.info/component/ninjarsssyndicator/?feed_id=3&format=raw>) and follow us on [Facebook](<http://www.facebook.com/pages/iProgrammer/127140977307932#%21/pages/iProgrammer/127140977307932?v=wall>) or [Linkedin](<http://www.linkedin.com/company/i-programmer>). [](<https://amzn.to/4iJFqTH>)