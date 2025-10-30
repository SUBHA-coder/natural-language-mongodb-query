from flask import Flask, request, jsonify, render_template
from werkzeug.exceptions import HTTPException
from flask_cors import CORS
import json
from database import setup_sample_data, execute_query, ping_db, import_csv_folder
import os
from llm_service import natural_language_to_query, test_groq_auth

app = Flask(__name__, static_folder='../frontend', static_url_path='')
CORS(app)  # Enable CORS for all routes

@app.route('/')
def index():
    return app.send_static_file('index.html')

@app.route('/api/setup', methods=['POST'])
def setup_db():
    """Setup sample database"""
    # Check DB health first
    status = ping_db()
    if not status.get("ok"):
        return jsonify({
            "error": "MongoDB is not reachable. Start MongoDB and try again.",
            "details": status.get("error")
        }), 503

    try:
        setup_sample_data()
        return jsonify({"message": "Sample data has been loaded into the database"})
    except Exception as e:
        return jsonify({
            "error": "Failed to set up sample data",
            "details": str(e)
        }), 500

@app.route('/api/health/db', methods=['GET'])
def health_db():
    """Return MongoDB connectivity status"""
    status = ping_db()
    http_status = 200 if status.get("ok") else 503
    return jsonify(status), http_status

@app.route('/api/health/groq', methods=['GET'])
def health_groq():
    """Return Groq API key validity status"""
    status = test_groq_auth()
    http_status = 200 if status.get("ok") else 503
    return jsonify(status), http_status

@app.route('/api/import-csv', methods=['POST'])
def import_csv():
    """Import all CSVs from the project csv/ directory into MongoDB."""
    # DB health check first
    status = ping_db()
    if not status.get("ok"):
        return jsonify({
            "error": "MongoDB is not reachable. Start MongoDB and try again.",
            "details": status.get("error")
        }), 503

    base_dir = os.path.dirname(__file__)
    project_root = os.path.abspath(os.path.join(base_dir, '..'))
    csv_dir = os.path.join(project_root, 'csv')

    result = import_csv_folder(csv_dir)
    if isinstance(result, dict) and result.get("error"):
        return jsonify(result), 400
    return jsonify({"message": "CSV import completed", "imported": result})

@app.route('/api/query', methods=['POST'])
def process_query():
    """Process natural language query"""
    data = request.get_json()
    if not data or 'question' not in data:
        return jsonify({"error": "No question provided"}), 400
    
    user_question = data['question']
    
    # Convert natural language to MongoDB query
    mongo_query = natural_language_to_query(user_question)
    
    # Handle errors in query generation
    if "error" in mongo_query:
        error_msg = mongo_query["error"]
        
        # Check if we have raw LLM response for debugging
        debug_info = {}
        if "raw_response" in mongo_query:
            debug_info["raw_llm_response"] = mongo_query["raw_response"]
        http_status = mongo_query.get("http_status", 500)
        return jsonify({
            "error": error_msg,
            "debug": debug_info,
            "question": user_question,
            "details": mongo_query.get("details")
        }), http_status
    
    # Execute the query
    result = execute_query(mongo_query)
    
    # Handle errors in query execution
    if isinstance(result, dict) and "error" in result:
        return jsonify({
            "error": f"Database error: {result['error']}",
            "query": mongo_query,
            "question": user_question
        }), 500
    
    # Format aggregate results for better display
    if mongo_query.get("operation") == "aggregate" and isinstance(result, list):
        # For aggregation results, we might need to flatten or reformat
        if len(result) == 1 and "_id" in result[0] and result[0]["_id"] is None:
            # This is a common pattern for aggregations like average, sum, etc.
            # Remove the null _id for cleaner display
            result = {k: v for k, v in result[0].items() if k != "_id"}
    
    # Return the successful response
    return jsonify({
        "query": mongo_query,
        "result": result,
        "question": user_question
    })

# Global error handlers to ensure JSON on errors instead of HTML
@app.errorhandler(HTTPException)
def handle_http_exception(e: HTTPException):
    response = {
        "error": e.name,
        "details": e.description
    }
    return jsonify(response), e.code

@app.errorhandler(Exception)
def handle_generic_exception(e: Exception):
    response = {
        "error": "Internal Server Error",
        "details": str(e)
    }
    return jsonify(response), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)