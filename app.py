from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

app.secret_key = "minichat-secret-key"


def get_database():
    connection = sqlite3.connect("database.db")
    connection.row_factory = sqlite3.Row
    return connection


@app.route("/")
def home():

    if "user_id" not in session:
        return redirect(url_for("login"))

    connection = get_database()

    groups = connection.execute("""
        SELECT groups.*
        FROM groups
        JOIN group_members
        ON groups.id = group_members.group_id
        WHERE group_members.user_id = ?
        ORDER BY groups.name
    """, (session["user_id"],)).fetchall()

    connection.close()

    return render_template(
        "index.html",
        username=session["username"],
        groups=groups,
        selected_group=None,
        messages=[],
        members=[]
    )


@app.route("/group/<int:group_id>")
def group(group_id):

    if "user_id" not in session:
        return redirect(url_for("login"))

    connection = get_database()

    membership = connection.execute("""
        SELECT *
        FROM group_members
        WHERE group_id = ? AND user_id = ?
    """, (group_id, session["user_id"])).fetchone()

    if not membership:
        connection.close()
        return redirect(url_for("home"))

    selected_group = connection.execute("""
        SELECT *
        FROM groups
        WHERE id = ?
    """, (group_id,)).fetchone()

    if not selected_group:
        connection.close()
        return redirect(url_for("home"))

    groups = connection.execute("""
        SELECT groups.*
        FROM groups
        JOIN group_members
        ON groups.id = group_members.group_id
        WHERE group_members.user_id = ?
        ORDER BY groups.name
    """, (session["user_id"],)).fetchall()

    messages = connection.execute("""
        SELECT messages.id,
               messages.content,
               messages.created_at,
               messages.user_id,
               users.username
        FROM messages
        JOIN users
        ON messages.user_id = users.id
        WHERE messages.group_id = ?
        ORDER BY messages.id ASC
    """, (group_id,)).fetchall()

    members = connection.execute("""
        SELECT users.id, users.username
        FROM users
        JOIN group_members
        ON users.id = group_members.user_id
        WHERE group_members.group_id = ?
        ORDER BY users.username
    """, (group_id,)).fetchall()

    connection.close()

    return render_template(
        "index.html",
        username=session["username"],
        groups=groups,
        selected_group=selected_group,
        messages=messages,
        members=members
    )


# -------------------------------------------------
# HENT MELDINGER
# -------------------------------------------------

@app.route("/messages/<int:group_id>")
def get_messages(group_id):

    if "user_id" not in session:
        return jsonify({"messages": []})

    connection = get_database()

    membership = connection.execute("""
        SELECT *
        FROM group_members
        WHERE group_id = ? AND user_id = ?
    """, (group_id, session["user_id"])).fetchone()

    if not membership:
        connection.close()
        return jsonify({"messages": []})

    messages = connection.execute("""
        SELECT messages.id,
               messages.content,
               messages.created_at,
               messages.user_id,
               users.username
        FROM messages
        JOIN users
        ON messages.user_id = users.id
        WHERE messages.group_id = ?
        ORDER BY messages.id ASC
    """, (group_id,)).fetchall()

    connection.close()

    return jsonify({
        "messages": [
            {
                "id": message["id"],
                "content": message["content"],
                "created_at": message["created_at"],
                "user_id": message["user_id"],
                "username": message["username"]
            }
            for message in messages
        ]
    })


# -------------------------------------------------
# SEND MELDING
# -------------------------------------------------

@app.route("/send_message", methods=["POST"])
def send_message():

    if "user_id" not in session:
        return redirect(url_for("login"))

    content = request.form.get("content", "").strip()
    group_id = request.form.get("group_id")

    if not group_id:
        return redirect(url_for("home"))

    if content == "":
        return redirect(url_for("group", group_id=group_id))

    connection = get_database()

    membership = connection.execute("""
        SELECT *
        FROM group_members
        WHERE group_id = ? AND user_id = ?
    """, (group_id, session["user_id"])).fetchone()

    if not membership:
        connection.close()
        return redirect(url_for("home"))

    connection.execute("""
        INSERT INTO messages
        (content, user_id, group_id)
        VALUES (?, ?, ?)
    """, (
        content,
        session["user_id"],
        group_id
    ))

    connection.commit()
    connection.close()

    return redirect(url_for("group", group_id=group_id))


# -------------------------------------------------
# OPPRETT GRUPPE
# -------------------------------------------------

@app.route("/create_group", methods=["POST"])
def create_group():

    if "user_id" not in session:
        return redirect(url_for("login"))

    group_name = request.form.get("group_name", "").strip()

    if group_name == "":
        return redirect(url_for("home"))

    connection = get_database()

    cursor = connection.execute("""
        INSERT INTO groups
        (name, owner_id)
        VALUES (?, ?)
    """, (
        group_name,
        session["user_id"]
    ))

    group_id = cursor.lastrowid

    connection.execute("""
        INSERT INTO group_members
        (group_id, user_id)
        VALUES (?, ?)
    """, (
        group_id,
        session["user_id"]
    ))

    connection.commit()
    connection.close()

    return redirect(url_for("group", group_id=group_id))


# -------------------------------------------------
# SLETT GRUPPE
# -------------------------------------------------

