import os
import sys
import logging
import git
import numpy as np
from datetime import datetime
from typing import List, Optional, Dict, Any
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                               QTextEdit, QLineEdit, QPushButton, QHBoxLayout)
from PySide6.QtCore import Qt
from haystack import Pipeline
from haystack.schema import Document
from haystack.document_stores.base import BaseDocumentStore
from haystack.nodes.retriever import EmbeddingRetriever
from couchdb import Server, Database, ResourceNotFound
from llama_cpp import Llama
from typing import List, Optional, Dict, Any
from haystack import BaseComponent

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
CONFIG = {
    "couchdb_url": "http://admin:441597@localhost:5984",
    "repo_path": "/media/hannesn/Hannes/WODA.2023/_var_dev/EAMD.ucp",
    "embedding_model": "sentence-transformers/all-mpnet-base-v2",
    "llm_model_path": "/media/hannesn/Hannes/gpt4all/Meta-Llama-3-8B-Instruct.Q4_0.gguf",
    "max_doc_size": 4 * 1024 * 1024,  # 4 MB
    "batch_size": 50
}

class CouchDBDocumentStore(BaseDocumentStore):
    def __init__(self, db, index: str = "default", embedding_dim: int = 768):
        super().__init__()
        self.db = db
        self.embedding_dim = embedding_dim
        self.max_doc_size = CONFIG["max_doc_size"]
        self.index = index

    def write_documents(self, documents: List[Document], index: Optional[str] = None) -> int:
        """Write documents to CouchDB."""
        if index and index != self.index:
            raise ValueError(f"Invalid index '{index}'. This store uses index '{self.index}'.")
        
        written_docs_count = 0

        for doc in documents:
            doc_content = doc.content
            doc_size = len(doc_content.encode("utf-8"))

            if doc_size > self.max_doc_size:
                chunks = self._split_document(doc_content)
                for idx, chunk in enumerate(chunks):
                    chunk_id = f"{doc.id}_chunk_{idx}"
                    self._save_document(
                        chunk_id,
                        chunk,
                        {**doc.meta, "chunk_index": idx, "original_id": doc.id},
                        doc.embedding,
                    )
                    written_docs_count += 1
            else:
                self._save_document(doc.id, doc_content, doc.meta, doc.embedding)
                written_docs_count += 1

        return written_docs_count

    def _split_document(self, content: str) -> List[str]:
        """Split document into byte-sized chunks."""
        encoded = content.encode("utf-8")
        return [
            encoded[i : i + self.max_doc_size].decode("utf-8", "ignore")
            for i in range(0, len(encoded), self.max_doc_size)
        ]

    def _save_document(self, doc_id: str, content: str, meta: Dict, embedding: Optional[np.ndarray]):
        doc_dict = {
            "_id": doc_id,
            "content": content,
            "meta": meta,
            "embedding": embedding.tolist() if embedding is not None else None,
        }

        try:
            existing = self.db[doc_id]
            doc_dict["_rev"] = existing["_rev"]
        except ResourceNotFound:
            pass

        self.db.save(doc_dict)

    def get_all_documents(self, index: Optional[str] = None) -> List[Document]:
        """Retrieve all documents from CouchDB."""
        return [
            self._couchdoc_to_haystack(row.doc)
            for row in self.db.view("_all_docs", include_docs=True)
            if not row.id.startswith("_design")
        ]

    def _couchdoc_to_haystack(self, couchdoc: Dict) -> Document:
        """Convert a CouchDB document to a Haystack Document."""
        return Document(
            content=couchdoc["content"],
            meta=couchdoc.get("meta", {}),
            embedding=np.array(couchdoc["embedding"]) if "embedding" in couchdoc else None,
            id=couchdoc["_id"],
        )

    # Required Abstract Methods
    def get_all_documents_generator(self, index: Optional[str] = None):
        """Generator for retrieving all documents."""
        for row in self.db.view("_all_docs", include_docs=True):
            if not row.id.startswith("_design"):
                yield self._couchdoc_to_haystack(row.doc)

    def delete_documents(self, index: Optional[str] = None):
        """Delete all documents."""
        for row in self.db.view("_all_docs", include_docs=True):
            if not row.id.startswith("_design"):
                self.db.delete(row["doc"])

    def get_document_by_id(self, id: str, index: Optional[str] = None) -> Optional[Document]:
        """Retrieve a document by its ID."""
        try:
            doc = self.db[id]
            return self._couchdoc_to_haystack(doc)
        except ResourceNotFound:
            return None

    def get_documents_by_id(self, ids: List[str], index: Optional[str] = None) -> List[Document]:
        """Retrieve multiple documents by their IDs."""
        return [self.get_document_by_id(id) for id in ids]

    def get_document_count(self, index: Optional[str] = None) -> int:
        """Get the total number of documents."""
        return len([row for row in self.db.view("_all_docs") if not row.id.startswith("_design")])

    def query_by_embedding(
        self, query_emb: np.ndarray, top_k: int = 10, index: Optional[str] = None, 
        filters: Optional[Dict[str, Any]] = None, headers: Optional[Dict[str, str]] = None,
        scale_score: bool = None
    ):
        """Perform a manual cosine similarity search over stored embeddings."""

        if filters:
            logger.warning("Filtering is not implemented for CouchDBDocumentStore, ignoring 'filters'.")
        
        if headers:
            logger.warning("Headers are not implemented for CouchDBDocumentStore, ignoring 'headers'.")

        if scale_score is not None:
            logger.warning("Scale score is not implemented for CouchDBDocumentStore, ignoring 'scale_score'.")

        # Retrieve all documents with embeddings
        docs = [
            self._couchdoc_to_haystack(row.doc)
            for row in self.db.view("_all_docs", include_docs=True)
            if not row.id.startswith("_design") and "embedding" in row.doc
        ]

        if not docs:
            return [], "output_1"  # No documents found

        # Ensure query embedding is not None
        if query_emb is None:
            logger.error("Query embedding is None. Cannot perform similarity search.")
            return [], "output_1"

        query_emb = query_emb / np.linalg.norm(query_emb)  # Normalize query embedding
        scores = []
        
        for doc in docs:
            if doc.embedding is None:
                continue  # Skip documents without embeddings

            doc_emb = np.array(doc.embedding)
            
            if doc_emb is None or np.linalg.norm(doc_emb) == 0:
                continue  # Skip invalid embeddings

            doc_emb = doc_emb / np.linalg.norm(doc_emb)  # Normalize document embedding
            score = np.dot(query_emb, doc_emb)  # Cosine similarity
            scores.append((doc, score))

        # Sort by score and return top_k
        scores.sort(key=lambda x: x[1], reverse=True)
        top_docs = [doc for doc, _ in scores[:top_k]]

        return top_docs, "output_1"

    def update_document_meta(self, id: str, meta: Dict[str, Any], index: Optional[str] = None):
        """Update metadata for a specific document."""
        try:
            doc = self.db[id]
            doc["meta"].update(meta)
            self.db.save(doc)
        except ResourceNotFound:
            logger.error(f"Document with ID {id} not found.")

    def delete_index(self, index: Optional[str] = None):
        """Raise error if index deletion is attempted."""
        raise NotImplementedError("Index deletion is not supported for CouchDBDocumentStore.")

    def write_labels(self, labels: List[Dict[str, Any]], index: Optional[str] = None):
        """Raise error if label writing is attempted."""
        raise NotImplementedError("Label writing is not supported for CouchDBDocumentStore.")

    def get_all_labels(self, index: Optional[str] = None) -> List[Dict[str, Any]]:
        """Raise error if label retrieval is attempted."""
        raise NotImplementedError("Retrieving labels is not supported for CouchDBDocumentStore.")

    def get_label_count(self, index: Optional[str] = None) -> int:
        """Raise error if label counting is attempted."""
        raise NotImplementedError("Label counting is not supported for CouchDBDocumentStore.")

    def delete_labels(self, index: Optional[str] = None):
        """Raise error if label deletion is attempted."""
        raise NotImplementedError("Label deletion is not supported for CouchDBDocumentStore.")

    def _create_document_field_map(self):
        """Define the document field map."""
        return {"content": "content", "meta": "meta", "embedding": "embedding"}

