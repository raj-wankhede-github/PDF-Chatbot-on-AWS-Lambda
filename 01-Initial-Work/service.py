import os
from dotenv import load_dotenv
import psycopg2

load_dotenv()

class rds_connect:
    def __init__(self):
        DB_HOST = os.getenv("DBHOST")
        DB_USER = os.getenv("DBUSER")
        DB_PASSWORD = os.getenv("DBPASSWORD")
        DB_NAME = os.getenv("DBNAME")
        self.conn = psycopg2.connect(
            host=DB_HOST, database=DB_NAME, user=DB_USER, password=DB_PASSWORD
        )

        self.cursor = self.conn.cursor()
        try:
            print("Creating Table")
            create_query = f"""
            CREATE TABLE train_status (
            user_id         varchar(80),
            deployment_id   varchar(80),
            status          int
            
            );
            """ 
            
            self.cursor.execute(create_query)
            print("Table created successfully........") 
        except Exception as e:
            print(f"ERROR: {str(e)}")
            self.conn.rollback()
            
    def update_status(self, user_id, deployment_id, status):
        user_id = str(user_id)
        deployment_id = str(deployment_id)
        status = int(status)
        print(f"user id: {user_id}, deployment id: {deployment_id}, status: {status}")
        insert_query = f"""
        INSERT INTO train_status (user_id, deployment_id, status)
        VALUES ('{user_id}','{deployment_id}', {status});
        """
        try:
            self.cursor.execute(insert_query)
            self.conn.commit()
        except Exception as e:
            print(f"Error: {str(e)}")
            self.conn.rollback()

    def query_database(self):
        self.cursor.execute("SELECT * FROM train_status")
        results = self.cursor.fetchall()
        print(results)


if __name__ == "__main__":
    db = rds_connect()
    # print("yo")
    db.query_database()
