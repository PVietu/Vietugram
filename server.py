#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Vietugram — Chat Server
Developer: Vietu
Version: 3.0
"""

import eventlet
eventlet.monkey_patch()

import os
import json
import time
import uuid
import base64
import hashlib
import threading
from datetime import datetime, timedelta
from flask import Flask, request, send_from_directory, jsonify
from flask_socketio import SocketIO, emit, join_room, leave_room, disconnect

# ─── Configuration ──────────────────────────────────────────────────────────────
HOST = "0.0.0.0"      # Use 0.0.0.0 for public server (white IP)
PORT = 5000            # Change port if needed
ADMIN_CODE = "GGCheck"
VETERAN_MSG_THRESHOLD = 1000

app = Flask(__name__, static_folder=".", static_url_path="")
app.config["SECRET_KEY"] = "vietugram_secret_2024_xK9mP"
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="eventlet",
                    max_http_buffer_size=50 * 1024 * 1024,
                    ping_timeout=60, ping_interval=25)

# ─── In-Memory Storage ───────────────────────────────────────────────────────────
users = {}          # username -> {password_hash, role, custom_role, banned, total_msgs, join_time, ...}
sessions = {}       # sid -> username
rooms = {}          # room_id -> room_data
room_members = {}   # room_id -> set of sids
room_messages = {}  # room_id -> [messages]
bans = set()        # usernames
custom_roles = {}   # role_name -> {color, status, prefix}
observer_mode = {}  # username -> bool (admin observer mode)
veteran_awarded = set()  # usernames who got veteran

# ─── Helpers ────────────────────────────────────────────────────────────────────

def hash_password(pw):
    return hashlib.sha256(pw.encode()).hexdigest()

def get_user(sid):
    return sessions.get(sid)

def get_role(username):
    if username not in users:
        return "user"
    return users[username].get("role", "user")

def role_priority(role):
    p = {"admin": 3, "moderator": 2, "veteran": 1, "user": 0}
    return p.get(role, 0)

def can_moderate(username):
    return get_role(username) in ("admin", "moderator")

def can_admin(username):
    return get_role(username) == "admin"

def generate_id():
    return str(uuid.uuid4())[:8]

def now_ts():
    return int(time.time() * 1000)

def now_str():
    return datetime.now().strftime("%H:%M:%S")

def build_user_info(username):
    if username not in users:
        return None
    u = users[username]
    role = u.get("role", "user")
    cr_name = u.get("custom_role", None)
    cr = custom_roles.get(cr_name) if cr_name and cr_name in custom_roles else None
    return {
        "username": username,
        "role": role,
        "custom_role": cr_name,
        "custom_role_data": cr,
        "total_msgs": u.get("total_msgs", 0),
        "join_time": u.get("join_time", 0),
        "reactions_received": u.get("reactions_received", 0),
        "is_observer": observer_mode.get(username, False),
    }

def check_veteran(username):
    if username in users and username not in veteran_awarded:
        if users[username].get("total_msgs", 0) >= VETERAN_MSG_THRESHOLD:
            if users[username].get("role", "user") == "user":
                users[username]["role"] = "veteran"
                veteran_awarded.add(username)
                return True
    return False

def get_room_members_info(room_id):
    members = []
    for sid, uname in sessions.items():
        if sid in room_members.get(room_id, set()):
            if observer_mode.get(uname, False):
                continue
            info = build_user_info(uname)
            if info:
                members.append(info)
    members.sort(key=lambda x: -role_priority(x["role"]))
    return members

# ─── Room cleanup thread ─────────────────────────────────────────────────────────
def room_cleanup_worker():
    while True:
        eventlet.sleep(10)
        now = now_ts()
        to_delete = []
        for rid, room in list(rooms.items()):
            if room.get("lifetime_ms") and room.get("created_at"):
                if now - room["created_at"] > room["lifetime_ms"]:
                    to_delete.append(rid)
        for rid in to_delete:
            rooms.pop(rid, None)
            room_messages.pop(rid, None)
            members = list(room_members.get(rid, set()))
            room_members.pop(rid, None)
            socketio.emit("room_deleted", {"room_id": rid, "reason": "Комната истекла"}, room=rid)
            for sid in members:
                try:
                    leave_room(rid, sid=sid)
                except:
                    pass
        if to_delete:
            socketio.emit("rooms_list", build_rooms_list())

eventlet.spawn(room_cleanup_worker)

# ─── Build rooms list ────────────────────────────────────────────────────────────
def build_rooms_list():
    result = []
    for rid, r in rooms.items():
        members_count = len([s for s in room_members.get(rid, set())
                             if not observer_mode.get(sessions.get(s, ""), False)])
        result.append({
            "id": rid,
            "name": r["name"],
            "has_password": bool(r.get("password")),
            "is_voice": r.get("is_voice", False),
            "is_anonymous": r.get("is_anonymous", False),
            "is_bot_room": r.get("is_bot_room", False),
            "owner": r.get("owner", ""),
            "members_count": members_count,
            "lifetime_ms": r.get("lifetime_ms"),
            "created_at": r.get("created_at"),
            "spam_delay": r.get("spam_delay", 0),
            "custom_join_msg": r.get("custom_join_msg", ""),
        })
    return result

# ─── HTTP Routes ─────────────────────────────────────────────────────────────────
@app.route("/")
def index():
    return send_from_directory(".", "index.html")

@app.route("/api/rooms", methods=["GET"])
def api_rooms():
    return jsonify(build_rooms_list())

@app.route("/api/bot/connect", methods=["POST"])
def api_bot_connect():
    """Bot API endpoint"""
    data = request.json or {}
    token = data.get("token", "")
    bot_name = data.get("bot_name", "Bot")
    room_name = data.get("room_name", f"🤖 {bot_name}")
    if not token or len(token) < 8:
        return jsonify({"error": "Invalid token"}), 400
    bot_username = f"BOT_{bot_name}"
    if bot_username not in users:
        users[bot_username] = {
            "password_hash": hash_password(token),
            "role": "bot",
            "total_msgs": 0,
            "join_time": now_ts(),
            "reactions_received": 0,
        }
    rid = f"bot_{generate_id()}"
    rooms[rid] = {
        "name": room_name,
        "password": None,
        "owner": bot_username,
        "is_voice": False,
        "is_anonymous": False,
        "is_bot_room": True,
        "bot_token": token,
        "created_at": now_ts(),
        "spam_delay": 0,
    }
    room_members[rid] = set()
    room_messages[rid] = []
    socketio.emit("rooms_list", build_rooms_list())
    return jsonify({"room_id": rid, "bot_username": bot_username, "status": "connected"})

@app.route("/api/bot/send", methods=["POST"])
def api_bot_send():
    """Bot sends message"""
    data = request.json or {}
    token = data.get("token", "")
    room_id = data.get("room_id", "")
    text = data.get("text", "")
    if not token or not room_id or room_id not in rooms:
        return jsonify({"error": "Invalid params"}), 400
    room = rooms[room_id]
    if not room.get("is_bot_room") or room.get("bot_token") != token:
        return jsonify({"error": "Unauthorized"}), 403
    msg = {
        "id": generate_id(),
        "room_id": room_id,
        "author": room["owner"],
        "text": text,
        "image": None,
        "timestamp": now_str(),
        "ts": now_ts(),
        "is_announcement": False,
        "is_bot": True,
        "tags": [],
        "reactions": {},
        "edited": False,
        "pinned": False,
        "msg_tags": [],
    }
    room_messages.setdefault(room_id, []).append(msg)
    socketio.emit("message", msg, room=room_id)
    return jsonify({"status": "sent", "msg_id": msg["id"]})

@app.route("/api/bot/messages", methods=["GET"])
def api_bot_messages():
    """Bot reads messages"""
    token = request.args.get("token", "")
    room_id = request.args.get("room_id", "")
    since = int(request.args.get("since", 0))
    if not token or not room_id or room_id not in rooms:
        return jsonify({"error": "Invalid params"}), 400
    room = rooms[room_id]
    if not room.get("is_bot_room") or room.get("bot_token") != token:
        return jsonify({"error": "Unauthorized"}), 403
    msgs = [m for m in room_messages.get(room_id, []) if m["ts"] > since and not m.get("is_bot")]
    return jsonify({"messages": msgs})

# ─── Socket Events ───────────────────────────────────────────────────────────────

@socketio.on("connect")
def on_connect():
    pass

@socketio.on("disconnect")
def on_disconnect():
    sid = request.sid
    username = sessions.pop(sid, None)
    if not username:
        return
    # Remove from all rooms
    for rid, members in list(room_members.items()):
        if sid in members:
            members.discard(sid)
            leave_room(rid)
            room = rooms.get(rid, {})
            is_anon = room.get("is_anonymous", False)
            if not is_anon and not observer_mode.get(username, False):
                sys_msg = {
                    "id": generate_id(), "room_id": rid,
                    "author": "System", "text": f"👋 {username} покинул комнату",
                    "image": None, "timestamp": now_str(), "ts": now_ts(),
                    "is_system": True, "reactions": {}, "tags": [], "msg_tags": [],
                    "edited": False, "pinned": False,
                }
                room_messages.setdefault(rid, []).append(sys_msg)
                emit("message", sys_msg, room=rid)
            emit("members_update", get_room_members_info(rid), room=rid)
    socketio.emit("rooms_list", build_rooms_list())

# ── Auth ─────────────────────────────────────────────────────────────────────────

@socketio.on("register")
def on_register(data):
    username = (data.get("username") or "").strip()
    password = (data.get("password") or "").strip()
    if not username or not password:
        emit("register_result", {"ok": False, "error": "Введите ник и пароль"})
        return
    if len(username) > 24:
        emit("register_result", {"ok": False, "error": "Ник слишком длинный"})
        return
    if username in users:
        emit("register_result", {"ok": False, "error": "Ник уже занят"})
        return
    users[username] = {
        "password_hash": hash_password(password),
        "role": "user",
        "custom_role": None,
        "banned": False,
        "total_msgs": 0,
        "join_time": now_ts(),
        "reactions_received": 0,
    }
    emit("register_result", {"ok": True})

@socketio.on("login")
def on_login(data):
    username = (data.get("username") or "").strip()
    password = (data.get("password") or "").strip()
    if not username or not password:
        emit("login_result", {"ok": False, "error": "Введите ник и пароль"})
        return
    if username not in users:
        emit("login_result", {"ok": False, "error": "Пользователь не найден"})
        return
    u = users[username]
    if u.get("banned"):
        emit("login_result", {"ok": False, "error": "Вы заблокированы"})
        return
    if u.get("password_hash") != hash_password(password):
        emit("login_result", {"ok": False, "error": "Неверный пароль"})
        return
    sessions[request.sid] = username
    emit("login_result", {"ok": True, "user": build_user_info(username)})
    emit("rooms_list", build_rooms_list())

@socketio.on("admin_login")
def on_admin_login(data):
    code = data.get("code", "")
    username = get_user(request.sid)
    if not username:
        emit("admin_login_result", {"ok": False, "error": "Не авторизован"})
        return
    if code != ADMIN_CODE:
        emit("admin_login_result", {"ok": False, "error": "Неверный код"})
        return
    users[username]["role"] = "admin"
    emit("admin_login_result", {"ok": True})
    emit("user_update", build_user_info(username))

# ── Rooms ─────────────────────────────────────────────────────────────────────────

@socketio.on("create_room")
def on_create_room(data):
    username = get_user(request.sid)
    if not username:
        return
    name = (data.get("name") or "").strip()
    if not name:
        emit("error_msg", {"text": "Введите название комнаты"})
        return
    password = (data.get("password") or "").strip() or None
    is_voice = bool(data.get("is_voice", False))
    is_anonymous = bool(data.get("is_anonymous", False))
    lifetime_sec = data.get("lifetime_sec", 0)
    spam_delay = int(data.get("spam_delay", 0))
    rid = generate_id()
    rooms[rid] = {
        "name": name,
        "password": hash_password(password) if password else None,
        "owner": username,
        "is_voice": is_voice,
        "is_anonymous": is_anonymous,
        "is_bot_room": False,
        "created_at": now_ts(),
        "lifetime_ms": int(lifetime_sec) * 1000 if lifetime_sec else None,
        "spam_delay": spam_delay,
        "custom_join_msg": "",
        "pinned_msg_id": None,
    }
    room_members[rid] = set()
    room_messages[rid] = []
    socketio.emit("rooms_list", build_rooms_list())
    emit("room_created", {"room_id": rid})

@socketio.on("join_room_req")
def on_join_room(data):
    username = get_user(request.sid)
    if not username:
        return
    rid = data.get("room_id", "")
    password = (data.get("password") or "").strip()
    if rid not in rooms:
        emit("join_result", {"ok": False, "error": "Комната не найдена"})
        return
    room = rooms[rid]
    if users[username].get("banned"):
        emit("join_result", {"ok": False, "error": "Вы заблокированы"})
        return
    # Password check (admins bypass)
    if room.get("password") and get_role(username) != "admin":
        if not password or hash_password(password) != room["password"]:
            emit("join_result", {"ok": False, "error": "Неверный пароль"})
            return
    # Leave current rooms
    for other_rid, members in list(room_members.items()):
        if request.sid in members and other_rid != rid:
            members.discard(request.sid)
            leave_room(other_rid)
            other_room = rooms.get(other_rid, {})
            is_anon = other_room.get("is_anonymous", False)
            if not is_anon and not observer_mode.get(username, False):
                sys_msg = {
                    "id": generate_id(), "room_id": other_rid,
                    "author": "System", "text": f"👋 {username} покинул комнату",
                    "image": None, "timestamp": now_str(), "ts": now_ts(),
                    "is_system": True, "reactions": {}, "tags": [], "msg_tags": [],
                    "edited": False, "pinned": False,
                }
                room_messages.setdefault(other_rid, []).append(sys_msg)
                emit("message", sys_msg, room=other_rid)
            emit("members_update", get_room_members_info(other_rid), room=other_rid)

    join_room(rid)
    room_members.setdefault(rid, set()).add(request.sid)

    is_anon = room.get("is_anonymous", False)
    is_observer = observer_mode.get(username, False)

    if not is_anon and not is_observer:
        join_text = room.get("custom_join_msg") or f"✅ {username} вошёл в комнату"
        role = get_role(username)
        if role in ("admin", "moderator"):
            join_text = room.get("custom_join_msg") or f"⚡ {username} вошёл в комнату"
        sys_msg = {
            "id": generate_id(), "room_id": rid,
            "author": "System", "text": join_text,
            "image": None, "timestamp": now_str(), "ts": now_ts(),
            "is_system": True, "reactions": {}, "tags": [], "msg_tags": [],
            "edited": False, "pinned": False,
        }
        room_messages.setdefault(rid, []).append(sys_msg)
        emit("message", sys_msg, room=rid)

    emit("members_update", get_room_members_info(rid), room=rid)
    socketio.emit("rooms_list", build_rooms_list())

    pinned = None
    if room.get("pinned_msg_id"):
        for m in room_messages.get(rid, []):
            if m["id"] == room["pinned_msg_id"]:
                pinned = m
                break

    emit("join_result", {
        "ok": True,
        "room": {
            "id": rid,
            "name": room["name"],
            "is_voice": room.get("is_voice", False),
            "is_anonymous": room.get("is_anonymous", False),
            "is_bot_room": room.get("is_bot_room", False),
            "owner": room.get("owner"),
            "spam_delay": room.get("spam_delay", 0),
        },
        "messages": room_messages.get(rid, []),
        "members": get_room_members_info(rid),
        "pinned_msg": pinned,
    })

@socketio.on("leave_room_req")
def on_leave_room(data):
    username = get_user(request.sid)
    rid = data.get("room_id", "")
    if rid in room_members and request.sid in room_members[rid]:
        room_members[rid].discard(request.sid)
        leave_room(rid)
        room = rooms.get(rid, {})
        is_anon = room.get("is_anonymous", False)
        if not is_anon and not observer_mode.get(username, False):
            sys_msg = {
                "id": generate_id(), "room_id": rid,
                "author": "System", "text": f"👋 {username} покинул комнату",
                "image": None, "timestamp": now_str(), "ts": now_ts(),
                "is_system": True, "reactions": {}, "tags": [], "msg_tags": [],
                "edited": False, "pinned": False,
            }
            room_messages.setdefault(rid, []).append(sys_msg)
            emit("message", sys_msg, room=rid)
        emit("members_update", get_room_members_info(rid), room=rid)
    socketio.emit("rooms_list", build_rooms_list())
    emit("left_room", {})

@socketio.on("delete_room")
def on_delete_room(data):
    username = get_user(request.sid)
    rid = data.get("room_id", "")
    if rid not in rooms:
        return
    room = rooms[rid]
    if not (can_moderate(username) or room.get("owner") == username):
        emit("error_msg", {"text": "Нет прав"})
        return
    rooms.pop(rid, None)
    room_messages.pop(rid, None)
    members = list(room_members.pop(rid, set()))
    socketio.emit("room_deleted", {"room_id": rid, "reason": "Комната удалена"}, room=rid)
    for sid in members:
        try:
            leave_room(rid, sid=sid)
        except:
            pass
    socketio.emit("rooms_list", build_rooms_list())

# ── Messages ──────────────────────────────────────────────────────────────────────

last_message_time = {}  # username -> ts

@socketio.on("send_message")
def on_send_message(data):
    username = get_user(request.sid)
    if not username:
        return
    rid = data.get("room_id", "")
    if rid not in rooms:
        return
    if request.sid not in room_members.get(rid, set()):
        return
    room = rooms[rid]
    # Spam delay
    spam_delay = room.get("spam_delay", 0)
    if spam_delay > 0:
        last_t = last_message_time.get(username + rid, 0)
        now_t = now_ts()
        if now_t - last_t < spam_delay * 1000:
            emit("error_msg", {"text": f"⏳ Подождите {spam_delay} сек. перед следующим сообщением"})
            return
    last_message_time[username + rid] = now_ts()

    text = (data.get("text") or "").strip()
    image = data.get("image")  # base64 string or None
    is_announcement = bool(data.get("is_announcement", False)) and can_moderate(username)
    tags = data.get("tags", [])  # mentions
    msg_tags = data.get("msg_tags", [])  # #важное etc
    if not text and not image:
        return

    is_anon = room.get("is_anonymous", False)
    display_author = "Аноним" if is_anon else username

    msg = {
        "id": generate_id(),
        "room_id": rid,
        "author": display_author,
        "real_author": username,
        "text": text,
        "image": image,
        "timestamp": now_str(),
        "ts": now_ts(),
        "is_announcement": is_announcement,
        "reactions": {},
        "tags": tags,
        "msg_tags": msg_tags,
        "edited": False,
        "pinned": False,
        "is_system": False,
    }
    room_messages.setdefault(rid, []).append(msg)
    users[username]["total_msgs"] = users[username].get("total_msgs", 0) + 1

    # Check veteran
    if check_veteran(username):
        vet_msg = {
            "id": generate_id(), "room_id": rid,
            "author": "System", "text": f"🏆 {username} получил звание Ветерана!",
            "image": None, "timestamp": now_str(), "ts": now_ts(),
            "is_system": True, "reactions": {}, "tags": [], "msg_tags": [],
            "edited": False, "pinned": False,
        }
        room_messages.setdefault(rid, []).append(vet_msg)
        emit("message", vet_msg, room=rid)

    emit("message", msg, room=rid)

    # Notify mentioned users
    for mentioned in tags:
        for sid, uname in sessions.items():
            if uname == mentioned:
                socketio.emit("mention_notification", {
                    "from": username,
                    "room_id": rid,
                    "room_name": room["name"],
                    "text": text[:80],
                }, room=sid)

@socketio.on("edit_message")
def on_edit_message(data):
    username = get_user(request.sid)
    rid = data.get("room_id", "")
    msg_id = data.get("msg_id", "")
    new_text = (data.get("text") or "").strip()
    if not new_text:
        return
    for msg in room_messages.get(rid, []):
        if msg["id"] == msg_id:
            real_author = msg.get("real_author", msg.get("author"))
            if real_author != username and not can_moderate(username):
                emit("error_msg", {"text": "Нет прав"})
                return
            msg["text"] = new_text
            msg["edited"] = True
            emit("message_edited", {"msg_id": msg_id, "text": new_text}, room=rid)
            return

@socketio.on("delete_message")
def on_delete_message(data):
    username = get_user(request.sid)
    rid = data.get("room_id", "")
    msg_id = data.get("msg_id", "")
    room = rooms.get(rid)
    if not room:
        return
    is_owner = room.get("owner") == username
    if not can_moderate(username) and not is_owner:
        emit("error_msg", {"text": "Нет прав"})
        return
    msgs = room_messages.get(rid, [])
    for i, msg in enumerate(msgs):
        if msg["id"] == msg_id:
            msgs.pop(i)
            emit("message_deleted", {"msg_id": msg_id}, room=rid)
            return

@socketio.on("pin_message")
def on_pin_message(data):
    username = get_user(request.sid)
    rid = data.get("room_id", "")
    msg_id = data.get("msg_id", "")
    room = rooms.get(rid)
    if not room:
        return
    is_owner = room.get("owner") == username
    if not can_moderate(username) and not is_owner:
        emit("error_msg", {"text": "Нет прав"})
        return
    # Unpin all
    for msg in room_messages.get(rid, []):
        msg["pinned"] = False
    # Pin target
    for msg in room_messages.get(rid, []):
        if msg["id"] == msg_id:
            msg["pinned"] = True
            room["pinned_msg_id"] = msg_id
            emit("message_pinned", {"msg_id": msg_id, "msg": msg}, room=rid)
            return

@socketio.on("unpin_message")
def on_unpin_message(data):
    username = get_user(request.sid)
    rid = data.get("room_id", "")
    room = rooms.get(rid)
    if not room:
        return
    is_owner = room.get("owner") == username
    if not can_moderate(username) and not is_owner:
        emit("error_msg", {"text": "Нет прав"})
        return
    for msg in room_messages.get(rid, []):
        msg["pinned"] = False
    room["pinned_msg_id"] = None
    emit("message_unpinned", {}, room=rid)

@socketio.on("add_reaction")
def on_add_reaction(data):
    username = get_user(request.sid)
    rid = data.get("room_id", "")
    msg_id = data.get("msg_id", "")
    emoji = data.get("emoji", "")
    if not emoji:
        return
    for msg in room_messages.get(rid, []):
        if msg["id"] == msg_id:
            if emoji not in msg["reactions"]:
                msg["reactions"][emoji] = []
            if username in msg["reactions"][emoji]:
                msg["reactions"][emoji].remove(username)
            else:
                msg["reactions"][emoji].append(username)
                real_author = msg.get("real_author", msg.get("author"))
                if real_author in users:
                    users[real_author]["reactions_received"] = users[real_author].get("reactions_received", 0) + 1
            emit("reaction_update", {"msg_id": msg_id, "reactions": msg["reactions"]}, room=rid)
            return

# ── Moderation ────────────────────────────────────────────────────────────────────

@socketio.on("kick_user")
def on_kick_user(data):
    username = get_user(request.sid)
    rid = data.get("room_id", "")
    target = data.get("target", "")
    room = rooms.get(rid)
    if not room:
        return
    is_owner = room.get("owner") == username
    if not can_moderate(username) and not is_owner:
        emit("error_msg", {"text": "Нет прав"})
        return
    for sid, uname in list(sessions.items()):
        if uname == target and sid in room_members.get(rid, set()):
            room_members[rid].discard(sid)
            socketio.emit("kicked", {"room_id": rid, "reason": f"Вас выгнал {username}"}, room=sid)
            leave_room(rid, sid=sid)
            sys_msg = {
                "id": generate_id(), "room_id": rid,
                "author": "System", "text": f"🚫 {target} был выгнан из комнаты",
                "image": None, "timestamp": now_str(), "ts": now_ts(),
                "is_system": True, "reactions": {}, "tags": [], "msg_tags": [],
                "edited": False, "pinned": False,
            }
            room_messages.setdefault(rid, []).append(sys_msg)
            emit("message", sys_msg, room=rid)
            emit("members_update", get_room_members_info(rid), room=rid)
            return

@socketio.on("ban_user")
def on_ban_user(data):
    username = get_user(request.sid)
    if not can_admin(username):
        emit("error_msg", {"text": "Нет прав"})
        return
    target = data.get("target", "")
    if target in users:
        users[target]["banned"] = True
        bans.add(target)
        for sid, uname in list(sessions.items()):
            if uname == target:
                socketio.emit("banned", {"reason": "Вы заблокированы администратором"}, room=sid)
                disconnect(sid)

@socketio.on("unban_user")
def on_unban_user(data):
    username = get_user(request.sid)
    if not can_admin(username):
        emit("error_msg", {"text": "Нет прав"})
        return
    target = data.get("target", "")
    if target in users:
        users[target]["banned"] = False
        bans.discard(target)
    emit("admin_data", build_admin_data())

@socketio.on("set_moderator")
def on_set_moderator(data):
    username = get_user(request.sid)
    if not can_admin(username):
        emit("error_msg", {"text": "Нет прав"})
        return
    target = data.get("target", "")
    if target in users:
        users[target]["role"] = "moderator"
        for sid, uname in sessions.items():
            if uname == target:
                socketio.emit("user_update", build_user_info(target), room=sid)
    emit("admin_data", build_admin_data())

@socketio.on("remove_moderator")
def on_remove_moderator(data):
    username = get_user(request.sid)
    if not can_admin(username):
        emit("error_msg", {"text": "Нет прав"})
        return
    target = data.get("target", "")
    if target in users and users[target].get("role") == "moderator":
        users[target]["role"] = "user"
        for sid, uname in sessions.items():
            if uname == target:
                socketio.emit("user_update", build_user_info(target), room=sid)
    emit("admin_data", build_admin_data())

@socketio.on("set_custom_join_msg")
def on_set_custom_join_msg(data):
    username = get_user(request.sid)
    if not can_admin(username):
        emit("error_msg", {"text": "Нет прав"})
        return
    rid = data.get("room_id", "")
    msg = data.get("msg", "")
    if rid in rooms:
        rooms[rid]["custom_join_msg"] = msg
        emit("admin_data", build_admin_data())

@socketio.on("set_spam_delay")
def on_set_spam_delay(data):
    username = get_user(request.sid)
    rid = data.get("room_id", "")
    delay = int(data.get("delay", 0))
    room = rooms.get(rid)
    if not room:
        return
    is_owner = room.get("owner") == username
    if not can_moderate(username) and not is_owner:
        emit("error_msg", {"text": "Нет прав"})
        return
    room["spam_delay"] = delay
    emit("room_settings_update", {"room_id": rid, "spam_delay": delay}, room=rid)

# ── Observer Mode ─────────────────────────────────────────────────────────────────

@socketio.on("toggle_observer")
def on_toggle_observer(data):
    username = get_user(request.sid)
    if not can_admin(username):
        return
    state = bool(data.get("state", False))
    observer_mode[username] = state
    emit("observer_update", {"state": state})

# ── Custom Roles ──────────────────────────────────────────────────────────────────

@socketio.on("create_custom_role")
def on_create_custom_role(data):
    username = get_user(request.sid)
    if not can_moderate(username):
        emit("error_msg", {"text": "Нет прав"})
        return
    role_name = (data.get("name") or "").strip()
    color = data.get("color", "#aaaaaa")
    status = data.get("status", "")
    prefix = data.get("prefix", "")
    if not role_name:
        return
    custom_roles[role_name] = {"color": color, "status": status, "prefix": prefix, "name": role_name}
    socketio.emit("custom_roles_update", list(custom_roles.values()))

@socketio.on("delete_custom_role")
def on_delete_custom_role(data):
    username = get_user(request.sid)
    if not can_moderate(username):
        emit("error_msg", {"text": "Нет прав"})
        return
    role_name = data.get("name", "")
    custom_roles.pop(role_name, None)
    # Remove from all users
    for u in users.values():
        if u.get("custom_role") == role_name:
            u["custom_role"] = None
    socketio.emit("custom_roles_update", list(custom_roles.values()))

@socketio.on("assign_custom_role")
def on_assign_custom_role(data):
    username = get_user(request.sid)
    if not can_moderate(username):
        emit("error_msg", {"text": "Нет прав"})
        return
    target = data.get("target", "")
    role_name = data.get("role_name", "")
    if target not in users:
        emit("error_msg", {"text": "Пользователь не найден"})
        return
    if role_name and role_name not in custom_roles:
        emit("error_msg", {"text": "Роль не найдена"})
        return
    users[target]["custom_role"] = role_name if role_name else None
    for sid, uname in sessions.items():
        if uname == target:
            socketio.emit("user_update", build_user_info(target), room=sid)
    emit("admin_data", build_admin_data())

# ── Leaderboard ───────────────────────────────────────────────────────────────────

@socketio.on("get_leaderboard")
def on_get_leaderboard():
    board = []
    for uname, u in users.items():
        if u.get("role") == "bot":
            continue
        board.append({
            "username": uname,
            "role": u.get("role", "user"),
            "custom_role": u.get("custom_role"),
            "total_msgs": u.get("total_msgs", 0),
            "reactions_received": u.get("reactions_received", 0),
            "time_in_chat": now_ts() - u.get("join_time", now_ts()),
        })
    emit("leaderboard_data", board)

# ── Admin Panel ───────────────────────────────────────────────────────────────────

def build_admin_data():
    return {
        "users": [build_user_info(u) for u in users if users[u].get("role") != "bot"],
        "rooms": build_rooms_list(),
        "custom_roles": list(custom_roles.values()),
        "banned": list(bans),
        "moderators": [u for u in users if users[u].get("role") == "moderator"],
        "stats": {
            "total_users": len([u for u in users if users[u].get("role") != "bot"]),
            "total_rooms": len(rooms),
            "total_messages": sum(len(m) for m in room_messages.values()),
        }
    }

@socketio.on("get_admin_data")
def on_get_admin_data():
    username = get_user(request.sid)
    if not can_admin(username):
        return
    emit("admin_data", build_admin_data())

@socketio.on("get_custom_roles")
def on_get_custom_roles():
    emit("custom_roles_update", list(custom_roles.values()))

@socketio.on("broadcast_announcement")
def on_broadcast_announcement(data):
    username = get_user(request.sid)
    if not can_admin(username):
        return
    text = data.get("text", "")
    msg = {
        "id": generate_id(),
        "author": "📢 Администрация",
        "real_author": username,
        "text": text,
        "image": None,
        "timestamp": now_str(),
        "ts": now_ts(),
        "is_announcement": True,
        "is_global": True,
        "reactions": {},
        "tags": [],
        "msg_tags": [],
        "edited": False,
        "pinned": False,
        "is_system": False,
    }
    socketio.emit("global_announcement", msg)

# ── WebRTC Signaling ──────────────────────────────────────────────────────────────

@socketio.on("webrtc_offer")
def on_webrtc_offer(data):
    target_sid = data.get("target_sid")
    emit("webrtc_offer", {
        "offer": data.get("offer"),
        "from_sid": request.sid,
        "from_user": get_user(request.sid),
    }, room=target_sid)

@socketio.on("webrtc_answer")
def on_webrtc_answer(data):
    target_sid = data.get("target_sid")
    emit("webrtc_answer", {
        "answer": data.get("answer"),
        "from_sid": request.sid,
        "from_user": get_user(request.sid),
    }, room=target_sid)

@socketio.on("webrtc_ice")
def on_webrtc_ice(data):
    target_sid = data.get("target_sid")
    emit("webrtc_ice", {
        "candidate": data.get("candidate"),
        "from_sid": request.sid,
    }, room=target_sid)

@socketio.on("voice_join")
def on_voice_join(data):
    username = get_user(request.sid)
    rid = data.get("room_id", "")
    if rid not in rooms:
        return
    # Announce to room peers
    existing_peers = []
    for sid in list(room_members.get(rid, set())):
        if sid != request.sid:
            uname = sessions.get(sid)
            if uname:
                existing_peers.append({"sid": sid, "username": uname})
    emit("voice_peers", {"peers": existing_peers, "room_id": rid})
    emit("voice_user_joined", {"sid": request.sid, "username": username}, room=rid, skip_sid=request.sid)

@socketio.on("voice_leave")
def on_voice_leave(data):
    username = get_user(request.sid)
    rid = data.get("room_id", "")
    emit("voice_user_left", {"sid": request.sid, "username": username}, room=rid, skip_sid=request.sid)

@socketio.on("screen_share_start")
def on_screen_share_start(data):
    username = get_user(request.sid)
    rid = data.get("room_id", "")
    emit("screen_share_started", {"sid": request.sid, "username": username}, room=rid, skip_sid=request.sid)

@socketio.on("screen_share_stop")
def on_screen_share_stop(data):
    username = get_user(request.sid)
    rid = data.get("room_id", "")
    emit("screen_share_stopped", {"sid": request.sid, "username": username}, room=rid, skip_sid=request.sid)

@socketio.on("screen_share_offer")
def on_screen_share_offer(data):
    target_sid = data.get("target_sid")
    emit("screen_share_offer", {
        "offer": data.get("offer"),
        "from_sid": request.sid,
        "from_user": get_user(request.sid),
    }, room=target_sid)

@socketio.on("screen_share_answer")
def on_screen_share_answer(data):
    target_sid = data.get("target_sid")
    emit("screen_share_answer", {
        "answer": data.get("answer"),
        "from_sid": request.sid,
    }, room=target_sid)

@socketio.on("screen_share_ice")
def on_screen_share_ice(data):
    target_sid = data.get("target_sid")
    emit("screen_share_ice", {
        "candidate": data.get("candidate"),
        "from_sid": request.sid,
    }, room=target_sid)

# ── Main ───────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 60)
    print("  Vietugram Chat Server v3.0")
    print("  Developer: Vietu")
    print(f"  Running on http://{HOST}:{PORT}")
    print(f"  For local: http://localhost:{PORT}")
    print("=" * 60)
    socketio.run(app, host=HOST, port=PORT, debug=False)
