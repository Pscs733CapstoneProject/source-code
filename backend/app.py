import mysql.connector
from flask import Flask, request, jsonify
from flask_cors import CORS
import random, string, smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

app = Flask(__name__)
CORS(app)

# --- MySQL Config ---
db_config = {
    "host": "localhost",
    "user": "root",         # your MySQL username
    "password": "POOJA@24", # your MySQL password
    "database": "esarkar_bot"
}

def get_db_connection():
    return mysql.connector.connect(**db_config)

# --- Generate Username + Password ---
def generate_credentials(role):
    username = f"{role.upper()}{random.randint(100,999)}"
    password = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
    return username, password

# --- Register ---
@app.route("/register", methods=["POST"])
def register():
    data = request.json
    name, email, role = data["name"], data["email"], data["role"]

    conn = get_db_connection()
    c = conn.cursor(dictionary=True)

    # check if email already exists
    c.execute("SELECT COUNT(*) as count FROM users WHERE email=%s", (email,))
    row = c.fetchone()
    if row and row["count"] > 0:
        conn.close()
        return jsonify({"error": "User already exists!"}), 400

    username, password = generate_credentials(role)

    # insert new user
    c.execute("INSERT INTO users (email, name, role, username, password) VALUES (%s,%s,%s,%s,%s)",
              (email, name, role, username, password))
    conn.commit()
    conn.close()

    # --- Styled HTML Email ---
    msg = MIMEMultipart("alternative")
    msg["Subject"] = "🎉 Welcome to eSarkar Training Bot!"
    msg["From"] = "poojatumminakatti@gmail.com"
    msg["To"] = email

    html_content = f"""
    <html>
      <body style="font-family: Arial, sans-serif; background-color:#f4f4f4; padding:20px;">
        <div style="max-width:500px; margin:auto; background:white; border-radius:12px;
                    box-shadow:0 8px 20px rgba(0,0,0,0.15); padding:25px; text-align:center;">
            <h2 style="color:#1d3557;">👋 Welcome, {name}!</h2>
            <p style="font-size:16px; color:#333;">
              You are successfully registered as <b style="color:#e63946;">{role}</b>.
            </p>
            <div style="background:#f1faee; padding:15px; border-radius:10px;
                        box-shadow: inset 0 3px 8px rgba(0,0,0,0.1); margin:20px 0;">
                <h3 style="margin:0; color:#457b9d;">Your Login Credentials</h3>
                <p style="font-size:15px; margin:8px 0;">
                  <b>Username:</b> {username}<br>
                  <b>Password:</b> {password}
                </p>
            </div>
            <a href="http://127.0.0.1:3000/login" 
               style="display:inline-block; padding:12px 20px; background:#2a9d8f; 
                      color:white; border-radius:8px; text-decoration:none; font-weight:bold;">
                🚀 Go to Login
            </a>
            <p style="margin-top:25px; font-size:12px; color:#777;">
              © 2025 eSarkar Training Bot. All rights reserved.
            </p>
        </div>
      </body>
    </html>
    """

    msg.attach(MIMEText(html_content, "html"))

    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login("poojatumminakatti@gmail.com", "newu xfbx pcea mfvo")  # ⚠️ Gmail App Password
            server.sendmail("poojatumminakatti@gmail.com", email, msg.as_string())
    except Exception as e:
        print("Email error:", e)

    return jsonify({"message": "✅ Registered! Credentials sent to your email."})

# --- Login (username + password) ---
@app.route("/login", methods=["POST"])
def login():
    data = request.json
    username, password = data["username"], data["password"]

    conn = get_db_connection()
    c = conn.cursor(dictionary=True)
    c.execute("SELECT * FROM users WHERE username=%s AND password=%s", (username, password))
    user = c.fetchone()
    conn.close()

    if user:
        return jsonify({"message": "✅ Login success", "role": user["role"]})
    return jsonify({"error": "Invalid credentials"}), 401