@app.route("/delete_group/<int:group_id>", methods=["POST"])
def delete_group(group_id):

    if "user_id" not in session:
        return redirect(url_for("login"))

    connection = get_database()

    group = connection.execute("""
        SELECT *
        FROM groups
        WHERE id = ?
    """, (group_id,)).fetchone()

    if not group:
        connection.close()
        return redirect(url_for("home"))

    if group["owner_id"] != session["user_id"]:
        connection.close()
        return redirect(url_for("group", group_id=group_id))

    connection.execute("""
        DELETE FROM messages
        WHERE group_id = ?
    """, (group_id,))

    connection.execute("""
        DELETE FROM group_members
        WHERE group_id = ?
    """, (group_id,))

    connection.execute("""
        DELETE FROM groups
        WHERE id = ?
    """, (group_id,))

    connection.commit()
    connection.close()

    return redirect(url_for("home"))


# -------------------------------------------------
# FJERN MEDLEM
# -------------------------------------------------

@app.route("/remove_member/<int:group_id>/<int:user_id>", methods=["POST"])
def remove_member(group_id, user_id):

    if "user_id" not in session:
        return redirect(url_for("login"))

    connection = get_database()

    group = connection.execute("""
        SELECT *
        FROM groups
        WHERE id = ?
    """, (group_id,)).fetchone()

    if not group:
        connection.close()
        return redirect(url_for("home"))

    if group["owner_id"] != session["user_id"]:
        connection.close()
        return redirect(url_for("group", group_id=group_id))

    # Eieren kan ikke fjernes
    if user_id == group["owner_id"]:
        connection.close()
        return redirect(url_for("group", group_id=group_id))

    connection.execute("""
        DELETE FROM group_members
        WHERE group_id = ? AND user_id = ?
    """, (
        group_id,
        user_id
    ))

    connection.commit()
    connection.close()

    return redirect(url_for("group", group_id=group_id))


# -------------------------------------------------
# LEGG TIL MEDLEM
# -------------------------------------------------

@app.route("/add_member/<int:group_id>", methods=["POST"])
def add_member(group_id):

    if "user_id" not in session:
        return redirect(url_for("login"))

    username = request.form.get("username", "").strip()

    if username == "":
        return redirect(url_for("group", group_id=group_id))

    connection = get_database()

    # Finn gruppen
    group = connection.execute("""
        SELECT *
        FROM groups
        WHERE id = ?
    """, (group_id,)).fetchone()

    if not group:
        connection.close()
        return redirect(url_for("home"))

    # Bare eieren kan legge til medlemmer
    if group["owner_id"] != session["user_id"]:
        connection.close()
        return redirect(url_for("group", group_id=group_id))

    # Finn brukeren
    user = connection.execute("""
        SELECT id, username
        FROM users
        WHERE username = ?
    """, (username,)).fetchone()

    if not user:
        connection.close()
        return redirect(url_for("group", group_id=group_id))

    # Sjekk om brukeren allerede er medlem
    already_member = connection.execute("""
        SELECT 1
        FROM group_members
        WHERE group_id = ? AND user_id = ?
    """, (
        group_id,
        user["id"]
    )).fetchone()

    if not already_member:

        connection.execute("""
            INSERT INTO group_members
            (group_id, user_id)
            VALUES (?, ?)
        """, (
            group_id,
            user["id"]
        ))

        connection.commit()

    connection.close()

    return redirect(url_for("group", group_id=group_id))


# -------------------------------------------------
# SØK ETTER BRUKERE
# -------------------------------------------------

@app.route("/search_users/<int:group_id>")
def search_users(group_id):

    if "user_id" not in session:
        return jsonify({"users": []})

    connection = get_database()

    # Bare eieren får søke etter brukere til gruppen
    group = connection.execute("""
        SELECT owner_id
        FROM groups
        WHERE id = ?
    """, (group_id,)).fetchone()

    if not group or group["owner_id"] != session["user_id"]:
        connection.close()
        return jsonify({"users": []})

    search = request.args.get("q", "").strip()

    users = connection.execute("""
        SELECT users.id, users.username
        FROM users
        WHERE users.username LIKE ?
        AND users.id != ?
        AND users.id NOT IN (
            SELECT user_id
            FROM group_members
            WHERE group_id = ?
        )
        ORDER BY users.username
        LIMIT 10
    """, (
        "%" + search + "%",
        session["user_id"],
        group_id
    )).fetchall()

    connection.close()

    return jsonify({
        "users": [
            {
                "id": user["id"],
                "username": user["username"]
            }
            for user in users
        ]
    })


# -------------------------------------------------
# REGISTER
# -------------------------------------------------

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        if username == "" or password == "":
            return "Fyll inn brukernavn og passord!"

        password_hash = generate_password_hash(password)

        connection = get_database()

        try:

            connection.execute("""
                INSERT INTO users
                (username, password)
                VALUES (?, ?)
            """, (
                username,
                password_hash
            ))

            connection.commit()

        except sqlite3.IntegrityError:

            connection.close()

            return "Brukernavnet er allerede tatt!"

        connection.close()

        return redirect(url_for("login"))

    return render_template("register.html")


# -------------------------------------------------
# LOGIN
# -------------------------------------------------

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        connection = get_database()

        user = connection.execute("""
            SELECT *
            FROM users
            WHERE username = ?
        """, (username,)).fetchone()

        connection.close()

        if user and check_password_hash(
            user["password"],
            password
        ):

            session["user_id"] = user["id"]
            session["username"] = user["username"]

            return redirect(url_for("home"))

        return "Feil brukernavn eller passord!"

    return render_template("login.html")


# -------------------------------------------------
# LOGOUT
# -------------------------------------------------

@app.route("/logout")
def logout():

    session.clear()

    return redirect(url_for("login"))


# -------------------------------------------------
# START
# -------------------------------------------------

if __name__ == "__main__":
    app.run(debug=True)