class GitRepoLoader:
    def __init__(self, document_store: CouchDBDocumentStore, repo_path: str):
        self.document_store = document_store
        self.repo_path = repo_path
        self.repo = git.Repo(repo_path)
        self.file_types = ('.md', '.txt', '.py', '.js', '.html', '.css')

    def load_documents(self):
        documents = []
        file_count = 0

        for root, _, files in os.walk(self.repo_path):
            for file in files:
                if file.endswith(self.file_types):
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                            try:
                                last_commit = self.repo.git.log('-1', '--format=%H', file_path)
                            except git.exc.GitCommandError:
                                last_commit = "Not committed yet"
                            
                            doc = Document(
                                content=content,
                                meta={
                                    'path': file_path,
                                    'filename': file,
                                    'last_commit': last_commit,
                                    'file_type': os.path.splitext(file)[1]
                                }
                            )
                            documents.append(doc)
                            file_count += 1

                            if len(documents) >= CONFIG["batch_size"]:
                                self.document_store.write_documents(documents)
                                documents = []

                    except Exception as e:
                        logger.error(f"Error loading {file_path}: {str(e)}")

        if documents:
            self.document_store.write_documents(documents)
        logger.info(f"Total files processed: {file_count}")

class LlamaNode(BaseComponent):
    outgoing_edges = 1  # Add this line to define the number of outgoing edges

    def __init__(self, model_path: str, max_tokens: int = 500):
        super().__init__()
        self.llm = Llama(
            model_path=model_path,
            n_ctx=2048,
            n_threads=4,
            verbose=False
        )
        self.max_tokens = max_tokens
        self.system_prompt = """You are a helpful coding assistant. Use the provided context to answer 
        questions about the codebase. Be concise and specific, including relevant code snippets when 
        appropriate."""

    def run(self, query: str, documents: Optional[List[Document]] = None, **kwargs):
        """
        Run the LlamaNode on the provided query and documents.

        :param query: The user query.
        :param documents: Optional list of documents providing context.
        :param kwargs: Additional arguments.
        :return: A dictionary containing the generated answer.
        """
        context = "\n".join([doc.content for doc in documents]) if documents else ""
        prompt = f"""<|system|>
        {self.system_prompt}
        
        Context:
        {context}
        </s>
        <|user|>
        {query}
        </s>
        <|assistant|>"""

        output = self.llm(
            prompt=prompt,
            max_tokens=self.max_tokens,
            temperature=0.7,
            top_p=0.9,
            stop=["</s>"]
        )
        answer = output["choices"][0]["text"].strip()
        return {"answers": [{"answer": answer}]}, "output_1"

    def run_batch(self, queries: List[str], documents: Optional[List[List[Document]]] = None, **kwargs):
        """
        Run the LlamaNode on a batch of queries and documents.

        :param queries: A list of user queries.
        :param documents: A list of lists of documents providing context for each query.
        :param kwargs: Additional arguments.
        :return: A dictionary containing the generated answers for each query.
        """
        results = []
        for query, docs in zip(queries, documents or [[]]):
            result, _ = self.run(query, docs)
            results.append(result["answers"])
        return {"answers": results}, "output_1"

