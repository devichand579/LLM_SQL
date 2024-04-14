import os
from flask import Flask, render_template, request, flash
from openai import OpenAI
import psycopg2
import secrets
from contextlib import closing
import atexit




app = Flask(__name__)
secret_key = secrets.token_hex(16)  # Generate a 32-character hexadecimal string
app.secret_key = secret_key

# Setting up OpenAI client
client = OpenAI(base_url="http://localhost:1234/v1", api_key="lm-studio")


# Function to generate SQL query using OpenAI
def generate_sql_query(input_text,temper,db_schema):
    prompt = f"""
### Task
Generate a SQL query to answer [QUESTION]{input_text}[/QUESTION]

### Database Schema
The query will run on a database with the following schema:
{db_schema}

### Answer
Given the database schema, here is the SQL query that [QUESTION]{input_text}[/QUESTION]
[SQL]

"""
    
    system_prompt = f"""
   
You are a helpful AI assistant expert in querying SQL Database to find answers to user's question.
1. Create and execute a syntactically correct SQL Server query.
2. Limit the results to 10 unless specified otherwise.
3. Order the results by a relevant column to ensure the most interesting examples are returned.
4. Only request specific columns relevant to the query.
5. Not perform any Data Manipulation Language (DML) operations such as INSERT, UPDATE, DELETE, or DROP.
6. Double-check my queries before execution and provide a response based on the query results.
7. If a question doesn't relate to the database, I'll respond with "I don't know".
8. If a question is meangingless or empty, I'll respond with "Meaningless".
"""
    completion = client.chat.completions.create(
    model="model-identifier",
    messages=[
    {"role": "system", "content": system_prompt},
    {"role": "user", "content": prompt}
  ],
  temperature=temper,
)
    # Extract and return the generated SQL query
    return completion.choices[0].message.content



def connect_to_postgresql(username, password, host, database):
    try:
        # Establish a connection to the PostgreSQL database
        connection = psycopg2.connect(
            user=username,
            password=password,
            host=host,
            database=database
        )
        return connection
     # Catch exception if there is any problem in establishing the connection
    except Exception as e:
        print("Error connecting to PostgreSQL:", e)
        return None

def execute_psql_query(connection, query):
    try:
        # Create a cursor to execute SQL queries
        # cursor is a postgreSQL adaptor for python
        # This is used to interact with the database by executing SQL queries..
        cursor = connection.cursor()
        # Execute the provided SQL query
        cursor.execute(query)
        # Fetch all the results from the executed query
        results = cursor.fetchall()
        return results
    except Exception as e:
        # Print an error message if there is an issue executing the query
        flash("Query Execution was unsuccesful! Check the Query Properly!")
        flash(e)
        return None
    finally:
        # Close the cursor to free up resources
        if cursor:
            cursor.close()


# Define routes
@app.route('/', methods=['POST', 'GET'])
def index():
    if request.method == 'POST':
        user_text = request.form.get('user_text', '') 
        temper = request.form.get('temperature', '')
        db_schema = request.form.get('db_schema', '')
        # Generate SQL query
        sql_query = generate_sql_query(user_text,temper,db_schema)
        return render_template('index.html', sql_query=sql_query,user_text=user_text)
    else:
        return render_template('index.html')

@app.route('/execute_query', methods=['POST'])
def execute_query():
    query = request.form['query']
    user_name = request.form.get('user_name', '')
    password = request.form.get('password', '')
    host = request.form.get('host', '')
    database = request.form.get('database', '')
    feedback = request.form.get('feedback_score', '')
    connection = connect_to_postgresql(user_name, password, host, database)
    #try:

        # Execute the constructed SQL query
    results = execute_psql_query(connection, query)

    if results:
        print("Query Results:")
        for row in results:
            print(row)

        flash("Query executed successfully!")
        return render_template('index.html', output_tuples=results)
    else:
        print("No results or error in executing the query! (Check the Query Properly)")
        return render_template('index.html', sql_query= query, output_tuples=None)


if __name__ == '__main__':
    import os
    port = int(os.environ.get("PORT", 5001))
    app.run(host='127.0.0.1', port=port,debug=True)




