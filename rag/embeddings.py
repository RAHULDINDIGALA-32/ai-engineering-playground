import numpy as np
from sentence_transformers import SentenceTransformer


def cosine_similarity(vector1, vector2):
    return np.dot(vector1, vector2) / (np.linalg.norm(vector1) * np.linalg.norm(vector2))


model = SentenceTransformer("all-MiniLM-L6-v2") #374 features

text = "I am Rahul Dindigala."
text_embeddings = model.encode(text)

print("\n########################################")
print("Embeddings Shape: ", text_embeddings.shape)
print("Embeddings (first 10 features): ", text_embeddings[:10] )
print("########################################")


text1 = "Web3 Engineer is one of the highest paid role in 2025"
text2 = "I want to study Computer Science"
text3 = "I wanna become a Blockchain Engineer"

vector1 = model.encode(text1)
vector2 = model.encode(text2)
vector3 = model.encode(text3)

print("\n########################################")
print("Text1: ", text1)
print("Text2: ", text2)
print("Text3: ", text3)
print("\nConsine Similarity between text 1 & 2: ", cosine_similarity(vector1, vector2))
print("Consine Similarity between text 1 & 3: ", cosine_similarity(vector1, vector3))
print("Consine Similarity between text 2 & 3: ", cosine_similarity(vector2, vector3))
print("\n########################################")

