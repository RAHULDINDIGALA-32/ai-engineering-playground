from mcp.server.mcpserver import MCPServer

mcp = MCPServer("custom-encoder-decoder")


@mcp.tool()
def encode(input_text: str) -> str:
    """
    Encodes the input text using a custom encoding scheme.

    Args:
        input_text (str): The text to be encoded.

    Returns:
        str: The encoded representation of the input text.
    """

    encoded_text = input_text[::-1]  # reversing the string
    return encoded_text


@mcp.tool()
def decode(encoded_text: str) -> str:
    """
    Decodes the encoded text back to its original form.

    Args:
        encoded_text (str): The text to be decoded.

    Returns:
        str: The original representation of the encoded text.
    """

    decoded_text = encoded_text[::-1]  # reversing the string back
    return decoded_text


if __name__ == "__main__":
    mcp.run()
