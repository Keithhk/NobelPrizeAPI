from fastapi import FastAPI, Query, HTTPException
from pymongo import MongoClient
from bson.regex import Regex
import requests
import os
from rapidfuzz import process, fuzz
#
# class LaureateBase(BaseModel):
#     firstname: str = Field(..., title="First Name", min_length=1, max_length=100)
#     surname: Optional[str] = Field(None, title="Surname", max_length=100)
#     category: str = Field(..., title="Prize Category", min_length=2, max_length=50)
#     year: int = Field(..., title="Prize Year", ge=1901, le=2100)
#     motivation: Optional[str] = Field(None, title="Prize Motivation", max_length=500)
#
# class LaureateCreate(LaureateBase):
#     id: str = Field(default_factory=lambda: str(uuid4()), title="Unique Laureate ID")
#
# class LaureateUpdate(LaureateBase):
#     pass


MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DB_NAME = "nobel_prizes"
COLLECTION_NAME = "laureates"

app = FastAPI()

client = MongoClient(MONGO_URI)
db = client[DB_NAME]
collection = db[COLLECTION_NAME]


def fetch_and_store_data():
    if collection.count_documents({}) == 0:
        response = requests.get("https://api.nobelprize.org/v1/prize.json")
        if response.status_code == 200:
            prizes = response.json().get("prizes", [])
            formatted_data = []
            for prize in prizes:
                for laureate in prize.get("laureates", []):
                    laureate["category"] = prize["category"]
                    laureate["year"] = prize["year"]
                    formatted_data.append(laureate)
            collection.insert_many(formatted_data)
        else:
            raise HTTPException(status_code=500, detail="Failed to fetch Nobel Prize data.")


fetch_and_store_data()


@app.get("/search")
def search_nobel_prize(
    query: str = Query(..., title="Search Term"),
    threshold: int = Query(60, title="Fuzzy match threshold (0-100)"),
    limit: int = Query(10, title="Max results to return")
):

    exact_match_query = {
        "$or": [
            {"firstname": {"$regex": f"^{query}$", "$options": "i"}},
            {"surname": {"$regex": f"^{query}$", "$options": "i"}},
            {"category": {"$regex": f"^{query}$", "$options": "i"}},
            {"motivation": {"$regex": Regex(query, "i")}},
            {"year": query}
        ]
    }

    exact_matches = list(collection.find(exact_match_query, {"_id": 0}))

    # If we found exact matches, return them immediately as they have the highest priority)
    if exact_matches:
        return {"results": exact_matches[:limit]}

    # It no exact matches are found, do a fuzzy search across all fields
    all_records = list(collection.find({}, {"_id": 0}))
    ranked_results = []

    for record in all_records:
        first_name = record.get("firstname", "")
        last_name = record.get("surname", "")
        full_name = f"{first_name} {last_name}".strip()
        category = record.get("category", "")
        motivation = record.get("motivation", "")
        year = record.get("year", "")

        scores = [
            fuzz.ratio(query.lower(), full_name.lower()) * 1.5, # give a higher priority on full name matches
            fuzz.ratio(query.lower(), first_name.lower()),
            fuzz.ratio(query.lower(), last_name.lower()),
            fuzz.ratio(query.lower(), category.lower()),
            fuzz.ratio(query.lower(), motivation.lower()),
            fuzz.ratio(query.lower(), year.lower())
        ]

        final_score = sum(scores)

        if final_score >= threshold:
            ranked_results.append((final_score, record))

    ranked_results.sort(reverse=True, key=lambda x: x[0])

    return {"results": [r[1] for r in ranked_results[:limit]]}




# @app.post("/add_laureate")
# def add_laureate(laureate: LaureateCreate):
#     # Check if laureate already exists
#     existing_record = collection.find_one({
#         "firstname": laureate.firstname,
#         "surname": laureate.surname,
#         "category": laureate.category,
#         "year": laureate.year
#     })
#
#     if existing_record:
#         raise HTTPException(status_code=400, detail="Laureate already exists.")
#
#     # Insert new record
#     collection.insert_one(laureate.dict())
#     return {"message": "New laureate added successfully", "record": laureate.dict()}
#
#
# @app.put("/update_laureate/{id}")
# def update_laureate(id: str = Path(..., title="Laureate ID"), laureate: LaureateUpdate = None):
#     # Ensure the ID is a valid MongoDB ObjectId
#     if not ObjectId.is_valid(id):
#         raise HTTPException(status_code=400, detail="Invalid ID format.")
#
#     # Find existing record
#     existing_record = collection.find_one({"_id": ObjectId(id)})
#     if not existing_record:
#         raise HTTPException(status_code=404, detail="Laureate not found.")
#
#     # Update record
#     update_data = {k: v for k, v in laureate.dict().items() if v is not None}
#     collection.update_one({"_id": ObjectId(id)}, {"$set": update_data})
#
#     return {"message": "Laureate updated successfully", "updated_fields": update_data}
