# this code was written to generate random password for crating a populated DB 
import sqlite3
import hashlib
import secrets
import string
import csv
import sys
import os # all imports

DB = "securevault.db" # name of DB to refer
OUT = "passwords.csv"  # name of output CSV file with passwords

def gen_password(length=10):
    alphabet = string.ascii_letters + string.digits + "!@#$%&*?"
    return "".join(secrets.choice(alphabet) for _ in range(length))   # generated random passwords

def hash_pw(pw):
    return hashlib.sha256(pw.encode()).hexdigest()   # converts plain tect to random characters using SHA-256

if not os.path.exists(DB):
    print("ERROR: securevault.db not found in current folder.", file=sys.stderr)
    sys.exit(1)   # Check if DB Exists in project folder if not the operation exists

conn = sqlite3.connect(DB)
cur = conn.cursor()   # Connecting to DB

cur.execute("SELECT userid FROM users")
rows = cur.fetchall()
if not rows:
    print("No users found in users table.")
    conn.close()
    sys.exit(0)   # gets all USER ID

mapping = []
for (userid,) in rows:
    pw = gen_password(12)          
    h  = hash_pw(pw)
    cur.execute("UPDATE users SET password = ? WHERE userid = ?", (h, userid))
    mapping.append((userid, pw))   # Reset password for all users if existed

conn.commit()
conn.close()  # saving changes to DB

with open(OUT, "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["userid","password"])
    w.writerows(mapping)   # write result to a CSV file

print(f"Updated {len(mapping)} users. Plaintext mapping saved to: {OUT}")
print("DON'T SHARE that CSV publicly. Use it only for testing.")