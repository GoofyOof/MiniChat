from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

app.secret_key = "minichat-secret-key"


def get_database():
    connection = sqlite3.connect("database.db")
    connection.row_factory = sqlite3.Row
    return connection


# =========================================
# HJEM
# =========================================

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


# =========================================
# GRUPPE
# =========================================

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
        SELECT
            messages.id,
            messages.content,
            messages.created_at,
            messages.user_id,
            messages.edited,
            users.username
        FROM messages
        JOIN users
        ON messages.user_id = users.id
        WHERE messages.group_id = ?
        ORDER BY messages.id ASC
    """, (group_id,)).fetchall()

    members = connection.execute("""
        SELECT
            users.id,
            users.username
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


# =========================================
# HENT MELDINGER
# =========================================

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
        SELECT
            messages.id,
            messages.content,
            messages.created_at,
            messages.user_id,
            messages.edited,
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
                "edited": message["edited"],
                "username": message["username"]
            }
            for message in messages
        ]
    })


# =========================================
# SEND MELDING
# =========================================

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


# =========================================
# REDIGER MELDING
# =========================================

@app.route("/edit_message/<int:message_id>", methods=["POST"])
def edit_message(message_id):

    if "user_id" not in session:
        return jsonify({
            "success": False,
            "error": "Ikke innlogget"
        }), 401

    data = request.get_json(silent=True) or {}

    content = data.get("content", "").strip()

    if content == "":
        return jsonify({
            "success": False,
            "error": "Meldingen kan ikke være tom"
        }), 400

    connection = get_database()

    message = connection.execute("""
        SELECT
            id,
            content,
            user_id,
            group_id
        FROM messages
        WHERE id = ?
    """, (message_id,)).fetchone()

    if not message:
        connection.close()
        return jsonify({
            "success": False,
            "error": "Meldingen finnes ikke"
        }), 404

    if message["user_id"] != session["user_id"]:
        connection.close()
        return jsonify({
            "success": False,
            "error": "Du kan bare redigere dine egne meldinger"
        }), 403

    membership = connection.execute("""
        SELECT *
        FROM group_members
        WHERE group_id = ?
        AND user_id = ?
    """, (
        message["group_id"],
        session["user_id"]
    )).fetchone()

    if not membership:
        connection.close()
        return jsonify({
            "success": False,
            "error": "Du er ikke medlem av denne gruppen"
        }), 403

    connection.execute("""
        UPDATE messages
        SET content = ?,
            edited = 1
        WHERE id = ?
    """, (
        content,
        message_id
    ))

    connection.commit()
    connection.close()

    return jsonify({
        "success": True,
        "content": content,
        "edited": True
    })


# =========================================
# SLETT MELDING
# =========================================

@app.route("/delete_message/<int:message_id>", methods=["POST"])
def delete_message(message_id):

    if "user_id" not in session:
        return jsonify({
            "success": False,
            "error": "Ikke innlogget"
        }), 401

    connection = get_database()

    message = connection.execute("""
        SELECT
            id,
            user_id,
            group_id
        FROM messages
        WHERE id = ?
    """, (message_id,)).fetchone()

    if not message:
        connection.close()
        return jsonify({
            "success": False,
            "error": "Meldingen finnes ikke"
        }), 404

    # Bare den som skrev meldingen kan slette den
    if message["user_id"] != session["user_id"]:
        connection.close()
        return jsonify({
            "success": False,
            "error": "Du kan bare slette dine egne meldinger"
        }), 403

    # Sjekk at brukeren fortsatt er medlem av gruppen
    membership = connection.execute("""
        SELECT *
        FROM group_members
        WHERE group_id = ?
        AND user_id = ?
    """, (
        message["group_id"],
        session["user_id"]
    )).fetchone()

    if not membership:
        connection.close()
        return jsonify({
            "success": False,
            "error": "Du er ikke medlem av denne gruppen"
        }), 403

    connection.execute("""
        DELETE FROM messages
        WHERE id = ?
    """, (message_id,))

    connection.commit()
    connection.close()

    return jsonify({
        "success": True,
        "message_id": message_id
    })


# =========================================
# OPPRETT GRUPPE
# =========================================

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


# =========================================
# SLETT GRUPPE
# =========================================

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


# =========================================
# FJERN MEDLEM
# =========================================

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


# =========================================
# LEGG TIL MEDLEM
# =========================================

