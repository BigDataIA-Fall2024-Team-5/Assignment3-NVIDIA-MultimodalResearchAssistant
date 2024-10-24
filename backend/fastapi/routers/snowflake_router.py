# routers/snowflake_router.py

from fastapi import APIRouter, HTTPException
from typing import List
from pydantic import BaseModel
import snowflake.connector
import os

router = APIRouter(
    prefix="/snowflake",
    tags=["Snowflake"]
)

# Define a Publication model (same as in publication_router)
class Publication(BaseModel):
    id: int
    title: str
    description: str
    date: str
    author: str
    cover_image_link: str = None
    pdf_link: str

# Snowflake connection setup (fetch credentials from environment variables)
def get_snowflake_connection():
    try:
        connection = snowflake.connector.connect(
            user=os.getenv("SNOWFLAKE_USER"),
            password=os.getenv("SNOWFLAKE_PASSWORD"),
            account=os.getenv("SNOWFLAKE_ACCOUNT"),
            role=os.getenv("SNOWFLAKE_ROLE"),
            warehouse=os.getenv("SNOWFLAKE_WAREHOUSE", "WH_PUBLICATIONS_ETL"),
            database=os.getenv("SNOWFLAKE_DATABASE", "DB_CFA_PUBLICATIONS"),
            schema=os.getenv("SNOWFLAKE_SCHEMA", "CFA_PUBLICATIONS")
        )
        print("Connected to Snowflake successfully")  # Debug print
        return connection
    except Exception as e:
        print(f"Snowflake connection error: {str(e)}")  # Debug print
        raise

@router.get("/publications", response_model=List[Publication])
async def get_publications_from_snowflake():
    """
    Retrieve a list of all publications from Snowflake.
    """
    try:
        conn = get_snowflake_connection()
        cursor = conn.cursor()

        # Use fully qualified table name: {database}.{schema}.{table}
        cursor.execute("SELECT * FROM DB_CFA_PUBLICATIONS.CFA_PUBLICATIONS.PUBLICATION_LIST ORDER BY DATE DESC")
        
        publications = []
        for row in cursor:
            publications.append(Publication(
                id=row[0],
                title=row[1],
                description=row[2],
                date=row[3],
                author=row[4],
                cover_image_link=row[5],
                pdf_link=row[6]
            ))
        cursor.close()
        conn.close()
        
        print("Fetched publications successfully")  # Debug print
        return publications
    except Exception as e:
        print(f"Error fetching data from Snowflake: {str(e)}")  # Debug print
        raise HTTPException(status_code=500, detail=f"Error fetching data: {str(e)}")
