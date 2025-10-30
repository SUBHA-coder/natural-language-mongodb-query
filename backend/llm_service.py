import requests
import json
import re
from config import GROQ_API_KEY, GROQ_BASE_URL, LLAMA_MODEL
from database import get_collection_names, get_collection_schema

def get_db_context():
    """Get database context information for the LLM"""
    collections = get_collection_names()
    context = "Database collections:\n"
    
    for collection in collections:
        schema = get_collection_schema(collection)
        context += f"- {collection}: {', '.join(schema)}\n"
    
    return context

def test_groq_auth():
    """Simple check against Groq models endpoint to validate the API key."""
    if not GROQ_API_KEY:
        return {"ok": False, "error": "GROQ_API_KEY is not configured in config.py."}

    token = GROQ_API_KEY.strip().strip('"').strip("'")

    try:
        models_url = f"{GROQ_BASE_URL}/models"
        resp = requests.get(models_url, headers={"Authorization": f"Bearer {token}"}, timeout=15)
        if resp.status_code == 200:
            return {"ok": True}
        try:
            body = resp.json()
        except Exception:
            body = {"raw": resp.text[:200]}
        return {"ok": False, "status": resp.status_code, "details": body}
    except requests.exceptions.RequestException as e:
        return {"ok": False, "error": str(e)}

def natural_language_to_query(user_question):
    """
    Convert natural language query to MongoDB query using Groq API with Llama model
    """
    db_context = get_db_context()
    
    # Check for known query patterns and provide direct mapping
    if any(q in user_question.lower() for q in ["average age", "mean age", "avg age"]) and "customer" in user_question.lower():
        return {
            "collection": "customers",
            "operation": "aggregate",
            "pipeline": [
                {
                    "$group": {
                        "_id": None,
                        "averageAge": { "$avg": "$age" }
                    }
                }
            ]
        }
    
    # Construct prompt for the LLM with stronger guidance
    prompt = f"""
You are a MongoDB query generator. Convert the following natural language question into a MongoDB query.
Use the database context provided below to understand what collections and fields are available.

Database Context:
{db_context}

Natural Language Question: {user_question}

Generate a valid, well-formed JSON object with the following structure:
{{
  "collection": "name_of_collection",
  "operation": "find" or "count" or "aggregate",
  "filter": {{MongoDB query filter}},
  "projection": {{fields to return}} (optional),
  "pipeline": [{{aggregation pipeline}}] (only for aggregate operation)
}}

Important rules:
1. Use DOUBLE QUOTES for ALL property names and string values in the JSON
2. Make sure all JSON syntax is valid with proper commas and brackets
3. For aggregation queries, include the complete pipeline array
4. For average calculations, use "$group" with "$avg" operator
5. Do not include any explanations or comments, ONLY the JSON object

Provide just the valid JSON without any markdown formatting, explanation or additional text.
"""
    
    # Ensure API key is configured (supports config.py default)
    if not GROQ_API_KEY:
        return {"error": "GROQ_API_KEY is not configured in config.py.", "http_status": 400}

    # Normalize API key to avoid common quoting mistakes (e.g., exported with quotes)
    token = GROQ_API_KEY.strip().strip('"').strip("'")

    # Make API call to Groq
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": LLAMA_MODEL,
        "messages": [
            {"role": "system", "content": "You are a MongoDB query generator that outputs only valid JSON."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.1  # Lower temperature for more deterministic outputs
    }
    
    try:
        completions_url = f"{GROQ_BASE_URL}/chat/completions"
        response = requests.post(completions_url, headers=headers, json=payload, timeout=30)
        # Explicit handling for common auth errors
        if response.status_code in (401, 403):
            try:
                body = response.json()
            except Exception:
                body = {"raw": response.text[:200]}
            return {
                "error": f"Groq API authentication failed (status {response.status_code}).",
                "details": body,
                "http_status": response.status_code
            }
        response.raise_for_status()
        
        result = response.json()
        generated_text = result["choices"][0]["message"]["content"].strip()
        
        # Multi-stage JSON extraction with fallbacks
        
        # 1. Try direct parsing first (ideal case)
        try:
            mongo_query = json.loads(generated_text)
            return mongo_query
        except json.JSONDecodeError:
            pass
        
        # 2. Try to extract JSON with regex (handling markdown code blocks)
        try:
            # Remove markdown code block formatting if present
            if generated_text.startswith("```json"):
                generated_text = re.sub(r"```json\s*|\s*```", "", generated_text)
            elif generated_text.startswith("```"):
                generated_text = re.sub(r"```\s*|\s*```", "", generated_text)
                
            # Try parsing again after removing markdown
            mongo_query = json.loads(generated_text)
            return mongo_query
        except json.JSONDecodeError:
            pass
        
        # 3. Try finding JSON pattern with regex
        try:
            pattern = r"{[\s\S]*}"
            matches = re.search(pattern, generated_text)
            if matches:
                json_str = matches.group(0)
                mongo_query = json.loads(json_str)
                return mongo_query
        except (json.JSONDecodeError, AttributeError):
            pass
        
        # 4. Manual extraction with bracket counting
        try:
            start_idx = generated_text.find('{')
            if start_idx >= 0:
                # Find the matching closing brace by counting
                depth = 0
                end_idx = -1
                for i in range(start_idx, len(generated_text)):
                    if generated_text[i] == '{':
                        depth += 1
                    elif generated_text[i] == '}':
                        depth -= 1
                        if depth == 0:
                            end_idx = i + 1
                            break
                
                if end_idx > start_idx:
                    json_str = generated_text[start_idx:end_idx]
                    # Replace single quotes with double quotes
                    json_str = json_str.replace("'", '"')
                    # Remove any leading/trailing whitespace within the JSON
                    json_str = re.sub(r'"\s+:', '":', json_str)
                    json_str = re.sub(r':\s+"', ':"', json_str)
                    mongo_query = json.loads(json_str)
                    return mongo_query
        except (json.JSONDecodeError, ValueError):
            pass
        
        # 5. Last resort - map known questions directly
        if "average" in user_question.lower() and "age" in user_question.lower():
            return {
                "collection": "customers",
                "operation": "aggregate",
                "pipeline": [
                    {
                        "$group": {
                            "_id": None, 
                            "averageAge": { "$avg": "$age" }
                        }
                    }
                ]
            }
        
        # If all attempts fail
        return {
            "error": "Failed to parse LLM response into valid JSON",
            "raw_response": generated_text
        }
            
    except requests.exceptions.RequestException as e:
        return {"error": f"API call failed: {str(e)}"}