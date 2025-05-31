from flask import Flask, request, jsonify
import psycopg2
import os
import json
import time
import traceback

app = Flask(__name__)

for attempt in range(10):
    try:
        conn = psycopg2.connect(
            dbname=os.getenv("POSTGRES_DB"),
            user=os.getenv("POSTGRES_USER"),
            password=os.getenv("POSTGRES_PASSWORD"),
            host="postgres",  # Docker service name
            port="5432"
        )
        print("✅ Connected to PostgreSQL")
        break
    except psycopg2.OperationalError as e:
        print(f"❌ DB not ready (attempt {attempt + 1}/10):", e)
        time.sleep(2)
else:
    print("❌ Failed to connect to PostgreSQL after 10 attempts.")
    raise

@app.route("/submit", methods=["POST"])
def submit():
    try:
        data = request.json
        emirates_id = data.get("emirates_id")
        evaluation_result = data.get("evaluation_result")

        if not emirates_id or not evaluation_result:
            return jsonify({"error": "Missing required fields"}), 400

        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO social_evaluation_status (emirates_id, evaluation_result)
                    VALUES (%s, %s)
                    RETURNING id;
                    """,
                    (emirates_id, json.dumps(evaluation_result))
                )
                new_id = cur.fetchone()[0]

        return jsonify({"status": "success", "inserted_id": new_id})

    except Exception as e:
        print("Error during insertion:", e)
        traceback.print_exc()
        return jsonify({"error": "Internal server error"}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
