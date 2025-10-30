from pymongo import MongoClient
from pymongo.errors import ServerSelectionTimeoutError, PyMongoError
from config import MONGO_URI, MONGO_DB
import json
import os
import csv

# Connect to MongoDB with a reasonable timeout so the app doesn't hang
client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
db = client[MONGO_DB]

def ping_db():
    """Ping MongoDB to verify connectivity"""
    try:
        client.admin.command('ping')
        return {"ok": True, "message": "MongoDB reachable"}
    except ServerSelectionTimeoutError as e:
        return {"ok": False, "error": f"MongoDB not reachable (timeout): {str(e)}"}
    except PyMongoError as e:
        return {"ok": False, "error": f"MongoDB error: {str(e)}"}

def setup_sample_data():
    """
    Setup sample data for demonstration purposes.
    Creates a 'products' and 'customers' collection with sample data.
    """
    # Ensure MongoDB is reachable before proceeding
    client.admin.command('ping')

    # Clear existing collections if they exist
    db.products.drop()
    db.customers.drop()
    
    # Sample product data
    products = [
        {"name": "Laptop", "category": "Electronics", "price": 1200, "stock": 45},
        {"name": "Smartphone", "category": "Electronics", "price": 800, "stock": 75},
        {"name": "Headphones", "category": "Electronics", "price": 150, "stock": 100},
        {"name": "Desk Chair", "category": "Furniture", "price": 250, "stock": 30},
        {"name": "Coffee Table", "category": "Furniture", "price": 350, "stock": 20},
        {"name": "T-shirt", "category": "Clothing", "price": 25, "stock": 200},
        {"name": "Jeans", "category": "Clothing", "price": 75, "stock": 150},
        {"name": "Running Shoes", "category": "Footwear", "price": 120, "stock": 80}
    ]
    
    # Sample customer data
    customers = [
        {"name": "John Smith", "email": "john@example.com", "age": 35, "orders": 12, "total_spent": 3450},
        {"name": "Emily Johnson", "email": "emily@example.com", "age": 28, "orders": 8, "total_spent": 2100},
        {"name": "Michael Brown", "email": "michael@example.com", "age": 42, "orders": 5, "total_spent": 1850},
        {"name": "Sarah Wilson", "email": "sarah@example.com", "age": 31, "orders": 15, "total_spent": 4200},
        {"name": "David Lee", "email": "david@example.com", "age": 24, "orders": 3, "total_spent": 780}
    ]
    
    # Insert data into collections
    db.products.insert_many(products)
    db.customers.insert_many(customers)
    
    print("Sample data has been loaded into the database.")

def get_collection_names():
    """Return all collection names in the database"""
    return db.list_collection_names()

def get_collection_schema(collection_name):
    """Return schema for a specific collection"""
    sample = db[collection_name].find_one()
    if sample:
        return list(sample.keys())
    return []

def execute_query(query):
    """Execute a MongoDB query"""
    try:
        # The query should be a dictionary containing:
        # - collection: which collection to query
        # - operation: find, insert, update, etc.
        # - filter: the filter criteria
        # - projection: fields to return (optional)
        
        collection = query.get("collection")
        operation = query.get("operation")
        filter_criteria = query.get("filter", {})
        projection = query.get("projection", None)
        
        if operation == "find":
            if projection:
                result = list(db[collection].find(filter_criteria, projection))
            else:
                result = list(db[collection].find(filter_criteria))
            
            # Convert ObjectId to string for JSON serialization
            for item in result:
                if "_id" in item:
                    item["_id"] = str(item["_id"])
            
            return result
        
        elif operation == "count":
            return db[collection].count_documents(filter_criteria)
        
        elif operation == "aggregate":
            pipeline = query.get("pipeline", [])
            result = list(db[collection].aggregate(pipeline))
            
            # Convert ObjectId to string for JSON serialization
            for item in result:
                if "_id" in item:
                    item["_id"] = str(item["_id"])
            
            return result
        
        else:
            return {"error": f"Operation {operation} not supported"}
            
    except Exception as e:
        return {"error": str(e)}

def _infer_value_type(value: str):
    if value is None:
        return None
    v = value.strip()
    if v == "":
        return None
    lower = v.lower()
    if lower in ("true", "false"):
        return lower == "true"
    if lower in ("null", "none", "nan"):
        return None
    # int
    try:
        if v.isdigit() or (v.startswith('-') and v[1:].isdigit()):
            return int(v)
    except Exception:
        pass
    # float
    try:
        return float(v)
    except Exception:
        pass
    return value

def import_csv_folder(csv_dir: str):
    """Import all CSV files from a folder into MongoDB.
    Collection name is the CSV filename (without extension).
    Returns a dict of {collection: inserted_count}.
    """
    try:
        # Verify DB up
        client.admin.command('ping')
    except ServerSelectionTimeoutError as e:
        return {"error": f"MongoDB not reachable: {str(e)}"}
    except PyMongoError as e:
        return {"error": f"MongoDB error: {str(e)}"}

    if not os.path.isdir(csv_dir):
        return {"error": f"CSV directory not found: {csv_dir}"}

    results = {}
    for fname in os.listdir(csv_dir):
        if not fname.lower().endswith('.csv'):
            continue
        path = os.path.join(csv_dir, fname)
        collection_name = os.path.splitext(fname)[0]

        try:
            with open(path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                docs = []
                for row in reader:
                    doc = {k: _infer_value_type(v) for k, v in row.items()}
                    docs.append(doc)
                if docs:
                    db[collection_name].drop()  # replace existing for simplicity
                    db[collection_name].insert_many(docs)
                    results[collection_name] = len(docs)
                else:
                    results[collection_name] = 0
        except Exception as e:
            results[collection_name] = {"error": str(e)}

    return results