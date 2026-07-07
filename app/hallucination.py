
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.documents import Document
from langchain_core.messages import HumanMessage
from typing import List, Tuple

from app.config import Config
from app.prompt import JUDGE_PROMPT_TEMPLATE


class HallucinationChecker:
    
    # Required:  nothing
    # Modifies:  self.llm
    # Returns:   None
    def __init__(self):
        self.llm = self._build_llm()   # ChatGoogleGenerativeAI with HALLUCINATION_CHECK_MAX_TOKENS

    # Required:  GEMINI_MODEL, MAX_TOKENS
    # Modifies:  nothing
    # Returns:   ChatGoogleGenerativeAI instance
    def _build_llm(self) -> ChatGoogleGenerativeAI:
        return ChatGoogleGenerativeAI(
        model=Config.GEMINI_MODEL,
        max_tokens=Config.HALLUCINATION_CHECK_MAX_TOKENS,
        temperature=0.0 
    )
    
    # Required:  answer (str)
    # Modifies:  nothing
    # Returns:   True if model expressed uncertainty, False otherwise
    def _is_uncertain(self, answer: str) -> bool:
        message = HumanMessage(content= JUDGE_PROMPT_TEMPLATE.format(answer=answer))  # the judge prompt
        response = self.llm.invoke([message])
        return "yes" in response.text.lower() #(.lower() converts it to lower case)
    
    # Required:  answer (str), source_docs (List[Document])
    # Modifies:  nothing
    # Returns:   tuple (status: str, warning: str)
    #          status → "ok", "no_docs", or "warned"
    #           warning → "" if ok, warning message if not
    def check(self, answer: str, source_docs: List[Document]) -> Tuple[str, str]:
        # Situation 1 — model said IDK → good behaviour
        if self._is_uncertain(answer):
            return ("ok", "")
        
        # Situation 2 — no chunks retrieved → high risk
        if not source_docs:
            return ("no_docs", "⚠️ No source documents were retrieved. Answer may be inaccurate.")
        
        # Situation 3 — answer has no citations → warn
        if "[source:" not in answer.lower():
            return ("warned", "⚠️ No citations found in answer. Verify figures independently.")
        
        # All checks passed
        return ("ok", "")
        
    # Required:  source_docs (List[Document])
    # Modifies:  nothing
    # Returns:   str — formatted citation block for the UI
    def format_sources(self, source_docs:List[Document]) -> str :
        #1. if no source returned
        if not source_docs:
            return ""   # return empty string — nothing to show
        
        #2. keep track of source and format source
        seen = set()
        lines = ["**Sources retrieved:**"]
        for doc in source_docs:
            source = doc.metadata.get('source', 'unknown') 
            page = doc.metadata.get('page', '?')
            key = f"{source}-{page}"
            if key not in seen:
                seen.add(key)
                lines.append(f"- 📄 `{source}` — Page {page}")
        
        return "\n".join(lines)
        
        
        