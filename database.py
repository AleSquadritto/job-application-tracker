import json
import os

import mysql.connector


def get_db():
    """Open a new MySQL connection using environment settings."""
    return mysql.connector.connect(
        host=os.environ.get("DB_HOST", "localhost"),
        user=os.environ.get("DB_USER", "root"),
        password=os.environ.get("DB_PASSWORD", ""),
        database=os.environ.get("DB_NAME", "job_tracker"),
    )


def query(sql, params=(), one=False):
    """Run a SELECT. Returns a list of dicts, or one dict/None if one=True."""
    conn = get_db()
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(sql, params)
        rows = cursor.fetchall()
        if one:
            return rows[0] if rows else None
        return rows
    finally:
        conn.close()


def execute(sql, params=()):
    """Run an INSERT/UPDATE/DELETE and commit. Returns the last inserted id."""
    conn = get_db()
    try:
        cursor = conn.cursor()
        cursor.execute(sql, params)
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()


def parse_json(value):
    """Turn a JSON column value (str/bytes/None) into a Python object, or None."""
    if value is None:
        return None
    if isinstance(value, (bytes, bytearray)):
        value = value.decode("utf-8")
    if isinstance(value, (dict, list)):
        return value
    try:
        return json.loads(value)
    except (TypeError, ValueError):
        return None