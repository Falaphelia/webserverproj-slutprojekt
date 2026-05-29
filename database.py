import sqlite3
import bcrypt
import time
import uuid

DB_PATH = 'data/data.db'

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def create_uid():
    return str(uuid.uuid4())

def init_db():
    with get_connection() as conn:
        cursor = conn.cursor()
        # Accounts
        cursor.execute('''CREATE TABLE IF NOT EXISTS accounts (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            uid TEXT UNIQUE,
                            first_name TEXT,
                            last_name TEXT,
                            email TEXT UNIQUE,
                            creation_date INTEGER)''')
        # Credentials
        cursor.execute('''CREATE TABLE IF NOT EXISTS credentials (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            target_uid TEXT UNIQUE,
                            hashed_password BLOB)''')
        # User Lists
        cursor.execute('''CREATE TABLE IF NOT EXISTS user_lists (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            owner_uid TEXT,
                            list_name TEXT)''')
        # List Items
        cursor.execute('''CREATE TABLE IF NOT EXISTS list_items (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            target_list INTEGER,
                            content TEXT,
                            description TEXT)''')
        conn.commit()


def get_hashed_password(plain_password):
    return bcrypt.hashpw(plain_password.encode('utf-8'), bcrypt.gensalt())

def register_user(f_name, l_name, email, password):
    hashed = get_hashed_password(password)

    created_at = int(time.time())

    if match_user_email(email):
        return False

    with get_connection() as conn:
        cursor = conn.cursor()

        uid = create_uid()

        cursor.execute("""
            INSERT INTO accounts (uid, first_name, last_name, email, creation_date)
            VALUES (?,?,?,?,?)
        """, (uid, f_name, l_name, email, created_at))

        cursor.execute("INSERT INTO credentials (target_uid, hashed_password) VALUES (?,?)",
                       (uid, hashed))
        conn.commit()
        return True


def match_user_email(email):
    with get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute(
        "SELECT email FROM accounts WHERE email = ?",
        (email,)
        )

        result = cursor.fetchone()

        if result:
            return True
        else:
            return False

def login(email, password):
    with get_connection() as conn:
        cursor = conn.cursor()

        # Get account
        cursor.execute(
            "SELECT uid FROM accounts WHERE email = ?",
            (email,)
        )

        account = cursor.fetchone()

        if not account:
            return False

        uid = account["uid"]

        # Get password hash
        cursor.execute(
            "SELECT hashed_password FROM credentials WHERE target_uid = ?",
            (uid,)
        )

        credentials = cursor.fetchone()

        if not credentials:
            return False

        stored_hash = credentials["hashed_password"]

        # Check password
        if bcrypt.checkpw(
            password.encode("utf-8"),
            stored_hash
        ):
            return uid

        return False

def create_list(list_name, uid):
    with get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute(
            "INSERT INTO user_lists (owner_uid, list_name) VALUES (?, ?)",
            (uid, list_name)
        )

        conn.commit()


def delete_list(uid, list_id):
    with get_connection() as conn:
        cursor = conn.cursor()

        # Make sure the user owns the list
        cursor.execute(
            "SELECT id FROM user_lists WHERE id = ? AND owner_uid = ?",
            (list_id, uid)
        )

        owned_list = cursor.fetchone()

        if not owned_list:
            return False

        # Delete entries first to make sure there are no ghosts / unreferenced entries
        cursor.execute(
            "DELETE FROM list_items WHERE target_list = ?",
            (list_id,)
        )

        # Delete list
        cursor.execute(
            "DELETE FROM user_lists WHERE id = ?",
            (list_id,)
        )

        conn.commit()

        return True


def get_user_lists(uid):
    with get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute(
            "SELECT * FROM user_lists WHERE owner_uid = ?",
            (uid,)
        )

        all_lists = cursor.fetchall()

        final_lists = []

        for current_list in all_lists:

            cursor.execute(
                "SELECT * FROM list_items WHERE target_list = ?",
                (current_list["id"],)
            )

            entries = cursor.fetchall()

            formatted_entries = []

            for entry in entries:
                formatted_entries.append({
                    "entry_id": entry["id"],
                    "title": entry["content"],
                    "description": entry["description"]
                })

            final_lists.append({
                "list_id": current_list["id"],
                "name": current_list["list_name"],
                "entries": formatted_entries
            })

        return final_lists


def create_list_entry(list_id, content, description):
    with get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO list_items
            (target_list, content, description)
            VALUES (?, ?, ?)
            """,
            (list_id, content, description)
        )

        conn.commit()


def get_list_entries(list_id):
    with get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute(
            "SELECT * FROM list_items WHERE target_list = ?",
            (list_id,)
        )

        return cursor.fetchall()


def delete_list_entry(uid, entry_id):
    with get_connection() as conn:
        cursor = conn.cursor()

        # Verify ownership through the list
        cursor.execute(
            """
            SELECT list_items.id
            FROM list_items
            JOIN user_lists
            ON list_items.target_list = user_lists.id
            WHERE list_items.id = ?
            AND user_lists.owner_uid = ?
            """,
            (entry_id, uid)
        )

        owned_entry = cursor.fetchone()

        if not owned_entry:
            return False

        cursor.execute(
            "DELETE FROM list_items WHERE id = ?",
            (entry_id,)
        )

        conn.commit()

        return True