class ChatInterface(QMainWindow):
    def __init__(self, pipeline: Pipeline, chat_db: Database):
        super().__init__()
        self.pipeline = pipeline
        self.chat_db = chat_db
        self.current_session = []
        self.init_ui()
        self.load_chat_history()

    def init_ui(self):
        self.setWindowTitle("Code Assistant")
        self.setGeometry(100, 100, 800, 600)

        # Main widget and layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)

        # Chat history display
        self.chat_history = QTextEdit()
        self.chat_history.setReadOnly(True)
        layout.addWidget(self.chat_history)

        # Input area
        input_layout = QHBoxLayout()
        
        self.user_input = QLineEdit()
        self.user_input.setPlaceholderText("Ask about the codebase...")
        self.user_input.returnPressed.connect(self.send_message)
        input_layout.addWidget(self.user_input, 5)

        self.send_btn = QPushButton("Send")
        self.send_btn.clicked.connect(self.send_message)
        input_layout.addWidget(self.send_btn, 1)

        # Feedback buttons
        feedback_layout = QHBoxLayout()
        self.thumbs_up_btn = QPushButton("👍")
        self.thumbs_up_btn.clicked.connect(lambda: self.save_feedback(1))
        self.thumbs_down_btn = QPushButton("👎")
        self.thumbs_down_btn.clicked.connect(lambda: self.save_feedback(0))
        feedback_layout.addWidget(self.thumbs_up_btn)
        feedback_layout.addWidget(self.thumbs_down_btn)

        layout.addLayout(input_layout)
        layout.addLayout(feedback_layout)

    def load_chat_history(self):
        """Load previous chat history from database"""
        try:
            for row in self.chat_db.view('_all_docs', include_docs=True):
                doc = row.doc
                self.chat_history.append(f"User: {doc['query']}\n")
                self.chat_history.append(f"Assistant: {doc['response']}\n\n")
        except Exception as e:
            logger.error(f"Error loading chat history: {str(e)}")

    def send_message(self):
        """Handle sending of messages"""
        query = self.user_input.text().strip()
        if not query:
            return

        try:
            # Add user message to UI
            self.chat_history.append(f"User: {query}\n")
            self.user_input.clear()

            # Process query
            result = self.pipeline.run(query=query)
            response = result['answers'][0]['answer']

            # Add assistant response to UI
            self.chat_history.append(f"Assistant: {response}\n\n")

            # Save to chat history
            doc = {
                'type': 'chat',
                'timestamp': datetime.now().isoformat(),
                'query': query,
                'response': response
            }
            self.chat_db.save(doc)
            self.current_session.append(doc)

        except Exception as e:
            logger.error(f"Error processing query: {str(e)}")
            self.chat_history.append(f"Error: {str(e)}\n\n")