# --- Chatbot Intents (20 per role) ---
intents = {
    "Clerk": {
        "How do I enter data?": "Go to 'New Form' and fill in citizen details.",
        "How do I update a record?": "Use the 'Edit Form' option to update citizen records.",
        "How do I search for a citizen?": "Use the 'Search' option with citizen ID or name.",
        "How do I delete an entry?": "Only Admins can delete entries. Contact your Admin.",
        "What if I enter wrong data?": "Use 'Edit Form' to correct mistakes.",
        "How do I print a form?": "After filling the form, click 'Print Preview' → 'Print'.",
        "Can I save a draft entry?": "Yes, click 'Save as Draft' before submitting.",
        "How do I upload attachments?": "Use the 'Upload File' button in the form.",
        "How do I log complaints?": "Click on 'Complaints' and file a new complaint form.",
        "How do I track complaints?": "Use 'Complaint Status' in your dashboard.",
        "How do I update my profile?": "Click on 'My Profile' → 'Edit'.",
        "How do I reset my password?": "Click 'Forgot Password' on login screen.",
        "Can I handle multiple forms at once?": "Yes, open each form in a new tab.",
        "How do I export records?": "Use 'Export' button on the records page.",
        "How do I verify submitted data?": "Cross-check with original citizen documents.",
        "How do I contact technical support?": "Use 'Help' option in your dashboard.",
        "What if my system crashes?": "Data is auto-saved every 2 minutes.",
        "Can I see my activity history?": "Yes, under 'My Activity Log'.",
        "How do I logout safely?": "Click 'Logout' at top-right corner.",
        "What happens if I forget to submit?": "Drafts remain saved until submitted."
    },
    "Officer": {
        "How do I approve files?": "Go to 'Pending Files' and click 'Approve'.",
        "How do I generate reports?": "Go to 'Reports', select department, then click 'Generate'.",
        "How do I reject files?": "Open 'Pending Files' and click 'Reject'.",
        "How do I escalate issues?": "Forward files to Admin using 'Escalate'.",
        "How do I comment on a file?": "Use the 'Comments' box before approval/rejection.",
        "Can I re-open a rejected file?": "Yes, from 'Rejected Files' → 'Reopen'.",
        "How do I assign tasks?": "Use 'Task Assignment' in your dashboard.",
        "How do I check staff performance?": "Go to 'Reports' → 'Staff Performance'.",
        "How do I request additional info?": "Click 'Request Info' before approving.",
        "How do I mark files urgent?": "Use the 'Priority' option in file details.",
        "Can I download all reports?": "Yes, click 'Export to PDF/Excel'.",
        "How do I view escalated files?": "Open 'Escalated Files' in dashboard.",
        "How do I monitor deadlines?": "Use 'Deadline Tracker' widget.",
        "How do I notify staff?": "Use 'Send Notification' feature.",
        "What if a file is missing data?": "Reject with reason: 'Incomplete'.",
        "How do I handle duplicate files?": "Reject one, approve the valid file.",
        "Can I delegate approvals?": "Yes, assign them to another officer.",
        "How do I check file history?": "Click 'History' tab inside file view.",
        "How do I mark file as confidential?": "Check 'Confidential' option.",
        "What if system hangs?": "Log out and retry after 5 mins."
    },
    "Admin": {
        "How do I track staff progress?": "Go to Dashboard → Training Reports.",
        "How do I reset a password?": "Open User Management and reset credentials.",
        "How do I add new staff?": "Use 'Add Staff' in User Management.",
        "How do I remove staff?": "Open 'User Management' → 'Remove User'.",
        "How do I assign roles?": "Select user → 'Edit Role'.",
        "How do I view login activity?": "Check 'User Activity Logs'.",
        "How do I check system status?": "Go to 'System Dashboard'.",
        "How do I update system data?": "Click 'System Update' in settings.",
        "How do I backup data?": "Use 'Database Backup' option.",
        "How do I restore data?": "Upload backup file in 'Restore'.",
        "How do I send announcements?": "Use 'Broadcast Message' feature.",
        "How do I manage complaints?": "Go to 'Complaints Dashboard'.",
        "How do I view audit reports?": "Click 'Audit Logs' in reports.",
        "How do I configure permissions?": "Go to 'Role Permissions' tab.",
        "How do I lock inactive users?": "Set 'Auto Lock' in policies.",
        "How do I enable 2FA?": "Go to 'Security Settings' → Enable 2FA.",
        "How do I schedule training?": "Use 'Training Scheduler' module.",
        "How do I generate master report?": "Click 'Reports' → 'Master Report'.",
        "How do I handle data breaches?": "Follow incident management SOP.",
        "How do I contact developers?": "Use 'Support' → 'Contact Dev Team'."
    }
}

# --- API to get all questions for a role ---
@app.route("/intents/<role>", methods=["GET"])
def get_intents(role):
    if role in intents:
        return jsonify({"questions": list(intents[role].keys())})
    return jsonify({"questions": []})

# --- Chat API ---
@app.route("/chat", methods=["POST"])
def chat():
    data = request.json
    role = data.get("role")
    question = data.get("question")

    if role not in intents:
        return jsonify({"reply": "⚠️ Role not recognized."})

    reply = intents[role].get(question, "🤖 Sorry, I don’t know this question.")
    return jsonify({"reply": reply})

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
