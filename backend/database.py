from pymongo import MongoClient
from config import MONGO_URI, MONGO_DB
import json

# Connect to MongoDB
client = MongoClient(MONGO_URI)
db = client[MONGO_DB]

def setup_sample_data():
    """
    Setup sample data for demonstration purposes.
    Creates a 'products' and 'customers' collection with sample data.
    """
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