def initialize_databases():
    """Initialize CouchDB databases for documents and chat history."""
    server = Server(CONFIG["couchdb_url"])
    doc_db = None
    chat_db = None

    # Check for and create the documents database if it doesn't exist
    if "documents" in server:
        logger.info("Database 'documents' already exists. Skipping population.")
        doc_db = server["documents"]
    else:
        logger.info("Database 'documents' does not exist. Creating and populating...")
        doc_db = server.create("documents")

    # Check for and create the chat history database if it doesn't exist
    if "chat_history" in server:
        logger.info("Database 'chat_history' already exists.")
        chat_db = server["chat_history"]
    else:
        logger.info("Database 'chat_history' does not exist. Creating...")
        chat_db = server.create("chat_history")

    return doc_db, chat_db

def populate_documents(document_store, repo_loader):
    """
    Populate the document database only if it is empty.
    This avoids re-loading documents into the database if already populated.
    """
    doc_count = document_store.get_document_count()
    if doc_count > 0:
        logger.info(f"Database already populated with {doc_count} documents. Skipping population.")
    else:
        logger.info("Database is empty. Populating with documents...")
        repo_loader.load_documents()

if __name__ == "__main__":
    # Initialize CouchDB databases
    doc_db, chat_db = initialize_databases()

    # Create the document store and repository loader
    document_store = CouchDBDocumentStore(doc_db)
    repo_loader = GitRepoLoader(document_store, CONFIG["repo_path"])

    # Populate the document database only if needed
    populate_documents(document_store, repo_loader)

    # Initialize the pipeline with retriever and LlamaNode
    retriever = EmbeddingRetriever(
        document_store=document_store,
        embedding_model=CONFIG["embedding_model"]
    )
    pipeline = Pipeline()
    pipeline.add_node(component=retriever, name="Retriever", inputs=["Query"])
    pipeline.add_node(component=LlamaNode(CONFIG["llm_model_path"]), name="Llama", inputs=["Retriever"])

    # Start the application
    app = QApplication(sys.argv)
    window = ChatInterface(pipeline, chat_db)
    window.show()
    sys.exit(app.exec())
