import snowflake.connector
import logging
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

def get_snowflake_connection():
    """
    Establishes a connection to Snowflake using credentials from environment variables.

    Returns:
        conn: A Snowflake connection object.

    Raises:
        Exception: If there is an error while connecting to Snowflake.
    """
    try:
        # Fetch credentials from environment variables
        user = os.getenv("SNOWFLAKE_USER")
        password = os.getenv("SNOWFLAKE_PASSWORD")
        account = os.getenv("SNOWFLAKE_ACCOUNT")
        warehouse = os.getenv("SNOWFLAKE_WAREHOUSE")
        role = os.getenv("SNOWFLAKE_ROLE")
        database = os.getenv("SNOWFLAKE_DATABASE")
        schema = os.getenv("SNOWFLAKE_SCHEMA")

        # Log the connection details (don't log sensitive info like password)
        logging.debug(f"Connecting to Snowflake with account: {account}, user: {user}, database: {database}, schema: {schema}")

        # Establish the Snowflake connection
        conn = snowflake.connector.connect(
            user=user,
            password=password,
            account=account,
            warehouse=warehouse,
            role=role,
            database=database,
            schema=schema
        )

        logging.debug("Snowflake connection established successfully.")
        return conn

    except Exception as e:
        # Log the error with detailed information
        logging.error(f"Error connecting to Snowflake: {str(e)}")
        raise

# Testing the connection function (optional)
if __name__ == "__main__":
    try:
        conn = get_snowflake_connection()
        if conn:
            print("Connection to Snowflake successful!")
            conn.close()
    except Exception as e:
        print(f"Connection test failed: {e}")
