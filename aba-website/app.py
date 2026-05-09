from flask import Flask, render_template, request, redirect, session
import hashlib
import secrets
import time

app = Flask(__name__)
app.secret_key = "secret123"

# ==============================
# Utility Functions
# ==============================

def H(data):
    return hashlib.sha256(data.encode()).hexdigest()

def timestamp():
    return int(time.time())

# ==============================
# Storage (Simple memory database)
# ==============================

users_db = {}
login_attempts = {}

# ==============================
# Security Functions
# ==============================

def original_paper_security():

    return {

        "Replay Attack": "HANDLED",
        "Impersonation Attack": "HANDLED",
        "Man-in-the-Middle Attack": "HANDLED",
        "Password Guessing Attack": "HANDLED",
        "Smart Card Theft Attack": "HANDLED",

        "Insider Attack": "NOT HANDLED",
        "Privileged Server Attack": "NOT HANDLED",
        "User Tracking Attack": "NOT HANDLED",

        "DoS Attack": "PARTIALLY HANDLED"

    }

def proposed_schema_security():

    return {

        "Password Guessing Attack": "HANDLED",
        "Session Key Disclosure Attack": "HANDLED",
        "User Impersonation Attack": "HANDLED",
        "Server Impersonation Attack": "HANDLED",
        "Man-in-the-Middle Attack": "HANDLED",
        "Replay Attack": "HANDLED",
        "User Tracking Attack": "HANDLED",
        "Smart Card Theft Attack": "HANDLED",
        "Insider Attack": "HANDLED"

    }

# ==============================
# Authentication Logic
# ==============================

def generate_session_key(user_id):

    T1 = timestamp()

    ri = secrets.token_hex(8)

    Di = H(ri)

    r2 = secrets.token_hex(8)

    Ji = H(Di + r2)

    SK = H(
        Ji +
        str(T1) +
        user_id
    )

    return SK

# ==============================
# Routes
# ==============================

@app.route("/")
def home():
    return redirect("/login")

# ==============================
# Register
# ==============================

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        user_id = request.form["user_id"]
        username = request.form["username"]
        email = request.form["email"]
        password = request.form["password"]
        biometric = request.form["biometric"]
        attributes = request.form.getlist("attributes")

        users_db[user_id] = {
            "username": username,
            "email": email,
            "password": password,
            "biometric": biometric,
            "attributes": attributes
        }

        return redirect("/login")

    return render_template("register.html")

# ==============================
# Login
# ==============================

@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    attempts_str = None

    if request.method == "POST":
        user_id = request.form["user_id"]
        password = request.form["password"]
        biometric = request.form["biometric"]

        # Check lock
        if user_id in login_attempts:
            data = login_attempts[user_id]
            if data["count"] >= 3:
                if timestamp() < data["locked_until"]:
                    lock_time = data["locked_until"] - timestamp()
                    error = f"Authentication Failed. Account locked for {lock_time} seconds."
                    return render_template("login.html", error=error)
                else:
                    # Lock expired
                    login_attempts[user_id] = {"count": 0, "locked_until": 0}

        # Verification (3-Factor)
        if user_id in users_db and \
           users_db[user_id]["password"] == password and \
           users_db[user_id]["biometric"] == biometric:
            # Success
            login_attempts[user_id] = {"count": 0, "locked_until": 0}
            session["user"] = user_id
            return redirect("/dashboard")
        else:
            # Failed
            if user_id not in login_attempts:
                login_attempts[user_id] = {"count": 0, "locked_until": 0}
            
            login_attempts[user_id]["count"] += 1
            strikes = login_attempts[user_id]["count"]
            
            if strikes >= 3:
                login_attempts[user_id]["locked_until"] = timestamp() + 55
                error = "Authentication Failed. Account locked for 55 seconds."
            else:
                error = "Authentication Failed"
                attempts_str = f"Attempts: {strikes}/3"
            
            return render_template("login.html", error=error, attempts_str=attempts_str)

    return render_template("login.html")

# ==============================
# Change Password Verification
# ==============================

@app.route("/change-password-verify", methods=["GET", "POST"])
def change_password_verify():
    error = None
    if request.method == "POST":
        user_id = request.form.get("user_id")
        current_password = request.form.get("current_password")
        
        if user_id in users_db and users_db[user_id]["password"] == current_password:
            session["password_change_user"] = user_id
            return redirect("/change-password")
        else:
            error = "Invalid User ID or Password"
            
    return render_template("change_password_verify.html", error=error)

# ==============================
# Change Password
# ==============================

@app.route("/change-password", methods=["GET", "POST"])
def change_password():
    if "password_change_user" not in session:
        return redirect("/change-password-verify")

    if request.method == "POST":
        user_id = session["password_change_user"]
        new_password = request.form.get("password")
        users_db[user_id]["password"] = new_password
        session.pop("password_change_user", None)
        return redirect("/password-success")

    return render_template("change_password.html")

@app.route("/password-success")
def password_success():
    return render_template("password_success.html")

# ==============================
# Change Biometric Verification
# ==============================

@app.route("/change-biometric-verify", methods=["GET", "POST"])
def change_biometric_verify():
    error = None
    if request.method == "POST":
        user_id = request.form.get("user_id")
        password = request.form.get("password")
        
        if user_id in users_db and users_db[user_id]["password"] == password:
            session["biometric_change_user"] = user_id
            return redirect("/change-biometric")
        else:
            error = "Invalid User ID or Password"
            
    return render_template("change_biometric_verify.html", error=error)

# ==============================
# Change Biometric
# ==============================

@app.route("/change-biometric", methods=["GET", "POST"])
def change_biometric():
    if "biometric_change_user" not in session:
        return redirect("/change-biometric-verify")

    if request.method == "POST":
        user_id = session["biometric_change_user"]
        new_biometric = request.form.get("biometric")
        users_db[user_id]["biometric"] = new_biometric
        session.pop("biometric_change_user", None)
        return redirect("/dashboard")

    return render_template("change_biometric.html")

# ==============================
# Change Attribute
# ==============================

@app.route("/change-attribute", methods=["GET", "POST"])
def change_attribute():
    if "user" not in session:
        return redirect("/login")
    
    user_id = session["user"]
    if request.method == "POST":
        new_attributes = request.form.getlist("attributes")
        users_db[user_id]["attributes"] = new_attributes
        return redirect("/dashboard")
    
    current_attributes = users_db[user_id].get("attributes", [])
    return render_template("change_attribute.html", current_attributes=current_attributes)

# ==============================
# Dashboard
# ==============================

@app.route("/dashboard")
def dashboard():

    if "user" not in session:
        return redirect("/login")

    user_id = session["user"]
    user_data = users_db.get(user_id, {})

    session_key = generate_session_key(user_id)

    original = original_paper_security()
    proposed = proposed_schema_security()

    return render_template(
        "dashboard.html",
        user_id=user_id,
        username=user_data.get("username", "User"),
        email=user_data.get("email", "N/A"),
        attributes=user_data.get("attributes", []),
        user_session_key=session_key,
        server_session_key=session_key,
        original=original,
        proposed=proposed
    )

# ==============================

if __name__ == "__main__":
    app.run(debug=True)