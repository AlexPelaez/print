import mysql.connector
from mysql.connector import Error

class DBConnection:
    def __init__(self, host="localhost", user="root", password="", database="print_core_db"):
        self.host = host
        self.user = user
        self.password = password
        self.database = database
        self.connection = None
        self.cursor = None

    def connect(self):
        try:
            self.connection = mysql.connector.connect(
                host=self.host,
                user=self.user,
                password=self.password,
                database=self.database
            )
            self.cursor = self.connection.cursor(dictionary=True)
            print("Connected to the database successfully!")
        except Error as e:
            print(f"Error connecting to MySQL: {e}")

    def close(self):
        if self.cursor:
            self.cursor.close()
        if self.connection:
            self.connection.close()
        print("Database connection closed.")
