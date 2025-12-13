from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import sqlite3

DB = "securevault.db"
OUTPUT = "activity_log.pdf"

def export_to_pdf():
    conn = sqlite3.connect(DB)
    cur = conn.cursor()

    cur.execute("SELECT userid, action, details, ts FROM activity_log ORDER BY ts DESC")
    rows = cur.fetchall()
    conn.close() # gets activity log data 

    c = canvas.Canvas(OUTPUT, pagesize=letter)
    width, height = letter   # Create a PDF with specified page size

    x = 40
    y = height - 50 # text starting point

    c.setFont("Helvetica-Bold", 16)
    c.drawString(x, y, "SecureVault - User Activity Log")
    y -= 40  # PDf title and font 

    c.setFont("Helvetica", 10) # font fo records

    for row in rows:
        line = f"User: {row[0]} | Action: {row[1]} | Details: {row[2]} | Time: {row[3]}"
        c.drawString(x, y, line)
        y -= 15 # input all details in puf

        if y < 40:  
            c.showPage()
            c.setFont("Helvetica", 10)
            y = height - 40  # if page is over this creates a new page

    c.save()
    print("PDF exported successfully →", OUTPUT)  # saves pdf with filename specified above

if __name__ == "__main__":
    export_to_pdf()