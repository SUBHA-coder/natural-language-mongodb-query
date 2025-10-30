import argparse
import os
import csv
from typing import Dict, Any, List

from pymongo import MongoClient
from pymongo.errors import ServerSelectionTimeoutError, PyMongoError

from config import MONGO_URI, MONGO_DB


def infer_value_type(value: str):
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


def import_csv_file(client: MongoClient, file_path: str, collection_name: str, drop_existing: bool = True) -> Dict[str, Any]:
    db = client[MONGO_DB]
    if drop_existing:
        db[collection_name].drop()

    inserted = 0
    with open(file_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        docs: List[Dict[str, Any]] = []
        for row in reader:
            doc = {k: infer_value_type(v) for k, v in row.items()}
            docs.append(doc)
        if docs:
            db[collection_name].insert_many(docs)
            inserted = len(docs)

    return {"collection": collection_name, "inserted": inserted}


def import_csv_directory(client: MongoClient, dir_path: str, drop_existing: bool = True) -> Dict[str, Any]:
    results: Dict[str, Any] = {}
    for fname in os.listdir(dir_path):
        if not fname.lower().endswith('.csv'):
            continue
        path = os.path.join(dir_path, fname)
        collection = os.path.splitext(fname)[0]
        try:
            results[collection] = import_csv_file(client, path, collection, drop_existing)
        except Exception as e:
            results[collection] = {"error": str(e)}
    return results


def main():
    parser = argparse.ArgumentParser(description="Import CSV data into MongoDB collections")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--file", help="Path to a single CSV file")
    group.add_argument("--dir", help="Path to a directory containing CSV files")
    parser.add_argument("--collection", help="Collection name (required if using --file)")
    parser.add_argument("--no-drop", action="store_true", help="Do not drop existing collection before import")

    args = parser.parse_args()

    try:
        client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
        client.admin.command('ping')
    except (ServerSelectionTimeoutError, PyMongoError) as e:
        print(f"MongoDB connection error: {e}")
        raise SystemExit(1)

    drop_existing = not args.no_drop

    if args.file:
        if not args.collection:
            print("--collection is required when using --file")
            raise SystemExit(2)
        if not os.path.isfile(args.file):
            print(f"CSV file not found: {args.file}")
            raise SystemExit(2)
        result = import_csv_file(client, args.file, args.collection, drop_existing)
        print(result)
    else:
        if not os.path.isdir(args.dir):
            print(f"CSV directory not found: {args.dir}")
            raise SystemExit(2)
        result = import_csv_directory(client, args.dir, drop_existing)
        print(result)


if __name__ == "__main__":
    main()


