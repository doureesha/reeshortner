from flask import Flask, redirect, abort , render_template, request, Response
from functools import wraps
import sqlite3 as sq
import os

app = Flask(__name__)

ADMIN_USER = "admin"
ADMIN_PASS = os.environ.get("ADMIN_PASS", "change-this-locally")

def check_auth(username, password):
    return username == ADMIN_USER and password == ADMIN_PASS

def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return Response(
                "Login required", 401,
                {"WWW-Authenticate": "Basic realm='Login Required'"}
            )
        return f(*args, **kwargs)
    return decorated

@app.route("/<code>")
def redirectLink(code):
    conn = sq.connect("links.db")
    cursor = conn.cursor()
    cursor.execute("SELECT dest FROM links WHERE shortCode = ?", (code,))
    result = cursor.fetchone()
    conn.close()
    if result is None:
        abort(404)

    ip = request.headers.get("X-Forwarded-For", request.remote_addr)
    user_agent = request.headers.get("User-Agent", "")

    conn2 = sq.connect("links.db")
    cursor2 = conn2.cursor()
    cursor2.execute(
        "INSERT INTO clicks (shortCode, ip, userAgent) VALUES (?, ?, ?)",
        (code, ip, user_agent)
    )
    conn2.commit()
    conn2.close()
    return redirect(result[0])

@app.route("/admin")
@requires_auth
def admin():
    
    conn = sq.connect("links.db") # connection to db file itself
    cursor = conn.cursor() # what executes sql
    cursor.execute("SELECT links.shortCode, links.dest, COUNT(clicks.id) FROM links LEFT JOIN clicks ON links.shortCode = clicks.shortCode GROUP BY links.shortCode")
    result = cursor.fetchall() # gets all rows
    conn.close()
    
    return render_template("links.html", links=result)

@app.route("/admin/add", methods=["GET", "POST"])
def add_link():
    if request.method == "POST":
        code = request.form["code"]
        dest = request.form["dest"]
        
        conn = sq.connect("links.db")
        cursor = conn.cursor()
        cursor.execute("INSERT INTO links (shortCode, dest) VALUES (?, ?)", (code, dest))
        conn.commit()
        conn.close()
        
        return redirect("/admin")
    return render_template("add.html")

@app.route("/admin/delete/<code>")
def delete_link(code):
    conn = sq.connect("links.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM links WHERE shortCode = ?", (code,))
    conn.commit()
    conn.close()
    return redirect("/admin")

@app.route("/admin/edit/<code>", methods=["GET", "POST"])
def edit_link(code):
    if request.method == "POST":
        newDest = request.form["dest"]
        conn = sq.connect("links.db")
        cursor = conn.cursor()
        cursor.execute("UPDATE links SET dest = ? WHERE shortCode = ?", (newDest, code))
        conn.commit()
        conn.close()
        return redirect("/admin")
    if request.method == "GET":

        conn = sq.connect("links.db")
        cursor = conn.cursor()
        cursor.execute("SELECT dest FROM links WHERE shortCode = ?", (code,))
        row = cursor.fetchone()
        conn.close()
        return render_template("edit.html", code=code, dest=row[0])
        
    

if __name__ == "__main__":
    app.run()



