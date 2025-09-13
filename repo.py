from typing import List, Dict, Any, Optional
from db import connect

# ---------- PROXIES ----------

def list_proxies() -> List[Dict[str, Any]]:
    con = connect(); cur = con.cursor()
    rows = cur.execute("SELECT * FROM proxies ORDER BY id DESC").fetchall()
    con.close(); return [dict(r) for r in rows]

def get_proxy(pid: int) -> Optional[Dict[str, Any]]:
    con = connect(); cur = con.cursor()
    row = cur.execute("SELECT * FROM proxies WHERE id=?", (pid,)).fetchone()
    con.close(); return dict(row) if row else None

def create_proxy(p: Dict[str, Any]) -> int:
    con = connect(); cur = con.cursor()
    cur.execute(
        """
        INSERT INTO proxies (name, proxy_type, host, port, username, password)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            p["name"].strip(), p.get("proxy_type", "http"), p["host"].strip(), int(p["port"]),
            p.get("username"), p.get("password"),
        ),
    )
    con.commit(); rid = cur.lastrowid; con.close(); return rid

def update_proxy(pid: int, p: Dict[str, Any]):
    con = connect(); cur = con.cursor()
    cur.execute(
        """
        UPDATE proxies
        SET name=?, proxy_type=?, host=?, port=?, username=?, password=?, updated_at=datetime('now')
        WHERE id=?
        """,
        (
            p["name"].strip(), p.get("proxy_type", "http"), p["host"].strip(), int(p["port"]),
            p.get("username"), p.get("password"), pid,
        ),
    )
    con.commit(); con.close()

def delete_proxy(pid: int):
    con = connect(); cur = con.cursor()
    # Nếu xoá proxy đang gán cho profile -> SET NULL
    cur.execute("UPDATE profiles SET proxy_id=NULL, updated_at=datetime('now') WHERE proxy_id=?", (pid,))
    cur.execute("DELETE FROM proxies WHERE id=?", (pid,))
    con.commit(); con.close()

# ---------- PROFILES ----------

def list_profiles() -> List[Dict[str, Any]]:
    con = connect(); cur = con.cursor()
    rows = cur.execute(
        """
        SELECT p.*, pr.name AS proxy_name, pr.proxy_type, pr.host, pr.port, pr.username
        FROM profiles p
        LEFT JOIN proxies pr ON pr.id = p.proxy_id
        ORDER BY p.id DESC
        """
    ).fetchall()
    con.close(); return [dict(r) for r in rows]

def get_profile(pid: int) -> Optional[Dict[str, Any]]:
    con = connect(); cur = con.cursor()
    row = cur.execute("SELECT * FROM profiles WHERE id=?", (pid,)).fetchone()
    con.close(); return dict(row) if row else None

def create_profile(p: Dict[str, Any]) -> int:
    con = connect(); cur = con.cursor()
    cur.execute(
        """
        INSERT INTO profiles (name, proxy_id)
        VALUES (?, ?)
        """,
        (
            p["name"].strip(), p.get("proxy_id"),
        ),
    )
    con.commit(); rid = cur.lastrowid; con.close(); return rid

def update_profile(pid: int, p: Dict[str, Any]):
    con = connect(); cur = con.cursor()
    cur.execute(
        """
        UPDATE profiles
        SET name=?, proxy_id=?, updated_at=datetime('now')
        WHERE id=?
        """,
        (
            p["name"].strip(), p.get("proxy_id"), pid,
        ),
    )
    con.commit(); con.close()

def delete_profile(pid: int):
    con = connect(); cur = con.cursor()
    cur.execute("DELETE FROM profiles WHERE id=?", (pid,))
    con.commit(); con.close()