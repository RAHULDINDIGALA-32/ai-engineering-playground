# ============================================================
# SAMPLE DOCUMENTS
# ============================================================

PLAIN_TEXT = """
LangChain is a framework for developing applications powered by
large language models. It provides tools and abstractions that make
it easier to build applications such as chatbots, question-answering
systems, document analysis systems, and retrieval augmented generation
(RAG) applications.

A typical RAG application starts by collecting documents from different
sources. These documents might come from PDF files, websites, databases,
Word documents, Markdown files, or plain text files. Before the documents
can be used by a language model, they usually need to be processed and
prepared for retrieval.

One important step in this process is document chunking. Chunking means
breaking a large document into smaller pieces called chunks. Instead of
sending an entire document to an embedding model or language model, we
divide the document into manageable sections. Each chunk can then be
converted into an embedding and stored in a vector database.

Choosing the right chunk size is important. If chunks are too large,
retrieval may return more information than necessary and the language
model may have difficulty identifying the relevant information. If
chunks are too small, important context may be lost. Therefore, chunk
size and chunk overlap need to be selected according to the application.

Chunk overlap is the amount of text shared between two consecutive
chunks. For example, if a document is divided into chunks of 500
characters with an overlap of 50 characters, the last 50 characters
of one chunk will also appear at the beginning of the next chunk.
Overlap helps preserve context when an important sentence occurs near
a chunk boundary.

LangChain provides several text splitters for different situations.
The CharacterTextSplitter divides text using a specified separator
and attempts to create chunks of a particular size. It is simple and
useful when the structure of the source text is relatively uniform.

The RecursiveCharacterTextSplitter is one of the most commonly used
splitters for general-purpose RAG applications. Rather than splitting
the text using only one separator, it tries several separators in order.
For example, it may first try to split on paragraphs, then lines, then
sentences or spaces. This approach helps preserve the natural structure
of the document.

Different types of documents can benefit from specialized splitters.
Markdown documents contain headings, lists, code blocks, links, and
other structural elements. MarkdownHeaderTextSplitter can split a
Markdown document based on its heading hierarchy while preserving
metadata about the headers.

HTML documents have a similar hierarchical structure. HTMLHeaderTextSplitter
can split HTML content based on tags such as h1, h2, and h3. The resulting
documents can retain information about the section in which the text
appeared.

Source code should generally be chunked differently from ordinary
prose. PythonCodeTextSplitter understands Python source code and attempts
to create chunks while respecting the structure of the code. This can
be useful when building code-search or code-question-answering systems.

Token-based splitting is another important strategy. TokenTextSplitter
creates chunks based on tokens rather than characters. This can be useful
when the downstream language model or embedding model has token-based
limits.

JSON documents also have a structured format. RecursiveJsonSplitter can
recursively split large JSON objects while attempting to preserve their
structure. This is useful when applications need to retrieve information
from large API responses, configuration files, or structured datasets.

There is no single chunking strategy that works best for every RAG
application. The best strategy depends on the document format, the
embedding model, the retrieval method, and the questions users are
expected to ask. Developers should experiment with chunk sizes and
overlap values and evaluate retrieval quality using representative
questions.

After chunking, each chunk is typically passed to an embedding model.
The resulting vectors are stored in a vector database such as FAISS,
Chroma, Pinecone, or another vector store. When a user asks a question,
the question is embedded and the vector database searches for chunks
that are semantically similar to the question.

The retrieved chunks are then provided as context to a language model.
The language model uses that context to generate an answer. This
pipeline is commonly called retrieval augmented generation because the
model's generation process is augmented with information retrieved from
external documents.

Good chunking can significantly improve the quality of a RAG system.
However, chunking is only one part of the overall retrieval pipeline.
Document cleaning, metadata extraction, embedding quality, vector
database configuration, retrieval algorithms, reranking, and prompt
design can also have a major effect on the final results.

For this reason, chunking should be treated as an engineering decision
rather than simply selecting a default number of characters. A useful
RAG system usually requires testing different strategies against real
documents and real user questions.
"""


