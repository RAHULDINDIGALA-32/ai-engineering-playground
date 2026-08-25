from langchain_text_splitters import (
    CharacterTextSplitter,
    RecursiveCharacterTextSplitter,
    MarkdownHeaderTextSplitter,
    HTMLHeaderTextSplitter,
    PythonCodeTextSplitter,
    RecursiveJsonSplitter,
    Language,
    TokenTextSplitter,
)

from langchain_core.documents import Document

from sample_documents import (
    PLAIN_TEXT,
    MARKDOWN_TEXT,
    HTML_TEXT,
    PYTHON_CODE,
    JSON_DATA,
    JS_CODE
)


# ============================================================
# UTILITY FUNCTION
# ============================================================

def display_chunks(title, chunks):
    """Print chunks in a readable format."""

    print("\n")
    print("=" * 80)
    print(title)
    print("=" * 80)

    print(f"Total chunks: {len(chunks)}")

    for index, chunk in enumerate(chunks, start=1):
        print("\n" + "-" * 80)
        print(f"CHUNK {index}")
        print("-" * 80)

        # Handle both strings and LangChain Document objects
        if hasattr(chunk, "page_content"):
            print(chunk.page_content)

            if chunk.metadata:
                print("\nMetaData: ")
                print(chunk.metadata)
        else:
            print(chunk)


# ============================================================
# 1. CHARACTER TEXT SPLITTER
# ============================================================

def character_text_splitter():
    """
    Split text using a single separator.

    This is a simple strategy. It is useful when the document has a
    relatively consistent structure.
    """

    splitter = CharacterTextSplitter(
        separator="\n\n",
        chunk_size=500,
        chunk_overlap=50,
        length_function=len,
    )

    chunks = splitter.split_text(PLAIN_TEXT)

    display_chunks(
        "1. CharacterTextSplitter",
        chunks,
    )


# ============================================================
# 2. RECURSIVE CHARACTER TEXT SPLITTER
# ============================================================

def recursive_character_splitter():
    """
    General-purpose splitter.

    It tries separators recursively to keep related text together.
    """

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50,
        length_function=len,
        separators=[
            "\n\n",
            "\n",
            ". ",
            " ",
            "",
        ],
    )

    chunks = splitter.split_text(PLAIN_TEXT)

    display_chunks(
        "2. RecursiveCharacterTextSplitter",
        chunks,
    )


# ============================================================
# 3. TOKEN TEXT SPLITTER
# ============================================================

def token_text_splitter():
    """
    Split text according to tokens instead of characters.

    Useful when your model has token-based context limits.
    """

    splitter = TokenTextSplitter(
        chunk_size=100,
        chunk_overlap=20,
    )

    chunks = splitter.split_text(PLAIN_TEXT)

    display_chunks(
        "3. TokenTextSplitter",
        chunks,
    )

# ============================================================
# 4. MARKDOWN HEADER SPLITTER
# ============================================================

def markdown_header_splitter():
    """
    Split Markdown according to its heading structure.
    """
    headers_to_split_on = [
        ("#", "Header 1"),
        ("##", "Header 2"),
        ("###", "Header 3"),
    ]

    splitter = MarkdownHeaderTextSplitter(
        headers_to_split_on=headers_to_split_on
    )

    chunks = splitter.split_text(MARKDOWN_TEXT)

    display_chunks(
        "4. MarkdownHeaderTextSplitter",
        chunks,
    )


# ============================================================
# 5. HTML HEADER SPLITTER
# ============================================================

def html_header_splitter():
    """
    Split HTML based on heading tags.
    """
    headers_to_split_on = [
        ("h1", "Header 1"),
        ("h2", "Header 2"),
        ("h3", "Header 3"),
    ]

    splitter = HTMLHeaderTextSplitter(
        headers_to_split_on=headers_to_split_on
    )

    chunks = splitter.split_text(HTML_TEXT)

    display_chunks(
        "5. HTMLHeaderTextSplitter",
        chunks,
    )


# ============================================================
# 6. PYTHON CODE TEXT SPLITTER
# ============================================================

def python_code_splitter():
    """
    Split Python source code.

    This splitter is designed specifically for Python code.
    """
    splitter = PythonCodeTextSplitter(
        chunk_size=500,
        chunk_overlap=50,
    )

    chunks = splitter.split_text(PYTHON_CODE)

    display_chunks(
        "6. PythonCodeTextSplitter",
        chunks,
    )


# ============================================================
# 7. RECURSIVE JSON SPLITTER
# ============================================================

