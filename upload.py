from elasticsearch import Elasticsearch

es = Elasticsearch(
    "https://localhost:9200",
    basic_auth=("elastic", "password"),
    verify_certs=False
)

index_name = "automations"

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
                "dims": 1536,
                "index": True,
                "similarity": "cosine"
            }
        }
    }
}

if not es.indices.exists(index=index_name):
    es.indices.create(index=index_name, body=mapping)
