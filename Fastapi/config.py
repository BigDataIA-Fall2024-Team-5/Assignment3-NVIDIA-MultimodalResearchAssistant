import snowflake.connector
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

def get_snowflake_connection():
    """
    Establishes a connection to Snowflake using direct credentials.

    Returns:
        conn: A Snowflake connection object.

    Raises:
        Exception: If there is an error while connecting to Snowflake.
    """
    try:
        # Directly pass the credentials (replace these with actual values)
        user = "DHARUNRAMARAJ"
        password = "password@DAMG7245"
        account = "kvmqrcg-ol33191"
        warehouse = "WH_PUBLICATIONS_ETL"
        role = "ACCOUNTADMIN"
        database = "DB_CFA_PUBLICATIONS"
        schema = "CFA_PUBLICATIONS"

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
