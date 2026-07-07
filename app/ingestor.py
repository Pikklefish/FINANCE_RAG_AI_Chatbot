import os
import tempfile
from langchain_community.document_loaders import PyPDFLoader 
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document
from typing import List
from app.config import Config


class DocumentIngestor:
    
    #Required: none
    #Modifies: self.embedding_model, self.vectorstore
    #Effect: none
    def __init__(self):
        self.embedding_model = self._get_embedding_model()
        self.vectorstore = None

    #Required:none
    #Modifies: none
    #Effect: model with embedding_model
    def _get_embedding_model(self) -> GoogleGenerativeAIEmbeddings:
        return GoogleGenerativeAIEmbeddings(
        model=Config.EMBEDDING_MODEL
    )

    #Requried: Uplaoded pdf file (streamlit) - must be pdf
    #Modifies: none
    #Effect: List[Document] — one Document per page with source + page metadata attached
    def _load_file(self, uploaded_file):
        #step 1: get uploaded file and write to temp file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
            temp_file.write(uploaded_file.read())
            temp_file_path = temp_file.name #give it temp file path/name
            
        try:
            #step 2: load temp file with pypdfloader
            loader = PyPDFLoader(temp_file_path)
            docs = loader.load()

            #step 3: attach file name to each doc's metadata
            filename = uploaded_file.name
        
            for doc in docs: #PyPDF already adds metadata to the doc so we just need to update the anme and correct page count
                doc.metadata["source"] = filename
                
                if "page" in doc.metadata:
                    doc.metadata["page"] = doc.metadata["page"] + 1  #convert start from 0 to 1

            return docs

        # Handle errors
        except Exception as e:
            # raise a clean error with context
            raise ValueError(f"Failed to load PDF '{uploaded_file.name}': {e}")

        #Step 4: always delete temp docs
        finally:
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)

    #Required: List[docs] passed from _load_file()
    #Modifies: List[docs] splits its content [docs] into smaller chunks
    #Effect: List[docs] split into smaller chunks
    def _split_documents(self, docs: List[Document]) -> List[Document]:
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=Config.CHUNK_SIZE,
            chunk_overlap=Config.CHUNK_OVERLAP
        )

        chunks = splitter.split_documents(docs)
        return chunks


    #Required:  uploaded_file (Streamlit UploadedFile)
    #Modifies:  self.vectorstore — populates it with embedded chunks
    #Returns:   int — number of chunks ingested (so UI can display it)
    def ingest(self, uploaded_file):
        # Step 1. load the document
        docs = self._load_file(uploaded_file)

        # Step 2. chunk the document
        chunks = self._split_documents(docs)

        # Step 3. Store in Chroma DB
        self.vectorstore = Chroma.from_documents(
            documents=chunks,         # the chunks
            embedding=self.embedding_model        # the embedding model
            )

        # Step 4. Return chunk count
        return len(chunks) 
    

    #Required:  none
    #Modifies:  none
    #Returns:   Chroma instance
    def get_vectorstore(self):
        if self.vectorstore is None:
            raise ValueError("No documents ingested yet. Call ingest() first.")
        return self.vectorstore

