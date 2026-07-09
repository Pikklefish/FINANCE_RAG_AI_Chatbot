# RAG-Chatbot for Finance Documents

## Project Overview
Architected and deployed a containerized (DOCKER), production-ready Retrieval-Augmented Generation (RAG) chatbot for the finance sector. Built with `Python`, `LangChain`, `ChromaDB`, and the `Gemini 2.0 Flash API`, the system ingests unstructured financial PDFs and executes highly deterministic, context-grounded queries. To strictly mitigate the risk of financial hallucinations, the architecture features a custom "LLM-as-a-Judge" heuristic safety layer that intercepts unverified outputs, enforces strict citation tracking, and ensures users receive only factually grounded insights.

## File Structure
    A. /app
        1. config.py
        2. hallucination.py
        3. ingestor.py
        4. main.py
        5. prompt.py
        7. rag_pipeline.py
    B. /tests
        1. test_config.py
        2. 
    C. .dockerignore
    D. .env.example
    E. .gitignore
    F. docker-compose.yml
    G. Dockerfile
    H. requirements.txt


## `config.py`
### Purpose 
Functioned as the centralized hyperparameter registry and environment gatekeeper for the RAG architecture. It decoupled configuration variables from execution logic, ensuring the application remained modular and easily configurable for testing and evaluation.

### Functionality
1. **LLM Determinism (`TEMPERATURE = 0.1`)**: Configured near absolute zero to suppress LLM randomness. In the finance sector, where factual consistency is paramount, this parameter acted as a strict "reality factor" to force deterministic outputs.
2. **Cost & Compute Optimization**: `MAX_TOKEN = 700` imposed a strict upper bound on generation length to prevent infinite context loops and manage API expenditure (budgeted for ~125 free-tier queries/day).
    * **A.** `HALLUCINATION_CHECK_MAX_TOKEN = 10`: Optimized the secondary Judge LLM (used in `hallucination.py`) by restricting its output window. Since the judge only returned binary assertions (YES/NO), this tight cap prevented unnecessary compute overhead.
3. **Context Window Management (`MEMORY_MAX_TOKEN_LIMIT = 3000`)**: Implemented a sliding window truncation algorithm for LangChain conversation memory. It aggressively pruned older chat history to ensure prompts and retrieved context never exceeded context window limits or token budgets.
4. **Retrieval & Semantic Density**: `CHUNK_SIZE = 1024` and `CHUNK_OVERLAP = 154` defined the splitting heuristic for `PyPDFLoader`. The 1024-character size guaranteed sufficient semantic density for optimal speed and accuracy, while the ~15% overlap acted as a safety buffer against critical data loss at arbitrary splitting boundaries.
5. **Fail-Fast Validation (`validate()`)**: Statically verified the successful loading of required Gemini API environment variables upon initialization.

## `hallucination.py`
### Purpose 
Due to the critical cost of hallucinations in the finance sector, this module served as a post-generation safety layer. It evaluated the primary LLM's response for uncertainty and strictly enforced structural citation requirements before outputting data to the user.

### Functionality
1. **LLM-as-a-Judge Pattern (`_is_uncertain`)**: Rather than relying on rigid string matching, this module instantiated a secondary, highly constrained Gemini instance (`temperature = 0.0`, `MAX_TOKENS = 10`). This "Judge LLM" evaluated the semantic intent of the primary model's output to determine if it expressed uncertainty, returning a deterministic boolean flag.
2. **Gating System (`check`)**: Implemented a three-level risk assessment mechanism to categorize outputs.
    * **A. State 1 (Safe)**: The model explicitly admitted ignorance, and the response passed (encouraging safe failure modes). 
    * **B. State 2 (High Risk `no_docs`)**: If the retriever failed to surface context but the LLM still generated an answer, the system intercepted it and warned the user of a potential hallucination.
    * **C. State 3 (Warning `warned`)**: If explicit citation markers (`[source:`) were missing, the system warned the user to independently verify the generated values.
3. **Source Formatting (`format_sources`)**: Deduplicated and formatted sources to allow users to efficiently verify the location of retrieved documents.

## `ingestor.py`
### Purpose 
This module functioned as the primary ETL (Extract, Transform, Load) pipeline for the architecture. It converted unstructured binary PDF data into vector embeddings while strictly preserving document metadata.

### Functionality
1. **Secure File Abstraction (`_load_file`)**: Because Streamlit provided file uploads as in-memory byte streams, the system utilized the `tempfile` library to securely write this data to the host operating system's temporary directory, allowing `PyPDFLoader` to parse the document.
2. **Deterministic Resource Management**: To prevent memory leaks, temporary file deletion was strictly enforced within a `finally` execution block, ensuring OS-level cleanup even if the parsing algorithm failed.
3. **Metadata Mutation**: The ingestion engine systematically intercepted parsed documents to inject the original filename and shift the default zero-indexed page numbers to a one-indexed standard, aligning downstream UI citations with human-readable formats.
4. **Semantic Chunking (`_split_documents`)**: A `RecursiveCharacterTextSplitter` divided parsed pages into discrete semantic nodes based on predefined hyperparameters (`CHUNK_SIZE` and `CHUNK_OVERLAP`), maintaining optimal informational density and preventing context fragmentation.
5. **Vectorization and Ephemeral Storage (`ingest`)**: The `GoogleGenerativeAIEmbeddings` engine translated textual chunks into dense mathematical vectors, which were subsequently loaded into an ephemeral, in-memory ChromaDB instance for rapid approximate nearest neighbor retrieval.
6. **State Encapsulation (`get_vectorstore`)**: The module protected vector database integrity via a safe accessor method, raising an explicit `ValueError` if queried before ingestion successfully completed.

