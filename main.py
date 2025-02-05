import os
import pandas as pd
import difflib
import constants
from flask import Flask, request, jsonify, render_template
import google.generativeai as genai

# Configure Google Gemini API
googleapi_key = constants.googleapi_key
genai.configure(api_key=googleapi_key)

app = Flask(__name__)

# Load CSV data into Pandas DataFrame
csv_path = os.path.join(os.path.dirname(__file__), "data.csv")
df = pd.read_csv(csv_path)

# Normalize column names (convert to lowercase)
df.columns = df.columns.str.lower()

@app.route("/")
def home():
    return render_template("index.html")  # Serves the frontend

@app.route("/chat", methods=["POST"])
def chat():
    data = request.json
    query = data.get("query", "").strip().lower()

    if not query:
        return jsonify({"error": "Query is required"}), 400

    # Search only in the "product" column
    product_names = df["product"].astype(str).str.lower().tolist()

    # Find the closest match for the product in the query
    best_match = difflib.get_close_matches(query, product_names, n=1, cutoff=0.3)

    if best_match:
        matching_row = df[df["product"].str.lower() == best_match[0].lower()]
        retrieved_data = matching_row.to_dict(orient="records")[0]  # Convert row to dictionary
    else:
        return jsonify({"response": "No relevant data found in the CSV."})

    # Format the response
    response_text = (
        f"🔹 **Product:** {retrieved_data['product']}\n"
        f"💲 **Price:** {retrieved_data['price']}\n"
        f"📦 **Stock:** {retrieved_data['stock']}\n"
        f"📝 **Description:** {retrieved_data['description']}"
    )

    # Generate AI response using Gemini
    model = genai.GenerativeModel("gemini-pro")
    ai_response = model.generate_content(f"User asked: {query}. Based on this product data: {retrieved_data}, generate a helpful response.")

    return jsonify({"response": ai_response.text, "product_data": response_text})

if __name__ == "__main__":
    app.run(port=5000, debug=True)
