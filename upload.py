import pandas as pd
import ast
from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk

# ==========================
# Elasticsearch Configuration
# ==========================
ES_HOST = "https://localhost:9200"
ES_USERNAME = "elastic"
ES_PASSWORD = "your_password"

INDEX_NAME = "automations"

# CSV file path
CSV_FILE = "automations.csv"

# ==========================
# Connect to Elasticsearch
# ==========================
es = Elasticsearch(
    ES_HOST,
    basic_auth=(ES_USERNAME, ES_PASSWORD),
    verify_certs=False
)

if not es.ping():
    raise Exception("Could not connect to Elasticsearch")

print("Connected to Elasticsearch")

# ==========================
# Read CSV
# ==========================
df = pd.read_csv(CSV_FILE)

required_columns = {
    "id",
    "automation_name",
    "description",
    "embedding"
}

missing_columns = required_columns - set(df.columns)

if missing_columns:
    raise ValueError(f"Missing columns in CSV: {missing_columns}")

# ==========================
# Parse Embeddings
# ==========================
def parse_embedding(value):
    """
    Converts a string like:
    "[0.12, 0.34, 0.56]"
    into a Python list.
    """
    if pd.isna(value):
        return []

    if isinstance(value, list):
        return value

    return ast.literal_eval(value)

df["embedding"] = df["embedding"].apply(parse_embedding)

# Determine embedding dimension from first row
embedding_dims = len(df.iloc[0]["embedding"])

print(f"Detected embedding dimension: {embedding_dims}")

# ==========================
# Create Index (if needed)
# ==========================
mapping = {
    "mappings": {
        "properties": {
            "id": {
                "type": "keyword"
            },
            "automation_name": {
                "type": "text"
            },
            "description": {
                "type": "text"
            },
            "embedding": {
                "type": "dense_vector",
                "dims": embedding_dims,
                "index": True,
                "similarity": "cosine"
            }
        }
    }
}

if not es.indices.exists(index=INDEX_NAME):
    es.indices.create(
        index=INDEX_NAME,
        body=mapping
    )
    print(f"Created index: {INDEX_NAME}")
else:
    print(f"Index already exists: {INDEX_NAME}")

# ==========================
# Prepare Bulk Documents
# ==========================
actions = []

for _, row in df.iterrows():
    actions.append({
        "_index": INDEX_NAME,
        "_id": str(row["id"]),
        "_source": {
            "id": str(row["id"]),
            "automation_name": str(row["automation_name"]),
            "description": str(row["description"]),
            "embedding": row["embedding"]
        }
    })

# ==========================
# Bulk Upload
# ==========================
success, errors = bulk(
    es,
    actions,
    raise_on_error=False
)

print(f"Successfully indexed: {success}")

if errors:
    print(f"Failed documents: {len(errors)}")
    for error in errors[:10]:
        print(error)

# ==========================
# Verify Upload
# ==========================
response = es.search(
    index=INDEX_NAME,
    query={"match_all": {}},
    size=5
)

print("\nSample Documents:")
for hit in response["hits"]["hits"]:
    print(hit["_source"])