@app.route("/add_member/<int:group_id>", methods=["POST"])
def add_member(group_id):

    if "user_id" not in session:
        return redirect(url_for("login"))

    username = request.form.get("username", "").strip()

    if username == "":
        return redirect(url_for("group", group_id=group_id))

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

    user = connection.execute("""
        SELECT id, username
        FROM users
        WHERE username = ?
    """, (username,)).fetchone()

    if not user:
        connection.close()
        return redirect(url_for("group", group_id=group_id))

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


# =========================================
# BRUKERSØK
# =========================================

@app.route("/search_users/<int:group_id>")
def search_users(group_id):

    if "user_id" not in session:
        return jsonify({"users": []})

    connection = get_database()

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
        SELECT
            users.id,
            users.username
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


# =========================================
# REGISTRERING
# =========================================

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        username = request.form.get(
            "username",
            ""
        ).strip()

        password = request.form.get(
            "password",
            ""
        )

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


# =========================================
# LOGIN
# =========================================

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        username = request.form.get(
            "username",
            ""
        ).strip()

        password = request.form.get(
            "password",
            ""
        )

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

# =========================================
# PROFIL
# =========================================

@app.route("/profile")
def profile():

    if "user_id" not in session:
        return redirect(url_for("login"))

    return user_profile(session["user_id"], own_profile=True)


@app.route("/user/<int:user_id>")
def public_profile(user_id):

    if "user_id" not in session:
        return redirect(url_for("login"))

    return user_profile(
        user_id,
        own_profile=(user_id == session["user_id"])
    )


def user_profile(user_id, own_profile=False):

    connection = get_database()

    user = connection.execute("""
        SELECT
            id,
            username,
            display_name,
            bio,
            created_at
        FROM users
        WHERE id = ?
    """, (user_id,)).fetchone()

    if not user:
        connection.close()
        return redirect(url_for("home"))

    message_count = connection.execute("""
        SELECT COUNT(*) AS count
        FROM messages
        WHERE user_id = ?
    """, (user_id,)).fetchone()["count"]

    group_count = connection.execute("""
        SELECT COUNT(*) AS count
        FROM group_members
        WHERE user_id = ?
    """, (user_id,)).fetchone()["count"]

    connection.close()

    return render_template(
        "profile.html",
        user=user,
        message_count=message_count,
        group_count=group_count,
        own_profile=own_profile
    )

    if "user_id" not in session:
        return redirect(url_for("login"))

    connection = get_database()

    user = connection.execute("""
        SELECT
            id,
            username,
            display_name,
            bio,
            created_at
        FROM users
        WHERE id = ?
    """, (session["user_id"],)).fetchone()

    if not user:
        connection.close()
        return redirect(url_for("logout"))

    message_count = connection.execute("""
        SELECT COUNT(*) AS count
        FROM messages
        WHERE user_id = ?
    """, (session["user_id"],)).fetchone()["count"]

    group_count = connection.execute("""
        SELECT COUNT(*) AS count
        FROM group_members
        WHERE user_id = ?
    """, (session["user_id"],)).fetchone()["count"]

    connection.close()

    return render_template(
        "profile.html",
        user=user,
        message_count=message_count,
        group_count=group_count
    )


# =========================================
# REDIGER PROFIL
# =========================================

@app.route("/edit_profile", methods=["GET", "POST"])
def edit_profile():

    if "user_id" not in session:
        return redirect(url_for("login"))

    connection = get_database()

    if request.method == "POST":

        display_name = request.form.get(
            "display_name",
            ""
        ).strip()

        bio = request.form.get(
            "bio",
            ""
        ).strip()

        if display_name == "":
            display_name = session["username"]

        connection.execute("""
            UPDATE users
            SET display_name = ?,
                bio = ?
            WHERE id = ?
        """, (
            display_name,
            bio,
            session["user_id"]
        ))

        connection.commit()
        connection.close()

        return redirect(url_for("profile"))

    user = connection.execute("""
        SELECT
            username,
            display_name,
            bio
        FROM users
        WHERE id = ?
    """, (session["user_id"],)).fetchone()

    connection.close()

    return render_template(
        "edit_profile.html",
        user=user
    )

# =========================================
# LOGG UT
# =========================================

@app.route("/logout")
def logout():

    session.clear()

    return redirect(url_for("login"))


# =========================================
# START
# =========================================

if __name__ == "__main__":
    app.run(debug=True)