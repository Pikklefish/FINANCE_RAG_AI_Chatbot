
from langchain_core.documents import Document
from typing import List, Tuple
#Modified: removed inputs.libraries


class HallucinationChecker:
    
    # Required:  NONE
    # Modifies:  NONE
    # Returns:   NONE
    def __init__(self):
        pass
    
    # Required:  answer (str)
    # Modifies:  NONE
    # Returns:   True if "answer uncertain" in returned response
    def _is_uncertain(self, answer: str) -> bool:
        return "answer uncertain" in answer.lower() #(.lower() converts it to lower case)
    
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
        
        
        