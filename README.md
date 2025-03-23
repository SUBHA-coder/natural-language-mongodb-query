# Natural Language MongoDB Query

A web application that allows users to query MongoDB databases using natural language. The system uses the Groq API with Llama model to translate natural language questions into MongoDB queries.

## 🚀 Features

- **Natural Language Interface**: Ask questions about your data in plain English
- **MongoDB Integration**: Seamlessly works with MongoDB collections
- **LLM-Powered Translation**: Uses Groq API with Llama model for query generation
- **Interactive UI**: Chat-like interface for asking questions and viewing results
- **Query Transparency**: Shows the generated MongoDB query for educational purposes

## 📋 Requirements

- Python 3.8+
- MongoDB
- Groq API key

## 🔧 Installation

1. Clone this repository:
```bash
git clone https://github.com/yourusername/natural-language-mongodb-query.git
cd natural-language-mongodb-query
```

2. Install backend dependencies:
```bash
cd backend
pip install -r requirements.txt
```

3. Set up your configuration:
   - Edit `backend/config.py` with your MongoDB connection details and Groq API key

## 🏃‍♂️ Running the Application

1. Start MongoDB on your system:
```bash
mongod
```

2. Start the Flask server:
```bash
cd backend
python app.py
```

3. Open your browser and navigate to:
```
http://localhost:5000
```

4. Click the "Setup Sample Database" button to initialize the sample data.

5. Start asking questions about your data!

## 💬 Example Queries

Try asking questions like:
- "Show me all products in the Electronics category"
- "What's the average age of customers?"
- "Find customers who spent more than $3000"
- "How many products have more than 50 items in stock?"
- "What is the most expensive product in each category?"

## 🗄️ Sample Data

The application comes pre-configured with two collections:

**Products Collection:**
- Fields: name, category, price, stock

**Customers Collection:**
- Fields: name, email, age, orders, total_spent

## 🔄 Project Structure

```
project/
├── backend/
│   ├── app.py               # Flask application
│   ├── config.py            # Configuration settings
│   ├── database.py          # MongoDB connection and queries
│   ├── llm_service.py       # Groq/Llama integration
│   └── requirements.txt     # Python dependencies
├── frontend/
│   ├── index.html           # Main frontend page
│   ├── style.css            # Styling
│   └── script.js            # Frontend logic
└── README.md                # This file
```

## 🛠️ How It Works

1. User enters a natural language question in the chat interface
2. The question is sent to the backend server
3. LLM service translates the question into a MongoDB query
4. The query is executed against the MongoDB database
5. Results are formatted and displayed to the user
6. The generated MongoDB query is shown for educational purposes

