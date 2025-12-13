import io
import streamlit as st  # Streamlit
import sqlite3  # DB
import hashlib  # Password Hashing 
import random  # Captcha
import os 
import re
import datetime
import requests
import base64   # Backgroung images 

try:
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas
    REPORTLAB_AVAILABLE = True
except Exception:
    REPORTLAB_AVAILABLE = False    # this try block is added if the Report lab gives an error then Activity is downloaded as CSV

def set_bg(image_path):
    with open(image_path, "rb") as f:
        data = f.read()
    encoded = base64.b64encode(data).decode()   # converting image to base64 for stramlit
    st.markdown(
        f"""
        <style>
        [data-testid="stAppViewContainer"] {{
            background-image: url("data:image/jpg;base64,{encoded}");
            background-size: cover;
            background-position: center;
        }}
        </style> 
        """,   # CSS for image import
        unsafe_allow_html=True,
    )      # this function to set background image

from streamlit_extras.stylable_container import stylable_container # stlable container for UI and Background


st.set_page_config(page_title="SecureVault", layout="centered", page_icon="🔐")  # setting page details


if "theme" not in st.session_state:
    st.session_state["theme"] = "dark"     # this command is for setting default theme as dark

with st.sidebar:
    st.markdown("### Appearance")
    theme_choice = st.radio("Theme", ["Dark", "Light"], horizontal=True)
    st.session_state["theme"] = "dark" if theme_choice == "Dark" else "light"   # Mode changing Switch in Navigation Bar

def load_css(path):
    with open(path) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True) # load the css theme light or dark as per our selection


if st.session_state["theme"] == "dark":
    load_css("dark.css")
    set_bg("images/dark_bg.jpg")
else:
    load_css("light.css")
    set_bg("images/light_bg.jpg")     # this is for the background image according to the theme we select


