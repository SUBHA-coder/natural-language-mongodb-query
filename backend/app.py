from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import json
from database import setup_sample_data, execute_query
from llm_service import natural_language_to_query

app = Flask(__name__, static_folder='../frontend', static_url_path='')
CORS(app)  # Enable CORS for all routes

@app.route('/')
def index():
    return app.send_static_file('index.html')

@app.route('/api/setup', methods=['POST'])
def setup_db():
    """Setup sample database"""
    setup_sample_data()
    return jsonify({"message": "Sample data has been loaded into the database"})

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
        
        return jsonify({
            "error": error_msg,
            "debug": debug_info,
            "question": user_question
        }), 500
    
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

if __name__ == '__main__':
    app.run(debug=True, port=5000)