# RAG-Chatbot for Finance Documents

## Project Overview
Develope a AI Chatbot specialized for the finance sector. Main goal was to reduce hallucination and deliver a fail-proof system.

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

Centralized hyperparameter registry and environment gatekeeper for the RAG architecture. Decoupled configuration variables from execution logic to ensure the application remains modular, and easily configurable for testing/evaluation.

### Functionality

1. LLM Determinism (`TEMPERATURE = 0.1`): Configured near absolute zero (`gemini-api` temperature variable ranges from `0.0~2.0`) to suppress the LLM's randomness. In the finance sector factual consistency and grounding are paramount and this parameter acts as a strict "reality factor" forcing deterministic outputs.


2. Cost & Compute Optimization: `MAX_TOKEN=700` imposes a strict upper bound on generation length to prevent infinite context loops and manage API expenditure. This cap was determined from token budgeting calculations allowing around 125 queries/day from Gemini API free tier
    A. `HALLUCINATION_CHECK_MAX_TOKEN=10`: Optimized the ***Judge LLM*** (used in `hallucination.py`) by restricting its output window. Since the judge only needs to return binary assertions (YES/NO), a tight token cap prevents unnecessary compute overhead.


3. Context Window Management (`MEMORY_MAX_TOKEN_LIMIT=3000`): Implements a sliding window truncation algorithm for the LangChain conversation memory. It aggressively prunes older chat history to ensure the current prompt and retrieved vector context never exceed the Gemini 2.0 Flash context window limits. Also a strict limit of token budgeting to prevent over usage.


4. Retrieval & Semantic Density: 
    A. `CHUNK_SIZE = 1024` & `CHUNK_OVERLAP = 154`: Defines the splitting heuristic for `PyPDFLoader`. The 1024-character size guarantees sufficient semantic density per vector, while the ~15% overlap acts as a safety buffer to prevent critical financial data loss at arbitrary splitting boundaries.


5. Fail-Fast Validation (`validate()`): Verifies if Gemini-API environment variables have been loaded in.


## Tools Used
### Langchain


### Docker

### Chroma DB

### Streamlit

## Design choices

## Testing / Evaluation

## Deployment

## Troubleshooting

## Future Improvement