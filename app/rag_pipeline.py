from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_chroma import Chroma
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough, RunnableLambda
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.chat_history import InMemoryChatMessageHistory
from operator import itemgetter


from app.config import Config
from app.prompt import SYSTEM_PROMPT, QA_PROMPT_TEMPLATE


class RAGPipeline:


    # Required:  vectorstore (Chroma instance from DocumentIngestor.get_vectorstore())
    # Modifies:  self.retriever, self.llm, self.store, self.chain
    # Returns:   None
    def __init__(self, vectorstore: Chroma):
        self.retriever = self._build_retriever(vectorstore)
        self.llm = self._build_llm()
        self.store = {}       # ← stores chat history per session_id
        self.chain = self._build_chain()
    
    # Required:  GEMINI_MODEL, MAX_TOKENS
    # Modifies:  nothing
    # Returns:   ChatGoogleGenerativeAI instance
    def _build_llm(self) -> ChatGoogleGenerativeAI:
        return ChatGoogleGenerativeAI (
            model=Config.GEMINI_MODEL,
            max_tokens=Config.MAX_TOKENS,
            temperature=Config.TEMPERATURE 
            )

    # Required:  vectorstore (Chroma instance)
    # Modifies:  nothing
    # Returns:   retriever — a ChromaDB retriever configured for similarity search
    def _build_retriever(self, vectorstore: Chroma):
        return vectorstore.as_retriever(
            search_type="similarity",
            search_kwargs={"k": Config.RETRIEVAL_K}
        )

    # Required: Docs Session_ID, SYSTEM/QA PROMPT
    # Modifies: None
    # Returns: Conversation Memory Chain 
    def _build_chain(self):
        def _format_docs(docs):
            return "\n\n".join(
                f"[Source: {doc.metadata.get('source','Unknown')}, "
                f"Page {doc.metadata.get('page', 'Unknown')}]\n{doc.page_content}"
                for doc in docs
            )
        
        def get_session_history(session_id: str) -> InMemoryChatMessageHistory:
            if session_id not in self.store:
                self.store[session_id] = InMemoryChatMessageHistory()
            return self.store[session_id]
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", SYSTEM_PROMPT),
            MessagesPlaceholder("chat_history"),
            ("human", QA_PROMPT_TEMPLATE),
        ])

        # --- THE FIX IS HERE ---
        core_chain = (
            RunnablePassthrough.assign(
                context=itemgetter("question") | self.retriever | RunnableLambda(_format_docs)
            )
            | prompt  
            | self.llm  
            | StrOutputParser() 
        )
        
        return RunnableWithMessageHistory(
            core_chain,
            get_session_history,
            input_messages_key="question",
            history_messages_key="chat_history",
        )
    #Required:  question (str), session_id (str)
    # Modifies:  self.store — RunnableWithMessageHistory appends new turn automatically
    # Returns:   dict with two keys:
    #           "answer"   → clean string response from Gemini
    #           "sources"  → list of source Documents for citations
    
    def query(self, question: str, session_id: str) -> dict:
        
        # Step 1: invoke the chain with question and session_id config
        response = self.chain.invoke(
            {"question": question},                              # the user's question
            config={"configurable": {"session_id": session_id}}    # which session history to use
            )
        
        # Step 2: return answer and sources as a dict
        source_docs = self.retriever.invoke(question)
        return {
            "answer": response,
            "sources": source_docs
            }