def render_top_nav():
    logged_in = "userid" in st.session_state
    username = st.session_state.get("userid", "Guest")
    status_label = "Secure session" if logged_in else "Guest mode"
    status_class = "status-badge online" if logged_in else "status-badge offline"   

    st.markdown(
        f"""
        <div class="top-nav">
            <div class="brand-wrap">
                <div class="brand-logo">🔐</div>
                <div class="brand-text">
                    <div class="brand-title">SECUREVAULT</div>
                    <div class="brand-sub">Secure File storage</div>
                </div>
            </div>
            <div class="nav-right">
                <span class="{status_class}">{status_label}</span>
                <span class="nav-user">@{username}</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )        # top navigation bar

def hash_password(password: str) -> str: # uses hashing password for providing security
    return hashlib.sha256(password.encode()).hexdigest() # SHA-256 Hashing is used

def check_password_strength(password):
    score = 0
    if len(password) >= 8: score += 1
    if re.search(r"[A-Z]", password): score += 1
    if re.search(r"[a-z]", password): score += 1
    if re.search(r"[0-9]", password): score += 1
    if re.search(r"[@$!%*?&]", password): score += 1

    if score <= 2:
        return "Weak", "☹️"
    elif score in [3, 4]:
        return "Medium", "🤨"
    else:
        return "Strong", "🥳"     # logic for password strength checking

def get_db_connection():
    conn = sqlite3.connect("securevault.db")
    conn.row_factory = sqlite3.Row
    return conn    # connect to SQLite Database

def init_activity_log():
    conn = get_db_connection()
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS activity_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            userid TEXT,
            action TEXT NOT NULL,
            details TEXT,
            ts DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    conn.commit()
    conn.close()     # user activity log table (structure)

def log_activity(userid, action, details=None):
    conn = get_db_connection()
    conn.execute(
        "INSERT INTO activity_log (userid, action, details, ts) VALUES (?,?,?,CURRENT_TIMESTAMP)",
        (userid, action, details),
    )
    conn.commit()
    conn.close()  # insert user activity into the above table


def is_admin():
    return st.session_state.get("userid") == "admin" # checks if logged in user is admin or not 


init_activity_log() # calling it again to display user activity after login

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True) # folder to save uploaded files

def make_activity_pdf_bytes(filter_user=None):
    if not REPORTLAB_AVAILABLE:
        raise ImportError("reportlab not installed")
    conn = get_db_connection()
    cur = conn.cursor()
    if filter_user:
        cur.execute("SELECT userid, action, details, ts FROM activity_log WHERE userid=? ORDER BY ts DESC", (filter_user,))
    else:
        cur.execute("SELECT userid, action, details, ts FROM activity_log ORDER BY ts DESC")
    rows = cur.fetchall()
    conn.close()
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    x = 40
    y = height - 50
    c.setFont("Helvetica-Bold", 16)
    c.drawString(x, y, "SecureVault - User Activity Log")
    y -= 30
    c.setFont("Helvetica", 10)
    c.drawString(x, y, f"Generated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    y -= 20
    c.line(x, y, width - 40, y)
    y -= 20
    for row in rows:
        userid, action, details, ts = row
        details = details if details is not None else ""
        line = f"{ts} | {userid} | {action} | {details}"
        c.drawString(x, y, line[:120])
        y -= 12
        if y < 60:
            c.showPage()
            c.setFont("Helvetica", 10)
            y = height - 40
    c.save()
    buffer.seek(0)
    return buffer.read()  # for downloading user activity as pdf 

def export_activity_csv(filter_user=None):
    conn = get_db_connection()
    cur = conn.cursor()
    if filter_user:
        cur.execute("SELECT userid, action, details, ts FROM activity_log WHERE userid=? ORDER BY ts DESC", (filter_user,))
    else:
        cur.execute("SELECT userid, action, details, ts FROM activity_log ORDER BY ts DESC")
    rows = cur.fetchall()
    conn.close()
    output = io.StringIO()
    import csv
    w = csv.writer(output)
    w.writerow(["userid", "action", "details", "ts"])
    for r in rows:
        w.writerow([r["userid"], r["action"], r["details"], r["ts"]])
    return output.getvalue().encode("utf-8")   # for downloading user activity as CSV 

def login_page():
    with stylable_container(key="login_card", css_styles="{}"):
        st.markdown("### 🔐 SecureVault Login")
        userid = st.text_input("User ID")
        password = st.text_input("Password", type="password")

        
        if "captcha_a" not in st.session_state:
            st.session_state["captcha_a"] = random.randint(1, 9)
            st.session_state["captcha_b"] = random.randint(1, 9)  

        a = st.session_state["captcha_a"]
        b = st.session_state["captcha_b"]
        captcha_answer = st.text_input(f"Solve CAPTCHA: {a} + {b} = ?") 

        if st.button("Login"):
            try:
                if int(captcha_answer) != a + b:
                    st.error("Incorrect CAPTCHA.")
                    st.session_state["captcha_a"] = random.randint(1, 9)
                    st.session_state["captcha_b"] = random.randint(1, 9)
                    return
            except:
                st.error("Enter a valid number.")
                return   # This provides a captcha for user before login

            conn = get_db_connection()
            user = conn.execute(
                "SELECT * FROM users WHERE userid = ?", (userid,)
            ).fetchone()
            conn.close()

            if user and user["password"] == hash_password(password):
                st.session_state["userid"] = userid
                log_activity(userid, "login", "User logged in")
                st.success("Login successful!")
                st.rerun()
            else:
                st.error("Invalid credentials.") # logic for login page

def signup_page():
    with stylable_container(key="signup_card", css_styles="{}"):
        st.markdown("### 📝 Create SecureVault Account")
        userid = st.text_input("Choose UserID")
        email = st.text_input("Email ID")
        password = st.text_input("Password", type="password") 

        
        if password:
            strength, emoji = check_password_strength(password)
            st.write(f"Password Strength: {emoji} **{strength}**") # show password strength using emojin like shown above

        if st.button("Create Account"):
            if not userid or not email or not password:
                st.error("All fields required.")
                return

            conn = get_db_connection()
            try:
                conn.execute(
                    "INSERT INTO users (userid, password, email) VALUES (?,?,?)",
                    (userid, hash_password(password), email),
                )
                conn.commit()
                conn.close()
                st.success("Account created!")
                log_activity(userid, "signup", "New account created")
            except:
                st.error("UserID already exists.")   # logic for signup page

def upload_file_page():
    with stylable_container(key="upload_card", css_styles="{}"):
        st.markdown("### 📤 Upload File")

        if "userid" not in st.session_state:
            st.warning("Login required.")
            return

        uploaded_file = st.file_uploader("Choose a file")

        if uploaded_file:
            user_folder = os.path.join(UPLOAD_FOLDER, st.session_state["userid"])
            os.makedirs(user_folder, exist_ok=True)
            file_path = os.path.join(user_folder, uploaded_file.name)

            with open(file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())

            st.success(f"Uploaded: {uploaded_file.name}")
            log_activity(st.session_state["userid"], "upload", f"Uploaded {uploaded_file.name}")   # login for file upload page

def view_files_page():
    with stylable_container(key="files_card", css_styles="{}"):
        st.markdown("### 📁 Your Files")

        if "userid" not in st.session_state:
            st.warning("Login first.")
            return

        user_folder = os.path.join(UPLOAD_FOLDER, st.session_state["userid"])
        os.makedirs(user_folder, exist_ok=True)
        files = sorted(os.listdir(user_folder))

        st.write(f"📦 Total Files: {len(files)}")

        search = st.text_input("Search files:")
        if search:
            files = [f for f in files if search.lower() in f.lower()]

        if not files:
            st.info("No files found.")
            return

        for f in files:
            file_path = os.path.join(user_folder, f)
            col1, col2, col3 = st.columns([3, 1, 1])
            col1.write(f"📄 {f}")

            with open(file_path, "rb") as file:
                col2.download_button("Download", file, file_name=f, key=f"dl_{f}")

            if col3.button("⋮", key=f"menu_{f}"):
                st.session_state["file_menu"] = f

            if st.session_state.get("file_menu") == f:
                new_name = st.text_input("Rename to:", value=f, key=f"rn_{f}")
                c1, c2 = st.columns(2)
                if c1.button("Save name", key=f"sv_{f}"):
                    new_path = os.path.join(user_folder, new_name)
                    os.rename(file_path, new_path)
                    log_activity(st.session_state["userid"], "rename", f"{f} → {new_name}")
                    st.session_state["file_menu"] = None
                    st.rerun()
                if c2.button("Delete", key=f"del_{f}"):
                    os.remove(file_path)
                    log_activity(st.session_state["userid"], "delete", f"Deleted {f}")
                    st.session_state["file_menu"] = None
                    st.rerun()     # Logic for file viewing page and it also inclides logic for file renaming as well as file deletion 

def account_page():
    with stylable_container(key="account_card", css_styles="{}"):
        st.markdown("### 👤 My Account")
        userid = st.session_state.get("userid")
        if not userid:
            st.warning("Login first.")
            return

        conn = get_db_connection()
        user = conn.execute(
            "SELECT userid, email FROM users WHERE userid = ?", (userid,)
        ).fetchone()
        conn.close()

        st.write(f"**User ID:** {user['userid']}")
        st.write(f"**Email:** {user['email']}")

        user_folder = os.path.join(UPLOAD_FOLDER, userid)
        files = os.listdir(user_folder) if os.path.exists(user_folder) else []

        total_bytes = 0
        if os.path.exists(user_folder):
            for name in files:
                fp = os.path.join(user_folder, name)
                if os.path.isfile(fp):
                    total_bytes += os.path.getsize(fp)

        mb = total_bytes / (1024 * 1024)
        limit_mb = 200
        used_pct = min(int((mb / limit_mb) * 100), 100)

        st.write(f"📦 Files stored: **{len(files)}**")
        st.write(f"💾 Storage used: **{mb:.2f} MB / {limit_mb} MB**")
        st.progress(used_pct)

        conn = get_db_connection()
        rows = conn.execute(
            "SELECT action, details, ts FROM activity_log WHERE userid = ? ORDER BY ts DESC LIMIT 10",
            (userid,),
        ).fetchall()
        conn.close()

        st.markdown("#### Recent Activity")
        if not rows:
            st.write("No recent activity yet.")
        else:
            for r in rows:
                st.write(f"• {r['ts']} — **{r['action']}** — {r['details'] or ''}") # logic for user account page with user activity table and Storage used bar
                
        st.markdown("---")
        st.markdown("### Export activity")
        include_all = False
        if is_admin():
            include_all = st.checkbox("Include all users (admin only)", value=False)
        filter_user = None if include_all else userid

        if REPORTLAB_AVAILABLE:
            try:
                pdf_bytes = make_activity_pdf_bytes(filter_user)
                st.download_button(
                    label="📥 Download Activity as PDF",
                    data=pdf_bytes,
                    file_name="activity_log.pdf",
                    mime="application/pdf",
                )
            except Exception as e:
                st.error("Could not generate PDF: " + str(e))
                csv_bytes = export_activity_csv(filter_user)
                st.download_button("Download activity as CSV (fallback)", data=csv_bytes, file_name="activity_log.csv", mime="text/csv")
        else:
            st.warning("ReportLab is not installed. Install it with: pip install reportlab")
            csv_bytes = export_activity_csv(filter_user)
            st.download_button("Download activity as CSV", data=csv_bytes, file_name="activity_log.csv", mime="text/csv")

def support_page():
    with stylable_container(key="support_card", css_styles="{}"):
        st.markdown("### 🛟 Support")

        issue_type = st.selectbox("Issue Type", ["Login Issue", "Upload Issue", "Bug", "Other"])
        message = st.text_area("Describe your issue:")

        if st.button("Submit Support Request"):
            if not message.strip():
                st.error("Message cannot be empty.")
            else:
                st.success("Support request sent.")
                userid = st.session_state.get("userid")
                log_activity(userid, "support", f"{issue_type}: {message[:80]}")   # logic for support page
                
def admin_page():
    with stylable_container(key="admin_card", css_styles="{}"):
        st.markdown("### 🛡️ Admin Panel")
        
        if not is_admin():
            st.warning("Admin access only.")
            return

        st.caption("View all user folders and files.")
        if not os.path.exists(UPLOAD_FOLDER):
            st.write("No uploads folder yet.")
            return

        users = sorted(os.listdir(UPLOAD_FOLDER))
        for u in users:
            user_folder = os.path.join(UPLOAD_FOLDER, u)
            if not os.path.isdir(user_folder):
                continue
            st.markdown(f"#### 👤 {u}")
            files = os.listdir(user_folder)
            if not files:
                st.write("No files.")
                continue
            for f in files:
                st.write(f"• {f}")    # Logic for Admin Page

def dashboard():
    username = st.session_state.get("userid", "User")
    with stylable_container(key="dashboard_card", css_styles="{}"):
        st.markdown(f"### 🔒 Welcome, {username}")

        st.write("🕒 Current Time:", datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

options = ["📤 Upload File", "📁 View Files", "👤 Account", "🛟 Support", "🚪 Logout"]
if is_admin():  
    
    options.insert(-1, "🛡️ Admin")  

selected = st.sidebar.radio("Navigation", options)

if selected.startswith("📤"):
    upload_file_page()
elif selected.startswith("📁"):
    view_files_page()
elif selected.startswith("👤"):
    account_page()
elif selected.startswith("🛟"):
    support_page()
elif selected.startswith("🛡️"):
    admin_page()
elif selected.startswith("🚪"):
    if st.button("Confirm Logout"):
        userid = st.session_state.get("userid")
        if userid:
            log_activity(userid, "logout", "User logged out")
            st.session_state.clear()
            st.rerun()    # logic for user dashboard page


render_top_nav()  # Calling so that the navigation bar on top is always displayed 

if "userid" not in st.session_state:
    st.sidebar.title("Menu")
    page = st.sidebar.radio("Choose Page", ["Login", "Signup"])
    if page == "Login":
        login_page()
    else:
        signup_page()
else:
    dashboard()     # This shows login or signup if user not logged in or not.  