## `main.py`
### Purpose 
This module served as the application's reactive presentation layer and central execution orchestrator. It bridged the LangChain backend with the Streamlit UI, managed ephemeral state, enforced environment validation, and synchronized the data flow from input to evaluation.

### Functionality
1. **Initialization**: Executed a strict bootstrapping sequence (`Config.validate()`) prior to rendering. This enforced a "fail-fast" paradigm, halting the application immediately if critical environment variables were missing.
2. **Reactive State Architecture (`st.session_state`)**: Utilized a persistent session state dictionary to encapsulate critical singletons (`DocumentIngestor`, `RAGPipeline`, `HallucinationChecker`), ensuring expensive database instantiations occurred only once per session despite Streamlit's top-down re-execution model.
3. **Execution Context & Session Isolation**: Extracted a unique thread identifier (`session_id`) via `get_script_run_ctx()` and passed it directly to the LangChain graph, strictly isolating conversation histories across concurrent client sessions.
4. **Asynchronous-Style UI Blocking**: Implemented tactical UI mutability to manage latency. The chat input dynamically locked (`disabled=True`) when vector context was absent, and rendering spinners masked the latency of PDF chunking and LLM inference.
5. **Orchestrated Data Pipeline**: Managed the user query lifecycle through five sequential phases: capturing user input, executing the `RAGPipeline`, intercepting output via the `HallucinationChecker`, formatting metadata citations, and rendering the final validated response and warnings to the UI.

## `prompt.py`
### Purpose 
This module acted as the declarative instruction layer for the LLM ecosystem. It utilized explicit prompt engineering primitives to strictly constrain the model's latent space, enforcing a deterministic, cautious persona suitable for finance while mitigating ungrounded generation.

### Functionality
1. **Persistent Persona Enforcement (`SYSTEM_PROMPT`)**: Established foundational behavioral boundaries using explicit negative constraints (e.g., "Never use outside knowledge," "Never provide investment advice"). It engineered a predictable failure state by dictating a specific failure string rather than allowing probabilistic guessing.
2. **Context-Bound Generation (`QA_PROMPT_TEMPLATE`)**: Functioned as the operational payload during retrieval. It utilized variable injection (`{context}`, `{question}`) and exploited the LLM's "recency bias" by reiterating strict constraints immediately adjacent to the user's question, ensuring injected vector context superseded pre-trained memory.
3. **Semantic Output Forcing (`JUDGE_PROMPT_TEMPLATE`)**: Engineered for the `HallucinationChecker` using a zero-shot classification pattern. By explicitly commanding the secondary LLM to limit its vocabulary to "YES or NO", it collapsed natural language variability into a binary output, enabling deterministic programmatic parsing.

## `rag_pipeline.py`
### Purpose 
This module served as the central cognitive engine of the architecture. It integrated vectorized data retrieval, prompt engineering, LLM inference, and stateful conversational memory into a unified pipeline using LangChain Expression Language (LCEL).

### Functionality
1. **Contextual Retrieval (`_build_retriever`)**: Transformed the injected Chroma database into a dynamic retrieval interface. It executed dense vector similarity searches restricted to the top $K$ semantic matches (`RETRIEVAL_K`), guaranteeing context relevance without token bloat.
2. **Citation Pre-Processing (`_format_docs`)**: Programmatically concatenated retrieved vector nodes prior to model generation, injecting source filenames and page numbers directly into the text payload to force metadata-grounded assertions.
3. **Declarative Execution Graph (`core_chain`)**: Constructed a predictable Directed Acyclic Graph (DAG) using LCEL. The pipeline intercepted the user query, routed it concurrently to the retriever, formatted the context, injected it into the `ChatPromptTemplate`, and piped it directly to the Gemini inference engine.
4. **Stateful Memory Isolation (`RunnableWithMessageHistory`)**: Functioned as state-injection middleware. It mapped an `InMemoryChatMessageHistory` instance to a unique `session_id`, automating the injection and extraction of chat histories to prevent cross-session data leakage.
5. **Synchronous Inference & Payload Surfacing (`query`)**: Acted as the public execution interface. It invoked the retrieval-augmented generation loop and concurrently surfaced both the generated string and raw `Document` objects for downstream heuristic evaluation.


## Tools Used
1. Python (programming language)
2. Langchain (framework)
3. Docker (Container)
4. Chroma DB (Databse)
5. Streamlit (Frontend UI)

## Design choices
1. Docker Containerization:
    * A. Why?: Easy resource & dependency management. The project becomes future proof and can be easily integrated to a full CI/CD pipeline (testing, deployment and evaluation).
    * B. Python 3.12 SLIM: By downloading only the necessary Python libraries it minimizes the Contianer Image thus saving resources. 

## Testing / Evaluation

## Deployment

## Troubleshooting / Errors
1. Gemini API 429 Error: First attempt to send a query the Gemini API returned a 429 Error
    * Hypothesis: the chunk size (1024 * 4 chunks) was too big

## Future Improvement