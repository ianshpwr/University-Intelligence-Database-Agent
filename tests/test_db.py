import sqlite3
import os

os.makedirs("data", exist_ok=True)

conn = sqlite3.connect("data/university.db")

print("Database connected successfully")

conn.close()