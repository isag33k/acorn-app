from flask import Flask
import psycopg2

app = Flask(__name__)

@app.route('/')
def hello():
    message = "Hello from ACORN - Minimal DB Test App!"
    db_status = "Unknown"
    
    try:
        # Connect to the database directly with the correct name 'acorn'
        conn = psycopg2.connect(
            "dbname=acorn user=acorn_user password=Welcome1 host=localhost"
        )
        db_status = "Connected successfully!"
        conn.close()
    except Exception as e:
        db_status = f"Error: {str(e)}"
    
    return f"{message}<br><br>Database status: {db_status}"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
