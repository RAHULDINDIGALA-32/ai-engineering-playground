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

from sample_document import (
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



if __name__ == "__main__":
    main()