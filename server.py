#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Vietugram — Chat Server v4.0
Developer: Vietu
Full-featured realtime chat: WebSocket, WebRTC, roles, file storage, bot API
"""

import eventlet
eventlet.monkey_patch()

import os
import sys
import json
import time
import uuid
import base64
import hashlib
import hmac
import secrets
import logging
import shutil
import argparse
from datetime import datetime, timedelta
from logging.handlers import RotatingFileHandler
from flask import Flask, request, send_from_directory, jsonify, abort
from flask_socketio import SocketIO, emit, join_room, leave_room, disconnect

# ─── ARGPARSE ────────────────────────────────────────────────────────────────
parser = argparse.ArgumentParser(description='Vietugram Server')
parser.add_argument('--host', default='0.0.0.0', help='Host to listen on (default: 0.0.0.0)')
parser.add_argument('--port', type=int, default=5000, help='Port to listen on (default: 5000)')
args, _ = parser.parse_known_args()

# ─── CONFIGURATION ────────────────────────────────────────────────────────────
HOST = args.host
PORT = args.port
ADMIN_CODE = "GGCheck"           # Change before deploying!
VETERAN_MSG_THRESHOLD = 1000
MAX_IMAGE_SIZE = 5 * 1024 * 1024  # 5 MB
MAX_AVATAR_SIZE = 2 * 1024 * 1024  # 2 MB
BACKUP_INTERVAL = 3600            # seconds between auto backups

# ─── DATA DIRECTORIES ────────────────────────────────────────────────────────
DATA_DIRS = [
    "data/users", "data/rooms", "data/messages",
    "data/friends/requests", "data/friends/lists",
    "data/private_messages", "data/uploads/avatars",
    "data/bans", "data/roles", "data/leaderboard",
    "data/settings", "data/logs_action",
    "backups", "logs",
]

def ensure_dirs():
    for d in DATA_DIRS:
        os.makedirs(d, exist_ok=True)

ensure_dirs()

# ─── LOGGING ─────────────────────────────────────────────────────────────────
log_handler = RotatingFileHandler('logs/server.log', maxBytes=5*1024*1024, backupCount=3, encoding='utf-8')
log_handler.setLevel(logging.INFO)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[log_handler, logging.StreamHandler()]
)
logger = logging.getLogger('vietugram')

# ─── FLASK & SOCKETIO ────────────────────────────────────────────────────────
app = Flask(__name__, static_folder='.', static_url_path='')
app.config['SECRET_KEY'] = secrets.token_hex(32)
socketio = SocketIO(
    app,
    cors_allowed_origins='*',
    async_mode='eventlet',
    max_http_buffer_size=50 * 1024 * 1024,
    ping_timeout=60,
    ping_interval=25
)

# ─── IN-MEMORY STATE ─────────────────────────────────────────────────────────
users = {}           # username -> {...}
sessions = {}        # sid -> username
sessions_token = {}  # username -> token
rooms = {}           # room_id -> {...}
room_members = {}    # room_id -> set of sids
room_messages = {}   # room_id -> [messages]
custom_roles = {}    # role_name -> {color, emoji, prefix}
bans = set()         # usernames
observer_mode = {}   # username -> bool
veteran_awarded = set()
global_announcement = ''
global_join_msg = ''
action_log = []      # [{time, actor, action}]
spam_limits = {}     # room_id -> {username: delay_sec}
last_msg_time = {}   # room_id -> {username: timestamp}
chat_time_start = {} # sid -> timestamp when joined room
voice_rooms_active = {}  # room_id -> set of sids (voice)

# ─── DISK I/O HELPERS ────────────────────────────────────────────────────────
def atomic_write(path, data):
    tmp = path + '.tmp'
    try:
        with open(tmp, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        os.replace(tmp, path)
    except Exception as e:
        logger.error(f"atomic_write error {path}: {e}")

def read_json(path, default=None):
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return default if default is not None else {}

def save_user(username):
    if username in users:
        atomic_write(f"data/users/{username}.json", users[username])

def save_room(room_id):
    if room_id in rooms:
        r = dict(rooms[room_id])
        r.pop('password_hash', None)  # keep password separately
        atomic_write(f"data/rooms/{room_id}.json", rooms[room_id])

def save_messages(room_id):
    if room_id in room_messages:
        atomic_write(f"data/messages/{room_id}.json", room_messages[room_id])

def save_roles():
    atomic_write("data/roles/roles.json", custom_roles)

def save_bans():
    atomic_write("data/bans/bans.json", list(bans))

def save_settings():
    atomic_write("data/settings/global.json", {
        "global_announcement": global_announcement,
        "global_join_msg": global_join_msg,
    })

def save_action_log():
    atomic_write("data/logs_action/log.json", action_log[-2000:])

def save_friends(username):
    u = users.get(username, {})
    atomic_write(f"data/friends/lists/{username}.json", {
        "friends": u.get("friends", []),
        "requests_out": u.get("requests_out", []),
        "requests_in": u.get("requests_in", []),
    })

def save_pm(pm_id, messages):
    atomic_write(f"data/private_messages/{pm_id}.json", messages)

def save_leaderboard():
    lb = [build_user_info(u) for u in users]
    atomic_write("data/leaderboard/cache.json", lb)

def add_action_log(actor, action):
    entry = {"time": now_str(), "actor": actor, "action": action}
    action_log.append(entry)
    if len(action_log) > 2000:
        action_log.pop(0)
    eventlet.spawn(save_action_log)

# ─── LOAD DATA FROM DISK ─────────────────────────────────────────────────────
def load_all_data():
    global global_announcement, global_join_msg

    # Users
    for fname in os.listdir("data/users"):
        if fname.endswith(".json"):
            uname = fname[:-5]
            data = read_json(f"data/users/{fname}")
            if data:
                users[uname] = data
                if data.get("banned"):
                    bans.add(uname)

    # Rooms
    for fname in os.listdir("data/rooms"):
        if fname.endswith(".json"):
            room_id = fname[:-5]
            data = read_json(f"data/rooms/{fname}")
            if data:
                rooms[room_id] = data
                room_members[room_id] = set()

    # Messages
    for fname in os.listdir("data/messages"):
        if fname.endswith(".json"):
            room_id = fname[:-5]
            data = read_json(f"data/messages/{fname}", [])
            room_messages[room_id] = data

    # Roles
    roles_data = read_json("data/roles/roles.json", {})
    custom_roles.update(roles_data)

    # Bans
    bans_data = read_json("data/bans/bans.json", [])
    bans.update(bans_data)

    # Friends (merge into users)
    for fname in os.listdir("data/friends/lists"):
        if fname.endswith(".json"):
            uname = fname[:-5]
            data = read_json(f"data/friends/lists/{fname}", {})
            if uname in users:
                users[uname]["friends"] = data.get("friends", [])
                users[uname]["requests_in"] = data.get("requests_in", [])
                users[uname]["requests_out"] = data.get("requests_out", [])

    # Settings
    settings = read_json("data/settings/global.json", {})
    global_announcement = settings.get("global_announcement", "")
    global_join_msg = settings.get("global_join_msg", "")

    # Action log
    log_data = read_json("data/logs_action/log.json", [])
    action_log.extend(log_data)

    # Room messages for rooms that exist
    for room_id in rooms:
        if room_id not in room_messages:
            path = f"data/messages/{room_id}.json"
            room_messages[room_id] = read_json(path, [])

    logger.info(f"Loaded: {len(users)} users, {len(rooms)} rooms, {len(custom_roles)} roles")

# ─── HELPERS ─────────────────────────────────────────────────────────────────
def hash_password(pw: str) -> str:
    salt = b"vietugram_salt_v4"
    return hmac.new(salt, pw.encode('utf-8'), hashlib.sha256).hexdigest()

def generate_token() -> str:
    return secrets.token_hex(32)

def generate_id() -> str:
    return str(uuid.uuid4())[:8]

def now_ts() -> int:
    return int(time.time() * 1000)

def now_str() -> str:
    return datetime.now().strftime("%H:%M:%S %d.%m.%Y")

def now_time() -> str:
    return datetime.now().strftime("%H:%M")

def get_user(sid: str):
    return sessions.get(sid)

def get_role(username: str) -> str:
    return users.get(username, {}).get("role", "user")

def role_priority(role: str) -> int:
    return {"admin": 4, "moderator": 3, "owner": 2, "veteran": 1, "user": 0, "bot": 0}.get(role, 0)

def can_moderate(username: str) -> bool:
    return get_role(username) in ("admin", "moderator")

def can_admin(username: str) -> bool:
    return get_role(username) == "admin"

def is_room_owner(room_id: str, username: str) -> bool:
    return rooms.get(room_id, {}).get("owner") == username

def can_manage_room(room_id: str, username: str) -> bool:
    return can_moderate(username) or is_room_owner(room_id, username)

def build_user_info(username: str) -> dict:
    u = users.get(username, {})
    cr_name = u.get("custom_role")
    cr = custom_roles.get(cr_name) if cr_name and cr_name in custom_roles else None
    return {
        "username": username,
        "role": u.get("role", "user"),
        "custom_role": cr_name,
        "custom_role_data": cr,
        "total_msgs": u.get("total_msgs", 0),
        "reactions_received": u.get("reactions_received", 0),
        "chat_time": u.get("chat_time", 0),
        "bio": u.get("bio", ""),
        "avatar": u.get("avatar", ""),
        "banned": u.get("banned", False),
        "is_observer": observer_mode.get(username, False),
        "friends": u.get("friends", []),
    }

def get_room_members_info(room_id: str) -> list:
    members = []
    seen = set()
    for sid, uname in sessions.items():
        if sid in room_members.get(room_id, set()) and uname not in seen:
            if observer_mode.get(uname, False):
                continue
            seen.add(uname)
            info = build_user_info(uname)
            members.append(info)
    members.sort(key=lambda x: -role_priority(x["role"]))
    return members

def get_sid_of_user(username: str):
    for sid, uname in sessions.items():
        if uname == username:
            return sid
    return None

def check_veteran(username: str):
    u = users.get(username, {})
    if username not in veteran_awarded and u.get("total_msgs", 0) >= VETERAN_MSG_THRESHOLD:
        if u.get("role", "user") == "user":
            users[username]["role"] = "veteran"
            veteran_awarded.add(username)
            save_user(username)
            # notify all sids of this user
            sid = get_sid_of_user(username)
            if sid:
                info = build_user_info(username)
                socketio.emit("role_updated", info, room=sid)
                socketio.emit("notification", {"message": "🏆 Вы получили звание Ветерана!", "type": "success"}, room=sid)

def build_rooms_list(for_admin=False) -> list:
    result = []
    for rid, r in rooms.items():
        members_count = len([
            s for s in room_members.get(rid, set())
            if not observer_mode.get(sessions.get(s, ""), False)
        ])
        if r.get("is_hidden") and not for_admin:
            continue
        if r.get("is_bot_room") and not for_admin:
            continue
        result.append({
            "id": rid,
            "name": r["name"],
            "has_password": bool(r.get("password")),
            "is_voice": r.get("is_voice", False),
            "is_anonymous": r.get("is_anonymous", False),
            "is_bot_room": r.get("is_bot_room", False),
            "is_hidden": r.get("is_hidden", False),
            "owner": r.get("owner", ""),
            "members_count": members_count,
            "lifetime_ms": r.get("lifetime_ms"),
            "created_at": r.get("created_at"),
            "spam_delay": r.get("spam_delay", 0),
            "pinned": r.get("pinned", False),
            "custom_join_msg": r.get("custom_join_msg", ""),
        })
    return result

def broadcast_rooms():
    # send full list to admins, filtered to regular users
    for sid, uname in sessions.items():
        is_admin = can_admin(uname)
        socketio.emit("rooms_list", build_rooms_list(for_admin=is_admin), room=sid)

def save_image_base64(data_url: str, folder="data/uploads") -> str:
    """Save base64 image, return URL path"""
    try:
        header, encoded = data_url.split(",", 1)
        ext = "jpg"
        if "png" in header:
            ext = "png"
        elif "gif" in header:
            ext = "gif"
        elif "webp" in header:
            ext = "webp"
        img_bytes = base64.b64decode(encoded)
        if len(img_bytes) > MAX_IMAGE_SIZE:
            return None
        fname = f"{generate_id()}.{ext}"
        path = os.path.join(folder, fname)
        os.makedirs(folder, exist_ok=True)
        with open(path, 'wb') as f:
            f.write(img_bytes)
        return f"/uploads/{fname}"
    except Exception as e:
        logger.error(f"save_image error: {e}")
        return None

def save_avatar_base64(data_url: str, username: str) -> str:
    try:
        header, encoded = data_url.split(",", 1)
        ext = "jpg"
        if "png" in header:
            ext = "png"
        img_bytes = base64.b64decode(encoded)
        if len(img_bytes) > MAX_AVATAR_SIZE:
            return None
        fname = f"{username}.{ext}"
        path = f"data/uploads/avatars/{fname}"
        with open(path, 'wb') as f:
            f.write(img_bytes)
        return f"/avatars/{fname}"
    except Exception as e:
        logger.error(f"save_avatar error: {e}")
        return None

# ─── ROOM CLEANUP ─────────────────────────────────────────────────────────────
def room_cleanup_worker():
    while True:
        eventlet.sleep(15)
        now = now_ts()
        to_delete = []
        for rid, room in list(rooms.items()):
            if room.get("lifetime_ms") and room.get("created_at"):
                if now - room["created_at"] > room["lifetime_ms"]:
                    to_delete.append(rid)
        for rid in to_delete:
            _delete_room(rid, "Комната истекла")

eventlet.spawn(room_cleanup_worker)

# ─── AUTO BACKUP ─────────────────────────────────────────────────────────────
def auto_backup_worker():
    while True:
        eventlet.sleep(BACKUP_INTERVAL)
        do_backup("auto")

def do_backup(tag="manual"):
    try:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        dest = f"backups/{tag}_{ts}"
        shutil.copytree("data", dest)
        logger.info(f"Backup created: {dest}")
    except Exception as e:
        logger.error(f"Backup failed: {e}")

eventlet.spawn(auto_backup_worker)

# ─── DELETE ROOM HELPER ───────────────────────────────────────────────────────
def _delete_room(rid, reason="Удалено"):
    room_name = rooms.get(rid, {}).get("name", rid)
    # notify members
    socketio.emit("room_deleted", {"room_id": rid, "reason": reason}, room=rid)
    # remove members from room
    for sid in list(room_members.get(rid, set())):
        try:
            leave_room(rid, sid=sid)
        except:
            pass
    rooms.pop(rid, None)
    room_messages.pop(rid, None)
    room_members.pop(rid, None)
    # remove files
    try:
        room_file = f"data/rooms/{rid}.json"
        if os.path.exists(room_file):
            os.remove(room_file)
        msg_file = f"data/messages/{rid}.json"
        if os.path.exists(msg_file):
            os.remove(msg_file)
    except Exception as e:
        logger.error(f"Error removing room files {rid}: {e}")
    broadcast_rooms()
    logger.info(f"Room deleted: {room_name} ({rid}) — {reason}")

# ─── HTTP ROUTES ─────────────────────────────────────────────────────────────
@app.route("/")
def index():
    return send_from_directory(".", "index.html")

@app.route("/uploads/<path:filename>")
def serve_upload(filename):
    return send_from_directory("data/uploads", filename)

@app.route("/avatars/<path:filename>")
def serve_avatar(filename):
    return send_from_directory("data/uploads/avatars", filename)

@app.route("/api/rooms")
def api_rooms():
    return jsonify(build_rooms_list())

@app.route("/api/bot/connect", methods=["POST"])
def api_bot_connect():
    data = request.json or {}
    token = data.get("token", "")
    bot_name = data.get("bot_name", "Bot")
    room_name = data.get("room_name", f"🤖 {bot_name}")
    if not token or len(token) < 8:
        return jsonify({"error": "Token must be at least 8 characters"}), 400
    bot_username = f"BOT_{bot_name}"
    if bot_username not in users:
        users[bot_username] = {
            "password_hash": hash_password(token),
            "role": "bot",
            "total_msgs": 0,
            "join_time": now_ts(),
            "reactions_received": 0,
            "chat_time": 0,
            "bio": "Бот",
            "avatar": "",
            "friends": [],
            "requests_in": [],
            "requests_out": [],
        }
        save_user(bot_username)
    rid = f"bot_{generate_id()}"
    rooms[rid] = {
        "name": room_name,
        "password": None,
        "owner": bot_username,
        "is_voice": False,
        "is_anonymous": False,
        "is_bot_room": True,
        "is_hidden": True,
        "bot_token": token,
        "created_at": now_ts(),
        "spam_delay": 0,
        "pinned": False,
        "custom_join_msg": "",
        "pinned_msg": None,
    }
    room_members[rid] = set()
    room_messages[rid] = []
    save_room(rid)
    broadcast_rooms()
    return jsonify({"room_id": rid, "bot_username": bot_username, "status": "connected"})

@app.route("/api/bot/send", methods=["POST"])
def api_bot_send():
    data = request.json or {}
    token = data.get("token", "")
    room_id = data.get("room_id", "")
    text = data.get("text", "")
    if not token or room_id not in rooms:
        return jsonify({"error": "Invalid params"}), 400
    room = rooms[room_id]
    if not room.get("is_bot_room") or room.get("bot_token") != token:
        return jsonify({"error": "Unauthorized"}), 403
    msg = _build_message(room["owner"], text, None, False, [], room_id)
    room_messages.setdefault(room_id, []).append(msg)
    socketio.emit("message", msg, room=room_id)
    eventlet.spawn(save_messages, room_id)
    return jsonify({"status": "ok", "message_id": msg["id"]})

@app.route("/api/bot/messages")
def api_bot_messages():
    token = request.args.get("token", "")
    room_id = request.args.get("room_id", "")
    since = int(request.args.get("since", 0))
    if not token or room_id not in rooms:
        return jsonify({"error": "Invalid params"}), 400
    room = rooms[room_id]
    if not room.get("is_bot_room") or room.get("bot_token") != token:
        return jsonify({"error": "Unauthorized"}), 403
    msgs = [m for m in room_messages.get(room_id, []) if m.get("ts", 0) > since]
    return jsonify({"messages": msgs})

@app.route("/api/backup", methods=["POST"])
def api_backup():
    # only allow if admin header present (simple token)
    token = request.headers.get("X-Admin-Token", "")
    if not any(sessions_token.get(u) == token for u in users if can_admin(u)):
        return jsonify({"error": "Unauthorized"}), 403
    eventlet.spawn(do_backup, "api")
    return jsonify({"status": "backup scheduled"})

# ─── MESSAGE BUILDER ─────────────────────────────────────────────────────────
def _build_message(author, text, image_url, is_announcement, msg_tags, room_id):
    u = users.get(author, {})
    cr_name = u.get("custom_role")
    cr = custom_roles.get(cr_name) if cr_name and cr_name in custom_roles else None
    return {
        "id": generate_id(),
        "room_id": room_id,
        "author": author,
        "author_role": u.get("role", "user"),
        "author_avatar": u.get("avatar", ""),
        "custom_role_data": cr,
        "text": text,
        "image": image_url,
        "timestamp": now_time(),
        "ts": now_ts(),
        "is_announcement": is_announcement,
        "is_system": False,
        "msg_tags": msg_tags or [],
        "reactions": {},
        "edited": False,
        "deleted": False,
        "pinned": False,
    }

def _build_system_message(text, room_id):
    return {
        "id": generate_id(),
        "room_id": room_id,
        "author": "__system__",
        "text": text,
        "timestamp": now_time(),
        "ts": now_ts(),
        "is_system": True,
        "is_announcement": False,
        "msg_tags": [],
        "reactions": {},
        "edited": False,
        "deleted": False,
    }

# ─── SOCKET EVENTS ────────────────────────────────────────────────────────────

@socketio.on("connect")
def on_connect():
    logger.info(f"Client connected: {request.sid}")

@socketio.on("disconnect")
def on_disconnect():
    sid = request.sid
    username = sessions.pop(sid, None)
    if not username:
        return
    logger.info(f"Client disconnected: {username} ({sid})")
    # Update chat time
    if sid in chat_time_start:
        elapsed = now_ts() - chat_time_start.pop(sid)
        users[username]["chat_time"] = users.get(username, {}).get("chat_time", 0) + elapsed
        save_user(username)
    # leave all rooms
    for rid in list(room_members.keys()):
        if sid in room_members[rid]:
            room_members[rid].discard(sid)
            room = rooms.get(rid, {})
            is_anon = room.get("is_anonymous", False)
            if not is_anon and not observer_mode.get(username, False):
                sys_msg = _build_system_message(f"👋 {username} покинул(а) чат", rid)
                room_messages.setdefault(rid, []).append(sys_msg)
                socketio.emit("message", sys_msg, room=rid)
            members = get_room_members_info(rid)
            socketio.emit("members_update", {"room_id": rid, "members": members}, room=rid)
            voice_rooms_active.get(rid, set()).discard(sid)
            socketio.emit("voice_member_left", {"room_id": rid, "username": username}, room=rid)
    broadcast_rooms()

def _auth_user(username, role=None, token=None):
    """Send auth success to current sid"""
    sid = request.sid
    sessions[sid] = username
    sessions_token[username] = token or generate_token()
    chat_time_start[sid] = now_ts()
    u = users[username]
    cr_name = u.get("custom_role")
    cr = custom_roles.get(cr_name) if cr_name and cr_name in custom_roles else None
    data = {
        "username": username,
        "role": u.get("role", "user"),
        "token": sessions_token[username],
        "custom_role": cr_name,
        "custom_role_data": cr,
        "avatar": u.get("avatar", ""),
        "is_observer": observer_mode.get(username, False),
    }
    emit("auth_success", data)
    if global_announcement:
        emit("global_announcement", {"text": global_announcement})

@socketio.on("register")
def on_register(data):
    username = str(data.get("username", "")).strip()[:32]
    password = str(data.get("password", ""))
    sid = request.sid
    if not username or len(username) < 2:
        emit("register_error", {"message": "Ник должен содержать минимум 2 символа"})
        return
    if not all(c.isalnum() or c in "-_." for c in username):
        emit("register_error", {"message": "Ник может содержать только буквы, цифры, -_."})
        return
    if len(password) < 4:
        emit("register_error", {"message": "Пароль должен содержать минимум 4 символа"})
        return
    if username in users:
        emit("register_error", {"message": "Этот ник уже занят"})
        return
    if username in bans:
        emit("register_error", {"message": "Этот аккаунт заблокирован"})
        return
    users[username] = {
        "password_hash": hash_password(password),
        "role": "user",
        "total_msgs": 0,
        "join_time": now_ts(),
        "reactions_received": 0,
        "chat_time": 0,
        "bio": "",
        "avatar": "",
        "custom_role": None,
        "banned": False,
        "friends": [],
        "requests_in": [],
        "requests_out": [],
    }
    save_user(username)
    logger.info(f"New user registered: {username}")
    _auth_user(username)

@socketio.on("login")
def on_login(data):
    username = str(data.get("username", "")).strip()
    password = str(data.get("password", ""))
    if username not in users:
        emit("login_error", {"message": "Пользователь не найден"})
        return
    u = users[username]
    if u.get("banned"):
        emit("login_error", {"message": "Ваш аккаунт заблокирован"})
        return
    if u.get("password_hash") != hash_password(password):
        emit("login_error", {"message": "Неверный пароль"})
        return
    _auth_user(username)
    logger.info(f"User logged in: {username}")

@socketio.on("autologin")
def on_autologin(data):
    username = str(data.get("username", "")).strip()
    token = str(data.get("token", ""))
    if username not in users:
        return
    if users[username].get("banned"):
        return
    if sessions_token.get(username) == token:
        _auth_user(username, token=token)
    # else silent fail, client will show auth form

@socketio.on("logout")
def on_logout():
    sid = request.sid
    username = sessions.pop(sid, None)
    if username:
        sessions_token.pop(username, None)

@socketio.on("request_rooms")
def on_request_rooms():
    username = get_user(request.sid)
    is_admin = can_admin(username) if username else False
    emit("rooms_list", build_rooms_list(for_admin=is_admin))

@socketio.on("create_room")
def on_create_room(data):
    username = get_user(request.sid)
    if not username:
        return
    name = str(data.get("name", "")).strip()[:64]
    if not name:
        emit("notification", {"message": "Введите название комнаты", "type": "warning"})
        return
    # Check unique
    if any(r["name"] == name for r in rooms.values()):
        emit("notification", {"message": "Комната с таким названием уже существует", "type": "warning"})
        return
    password = str(data.get("password", "")).strip()
    is_voice = bool(data.get("is_voice", False))
    is_anonymous = bool(data.get("is_anonymous", False))
    is_hidden = bool(data.get("is_hidden", False))
    lifetime_sec = int(data.get("lifetime_sec", 0))
    spam_delay = int(data.get("spam_delay", 0))
    rid = generate_id()
    rooms[rid] = {
        "name": name,
        "password": password if password else None,
        "owner": username,
        "is_voice": is_voice,
        "is_anonymous": is_anonymous,
        "is_hidden": is_hidden,
        "is_bot_room": False,
        "lifetime_ms": lifetime_sec * 1000 if lifetime_sec > 0 else None,
        "created_at": now_ts(),
        "spam_delay": spam_delay,
        "pinned": False,
        "custom_join_msg": "",
        "pinned_msg": None,
    }
    room_members[rid] = set()
    room_messages[rid] = []
    save_room(rid)
    logger.info(f"Room created: {name} ({rid}) by {username}")
    # Auto-join
    _do_join_room(request.sid, username, rid, skip_password=True)
    broadcast_rooms()

def _do_join_room(sid, username, room_id, skip_password=False):
    room = rooms.get(room_id)
    if not room:
        emit("room_join_error", {"message": "Комната не найдена"}, room=sid)
        return
    if room.get("password") and not skip_password and not can_admin(username):
        emit("room_join_error", {"message": "Неверный пароль"}, room=sid)
        return
    # Leave previous rooms
    for rid in list(room_members.keys()):
        if sid in room_members[rid] and rid != room_id:
            room_members[rid].discard(sid)
            _on_leave_room_silent(sid, username, rid)
    join_room(room_id)
    room_members[room_id].add(sid)
    # System message
    is_anon = room.get("is_anonymous", False)
    is_obs = observer_mode.get(username, False)
    if not is_anon and not is_obs:
        join_msg_text = room.get("custom_join_msg") or global_join_msg or ""
        if join_msg_text:
            join_msg_text = join_msg_text.replace("{username}", username).replace("{room_name}", room["name"])
            sys_msg = _build_system_message(join_msg_text, room_id)
        else:
            sys_msg = _build_system_message(f"👋 {username} вошёл(а) в чат", room_id)
        room_messages.setdefault(room_id, []).append(sys_msg)
        socketio.emit("message", sys_msg, room=room_id)
    # Update members
    members = get_room_members_info(room_id)
    socketio.emit("members_update", {"room_id": room_id, "members": members}, room=room_id)
    # Build history
    history = room_messages.get(room_id, [])
    local_role = "owner" if room.get("owner") == username else None
    room_info = {
        "id": room_id,
        "name": room["name"],
        "is_voice": room.get("is_voice", False),
        "is_anonymous": is_anon,
        "owner": room.get("owner"),
        "spam_delay": room.get("spam_delay", 0),
        "pinned_msg": room.get("pinned_msg"),
        "custom_join_msg": room.get("custom_join_msg", ""),
    }
    emit("room_joined", {
        "room_id": room_id,
        "room": room_info,
        "history": history,
        "members": members,
    }, room=sid)
    broadcast_rooms()
    # Voice
    if room.get("is_voice"):
        voice_rooms_active.setdefault(room_id, set()).add(sid)
        # Notify existing peers
        for other_sid in voice_rooms_active.get(room_id, set()):
            if other_sid != sid:
                socketio.emit("rtc_new_user", {"sid": sid, "username": username, "room_id": room_id}, room=other_sid)

def _on_leave_room_silent(sid, username, room_id):
    room = rooms.get(room_id, {})
    is_anon = room.get("is_anonymous", False)
    if not is_anon and not observer_mode.get(username, False):
        sys_msg = _build_system_message(f"👋 {username} покинул(а) комнату", room_id)
        room_messages.setdefault(room_id, []).append(sys_msg)
        socketio.emit("message", sys_msg, room=room_id)
    members = get_room_members_info(room_id)
    socketio.emit("members_update", {"room_id": room_id, "members": members}, room=room_id)
    leave_room(room_id, sid=sid)
    voice_rooms_active.get(room_id, set()).discard(sid)
    socketio.emit("voice_member_left", {"room_id": room_id, "username": username}, room=room_id)

@socketio.on("join_room")
def on_join_room(data):
    sid = request.sid
    username = get_user(sid)
    if not username:
        return
    room_id = str(data.get("room_id", ""))
    password = str(data.get("password", ""))
    admin_override = bool(data.get("admin_override", False))
    room = rooms.get(room_id)
    if not room:
        emit("room_join_error", {"message": "Комната не найдена"})
        return
    # Check ban
    if username in bans:
        emit("room_join_error", {"message": "Вы заблокированы"})
        return
    # Password check
    if room.get("password") and not can_admin(username) and not admin_override:
        if password != room["password"]:
            emit("room_join_error", {"message": "Неверный пароль"})
            return
    _do_join_room(sid, username, room_id, skip_password=True)

@socketio.on("connect_by_name")
def on_connect_by_name(data):
    sid = request.sid
    username = get_user(sid)
    if not username:
        return
    room_name = str(data.get("room_name", "")).strip()
    for rid, room in rooms.items():
        if room["name"].lower() == room_name.lower():
            if room.get("password") and not can_admin(username):
                emit("room_join_error", {"message": "Комната защищена паролем. Введите пароль."})
                # send room_id for password modal
                emit("room_needs_password", {"room_id": rid, "room_name": room["name"]})
                return
            _do_join_room(sid, username, rid, skip_password=True)
            return
    emit("connect_by_name_error", {"message": f"Комната '{room_name}' не найдена"})

@socketio.on("leave_room")
def on_leave_room(data):
    sid = request.sid
    username = get_user(sid)
    if not username:
        return
    room_id = str(data.get("room_id", ""))
    if room_id in room_members and sid in room_members[room_id]:
        room_members[room_id].discard(sid)
        _on_leave_room_silent(sid, username, room_id)
    broadcast_rooms()

@socketio.on("send_message")
def on_send_message(data):
    sid = request.sid
    username = get_user(sid)
    if not username:
        return
    room_id = str(data.get("room_id", ""))
    if room_id not in rooms:
        return
    if sid not in room_members.get(room_id, set()):
        return
    text = str(data.get("text", "")).strip()[:4000]
    image_data = data.get("image")
    msg_tags = data.get("msg_tags", [])
    is_announcement = bool(data.get("is_announcement", False)) and can_moderate(username)
    # Spam check
    delay = rooms[room_id].get("spam_delay", 0)
    user_delay = spam_limits.get(room_id, {}).get(username, 0)
    effective_delay = max(delay, user_delay)
    if effective_delay > 0:
        last = last_msg_time.get(room_id, {}).get(username, 0)
        if (now_ts() - last) < effective_delay * 1000:
            remaining = effective_delay - (now_ts() - last) / 1000
            emit("notification", {"message": f"⏳ Подождите {remaining:.1f}с перед следующим сообщением", "type": "warning"})
            return
    if not text and not image_data:
        return
    # Handle image
    image_url = None
    if image_data:
        image_url = save_image_base64(image_data)
    # Build message
    msg = _build_message(username, text, image_url, is_announcement, msg_tags, room_id)
    room_messages.setdefault(room_id, []).append(msg)
    # Update stats
    users[username]["total_msgs"] = users[username].get("total_msgs", 0) + 1
    last_msg_time.setdefault(room_id, {})[username] = now_ts()
    # Save
    eventlet.spawn(save_messages, room_id)
    eventlet.spawn(save_user, username)
    # Check veteran
    check_veteran(username)
    # Broadcast
    socketio.emit("message", msg, room=room_id)

@socketio.on("edit_message")
def on_edit_message(data):
    sid = request.sid
    username = get_user(sid)
    if not username:
        return
    room_id = str(data.get("room_id", ""))
    msg_id = str(data.get("msg_id", ""))
    text = str(data.get("text", "")).strip()[:4000]
    msgs = room_messages.get(room_id, [])
    for m in msgs:
        if m["id"] == msg_id:
            if m["author"] != username and not can_moderate(username):
                return
            m["text"] = text
            m["edited"] = True
            socketio.emit("message_edited", {"room_id": room_id, "msg_id": msg_id, "text": text}, room=room_id)
            eventlet.spawn(save_messages, room_id)
            return

@socketio.on("delete_message")
def on_delete_message(data):
    sid = request.sid
    username = get_user(sid)
    if not username:
        return
    room_id = str(data.get("room_id", ""))
    msg_id = str(data.get("msg_id", ""))
    msgs = room_messages.get(room_id, [])
    for m in msgs:
        if m["id"] == msg_id:
            if m["author"] != username and not can_moderate(username):
                return
            m["deleted"] = True
            m["text"] = ""
            socketio.emit("message_deleted", {"room_id": room_id, "msg_id": msg_id}, room=room_id)
            if username != m["author"]:
                add_action_log(username, f"Удалил сообщение {msg_id} в комнате {rooms.get(room_id, {}).get('name', room_id)}")
            eventlet.spawn(save_messages, room_id)
            return

@socketio.on("pin_message")
def on_pin_message(data):
    sid = request.sid
    username = get_user(sid)
    if not username:
        return
    room_id = str(data.get("room_id", ""))
    msg_id = str(data.get("msg_id", ""))
    if not can_manage_room(room_id, username):
        return
    msgs = room_messages.get(room_id, [])
    for m in msgs:
        if m["id"] == msg_id:
            rooms[room_id]["pinned_msg"] = m
            eventlet.spawn(save_room, room_id)
            socketio.emit("message_pinned", {"room_id": room_id, "msg": m}, room=room_id)
            return

@socketio.on("unpin_message")
def on_unpin_message(data):
    sid = request.sid
    username = get_user(sid)
    if not username:
        return
    room_id = str(data.get("room_id", ""))
    if not can_manage_room(room_id, username):
        return
    rooms[room_id]["pinned_msg"] = None
    eventlet.spawn(save_room, room_id)
    socketio.emit("message_unpinned", {"room_id": room_id}, room=room_id)

@socketio.on("react_message")
def on_react_message(data):
    sid = request.sid
    username = get_user(sid)
    if not username:
        return
    room_id = str(data.get("room_id", ""))
    msg_id = str(data.get("msg_id", ""))
    emoji = str(data.get("emoji", ""))[:4]
    if not emoji:
        return
    msgs = room_messages.get(room_id, [])
    for m in msgs:
        if m["id"] == msg_id:
            reactions = m.setdefault("reactions", {})
            if emoji not in reactions:
                reactions[emoji] = []
            if username in reactions[emoji]:
                reactions[emoji].remove(username)
            else:
                reactions[emoji].append(username)
                # credit to author
                author = m.get("author")
                if author and author in users:
                    users[author]["reactions_received"] = users[author].get("reactions_received", 0) + 1
                    eventlet.spawn(save_user, author)
            if not reactions[emoji]:
                del reactions[emoji]
            socketio.emit("reaction_updated", {"room_id": room_id, "msg_id": msg_id, "reactions": m["reactions"]}, room=room_id)
            eventlet.spawn(save_messages, room_id)
            return

@socketio.on("delete_room")
def on_delete_room(data):
    sid = request.sid
    username = get_user(sid)
    if not username:
        return
    room_id = str(data.get("room_id", ""))
    if room_id not in rooms:
        emit("notification", {"message": "Комната не найдена", "type": "warning"})
        return
    if not can_manage_room(room_id, username):
        emit("notification", {"message": "Нет прав для удаления", "type": "danger"})
        return
    add_action_log(username, f"Удалил комнату '{rooms[room_id]['name']}'")
    _delete_room(room_id, f"Удалено модератором {username}")

@socketio.on("kick_user")
def on_kick_user(data):
    sid = request.sid
    username = get_user(sid)
    if not username:
        return
    room_id = str(data.get("room_id", ""))
    target = str(data.get("username", ""))
    reason = str(data.get("reason", ""))[:200]
    if not can_manage_room(room_id, username):
        return
    # Find target sid
    target_sid = None
    for s, u in sessions.items():
        if u == target and s in room_members.get(room_id, set()):
            target_sid = s
            break
    if target_sid:
        room_members[room_id].discard(target_sid)
        socketio.emit("kicked", {"room_id": room_id, "reason": reason}, room=target_sid)
        leave_room(room_id, sid=target_sid)
        sys_msg = _build_system_message(f"🚫 {target} был(а) кикнут(а) ({reason})", room_id)
        room_messages.setdefault(room_id, []).append(sys_msg)
        socketio.emit("message", sys_msg, room=room_id)
        members = get_room_members_info(room_id)
        socketio.emit("members_update", {"room_id": room_id, "members": members}, room=room_id)
        add_action_log(username, f"Кик {target} из '{rooms.get(room_id, {}).get('name', room_id)}': {reason}")
        broadcast_rooms()

@socketio.on("set_spam_limit")
def on_set_spam_limit(data):
    sid = request.sid
    username = get_user(sid)
    if not username or not can_manage_room(str(data.get("room_id", "")), username):
        return
    room_id = str(data.get("room_id", ""))
    target = str(data.get("username", ""))
    delay = int(data.get("delay", 0))
    spam_limits.setdefault(room_id, {})[target] = delay
    emit("notification", {"message": f"Задержка для {target} установлена: {delay}с", "type": "success"})

@socketio.on("transfer_owner")
def on_transfer_owner(data):
    sid = request.sid
    username = get_user(sid)
    room_id = str(data.get("room_id", ""))
    target = str(data.get("username", ""))
    if not is_room_owner(room_id, username):
        return
    if target not in users:
        return
    rooms[room_id]["owner"] = target
    eventlet.spawn(save_room, room_id)
    sys_msg = _build_system_message(f"🏠 {target} стал(а) новым владельцем комнаты", room_id)
    room_messages.setdefault(room_id, []).append(sys_msg)
    socketio.emit("message", sys_msg, room=room_id)
    emit("notification", {"message": f"Права владельца переданы {target}", "type": "success"})

# ─── ADMIN EVENTS ─────────────────────────────────────────────────────────────

@socketio.on("admin_code")
def on_admin_code(data):
    sid = request.sid
    username = get_user(sid)
    if not username:
        return
    code = str(data.get("code", ""))
    if code == ADMIN_CODE:
        users[username]["role"] = "admin"
        save_user(username)
        cr_name = users[username].get("custom_role")
        cr = custom_roles.get(cr_name) if cr_name else None
        info = {
            "username": username,
            "role": "admin",
            "token": sessions_token.get(username, ""),
            "custom_role": cr_name,
            "custom_role_data": cr,
            "avatar": users[username].get("avatar", ""),
            "is_observer": observer_mode.get(username, False),
        }
        emit("admin_access_granted", info)
        add_action_log(username, "Получил права администратора")
        logger.info(f"Admin granted: {username}")
    else:
        emit("admin_code_error", {})

@socketio.on("set_moderator")
def on_set_moderator(data):
    sid = request.sid
    username = get_user(sid)
    if not can_admin(username):
        return
    target = str(data.get("username", ""))
    add = bool(data.get("add", True))
    if target not in users:
        emit("notification", {"message": "Пользователь не найден", "type": "warning"})
        return
    if add:
        users[target]["role"] = "moderator"
        action = "Назначен модератором"
    else:
        if users[target].get("role") == "moderator":
            users[target]["role"] = "user"
        action = "Снят с должности модератора"
    save_user(target)
    add_action_log(username, f"{action}: {target}")
    # Notify target
    target_sid = get_sid_of_user(target)
    if target_sid:
        info = build_user_info(target)
        socketio.emit("role_updated", info, room=target_sid)
    socketio.emit("admin_users_data", {"users": [build_user_info(u) for u in users]})

@socketio.on("ban_user")
def on_ban_user(data):
    sid = request.sid
    username = get_user(sid)
    if not can_admin(username):
        return
    target = str(data.get("username", ""))
    reason = str(data.get("reason", ""))
    if target not in users:
        emit("notification", {"message": "Пользователь не найден", "type": "warning"})
        return
    users[target]["banned"] = True
    bans.add(target)
    save_user(target)
    save_bans()
    add_action_log(username, f"Бан {target}: {reason}")
    # Kick from all rooms
    target_sid = get_sid_of_user(target)
    if target_sid:
        socketio.emit("banned", {}, room=target_sid)
    emit("notification", {"message": f"{target} заблокирован", "type": "success"})
    socketio.emit("admin_users_data", {"users": [build_user_info(u) for u in users]})

@socketio.on("unban_user")
def on_unban_user(data):
    sid = request.sid
    username = get_user(sid)
    if not can_admin(username):
        return
    target = str(data.get("username", ""))
    if target in users:
        users[target]["banned"] = False
        bans.discard(target)
        save_user(target)
        save_bans()
        add_action_log(username, f"Разбан {target}")
    emit("notification", {"message": f"{target} разблокирован", "type": "success"})
    socketio.emit("admin_users_data", {"users": [build_user_info(u) for u in users]})

@socketio.on("pin_room")
def on_pin_room(data):
    sid = request.sid
    username = get_user(sid)
    if not can_moderate(username):
        return
    room_id = str(data.get("room_id", ""))
    pin = bool(data.get("pin", True))
    if room_id in rooms:
        rooms[room_id]["pinned"] = pin
        eventlet.spawn(save_room, room_id)
        broadcast_rooms()
        add_action_log(username, f"{'Закрепил' if pin else 'Открепил'} комнату '{rooms[room_id]['name']}'")

@socketio.on("set_global_announcement")
def on_set_global_announcement(data):
    global global_announcement
    sid = request.sid
    username = get_user(sid)
    if not can_admin(username):
        return
    global_announcement = str(data.get("text", ""))
    save_settings()
    socketio.emit("global_announcement", {"text": global_announcement})
    add_action_log(username, f"Установил глобальное объявление: {global_announcement[:50]}")

@socketio.on("set_global_join_msg")
def on_set_global_join_msg(data):
    global global_join_msg
    sid = request.sid
    username = get_user(sid)
    if not can_admin(username):
        return
    global_join_msg = str(data.get("text", ""))
    save_settings()
    emit("notification", {"message": "Сообщение входа установлено", "type": "success"})

@socketio.on("set_room_join_msg")
def on_set_room_join_msg(data):
    sid = request.sid
    username = get_user(sid)
    if not can_admin(username):
        return
    room_name = str(data.get("room_name", "")).strip()
    text = str(data.get("text", ""))
    for rid, r in rooms.items():
        if r["name"].lower() == room_name.lower():
            rooms[rid]["custom_join_msg"] = text
            eventlet.spawn(save_room, rid)
            emit("notification", {"message": f"Сообщение для '{room_name}' установлено", "type": "success"})
            return
    emit("notification", {"message": "Комната не найдена", "type": "warning"})

@socketio.on("set_observer")
def on_set_observer(data):
    sid = request.sid
    username = get_user(sid)
    if not can_admin(username):
        return
    active = bool(data.get("active", False))
    observer_mode[username] = active
    emit("observer_updated", {"active": active})
    add_action_log(username, f"{'Активировал' if active else 'Деактивировал'} режим наблюдателя")

@socketio.on("admin_request_all_users")
def on_admin_request_all_users():
    sid = request.sid
    username = get_user(sid)
    if not can_admin(username):
        return
    emit("admin_users_data", {"users": [build_user_info(u) for u in users]})

@socketio.on("admin_request_stats")
def on_admin_request_stats():
    sid = request.sid
    username = get_user(sid)
    if not can_admin(username):
        return
    total_msgs = sum(len(msgs) for msgs in room_messages.values())
    online = len(sessions)
    emit("admin_stats", {
        "users": len(users),
        "rooms": len(rooms),
        "messages": total_msgs,
        "online": online,
    })

@socketio.on("admin_request_all_rooms")
def on_admin_request_all_rooms():
    sid = request.sid
    username = get_user(sid)
    if not can_admin(username):
        return
    emit("admin_rooms_data", {"rooms": build_rooms_list(for_admin=True)})

@socketio.on("request_action_log")
def on_request_action_log():
    sid = request.sid
    username = get_user(sid)
    if not can_admin(username):
        return
    emit("action_log", {"entries": action_log[-100:]})

@socketio.on("request_leaderboard")
def on_request_leaderboard():
    data = [build_user_info(u) for u in users if users[u].get("role") != "bot"]
    emit("leaderboard_data", {"users": data})

# ─── PROFILE EVENTS ───────────────────────────────────────────────────────────

@socketio.on("get_profile")
def on_get_profile(data):
    sid = request.sid
    username = get_user(sid)
    if not username:
        return
    target = str(data.get("username", username))
    if target not in users:
        emit("notification", {"message": "Пользователь не найден", "type": "warning"})
        return
    emit("profile_data", build_user_info(target))

@socketio.on("update_profile")
def on_update_profile(data):
    sid = request.sid
    username = get_user(sid)
    if not username:
        return
    bio = str(data.get("bio", ""))[:200]
    avatar_data = data.get("avatar")
    users[username]["bio"] = bio
    if avatar_data:
        url = save_avatar_base64(avatar_data, username)
        if url:
            users[username]["avatar"] = url
    save_user(username)
    emit("profile_data", build_user_info(username))
    emit("notification", {"message": "Профиль обновлён", "type": "success"})
    # update topbar badge
    cr_name = users[username].get("custom_role")
    cr = custom_roles.get(cr_name) if cr_name else None
    emit("auth_success", {
        "username": username,
        "role": users[username].get("role", "user"),
        "token": sessions_token.get(username, ""),
        "custom_role": cr_name,
        "custom_role_data": cr,
        "avatar": users[username].get("avatar", ""),
        "is_observer": observer_mode.get(username, False),
    })

# ─── FRIENDS & PM ─────────────────────────────────────────────────────────────

@socketio.on("request_friends")
def on_request_friends():
    sid = request.sid
    username = get_user(sid)
    if not username:
        return
    u = users.get(username, {})
    emit("friends_data", {
        "friends": u.get("friends", []),
        "requests": u.get("requests_in", []),
    })

@socketio.on("friend_request")
def on_friend_request(data):
    sid = request.sid
    username = get_user(sid)
    if not username:
        return
    to = str(data.get("to", ""))
    if to == username or to not in users:
        emit("notification", {"message": "Пользователь не найден", "type": "warning"})
        return
    if to in users[username].get("friends", []):
        emit("notification", {"message": "Уже в друзьях", "type": "warning"})
        return
    users[to].setdefault("requests_in", [])
    if username not in users[to]["requests_in"]:
        users[to]["requests_in"].append(username)
    users[username].setdefault("requests_out", [])
    if to not in users[username]["requests_out"]:
        users[username]["requests_out"].append(to)
    save_user(to)
    save_user(username)
    # Notify target
    target_sid = get_sid_of_user(to)
    if target_sid:
        socketio.emit("friend_request_received", {"from": username}, room=target_sid)

@socketio.on("friend_respond")
def on_friend_respond(data):
    sid = request.sid
    username = get_user(sid)
    if not username:
        return
    frm = str(data.get("from", ""))
    accept = bool(data.get("accept", False))
    if frm in users[username].get("requests_in", []):
        users[username]["requests_in"].remove(frm)
    if accept:
        users[username].setdefault("friends", [])
        if frm not in users[username]["friends"]:
            users[username]["friends"].append(frm)
        if frm in users:
            users[frm].setdefault("friends", [])
            if username not in users[frm]["friends"]:
                users[frm]["friends"].append(username)
            users[frm].get("requests_out", []).remove(username) if username in users[frm].get("requests_out", []) else None
            save_user(frm)
        save_user(username)
        frm_sid = get_sid_of_user(frm)
        if frm_sid:
            socketio.emit("friend_accepted", {"username": username}, room=frm_sid)
        emit("notification", {"message": f"Вы добавили {frm} в друзья", "type": "success"})
    else:
        save_user(username)
    emit("friends_data", {"friends": users[username].get("friends", []), "requests": users[username].get("requests_in", [])})

@socketio.on("remove_friend")
def on_remove_friend(data):
    sid = request.sid
    username = get_user(sid)
    if not username:
        return
    target = str(data.get("username", ""))
    friends = users[username].get("friends", [])
    if target in friends:
        friends.remove(target)
    if target in users:
        tf = users[target].get("friends", [])
        if username in tf:
            tf.remove(username)
        save_user(target)
    save_user(username)
    emit("friends_data", {"friends": friends, "requests": users[username].get("requests_in", [])})

@socketio.on("send_pm")
def on_send_pm(data):
    sid = request.sid
    username = get_user(sid)
    if not username:
        return
    to = str(data.get("to", ""))
    text = str(data.get("text", "")).strip()[:2000]
    if not text or to not in users:
        return
    # PM id is sorted pair
    pm_id = "_".join(sorted([username, to]))
    pm_path = f"data/private_messages/{pm_id}.json"
    history = read_json(pm_path, [])
    msg = {
        "id": generate_id(),
        "author": username,
        "from": username,
        "to": to,
        "text": text,
        "timestamp": now_time(),
        "ts": now_ts(),
    }
    history.append(msg)
    eventlet.spawn(save_pm, pm_id, history)
    # Deliver to sender
    emit("pm_message", msg)
    # Deliver to recipient
    to_sid = get_sid_of_user(to)
    if to_sid:
        socketio.emit("pm_message", msg, room=to_sid)

@socketio.on("request_pm_history")
def on_request_pm_history(data):
    sid = request.sid
    username = get_user(sid)
    if not username:
        return
    other = str(data.get("with", ""))
    pm_id = "_".join(sorted([username, other]))
    history = read_json(f"data/private_messages/{pm_id}.json", [])
    emit("pm_history", {"messages": history})

# ─── CUSTOM ROLES ─────────────────────────────────────────────────────────────

@socketio.on("request_roles")
def on_request_roles():
    emit("roles_data", {"roles": [{"name": k, **v} for k, v in custom_roles.items()]})

@socketio.on("create_role")
def on_create_role(data):
    sid = request.sid
    username = get_user(sid)
    if not can_moderate(username):
        return
    name = str(data.get("name", "")).strip()[:32]
    if not name:
        return
    color = str(data.get("color", "#ffffff"))[:20]
    emoji = str(data.get("emoji", ""))[:4]
    prefix = str(data.get("prefix", ""))[:16]
    custom_roles[name] = {"color": color, "emoji": emoji, "prefix": prefix, "name": name}
    save_roles()
    add_action_log(username, f"Создал роль '{name}'")
    emit("role_created", {"name": name})
    socketio.emit("roles_data", {"roles": [{"name": k, **v} for k, v in custom_roles.items()]})

@socketio.on("delete_role")
def on_delete_role(data):
    sid = request.sid
    username = get_user(sid)
    if not can_moderate(username):
        return
    name = str(data.get("name", ""))
    if name in custom_roles:
        del custom_roles[name]
        # Remove from users
        for u in users.values():
            if u.get("custom_role") == name:
                u["custom_role"] = None
        save_roles()
        for u in users:
            if users[u].get("custom_role") is None:
                save_user(u)
        add_action_log(username, f"Удалил роль '{name}'")
        emit("role_deleted", {})
        socketio.emit("roles_data", {"roles": [{"name": k, **v} for k, v in custom_roles.items()]})
        # Update all affected users
        for u, udata in users.items():
            uid_sid = get_sid_of_user(u)
            if uid_sid:
                info = build_user_info(u)
                socketio.emit("role_updated", info, room=uid_sid)

@socketio.on("assign_role")
def on_assign_role(data):
    sid = request.sid
    username = get_user(sid)
    if not can_moderate(username):
        return
    target = str(data.get("username", ""))
    role_name = str(data.get("role_name", ""))
    if target not in users:
        emit("notification", {"message": "Пользователь не найден", "type": "warning"})
        return
    if role_name and role_name not in custom_roles:
        emit("notification", {"message": "Роль не найдена", "type": "warning"})
        return
    users[target]["custom_role"] = role_name or None
    save_user(target)
    add_action_log(username, f"Назначил роль '{role_name}' пользователю {target}")
    emit("role_assigned", {"username": target, "role_name": role_name})
    target_sid = get_sid_of_user(target)
    if target_sid:
        info = build_user_info(target)
        socketio.emit("role_updated", info, room=target_sid)

# ─── WEBRTC SIGNALING ─────────────────────────────────────────────────────────

@socketio.on("voice_joined")
def on_voice_joined(data):
    sid = request.sid
    username = get_user(sid)
    if not username:
        return
    room_id = str(data.get("room_id", ""))
    voice_rooms_active.setdefault(room_id, set()).add(sid)
    # Notify all other members in voice
    for other_sid in list(voice_rooms_active.get(room_id, set())):
        if other_sid != sid and other_sid in room_members.get(room_id, set()):
            socketio.emit("voice_member_joined", {"room_id": room_id, "username": username}, room=other_sid)

@socketio.on("rtc_offer")
def on_rtc_offer(data):
    sid = request.sid
    username = get_user(sid)
    target = str(data.get("target", ""))
    socketio.emit("rtc_offer", {"from": sid, "username": username, "offer": data.get("offer"), "room_id": data.get("room_id")}, room=target)

@socketio.on("rtc_answer")
def on_rtc_answer(data):
    sid = request.sid
    target = str(data.get("target", ""))
    socketio.emit("rtc_answer", {"from": sid, "answer": data.get("answer")}, room=target)

@socketio.on("rtc_ice")
def on_rtc_ice(data):
    sid = request.sid
    target = str(data.get("target", ""))
    socketio.emit("rtc_ice", {"from": sid, "candidate": data.get("candidate")}, room=target)

@socketio.on("voice_mute")
def on_voice_mute(data):
    sid = request.sid
    username = get_user(sid)
    if not username:
        return
    room_id = str(data.get("room_id", ""))
    muted = bool(data.get("muted", False))
    socketio.emit("voice_mute_update", {"room_id": room_id, "username": username, "muted": muted}, room=room_id)

@socketio.on("screen_share_start")
def on_screen_share_start(data):
    sid = request.sid
    username = get_user(sid)
    if not username:
        return
    room_id = str(data.get("room_id", ""))
    socketio.emit("screen_share_started", {"room_id": room_id, "username": username, "sid": sid}, room=room_id)

@socketio.on("screen_share_stop")
def on_screen_share_stop(data):
    sid = request.sid
    username = get_user(sid)
    if not username:
        return
    room_id = str(data.get("room_id", ""))
    socketio.emit("screen_share_stopped", {"room_id": room_id, "username": username}, room=room_id)

# ─── GRACEFUL SHUTDOWN ────────────────────────────────────────────────────────
import signal

def shutdown_handler(sig, frame):
    logger.info("Shutting down, saving all data...")
    for u in users:
        save_user(u)
    for rid in rooms:
        save_room(rid)
        save_messages(rid)
    save_roles()
    save_bans()
    save_settings()
    save_action_log()
    save_leaderboard()
    logger.info("All data saved. Goodbye.")
    sys.exit(0)

signal.signal(signal.SIGINT, shutdown_handler)
signal.signal(signal.SIGTERM, shutdown_handler)

# ─── STARTUP ─────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    load_all_data()
    logger.info(f"╔══════════════════════════════════════╗")
    logger.info(f"║       Vietugram Server v4.0          ║")
    logger.info(f"║  Developer: Vietu                    ║")
    logger.info(f"╚══════════════════════════════════════╝")
    logger.info(f"Starting on http://{HOST}:{PORT}")
    logger.info(f"Admin code: {ADMIN_CODE}")
    logger.info(f"Users loaded: {len(users)}, Rooms: {len(rooms)}")
    socketio.run(app, host=HOST, port=PORT, debug=False, log_output=False)