MARKDOWN_TEXT = """
# LangChain and RAG

LangChain is a framework for building applications powered by
large language models.

## Document Processing

Documents need to be loaded and processed before they can be used
by a RAG application.

### Document Loading

Documents may come from PDFs, websites, databases, or text files.

### Document Chunking

Large documents are divided into smaller chunks.

Chunk size and overlap are important parameters.

## Retrieval

After chunking, the chunks are converted into embeddings.

### Vector Database

Embeddings can be stored in a vector database.

### Similarity Search

User questions can be compared with stored embeddings.

## Generation

Retrieved chunks are passed to the language model as context.
"""


HTML_TEXT = """
    <html>
        <body>

            <h1>LangChain and RAG</h1>

            <p>
                LangChain is a framework for building applications
                powered by large language models.
            </p>

            <h2>Document Processing</h2>

            <p>
                Documents need to be loaded and processed before they
                can be used in a RAG application.
            </p>

            <h3>Document Loading</h3>

            <p>
                Documents may come from PDFs, websites, databases,
                and text files.
            </p>

            <h3>Document Chunking</h3>

            <p>
                Large documents are divided into smaller chunks.
            </p>

            <h2>Retrieval</h2>

            <p>
                Chunks are converted into embeddings and stored in
                a vector database.
            </p>

            <h2>Generation</h2>

            <p>
                Retrieved chunks are passed to the language model
                as context.
            </p>

        </body>
    </html>
    """


PYTHON_CODE = '''
from langchain_text_splitters import RecursiveCharacterTextSplitter


class DocumentProcessor:

    def __init__(self, chunk_size=500, chunk_overlap=50):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def create_splitter(self):
        return RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
        )

    def split_document(self, text):
        splitter = self.create_splitter()
        return splitter.split_text(text)

    def process_documents(self, documents):
        results = []

        for document in documents:
            chunks = self.split_document(document)
            results.extend(chunks)

        return results


def load_document(path):
    with open(path, "r", encoding="utf-8") as file:
        return file.read()


def main():
    processor = DocumentProcessor(
        chunk_size=500,
        chunk_overlap=50,
    )

    text = load_document("document.txt")

    chunks = processor.split_document(text)

    for index, chunk in enumerate(chunks):
        print(f"Chunk {index + 1}")
        print(chunk)


if __name__ == "__main__":
    main()
'''


JSON_DATA = {
        "application": {
            "name": "RAG Application",
            "description": (
                "An application that retrieves relevant document "
                "chunks and uses them as context for a language model."
            ),
            "document_processing": {
                "loading": {
                    "formats": [
                        "PDF",
                        "HTML",
                        "Markdown",
                        "TXT",
                        "DOCX",
                    ]
                },
                "chunking": {
                    "strategies": [
                        "CharacterTextSplitter",
                        "RecursiveCharacterTextSplitter",
                        "TokenTextSplitter",
                        "MarkdownHeaderTextSplitter",
                        "HTMLHeaderTextSplitter",
                    ],
                    "parameters": {
                        "chunk_size": 500,
                        "chunk_overlap": 50,
                    },
                },
            },
            "retrieval": {
                "embedding_model": "Example Embedding Model",
                "vector_database": "FAISS",
                "search_type": "similarity",
                "top_k": 5,
            },
            "generation": {
                "model": "Example Language Model",
                "temperature": 0.0,
                "context_window": 8192,
            },
        }
    }


JS_CODE = """
function createSplitter(chunkSize, chunkOverlap) {
    return {
        chunkSize: chunkSize,
        chunkOverlap: chunkOverlap
    };
}

function processDocument(document) {
    const splitter = createSplitter(500, 50);

    const chunks = splitter.split(document);

    for (const chunk of chunks) {
        console.log(chunk);
    }

    return chunks;
}

class DocumentProcessor {
    constructor() {
        this.documents = [];
    }

    addDocument(document) {
        this.documents.push(document);
    }

    process() {
        return this.documents.map(
            document => processDocument(document)
        );
    }
}
"""