def recursive_json_splitter():
    """
    Split structured JSON data recursively.
    """

    splitter = RecursiveJsonSplitter(
        max_chunk_size=500
    )

    chunks = splitter.split_json(JSON_DATA)

    display_chunks(
        "7. RecursiveJsonSplitter",
        chunks,
    )


# ============================================================
# 8. LANGUAGE-AWARE SPLITTER
# ============================================================

def language_aware_splitter():
    """
    Demonstrate RecursiveCharacterTextSplitter using a language.

    LangChain provides language-aware separators for several
    programming languages.
    """

    splitter = RecursiveCharacterTextSplitter.from_language(
        language=Language.JS,
        chunk_size=300,
        chunk_overlap=50,
    )

    chunks = splitter.split_text(JS_CODE)

    display_chunks(
        "8. Language-Aware Recursive Splitter",
        chunks,
    )


# ============================================================
# 9. DOCUMENT OBJECTS + METADATA
# ============================================================

def document_based_chunking():
    """
    Demonstrate splitting LangChain Document objects.

    This is particularly useful for RAG because metadata can
    be preserved alongside the chunks.
    """

    documents = [
        Document(
            page_content=PLAIN_TEXT,
            metadata={
                "source": "rag-introduction.txt",
                "document_type": "text",
                "topic": "RAG and chunking",
            },
        )
    ]

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50,
    )

    chunks = splitter.split_documents(documents)

    display_chunks(
        "9. Document-Based Chunking With Metadata",
        chunks,
    )


# ============================================================
# 10. COMPARE DIFFERENT CHUNK SIZES
# ============================================================

def compare_chunk_sizes():
    """
    Demonstrate how chunk_size affects the number of chunks.
    """

    print("\n")
    print("=" * 80)
    print("10. COMPARING DIFFERENT CHUNK SIZES")
    print("=" * 80)

    for chunk_size in [200, 500, 1000]:

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=50,
        )

        chunks = splitter.split_text(PLAIN_TEXT)

        print(
            f"chunk_size={chunk_size:4} "
            f"-> {len(chunks):3} chunks"
        )


# ============================================================
# 11. COMPARE DIFFERENT OVERLAP VALUES
# ============================================================

def compare_chunk_overlap():
    """
    Demonstrate how chunk overlap affects chunk boundaries.
    """

    print("\n")
    print("=" * 80)
    print("11. COMPARING DIFFERENT CHUNK OVERLAPS")
    print("=" * 80)

    for overlap in [0, 20, 50, 100]:

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=overlap,
        )

        chunks = splitter.split_text(PLAIN_TEXT)

        print(
            f"chunk_overlap={overlap:3} "
            f"-> {len(chunks):3} chunks"
        )


# ============================================================
# 12. SHOW CHUNK LENGTHS
# ============================================================

def analyze_chunks():
    """
    Analyze the size of generated chunks.

    This is useful when tuning a RAG pipeline.
    """

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50,
    )

    chunks = splitter.split_text(PLAIN_TEXT)

    print("\n")
    print("=" * 80)
    print("12. CHUNK SIZE ANALYSIS")
    print("=" * 80)

    lengths = [len(chunk) for chunk in chunks]

    print(f"Number of chunks : {len(chunks)}")
    print(f"Smallest chunk   : {min(lengths)} characters")
    print(f"Largest chunk    : {max(lengths)} characters")
    print(f"Average chunk    : {sum(lengths) / len(lengths):.2f} characters")

    print("\nIndividual chunk sizes:")

    for index, length in enumerate(lengths, start=1):
        print(f"Chunk {index:3}: {length:4} characters")



# ============================================================
# MAIN PROGRAM
# ============================================================

def main():

    print("=" * 80)
    print("LANGCHAIN TEXT CHUNKING DEMONSTRATION")
    print("=" * 80)

    print("\nOriginal document length:")
    print(f"{len(PLAIN_TEXT)} characters")

    # Basic character splitting
    character_text_splitter()

    # Recommended general-purpose approach
    recursive_character_splitter()

    # Token-based splitting
    token_text_splitter()

    # Markdown
    markdown_header_splitter()

    # HTML
    html_header_splitter()

    # Python source code
    python_code_splitter()

    # JSON
    recursive_json_splitter()

    # Language-aware splitting
    language_aware_splitter()

    # RAG-style Document objects
    document_based_chunking()

    # Experiment with parameters
    compare_chunk_sizes()

    compare_chunk_overlap()

    # Analyze resulting chunks
    analyze_chunks()


if __name__ == "__main__":
    main()