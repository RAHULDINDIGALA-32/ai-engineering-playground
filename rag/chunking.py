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
    PLAIN_TEXT
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



if __name__ == "__main__":
    main()