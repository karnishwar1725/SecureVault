import sqlite3
import csv
import os

DB_NAME = "securevault.db"
OUTPUT_DIR = "db_exports"  

os.makedirs(OUTPUT_DIR, exist_ok=True)  # created folder id does not exist

def export_table(table_name):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor() 

    cur.execute(f"SELECT * FROM {table_name}")
    rows = cur.fetchall()  # gets all user info from DB table

    col_names = [desc[0] for desc in cur.description]  # puts column names for table

    file_path = os.path.join(OUTPUT_DIR, f"{table_name}.csv")  # updates the table details to a CSV file

    with open(file_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(col_names)
        writer.writerows(rows)   # provides CSV file

    conn.close()
    print(f"Exported {table_name} → {file_path}")

def main():
    export_table("users")
    export_table("activity_log")

if __name__ == "__main__":
    main()