# RAG with vector embeddings + Vector DB (Qdrant)

# Imports & Environment setup
import os
from dotenv import load_dotenv
from groq import Groq
import logging
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct


load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
QDRAT_URL = os.getenv("QDRANT_URL")

if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY environment variable is not set. Please set it in your .env file.")
elif not QDRANT_API_KEY:
    raise ValueError("QDRANT_API_KEY environment variable is not set. Please set it in your .env file.")
elif not QDRAT_URL:
    raise ValueError("QDRANT_URL environment variable is not set. Please set it in your .env file.")


# Connect to Qdrant (Vector DB)
qdrant_client = QdrantClient(
    url=QDRAT_URL,
    api_key=QDRANT_API_KEY
)

print("Connected to Qdrant Cloud!!")


# Create Qdrant Collection
COLLECTION_NAME = "Knowledge_base"
EMBEDDING_SIZE = 384

if qdrant_client.collection_exists(COLLECTION_NAME):
    print(f"Deleting existing collection: {COLLECTION_NAME}")
    qdrant_client.delete_collection(COLLECTION_NAME)

qdrant_client.create_collection(
    collection_name=COLLECTION_NAME,
    vectors_config=VectorParams(
        size=EMBEDDING_SIZE,
        distance=Distance.COSINE,
    ),
)

print(f"Created collection: {COLLECTION_NAME}")
print(f"Vector size: {EMBEDDING_SIZE}")
print("Distance Metric: COSINE")


# Load knowledge Base
with open("knowledge_base.txt", "r", encoding="utf-8") as f:
    documents = [
        line.strip()
        for line in f
        if line.strip()
    ]

print(f"Loaded {len(documents)} documents.")


# Create Vector Embeddings
embedding_model = SentenceTransformer("all-MiniLM-L6-v2") # 384 dims (features)
print("Embedding model loaded!!")

embeddings = embedding_model.encode(documents)

print(f"Generated {len(embeddings)} embeddings")
print(f"Embedding Size: {len(embeddings[0])}")


# Create Qdrant Points
points = []

for i, embedding in enumerate(embeddings):
    point = PointStruct(
        id=i+1,
        vector=embedding.tolist(),
        payload={
            "text": documents[i]
        }
    )

    points.append(point)


# Upload to Qdrant Collection 
qdrant_client.upsert( # upload + insert
    collection_name=COLLECTION_NAME,
    points=points
) 

print(f"Uploaded {len(points)} documents to Qdrant collection {COLLECTION_NAME}")


# Search Qdrant Collection
def search_db(query, top_k=3):

    # convert query into vector embedding
    query_vector = embedding_model.encode(query)

    # search Qdrant for similar vectors (Metric: Cosine Similarity)
    results = qdrant_client.query_points(
        collection_name=COLLECTION_NAME,
        query=query_vector,
        limit=top_k,
        with_payload=True,
    ).points

    return results

# Extract the Context
def extract_context(results):

    context = "\n".join(
        result.payload["text"]
        for result in results
    )

    return context



# Test Qdrant DB Search
sample_query = "How many vacation days do I get ?"
results = search_db(sample_query, top_k=3)

print("\nSearch Results:")

for result in results:
    print(f"Score: {result.score:.3f}")
    print(result.payload["text"])
    print()


# Connect to Groq
llm_client = Groq(api_key=GROQ_API_KEY)
LLM_MODEL = "openai/gpt-oss-120b"

# Call the LLM
def call_llm(query, context):

    system_prompt = """
    You are a helpful question-answering assistant.

    Answer the user's question using ONLY the provided context.
    Do not use outside knowledge.
    Do not hallucinate or make assumptions.
    If the answer cannot be found in the context, say:
    "I don't know based on the provided context."

    Answer in exactly one sentence.
    """

    user_prompt = f"""
    Context:
    {context}

    Question:
    {query}
    """
    system_message = {
        "role": "system",
        "content": system_prompt
    }
    
    user_message = {
        "role": "user",
        "content": user_prompt
    }
    
    messages = [system_message, user_message]
    
    try:
        response = llm_client.chat.completions.create(
            model=LLM_MODEL,
            messages=messages
        )
        answer = response.choices[0].message.content
        return answer
    except Exception:
        logging.exception("Failed to call LLM")
        return None



# ============================================================
# COMPLETE RAG PIPELINE
# ============================================================

def rag_pipeline(query):

    # 1. Retrieve relevant documents
    results = search_db(query, top_k=5)

    # 2. Extract context from retrieved documents
    context = extract_context(results)

    # 3. Augmnetation Generation through LLM
    answer = call_llm(query, context)

    return answer



query = "What is the difference between gym reimbursement and professional development allowance?"


# 1. DIRECT / SIMPLE QUERY
# query = "How many paid leave days do employees get per year?"

# 2. CONDITIONAL QUERY
# query = "When can an employee claim home internet reimbursement?"

# 3. MULTI-DOCUMENT QUERY
# query = "What benefits are available to employees who work remotely?"

# 4. COMPARISON QUERY
# query = "What is the difference between the normal notice period and the probation notice period?"

# 5. NEGATIVE / HALLUCINATION TEST
# query = "Does the company provide dental insurance?"

answer = rag_pipeline(query)

print("\nAnswer: ")
print(answer)

