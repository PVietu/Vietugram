# =============================================================================
# VIETUGRAM - Запуск в Google Colab (одна ячейка, Python)
# Автор: Vietu
# Версия: 3.0 (полный набор функций)
# =============================================================================

# Вставьте это в ячейку Colab и запустите как %%python (не %%shell)
# Или просто скопируйте содержимое в ячейку без магии.

import subprocess, sys

# 1. Установка библиотек
subprocess.run([sys.executable, "-m", "pip", "install",
                "flask", "flask-socketio", "flask-cors", "eventlet", "pyngrok", "-q"],
               check=True)

# 2. Запись index.html
HTML_CONTENT = r"""<!DOCTYPE html>
<html lang="ru">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Vietugram — Чат</title>
  <script src="https://cdn.socket.io/4.7.2/socket.io.min.js"></script>
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet" />
  <style>
    :root {
      --bg-primary:    #0d0f14;
      --bg-secondary:  #131720;
      --bg-tertiary:   #1a1f2e;
      --bg-card:       #1e2436;
      --bg-input:      #252b3b;
      --bg-hover:      #2a3147;
      --accent:        #6c63ff;
      --accent-hover:  #7c74ff;
      --accent-glow:   rgba(108,99,255,0.3);
      --color-user:    #e2e8f0;
      --color-mod:     #34d399;
      --color-admin:   #fbbf24;
      --color-owner:   #f472b6;
      --text-primary:  #e2e8f0;
      --text-secondary:#94a3b8;
      --text-muted:    #4a5568;
      --border:        rgba(255,255,255,0.07);
      --border-accent: rgba(108,99,255,0.4);
      --red:    #ef4444;
      --green:  #22c55e;
      --yellow: #eab308;
      --blue:   #3b82f6;
      --pink:   #ec4899;
      --radius-sm: 6px;
      --radius:    12px;
      --radius-lg: 18px;
      --radius-xl: 24px;
      --shadow:      0 4px 24px rgba(0,0,0,0.4);
      --shadow-glow: 0 0 40px rgba(108,99,255,0.15);
      --transition: 0.2s ease;
    }
    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
    html, body {
      height: 100%; font-family: 'Inter', system-ui, sans-serif;
      background: var(--bg-primary); color: var(--text-primary);
      overflow: hidden; -webkit-font-smoothing: antialiased;
    }
    .hidden { display: none !important; }
    .flex { display: flex; } .flex-col { flex-direction: column; }
    .items-center { align-items: center; } .justify-center { justify-content: center; }
    .justify-between { justify-content: space-between; }
    .gap-1{gap:4px}.gap-2{gap:8px}.gap-3{gap:12px}.gap-4{gap:16px}
    .flex-1{flex:1;min-width:0}.w-full{width:100%}
    .text-sm{font-size:13px}.text-xs{font-size:11px}.text-lg{font-size:18px}
    .text-xl{font-size:22px}.text-2xl{font-size:28px}
    .font-bold{font-weight:700}.font-semibold{font-weight:600}.font-medium{font-weight:500}
    .truncate{overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
    ::-webkit-scrollbar{width:5px;height:5px}
    ::-webkit-scrollbar-track{background:transparent}
    ::-webkit-scrollbar-thumb{background:var(--bg-hover);border-radius:99px}
    .btn {
      display:inline-flex;align-items:center;justify-content:center;gap:8px;
      padding:10px 20px;border:none;border-radius:var(--radius);
      font-family:inherit;font-size:14px;font-weight:600;cursor:pointer;
      transition:var(--transition);white-space:nowrap;outline:none;
    }
    .btn:active{transform:scale(0.97)}
    .btn-primary{background:var(--accent);color:#fff;box-shadow:0 4px 16px var(--accent-glow)}
    .btn-primary:hover{background:var(--accent-hover);box-shadow:0 4px 24px var(--accent-glow)}
    .btn-ghost{background:transparent;color:var(--text-secondary);border:1px solid var(--border)}
    .btn-ghost:hover{background:var(--bg-hover);color:var(--text-primary)}
    .btn-danger{background:rgba(239,68,68,0.15);color:var(--red);border:1px solid rgba(239,68,68,0.3)}
    .btn-danger:hover{background:rgba(239,68,68,0.25)}
    .btn-success{background:rgba(34,197,94,0.15);color:var(--green);border:1px solid rgba(34,197,94,0.3)}
    .btn-success:hover{background:rgba(34,197,94,0.25)}
    .btn-warning{background:rgba(234,179,8,0.15);color:var(--yellow);border:1px solid rgba(234,179,8,0.3)}
    .btn-warning:hover{background:rgba(234,179,8,0.25)}
    .btn-sm{padding:6px 12px;font-size:12px;border-radius:var(--radius-sm)}
    .btn-icon{padding:8px;border-radius:var(--radius-sm);min-width:36px}
    .input {
      width:100%;padding:12px 16px;background:var(--bg-input);border:1px solid var(--border);
      border-radius:var(--radius);color:var(--text-primary);font-family:inherit;
      font-size:14px;outline:none;transition:var(--transition);
    }
    .input:focus{border-color:var(--accent);box-shadow:0 0 0 3px var(--accent-glow)}
    .input::placeholder{color:var(--text-muted)}
    .input-sm{padding:8px 12px;font-size:13px}
    textarea.input{resize:none}
    #app{width:100vw;height:100vh;position:relative;overflow:hidden}
    .screen{position:absolute;inset:0;display:flex;opacity:0;pointer-events:none;transition:opacity 0.3s ease}
    .screen.active{opacity:1;pointer-events:all}

    /* LOGIN */
    #screen-login{align-items:center;justify-content:center;background:var(--bg-primary)}
    #screen-login::before{
      content:'';position:absolute;inset:0;pointer-events:none;
      background:radial-gradient(ellipse 80% 60% at 20% 40%,rgba(108,99,255,0.12) 0%,transparent 60%),
                 radial-gradient(ellipse 60% 50% at 80% 70%,rgba(251,191,36,0.06) 0%,transparent 50%);
    }
    .login-card{
      position:relative;background:var(--bg-card);border:1px solid var(--border);
      border-radius:var(--radius-xl);padding:48px 40px;width:100%;max-width:420px;
      box-shadow:var(--shadow),var(--shadow-glow);z-index:1;
    }
    .logo{text-align:center;margin-bottom:32px}
    .logo-icon{
      width:64px;height:64px;background:linear-gradient(135deg,var(--accent),#a78bfa);
      border-radius:20px;display:flex;align-items:center;justify-content:center;
      font-size:32px;margin:0 auto 16px;box-shadow:0 8px 32px var(--accent-glow);
    }
    .logo h1{
      font-size:28px;font-weight:800;
      background:linear-gradient(135deg,#fff 0%,var(--accent) 100%);
      -webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;
    }
    .logo p{color:var(--text-secondary);font-size:13px;margin-top:6px}
    .login-form{display:flex;flex-direction:column;gap:16px}
    .login-form label{font-size:13px;font-weight:500;color:var(--text-secondary);margin-bottom:6px;display:block}
    .author-badge{position:absolute;bottom:18px;right:20px;font-size:11px;color:var(--text-muted)}

    /* LOBBY */
    #screen-lobby{flex-direction:column;background:var(--bg-primary)}
    .topbar{
      height:60px;min-height:60px;background:var(--bg-secondary);border-bottom:1px solid var(--border);
      display:flex;align-items:center;padding:0 20px;gap:12px;z-index:10;flex-wrap:wrap;
    }
    .topbar-brand{
      font-size:18px;font-weight:800;
      background:linear-gradient(135deg,#fff 0%,var(--accent) 100%);
      -webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;
      letter-spacing:-0.5px;
    }
    .topbar-user{display:flex;align-items:center;gap:8px;margin-left:auto}
    .user-avatar{
      width:34px;height:34px;border-radius:50%;background:var(--accent);
      display:flex;align-items:center;justify-content:center;
      font-size:14px;font-weight:700;color:#fff;flex-shrink:0;
    }
    .nick-tag{font-size:14px;font-weight:600}
    .nick-tag.admin{color:var(--color-admin)}
    .nick-tag.moderator{color:var(--color-mod)}
    .nick-tag.owner{color:var(--color-owner)}
    .nick-tag.user{color:var(--color-user)}

    .announcement-bar{
      background:linear-gradient(135deg,rgba(108,99,255,0.2),rgba(167,139,250,0.1));
      border-bottom:1px solid var(--border-accent);padding:10px 20px;
      display:flex;align-items:center;gap:10px;font-size:14px;color:var(--text-primary);
    }
    .announcement-bar .ann-icon{font-size:18px}
    .lobby-content{flex:1;display:flex;overflow:hidden}
    .online-sidebar{
      width:220px;min-width:220px;background:var(--bg-secondary);
      border-right:1px solid var(--border);display:flex;flex-direction:column;overflow:hidden;
    }
    .sidebar-header{
      padding:16px;font-size:12px;font-weight:600;color:var(--text-muted);
      text-transform:uppercase;letter-spacing:1px;border-bottom:1px solid var(--border);
    }
    .online-list{flex:1;overflow-y:auto;padding:8px}
    .online-item{display:flex;align-items:center;gap:10px;padding:8px 10px;border-radius:var(--radius-sm);font-size:13px}
    .online-dot{width:8px;height:8px;border-radius:50%;background:var(--green);flex-shrink:0;box-shadow:0 0 6px rgba(34,197,94,0.5)}
    .role-group-header{
      font-size:10px;font-weight:700;color:var(--text-muted);text-transform:uppercase;
      letter-spacing:1px;padding:8px 10px 4px;
    }

    .lobby-main{flex:1;overflow-y:auto;padding:24px}
    .lobby-toolbar{display:flex;align-items:center;gap:12px;margin-bottom:24px;flex-wrap:wrap}
    .lobby-toolbar h2{font-size:22px;font-weight:700;flex:1}
    .rooms-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:16px}
    .room-card{
      background:var(--bg-card);border:1px solid var(--border);border-radius:var(--radius-lg);
      padding:20px;cursor:pointer;transition:var(--transition);position:relative;overflow:hidden;
    }
    .room-card.room-pinned{border:2px solid gold!important;box-shadow:0 0 15px rgba(255,215,0,0.4)}
    .room-card::before{
      content:'';position:absolute;inset:0;
      background:linear-gradient(135deg,var(--accent-glow),transparent);
      opacity:0;transition:var(--transition);
    }
    .room-card:hover{border-color:var(--border-accent);transform:translateY(-2px);box-shadow:var(--shadow)}
    .room-card:hover::before{opacity:1}
    .room-card-header{display:flex;align-items:flex-start;justify-content:space-between;gap:12px;margin-bottom:12px}
    .room-card-icon{
      width:42px;height:42px;background:var(--accent-glow);border-radius:12px;
      display:flex;align-items:center;justify-content:center;font-size:20px;flex-shrink:0;
      border:1px solid var(--border-accent);
    }
    .room-card-name{font-weight:700;font-size:16px;line-height:1.3}
    .room-badge{font-size:11px;padding:2px 8px;border-radius:99px;font-weight:600}
    .badge-lock{background:rgba(234,179,8,0.15);color:var(--yellow);border:1px solid rgba(234,179,8,0.3)}
    .badge-open{background:rgba(34,197,94,0.12);color:var(--green);border:1px solid rgba(34,197,94,0.25)}
    .badge-voice{background:rgba(59,130,246,0.15);color:var(--blue);border:1px solid rgba(59,130,246,0.3)}
    .badge-anon{background:rgba(107,114,128,0.2);color:#9ca3af;border:1px solid rgba(107,114,128,0.3)}
    .badge-temp{background:rgba(239,68,68,0.15);color:var(--red);border:1px solid rgba(239,68,68,0.3)}
    .room-meta{font-size:12px;color:var(--text-muted);display:flex;align-items:center;gap:8px;flex-wrap:wrap}
    .rooms-empty{text-align:center;padding:80px 20px;color:var(--text-muted)}
    .rooms-empty .empty-icon{font-size:56px;margin-bottom:16px;opacity:0.5}
    .rooms-empty p{font-size:16px;margin-bottom:8px;color:var(--text-secondary)}
    .pin-btn{position:absolute;top:8px;right:8px;z-index:5}

    /* CHAT */
    #screen-chat{flex-direction:column;background:var(--bg-primary)}
    .chat-topbar{
      height:60px;min-height:60px;background:var(--bg-secondary);
      border-bottom:1px solid var(--border);display:flex;align-items:center;
      padding:0 16px;gap:12px;z-index:10;
    }
    .chat-room-name{font-size:16px;font-weight:700;flex:1}
    .chat-layout{flex:1;display:flex;overflow:hidden}
    .messages-area{flex:1;display:flex;flex-direction:column;overflow:hidden;position:relative}

    /* Pinned message banner */
    .pinned-banner{
      background:linear-gradient(90deg,rgba(108,99,255,0.2),rgba(108,99,255,0.05));
      border-bottom:2px solid var(--border-accent);padding:8px 16px;
      display:flex;align-items:center;gap:10px;cursor:pointer;
      font-size:13px;transition:var(--transition);
    }
    .pinned-banner:hover{background:rgba(108,99,255,0.25)}
    .pinned-banner .pin-icon{font-size:16px;flex-shrink:0}
    .pinned-banner .pin-text{flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;color:var(--text-secondary)}
    .pinned-banner .pin-nick{color:var(--accent);font-weight:600;margin-right:6px}

    /* Drag overlay */
    .drag-overlay{
      position:absolute;inset:0;background:rgba(108,99,255,0.15);
      border:3px dashed var(--accent);border-radius:var(--radius);
      display:flex;align-items:center;justify-content:center;
      font-size:24px;font-weight:700;color:var(--accent);
      z-index:50;pointer-events:none;opacity:0;transition:opacity 0.2s;
    }
    .drag-overlay.active{opacity:1}

    .messages-list{flex:1;overflow-y:auto;padding:16px;display:flex;flex-direction:column;gap:2px}
    .msg{
      display:flex;flex-direction:column;padding:10px 14px;
      border-radius:var(--radius);max-width:100%;animation:msgIn 0.2s ease;
    }
    @keyframes msgIn{from{opacity:0;transform:translateY(8px)}to{opacity:1;transform:translateY(0)}}
    .msg:hover{background:var(--bg-tertiary)}
    .msg:hover .msg-actions{opacity:1}
    .msg.pinned-msg{border-left:3px solid var(--accent);background:rgba(108,99,255,0.06)}
    .msg-header{display:flex;align-items:baseline;gap:10px;margin-bottom:4px;flex-wrap:wrap}
    .msg-nick{font-weight:700;font-size:14px;cursor:default}
    .msg-nick.user{color:var(--color-user)}
    .msg-nick.moderator{color:var(--color-mod)}
    .msg-nick.admin{color:var(--color-admin)}
    .msg-nick.owner{color:var(--color-owner)}
    .msg-time{font-size:11px;color:var(--text-muted)}
    .msg-actions{margin-left:auto;opacity:0;transition:var(--transition);display:flex;gap:4px}
    .msg-body{font-size:14px;line-height:1.6;color:var(--text-primary);word-break:break-word;white-space:pre-wrap}
    .mention{
      color:var(--accent);background:rgba(108,99,255,0.15);
      padding:0 3px;border-radius:3px;font-weight:600;
    }
    .mention.me{
      background:rgba(108,99,255,0.3);color:#fff;
    }
    .msg-tag{
      display:inline-block;padding:1px 8px;border-radius:99px;font-size:11px;
      font-weight:700;margin-right:4px;margin-bottom:2px;
    }
    .msg-tag.important{background:rgba(239,68,68,0.2);color:var(--red);border:1px solid rgba(239,68,68,0.3)}
    .msg-tag.urgent{background:rgba(234,179,8,0.2);color:var(--yellow);border:1px solid rgba(234,179,8,0.3)}
    .msg-tag.todo{background:rgba(59,130,246,0.2);color:var(--blue);border:1px solid rgba(59,130,246,0.3)}
    .msg-edited{font-size:10px;color:var(--text-muted);font-style:italic;margin-left:6px}
    .msg-image{
      margin-top:8px;max-width:320px;max-height:240px;border-radius:var(--radius);
      cursor:zoom-in;object-fit:cover;border:1px solid var(--border);transition:var(--transition);
    }
    .msg-image:hover{border-color:var(--accent)}
    .msg-reactions{margin-top:6px;display:flex;gap:6px;flex-wrap:wrap}
    .react-btn{
      background:transparent;border:1px solid var(--border);border-radius:6px;
      padding:2px 8px;font-size:14px;cursor:pointer;color:var(--text-secondary);user-select:none;
      transition:var(--transition);
    }
    .react-btn:hover{background:var(--bg-hover)}
    .react-btn.active{background:var(--accent-glow);color:var(--accent);border-color:var(--accent)}
    .msg-system{text-align:center;padding:6px 16px;font-size:12px;color:var(--text-muted);background:transparent}
    .msg-system:hover{background:transparent}
    .msg-system span{background:var(--bg-tertiary);padding:3px 12px;border-radius:99px}
    .msg-system-mod{text-align:center;padding:6px 16px;font-size:12px;color:var(--color-mod);background:transparent}
    .msg-system-mod:hover{background:transparent}
    .msg-system-mod span{background:rgba(52,211,153,0.1);border:1px solid rgba(52,211,153,0.2);padding:3px 12px;border-radius:99px}
    .msg-system-admin{text-align:center;padding:6px 16px;font-size:12px;color:var(--color-admin);background:transparent}
    .msg-system-admin:hover{background:transparent}
    .msg-system-admin span{background:rgba(251,191,36,0.1);border:1px solid rgba(251,191,36,0.2);padding:3px 12px;border-radius:99px}
    .msg-announcement{
      background:linear-gradient(135deg,rgba(108,99,255,0.15),rgba(108,99,255,0.05));
      border:1px solid var(--border-accent);border-radius:var(--radius);padding:12px 16px;margin:4px 0;
    }
    .msg-announcement:hover{background:linear-gradient(135deg,rgba(108,99,255,0.2),rgba(108,99,255,0.08))}
    .announcement-label{
      font-size:11px;font-weight:700;color:var(--accent);text-transform:uppercase;
      letter-spacing:1px;margin-bottom:6px;display:flex;align-items:center;gap:6px;
    }

    /* Edit mode */
    .msg-edit-area{
      width:100%;margin-top:6px;padding:8px;background:var(--bg-input);
      border:1px solid var(--accent);border-radius:var(--radius-sm);
      color:var(--text-primary);font-family:inherit;font-size:14px;
      resize:none;outline:none;
    }
    .msg-edit-btns{display:flex;gap:6px;margin-top:6px}

    /* Spam cooldown */
    .spam-warning{
      font-size:12px;color:var(--red);padding:4px 16px;
      display:none;
    }

    /* Chat input */
    .chat-input-area{padding:16px;background:var(--bg-secondary);border-top:1px solid var(--border)}
    .chat-input-row{
      display:flex;align-items:flex-end;gap:10px;background:var(--bg-input);
      border:1px solid var(--border);border-radius:var(--radius-lg);padding:10px 14px;transition:var(--transition);
    }
    .chat-input-row:focus-within{border-color:var(--accent);box-shadow:0 0 0 3px var(--accent-glow)}
    .chat-textarea{
      flex:1;background:transparent;border:none;color:var(--text-primary);
      font-family:inherit;font-size:14px;line-height:1.5;resize:none;
      min-height:22px;max-height:120px;outline:none;overflow-y:auto;
    }
    .chat-textarea::placeholder{color:var(--text-muted)}
    .attach-preview{display:none;margin-bottom:10px;position:relative;width:fit-content}
    .attach-preview img{max-height:80px;border-radius:var(--radius-sm);border:1px solid var(--border)}
    .attach-preview .remove-img{
      position:absolute;top:-6px;right:-6px;width:20px;height:20px;
      background:var(--red);border-radius:50%;display:flex;align-items:center;
      justify-content:center;font-size:12px;cursor:pointer;color:#fff;
    }
    .announce-toggle{display:flex;align-items:center;gap:8px;font-size:12px;color:var(--text-muted);margin-bottom:8px;padding:0 4px}
    .announce-toggle input{cursor:pointer;accent-color:var(--accent)}
    .announce-toggle label{cursor:pointer}
    .tag-selector{display:flex;gap:6px;margin-bottom:8px;padding:0 4px;flex-wrap:wrap}
    .tag-selector-btn{
      padding:3px 10px;border-radius:99px;font-size:11px;font-weight:700;cursor:pointer;
      border:1px solid;background:transparent;font-family:inherit;transition:var(--transition);
    }
    .tag-selector-btn.important{color:var(--red);border-color:rgba(239,68,68,0.4)}
    .tag-selector-btn.important.active{background:rgba(239,68,68,0.2)}
    .tag-selector-btn.urgent{color:var(--yellow);border-color:rgba(234,179,8,0.4)}
    .tag-selector-btn.urgent.active{background:rgba(234,179,8,0.2)}
    .tag-selector-btn.todo{color:var(--blue);border-color:rgba(59,130,246,0.4)}
    .tag-selector-btn.todo.active{background:rgba(59,130,246,0.2)}

    /* Members sidebar */
    .members-sidebar{
      width:200px;min-width:200px;background:var(--bg-secondary);
      border-left:1px solid var(--border);display:flex;flex-direction:column;overflow:hidden;
    }
    .member-item{
      display:flex;align-items:center;gap:8px;padding:8px 12px;
      border-radius:var(--radius-sm);font-size:13px;transition:var(--transition);
    }
    .member-item:hover{background:var(--bg-hover)}
    .member-actions{margin-left:auto;display:none;gap:4px}
    .member-item:hover .member-actions{display:flex}
    .member-emoji{font-size:14px}

    /* Voice room */
    #screen-voice{flex-direction:column;background:var(--bg-primary);align-items:center;justify-content:center}
    .voice-room-bg{
      position:absolute;inset:0;
      background:radial-gradient(ellipse 80% 60% at 50% 50%,rgba(59,130,246,0.08) 0%,transparent 70%);
    }
    .voice-room-container{
      position:relative;z-index:1;display:flex;flex-direction:column;align-items:center;
      width:100%;max-width:900px;padding:24px;
    }
    .voice-topbar{
      width:100%;display:flex;align-items:center;gap:12px;margin-bottom:24px;
      background:var(--bg-secondary);border:1px solid var(--border);border-radius:var(--radius-lg);padding:12px 20px;
    }
    .voice-room-title{font-size:18px;font-weight:700;flex:1}
    .voice-participants{
      display:flex;flex-wrap:wrap;gap:20px;justify-content:center;width:100%;
      margin-bottom:32px;min-height:200px;
    }
    .voice-participant{
      display:flex;flex-direction:column;align-items:center;gap:10px;
      padding:20px;background:var(--bg-card);border:1px solid var(--border);
      border-radius:var(--radius-lg);min-width:130px;transition:var(--transition);position:relative;
    }
    .voice-participant.speaking{
      border-color:var(--green);box-shadow:0 0 20px rgba(34,197,94,0.3);
    }
    .voice-participant.muted-mic{border-color:var(--red)}
    .voice-avatar{
      width:72px;height:72px;border-radius:50%;background:var(--accent);
      display:flex;align-items:center;justify-content:center;font-size:30px;
      font-weight:700;position:relative;
    }
    .voice-avatar-ring{
      position:absolute;inset:-4px;border-radius:50%;border:2px solid var(--green);
      animation:voicePulse 1s ease-in-out infinite;opacity:0;
    }
    .speaking .voice-avatar-ring{opacity:1}
    @keyframes voicePulse{0%,100%{transform:scale(1);opacity:0.8}50%{transform:scale(1.05);opacity:0.4}}
    .voice-nick{font-size:13px;font-weight:600;max-width:120px;text-align:center;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
    .voice-status-icons{display:flex;gap:6px;font-size:14px}
    .voice-controls{
      display:flex;gap:12px;align-items:center;
      background:var(--bg-card);border:1px solid var(--border);
      border-radius:var(--radius-xl);padding:16px 24px;
    }
    .voice-ctrl-btn{
      width:56px;height:56px;border-radius:50%;border:none;cursor:pointer;
      display:flex;align-items:center;justify-content:center;font-size:22px;
      transition:var(--transition);
    }
    .voice-ctrl-btn:hover{transform:scale(1.1)}
    .voice-ctrl-btn.mic-on{background:var(--bg-hover);color:var(--text-primary)}
    .voice-ctrl-btn.mic-off{background:rgba(239,68,68,0.2);color:var(--red);border:1px solid rgba(239,68,68,0.4)}
    .voice-ctrl-btn.deaf-off{background:rgba(234,179,8,0.2);color:var(--yellow);border:1px solid rgba(234,179,8,0.4)}
    .voice-ctrl-btn.deaf-on{background:var(--bg-hover);color:var(--text-primary)}
    .voice-ctrl-btn.leave-btn{background:rgba(239,68,68,0.8);color:#fff;width:64px;height:64px;font-size:20px}
    .voice-ctrl-btn.leave-btn:hover{background:var(--red)}
    .voice-ctrl-btn.screen-btn{background:var(--bg-hover);color:var(--text-primary)}
    .voice-ctrl-btn.screen-btn.active{background:rgba(59,130,246,0.3);color:var(--blue);border:1px solid rgba(59,130,246,0.5)}

    /* Modals */
    .modal-overlay{
      position:fixed;inset:0;background:rgba(0,0,0,0.7);backdrop-filter:blur(6px);
      z-index:1000;display:flex;align-items:center;justify-content:center;padding:20px;
      opacity:0;pointer-events:none;transition:opacity 0.25s ease;
    }
    .modal-overlay.open{opacity:1;pointer-events:all}
    .modal{
      background:var(--bg-card);border:1px solid var(--border);border-radius:var(--radius-xl);
      padding:32px;width:100%;max-width:480px;
      box-shadow:var(--shadow),0 0 60px rgba(0,0,0,0.5);
      transform:scale(0.95) translateY(10px);transition:transform 0.25s ease;
      max-height:90vh;overflow-y:auto;
    }
    .modal-overlay.open .modal{transform:scale(1) translateY(0)}
    .modal-lg{max-width:640px}
    .modal-header{display:flex;align-items:center;gap:12px;margin-bottom:24px}
    .modal-title{font-size:20px;font-weight:700;flex:1}
    .modal-close{
      width:32px;height:32px;border-radius:50%;background:var(--bg-hover);border:none;
      color:var(--text-secondary);cursor:pointer;display:flex;align-items:center;
      justify-content:center;font-size:18px;transition:var(--transition);
    }
    .modal-close:hover{background:var(--red);color:#fff}
    .modal-body{display:flex;flex-direction:column;gap:16px}
    .modal-footer{display:flex;gap:12px;margin-top:24px;justify-content:flex-end}
    .form-group{display:flex;flex-direction:column;gap:6px}
    .form-label{font-size:13px;font-weight:500;color:var(--text-secondary)}
    .toggle-row{
      display:flex;align-items:center;justify-content:space-between;
      padding:12px 16px;background:var(--bg-tertiary);border-radius:var(--radius);border:1px solid var(--border);
    }
    .toggle-label{font-size:14px;font-weight:500}
    .toggle{position:relative;width:44px;height:24px}
    .toggle input{opacity:0;width:0;height:0}
    .toggle-slider{
      position:absolute;inset:0;background:var(--bg-hover);border-radius:99px;
      transition:var(--transition);cursor:pointer;
    }
    .toggle-slider::before{
      content:'';position:absolute;width:18px;height:18px;left:3px;top:3px;
      background:#fff;border-radius:50%;transition:var(--transition);
    }
    .toggle input:checked + .toggle-slider{background:var(--accent)}
    .toggle input:checked + .toggle-slider::before{transform:translateX(20px)}

    /* Admin panel */
    .admin-panel{display:flex;flex-direction:column;gap:20px}
    .admin-section{background:var(--bg-tertiary);border:1px solid var(--border);border-radius:var(--radius-lg);padding:20px}
    .admin-section h3{font-size:15px;font-weight:700;margin-bottom:16px;color:var(--text-secondary);display:flex;align-items:center;gap:8px}
    .stat-grid{display:grid;grid-template-columns:repeat(2,1fr);gap:12px}
    .stat-card{background:var(--bg-card);border:1px solid var(--border);border-radius:var(--radius);padding:16px;text-align:center}
    .stat-value{font-size:28px;font-weight:800;color:var(--accent)}
    .stat-label{font-size:12px;color:var(--text-muted);margin-top:4px}
    .tag-list{display:flex;flex-wrap:wrap;gap:8px;min-height:32px}
    .tag{display:flex;align-items:center;gap:6px;padding:4px 10px;border-radius:99px;font-size:13px;font-weight:600}
    .tag-mod{background:rgba(52,211,153,0.15);color:var(--color-mod);border:1px solid rgba(52,211,153,0.3)}
    .tag-ban{background:rgba(239,68,68,0.15);color:var(--red);border:1px solid rgba(239,68,68,0.3)}
    .tag-custom-role{background:rgba(108,99,255,0.15);color:var(--accent);border:1px solid rgba(108,99,255,0.3)}
    .tag-remove{cursor:pointer;font-size:14px;line-height:1;opacity:0.7;transition:var(--transition)}
    .tag-remove:hover{opacity:1}
    .input-action-row{display:flex;gap:8px}
    .input-action-row .input{flex:1}

    /* Custom roles editor */
    .custom-role-item{
      display:flex;align-items:center;gap:10px;padding:10px 14px;
      background:var(--bg-card);border:1px solid var(--border);border-radius:var(--radius);margin-bottom:8px;
    }
    .role-color-dot{width:14px;height:14px;border-radius:50%;flex-shrink:0}

    /* Leaderboard */
    .lb-table{width:100%;border-collapse:collapse}
    .lb-table th{
      text-align:left;font-size:11px;font-weight:600;color:var(--text-muted);
      text-transform:uppercase;letter-spacing:1px;padding:8px 12px;
      border-bottom:1px solid var(--border);
    }
    .lb-table td{padding:10px 12px;font-size:13px;border-bottom:1px solid rgba(255,255,255,0.04)}
    .lb-table tr:hover td{background:var(--bg-hover)}
    .lb-rank{font-weight:800;color:var(--accent);width:32px}
    .lb-gold{color:gold}.lb-silver{color:silver}.lb-bronze{color:#cd7f32}

    /* Toast */
    #toast-container{position:fixed;bottom:24px;right:24px;z-index:9999;display:flex;flex-direction:column;gap:10px;pointer-events:none}
    .toast{
      background:var(--bg-card);border:1px solid var(--border);border-radius:var(--radius);
      padding:14px 20px;font-size:14px;font-weight:500;box-shadow:var(--shadow);
      animation:toastIn 0.3s ease;min-width:240px;max-width:360px;
      display:flex;align-items:center;gap:10px;pointer-events:all;
    }
    @keyframes toastIn{from{opacity:0;transform:translateX(20px)}to{opacity:1;transform:translateX(0)}}
    .toast.fade-out{animation:toastOut 0.3s ease forwards}
    @keyframes toastOut{to{opacity:0;transform:translateX(20px)}}
    .toast.success{border-left:3px solid var(--green)}
    .toast.error{border-left:3px solid var(--red)}
    .toast.info{border-left:3px solid var(--accent)}
    .toast.warning{border-left:3px solid var(--yellow)}
    .toast.mention{border-left:3px solid var(--pink)}

    /* Lightbox */
    #lightbox{position:fixed;inset:0;background:rgba(0,0,0,0.92);z-index:9998;display:flex;align-items:center;justify-content:center;cursor:zoom-out}
    #lightbox img{max-width:90vw;max-height:90vh;border-radius:var(--radius);object-fit:contain}

    /* Search author */
    .search-author-panel{
      background:var(--bg-tertiary);border-top:1px solid var(--border);
      padding:10px 16px;display:flex;align-items:center;gap:10px;
      font-size:13px;
    }
    .search-author-panel .search-info{flex:1}

    .date-divider{display:flex;align-items:center;gap:12px;padding:8px 0;font-size:12px;color:var(--text-muted)}
    .date-divider::before,.date-divider::after{content:'';flex:1;height:1px;background:var(--border)}
    .divider{height:1px;background:var(--border);margin:4px 0}
    .badge-role{font-size:10px;padding:2px 6px;border-radius:99px;font-weight:700;text-transform:uppercase;letter-spacing:0.5px}
    .badge-role.admin{background:rgba(251,191,36,0.15);color:var(--color-admin)}
    .badge-role.moderator{background:rgba(52,211,153,0.15);color:var(--color-mod)}
    .badge-role.owner{background:rgba(244,114,182,0.15);color:var(--color-owner)}
    .spinner{width:20px;height:20px;border:2px solid rgba(255,255,255,0.2);border-top-color:#fff;border-radius:50%;animation:spin 0.6s linear infinite}
    @keyframes spin{to{transform:rotate(360deg)}}
    .typing-indicator{padding:4px 16px;font-size:12px;color:var(--text-muted);height:20px}

    @media(max-width:768px){
      .online-sidebar{display:none}
      .members-sidebar{display:none}
      .login-card{padding:32px 24px}
      .lobby-main{padding:16px}
      .rooms-grid{grid-template-columns:1fr}
      .topbar{padding:0 12px}
      .lobby-toolbar{gap:8px}
      .modal{padding:24px 20px}
      .stat-grid{grid-template-columns:repeat(2,1fr)}
      #members-toggle-btn{display:flex!important}
      .members-sidebar{
        display:flex;position:fixed;top:60px;right:0;bottom:0;z-index:100;
        transform:translateX(100%);transition:transform 0.3s ease;box-shadow:-4px 0 24px rgba(0,0,0,0.4);
      }
      .members-sidebar.open{transform:translateX(0)}
    }
    @media(min-width:769px){#members-toggle-btn{display:none!important}}
  </style>
</head>
<body>
<div id="app">

  <!-- LOGIN -->
  <div id="screen-login" class="screen active">
    <div class="login-card">
      <div class="logo">
        <div class="logo-icon">💬</div>
        <h1>Vietugram</h1>
        <p>Мгновенный обмен сообщениями</p>
      </div>
      <div class="login-form">
        <div>
          <label for="nick-input">Ваш ник</label>
          <input id="nick-input" class="input" type="text" placeholder="Введите ник (2–30 символов)" maxlength="30" autocomplete="off" />
        </div>
        <button id="btn-login" class="btn btn-primary w-full" style="margin-top:4px;">Войти в Vietugram</button>
        <div id="login-error" class="hidden" style="color:var(--red);font-size:13px;text-align:center;"></div>
      </div>
      <div class="author-badge">by Vietu</div>
    </div>
  </div>

  <!-- LOBBY -->
  <div id="screen-lobby" class="screen">
    <div class="topbar">
      <span class="topbar-brand">💬 Vietugram</span>
      <button id="btn-leaderboard" class="btn btn-ghost btn-sm">🏆 Лидеры</button>
      <button id="btn-custom-roles" class="btn btn-ghost btn-sm hidden" id="btn-custom-roles">🎨 Роли</button>
      <button id="btn-admin-panel" class="btn btn-ghost btn-sm">🔑 Панель</button>
      <div class="topbar-user">
        <div class="user-avatar" id="topbar-avatar">?</div>
        <div>
          <div class="nick-tag" id="topbar-nick">—</div>
          <div style="font-size:11px;color:var(--text-muted);" id="topbar-role">Пользователь</div>
        </div>
      </div>
    </div>
    <div id="global-announcement-bar" class="announcement-bar hidden">
      <span class="ann-icon">📢</span>
      <span id="global-announcement-text"></span>
    </div>
    <div class="lobby-content">
      <div class="online-sidebar">
        <div class="sidebar-header">🟢 Онлайн</div>
        <div class="online-list" id="online-list"></div>
      </div>
      <div class="lobby-main">
        <div class="lobby-toolbar">
          <h2>Комнаты</h2>
          <button id="btn-create-room" class="btn btn-primary btn-sm">➕ Создать комнату</button>
        </div>
        <div class="rooms-grid" id="rooms-grid"></div>
        <div id="rooms-empty" class="rooms-empty hidden">
          <div class="empty-icon">🏠</div>
          <p>Комнат пока нет</p>
          <span style="font-size:14px;">Создайте первую комнату!</span>
        </div>
      </div>
    </div>
  </div>

  <!-- CHAT -->
  <div id="screen-chat" class="screen">
    <div class="chat-topbar">
      <button id="btn-leave-room" class="btn btn-ghost btn-sm btn-icon" title="Выйти из комнаты">←</button>
      <div>
        <div class="chat-room-name" id="chat-room-name">Комната</div>
        <div style="font-size:11px;color:var(--text-muted);" id="chat-room-meta">0 участников</div>
      </div>
      <div style="margin-left:auto;display:flex;gap:8px;align-items:center;flex-wrap:wrap;">
        <button id="btn-search-author" class="btn btn-ghost btn-sm">🔍 Авт.</button>
        <button id="btn-delete-room" class="btn btn-danger btn-sm hidden">🗑️ Удалить</button>
        <button id="btn-spam-settings" class="btn btn-warning btn-sm hidden">⏱️ Антиспам</button>
        <button id="btn-send-announcement" class="btn btn-ghost btn-sm hidden">📢 Объявление</button>
        <button id="members-toggle-btn" class="btn btn-ghost btn-sm btn-icon" style="display:none;" title="Участники">👥</button>
      </div>
    </div>
    <div class="chat-layout">
      <div class="messages-area" id="messages-area">
        <div id="pinned-banner" class="pinned-banner hidden">
          <span class="pin-icon">📌</span>
          <span class="pin-text"><span class="pin-nick" id="pin-nick"></span><span id="pin-text-content"></span></span>
          <button class="btn btn-ghost btn-sm" id="btn-goto-pin">Перейти</button>
          <button class="btn btn-ghost btn-sm" id="btn-unpin-msg" style="display:none;">✕</button>
        </div>
        <div class="drag-overlay" id="drag-overlay">📷 Отпустите для загрузки</div>
        <div class="messages-list" id="messages-list"></div>
        <div class="typing-indicator" id="typing-indicator"></div>
        <div id="search-author-panel" class="search-author-panel hidden">
          <span class="search-info">🔍 Сообщения от: <strong id="search-author-name"></strong></span>
          <button class="btn btn-ghost btn-sm" id="btn-clear-author-search">✕ Очистить</button>
        </div>
        <div id="spam-warning" class="spam-warning">⏳ Подождите перед следующим сообщением...</div>
        <div class="chat-input-area">
          <div id="attach-preview" class="attach-preview">
            <img id="attach-preview-img" src="" alt="" />
            <div class="remove-img" id="btn-remove-attach">✕</div>
          </div>
          <div id="announce-row" class="announce-toggle hidden">
            <input type="checkbox" id="announce-check" />
            <label for="announce-check">📢 Отправить как объявление</label>
          </div>
          <div id="tag-selector" class="tag-selector hidden">
            <button class="tag-selector-btn important" data-tag="important">#важное</button>
            <button class="tag-selector-btn urgent" data-tag="urgent">#срочно</button>
            <button class="tag-selector-btn todo" data-tag="todo">#todo</button>
          </div>
          <div class="chat-input-row">
            <button class="btn btn-ghost btn-sm btn-icon" id="btn-attach" title="Прикрепить изображение" style="flex-shrink:0;">🖼️</button>
            <input type="file" id="file-input" accept="image/*" style="display:none;" />
            <textarea id="chat-textarea" class="chat-textarea" placeholder="Написать сообщение... (Shift+Enter — новая строка)" rows="1"></textarea>
            <button class="btn btn-ghost btn-sm btn-icon" id="btn-toggle-tags" title="Тегировать сообщение" style="flex-shrink:0;">🏷️</button>
            <button class="btn btn-primary btn-sm btn-icon" id="btn-send" style="flex-shrink:0;">➤</button>
          </div>
        </div>
      </div>
      <div class="members-sidebar" id="members-sidebar">
        <div class="sidebar-header">👥 Участники</div>
        <div class="online-list" id="members-list"></div>
        <div id="members-sidebar-footer" style="padding:8px;border-top:1px solid var(--border);display:none;">
          <button class="btn btn-primary w-full" id="btn-open-invite-modal">📨 Пригласить</button>
        </div>
      </div>
    </div>
  </div>

  <!-- VOICE ROOM -->
  <div id="screen-voice" class="screen">
    <div class="voice-room-bg"></div>
    <div class="voice-room-container">
      <div class="voice-topbar">
        <span style="font-size:24px;">🎙️</span>
        <span class="voice-room-title" id="voice-room-title">Голосовая комната</span>
        <span id="voice-room-meta" style="font-size:13px;color:var(--text-muted);">0 участников</span>
      </div>
      <div class="voice-participants" id="voice-participants"></div>
      <div class="voice-controls">
        <button class="voice-ctrl-btn mic-on" id="voice-btn-mic" title="Микрофон">🎙️</button>
        <button class="voice-ctrl-btn deaf-on" id="voice-btn-deaf" title="Звук">🔊</button>
        <button class="voice-ctrl-btn screen-btn" id="voice-btn-screen" title="Экран">🖥️</button>
        <button class="voice-ctrl-btn leave-btn" id="voice-btn-leave" title="Покинуть">📞</button>
      </div>
    </div>
  </div>

</div>

<!-- MODALS -->

<!-- Create room -->
<div class="modal-overlay" id="modal-create-room">
  <div class="modal">
    <div class="modal-header">
      <span style="font-size:24px;">🏠</span>
      <h2 class="modal-title">Создать комнату</h2>
      <button class="modal-close" data-close="modal-create-room">✕</button>
    </div>
    <div class="modal-body">
      <div class="form-group">
        <label class="form-label">Название комнаты</label>
        <input id="room-name-input" class="input" type="text" placeholder="Введите название..." maxlength="50" />
      </div>
      <div class="toggle-row">
        <span class="toggle-label">🔒 Защитить паролем</span>
        <label class="toggle"><input type="checkbox" id="room-password-toggle" /><span class="toggle-slider"></span></label>
      </div>
      <div id="room-password-field" class="form-group hidden">
        <label class="form-label">Пароль</label>
        <input id="room-password-input" class="input" type="password" placeholder="Введите пароль..." maxlength="100" />
      </div>
      <div class="toggle-row">
        <span class="toggle-label">🎙️ Голосовая комната (WebRTC)</span>
        <label class="toggle"><input type="checkbox" id="room-voice-toggle" /><span class="toggle-slider"></span></label>
      </div>
      <div class="toggle-row">
        <span class="toggle-label">👻 Анонимная комната</span>
        <label class="toggle"><input type="checkbox" id="room-anon-toggle" /><span class="toggle-slider"></span></label>
      </div>
      <div class="toggle-row">
        <span class="toggle-label">⏳ Временная комната</span>
        <label class="toggle"><input type="checkbox" id="room-temp-toggle" /><span class="toggle-slider"></span></label>
      </div>
      <div id="room-temp-field" class="form-group hidden">
        <label class="form-label">Время жизни</label>
        <div style="display:flex;gap:8px;">
          <input id="room-temp-value" class="input" type="number" min="1" value="60" style="width:80px;" />
          <select id="room-temp-unit" class="input" style="flex:1;">
            <option value="seconds">Секунд</option>
            <option value="minutes" selected>Минут</option>
            <option value="hours">Часов</option>
          </select>
        </div>
      </div>
    </div>
    <div class="modal-footer">
      <button class="btn btn-ghost" data-close="modal-create-room">Отмена</button>
      <button class="btn btn-primary" id="btn-confirm-create-room">Создать</button>
    </div>
  </div>
</div>

<!-- Room password -->
<div class="modal-overlay" id="modal-room-password">
  <div class="modal">
    <div class="modal-header">
      <span style="font-size:24px;">🔒</span>
      <h2 class="modal-title">Введите пароль</h2>
      <button class="modal-close" data-close="modal-room-password">✕</button>
    </div>
    <div class="modal-body">
      <p style="color:var(--text-secondary);font-size:14px;">Эта комната защищена паролем.</p>
      <div class="form-group">
        <label class="form-label">Пароль</label>
        <input id="join-password-input" class="input" type="password" placeholder="Введите пароль..." />
      </div>
      <div id="join-password-error" class="hidden" style="color:var(--red);font-size:13px;"></div>
    </div>
    <div class="modal-footer">
      <button class="btn btn-ghost" data-close="modal-room-password">Отмена</button>
      <button class="btn btn-primary" id="btn-confirm-join-password">Войти</button>
    </div>
  </div>
</div>

<!-- Confirm delete room -->
<div class="modal-overlay" id="modal-confirm-delete">
  <div class="modal">
    <div class="modal-header">
      <span style="font-size:24px;">⚠️</span>
      <h2 class="modal-title">Удалить комнату?</h2>
      <button class="modal-close" data-close="modal-confirm-delete">✕</button>
    </div>
    <div class="modal-body">
      <p style="color:var(--text-secondary);font-size:14px;">
        Комната <strong id="delete-room-name-display" style="color:var(--text-primary);"></strong> и все её сообщения будут удалены безвозвратно.
      </p>
    </div>
    <div class="modal-footer">
      <button class="btn btn-ghost" data-close="modal-confirm-delete">Отмена</button>
      <button class="btn btn-danger" id="btn-confirm-delete-room">Удалить</button>
    </div>
  </div>
</div>

<!-- Spam settings -->
<div class="modal-overlay" id="modal-spam-settings">
  <div class="modal">
    <div class="modal-header">
      <span style="font-size:24px;">⏱️</span>
      <h2 class="modal-title">Настройки антиспама</h2>
      <button class="modal-close" data-close="modal-spam-settings">✕</button>
    </div>
    <div class="modal-body">
      <p style="color:var(--text-secondary);font-size:14px;">Минимальная задержка между сообщениями для обычных пользователей.</p>
      <div class="form-group">
        <label class="form-label">Задержка (секунды, 0 = отключить)</label>
        <input id="spam-delay-input" class="input" type="number" min="0" max="300" value="0" />
      </div>
    </div>
    <div class="modal-footer">
      <button class="btn btn-ghost" data-close="modal-spam-settings">Отмена</button>
      <button class="btn btn-primary" id="btn-save-spam-settings">Сохранить</button>
    </div>
  </div>
</div>

<!-- Search author modal -->
<div class="modal-overlay" id="modal-search-author">
  <div class="modal">
    <div class="modal-header">
      <span style="font-size:24px;">🔍</span>
      <h2 class="modal-title">Поиск по автору</h2>
      <button class="modal-close" data-close="modal-search-author">✕</button>
    </div>
    <div class="modal-body">
      <p style="color:var(--text-secondary);font-size:14px;">Введите ник пользователя чтобы показать только его сообщения.</p>
      <div class="form-group">
        <label class="form-label">Ник пользователя</label>
        <input id="search-author-input" class="input" type="text" placeholder="Введите ник..." />
      </div>
    </div>
    <div class="modal-footer">
      <button class="btn btn-ghost" data-close="modal-search-author">Отмена</button>
      <button class="btn btn-primary" id="btn-do-search-author">Найти</button>
    </div>
  </div>
</div>

<!-- Leaderboard -->
<div class="modal-overlay" id="modal-leaderboard">
  <div class="modal modal-lg">
    <div class="modal-header">
      <span style="font-size:24px;">🏆</span>
      <h2 class="modal-title">Таблица лидеров</h2>
      <button class="modal-close" data-close="modal-leaderboard">✕</button>
    </div>
    <div class="modal-body">
      <div style="display:flex;gap:8px;margin-bottom:16px;">
        <button class="btn btn-primary btn-sm lb-tab-btn active" data-tab="messages">💬 Сообщения</button>
        <button class="btn btn-ghost btn-sm lb-tab-btn" data-tab="reactions">👍 Реакции</button>
        <button class="btn btn-ghost btn-sm lb-tab-btn" data-tab="time">⏱️ Время в чате</button>
      </div>
      <div id="lb-content"></div>
    </div>
  </div>
</div>

<!-- Custom roles -->
<div class="modal-overlay" id="modal-custom-roles">
  <div class="modal modal-lg">
    <div class="modal-header">
      <span style="font-size:24px;">🎨</span>
      <h2 class="modal-title">Кастомные роли</h2>
      <button class="modal-close" data-close="modal-custom-roles">✕</button>
    </div>
    <div class="modal-body">
      <div id="custom-roles-list" style="margin-bottom:16px;"></div>
      <div style="background:var(--bg-tertiary);border:1px solid var(--border);border-radius:var(--radius);padding:16px;">
        <h3 style="font-size:14px;font-weight:600;margin-bottom:12px;">Создать новую роль</h3>
        <div style="display:flex;gap:8px;flex-wrap:wrap;align-items:flex-end;">
          <div class="form-group" style="flex:1;min-width:120px;">
            <label class="form-label">Название</label>
            <input id="new-role-name" class="input input-sm" placeholder="Название роли..." />
          </div>
          <div class="form-group">
            <label class="form-label">Цвет ника</label>
            <input id="new-role-color" type="color" value="#a78bfa" style="width:48px;height:38px;border-radius:var(--radius-sm);border:1px solid var(--border);background:var(--bg-input);cursor:pointer;" />
          </div>
          <div class="form-group" style="flex:1;min-width:120px;">
            <label class="form-label">Статус (эмодзи)</label>
            <input id="new-role-emoji" class="input input-sm" placeholder="🌟" maxlength="4" />
          </div>
          <button class="btn btn-primary btn-sm" id="btn-create-custom-role" style="align-self:flex-end;">Создать</button>
        </div>
      </div>
      <div style="margin-top:16px;">
        <h3 style="font-size:14px;font-weight:600;margin-bottom:12px;">Выдать роль пользователю</h3>
        <div style="display:flex;gap:8px;flex-wrap:wrap;">
          <input id="assign-role-nick" class="input input-sm" placeholder="Ник пользователя..." style="flex:1;min-width:140px;" />
          <select id="assign-role-select" class="input input-sm" style="flex:1;min-width:140px;"></select>
          <button class="btn btn-primary btn-sm" id="btn-assign-custom-role">Выдать</button>
        </div>
      </div>
    </div>
  </div>
</div>

<!-- Admin panel -->
<div class="modal-overlay" id="modal-admin">
  <div class="modal modal-lg" style="max-width:620px;">
    <div class="modal-header">
      <span style="font-size:24px;">👑</span>
      <h2 class="modal-title">Панель управления</h2>
      <button class="modal-close" data-close="modal-admin">✕</button>
    </div>
    <div class="modal-body">
      <div id="admin-code-section" class="admin-section">
        <h3>🔑 Получить права администратора</h3>
        <div class="input-action-row">
          <input id="admin-code-input" class="input" type="password" placeholder="Введите секретный код..." />
          <button class="btn btn-primary btn-sm" id="btn-verify-admin-code">Проверить</button>
        </div>
        <div id="admin-code-result" style="font-size:13px;margin-top:8px;"></div>
      </div>
      <div id="admin-only-section" class="hidden">
        <div class="admin-section">
          <h3>📊 Статистика</h3>
          <div class="stat-grid" id="admin-stats">
            <div class="stat-card"><div class="stat-value" id="stat-online">0</div><div class="stat-label">Онлайн</div></div>
            <div class="stat-card"><div class="stat-value" id="stat-rooms">0</div><div class="stat-label">Комнат</div></div>
            <div class="stat-card"><div class="stat-value" id="stat-messages">0</div><div class="stat-label">Сообщений</div></div>
            <div class="stat-card"><div class="stat-value" id="stat-users">0</div><div class="stat-label">Всего пользователей</div></div>
          </div>
        </div>
        <div class="admin-section">
          <h3>👁️ Режим наблюдателя</h3>
          <p style="font-size:13px;color:var(--text-muted);margin-bottom:10px;">Вы видите все чаты, но вас никто не видит в списках участников.</p>
          <button class="btn btn-ghost btn-sm" id="btn-toggle-observer">Включить режим наблюдателя</button>
          <span id="observer-status" style="font-size:12px;color:var(--text-muted);margin-left:10px;"></span>
        </div>
        <div class="admin-section">
          <h3>🛡️ Модераторы</h3>
          <div class="tag-list" id="moderators-list" style="margin-bottom:12px;"></div>
          <div class="input-action-row">
            <input id="mod-nick-input" class="input input-sm" type="text" placeholder="Ник пользователя..." />
            <button class="btn btn-success btn-sm" id="btn-add-mod">Назначить</button>
          </div>
        </div>
        <div class="admin-section">
          <h3>🚫 Заблокированные пользователи</h3>
          <div class="tag-list" id="banned-list" style="margin-bottom:12px;"></div>
          <div class="input-action-row">
            <input id="ban-nick-input" class="input input-sm" type="text" placeholder="Ник пользователя..." />
            <button class="btn btn-danger btn-sm" id="btn-ban-user">Заблокировать</button>
          </div>
        </div>
        <div class="admin-section">
          <h3>📢 Глобальное объявление</h3>
          <p style="font-size:13px;color:var(--text-muted);margin-bottom:10px;">Отображается всем пользователям в лобби</p>
          <textarea id="global-ann-input" class="input" rows="2" placeholder="Введите объявление (пусто — скрыть)..."></textarea>
          <button class="btn btn-primary btn-sm" id="btn-set-announcement" style="margin-top:8px;">Сохранить</button>
        </div>
        <div class="admin-section">
          <h3>🚪 Кастомное сообщение входа</h3>
          <p style="font-size:13px;color:var(--text-muted);margin-bottom:10px;">Используйте {nick} как плейсхолдер</p>
          <input id="join-msg-input" class="input" type="text" placeholder="{nick} присоединился к комнате" />
          <button class="btn btn-primary btn-sm" id="btn-set-join-msg" style="margin-top:8px;">Сохранить</button>
        </div>
        <div class="admin-section">
          <h3>😀 Мой статус-эмодзи</h3>
          <div class="input-action-row">
            <input id="emoji-input" class="input input-sm" type="text" placeholder="Введите эмодзи (например 🌟)..." maxlength="4" />
            <button class="btn btn-ghost btn-sm" id="btn-set-emoji">Применить</button>
          </div>
        </div>
      </div>
    </div>
  </div>
</div>

<!-- Invite -->
<div class="modal-overlay" id="modal-invite">
  <div class="modal" style="max-width:500px;">
    <div class="modal-header">
      <span style="font-size:24px;">📨</span>
      <h2 class="modal-title">Пригласить в комнату</h2>
      <button class="modal-close" data-close="modal-invite">✕</button>
    </div>
    <div class="modal-body">
      <p style="font-size:14px;color:var(--text-secondary);">Выберите пользователя из онлайн-списка:</p>
      <div id="invite-online-list" class="online-list" style="max-height:300px;overflow-y:auto;"></div>
    </div>
  </div>
</div>

<!-- Lightbox -->
<div id="lightbox" class="hidden">
  <img id="lightbox-img" src="" alt="" />
</div>

<!-- Toast -->
<div id="toast-container"></div>

<script>
/* ============================================================
   STATE
============================================================ */
const state = {
  socket: null,
  nick: '',
  role: 'user',
  emoji: '👤',
  currentRoomId: null,
  currentRoomName: '',
  currentRoomIsVoice: false,
  currentRoomIsAnon: false,
  currentRoomOwner: null,
  rooms: [],
  pendingRoomId: null,
  attachedImage: null,
  isAdmin: false,
  isMod: false,
  isObserver: false,
  onlineUsers: [],
  pinnedMessageId: null,
  pinnedMessageData: null,
  spamDelay: 0,
  lastMessageTime: 0,
  spamCooldownTimer: null,
  searchAuthorFilter: null,
  activeMessageTags: [],
  customRoles: [],
  // Voice
  voiceStream: null,
  voicePeerConnections: {},
  voiceParticipants: {},
  micMuted: false,
  deafened: false,
  screenSharing: false,
  screenStream: null,
  // Stats
  joinTime: Date.now(),
  messageCount: 0,
  totalReactionsReceived: 0,
};

/* ============================================================
   UTILS
============================================================ */
function showScreen(id) {
  document.querySelectorAll('.screen').forEach(s => s.classList.remove('active'));
  document.getElementById(id).classList.add('active');
}
function openModal(id) { document.getElementById(id).classList.add('open'); }
function closeModal(id) { document.getElementById(id).classList.remove('open'); }

function toast(message, type = 'info', duration = 4000) {
  const icons = { success: '✅', error: '❌', info: 'ℹ️', warning: '⚠️', mention: '🔔' };
  const container = document.getElementById('toast-container');
  const el = document.createElement('div');
  el.className = `toast ${type}`;
  el.innerHTML = `<span>${icons[type] || 'ℹ️'}</span><span>${escapeHtml(message)}</span>`;
  container.appendChild(el);
  setTimeout(() => {
    el.classList.add('fade-out');
    el.addEventListener('animationend', () => el.remove());
  }, duration);
}

function escapeHtml(str) {
  if (!str) return '';
  return String(str)
    .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;').replace(/'/g, '&#039;');
}

function scrollToBottom(smooth = true) {
  const list = document.getElementById('messages-list');
  list.scrollTo({ top: list.scrollHeight, behavior: smooth ? 'smooth' : 'auto' });
}

function autoResizeTextarea(el) {
  el.style.height = 'auto';
  el.style.height = Math.min(el.scrollHeight, 120) + 'px';
}

function formatTime(timestamp) {
  const d = timestamp ? new Date(timestamp * 1000) : new Date();
  return d.toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit' });
}

function formatDuration(ms) {
  const s = Math.floor(ms / 1000);
  const m = Math.floor(s / 60);
  const h = Math.floor(m / 60);
  if (h > 0) return `${h}ч ${m % 60}м`;
  if (m > 0) return `${m}м ${s % 60}с`;
  return `${s}с`;
}

function pluralize(n) {
  if (n % 10 === 1 && n % 100 !== 11) return '';
  if ([2,3,4].includes(n % 10) && ![12,13,14].includes(n % 100)) return 'а';
  return 'ов';
}

function linkify(text) {
  return text.replace(/(https?:\/\/[^\s<>"]+)/g, '<a href="$1" target="_blank" rel="noopener noreferrer" style="color:var(--accent);text-decoration:underline;">$1</a>');
}

function processMentions(text, myNick) {
  return text.replace(/@(\S+)/g, (match, nick) => {
    const cls = nick === myNick ? 'mention me' : 'mention';
    return `<span class="${cls}">@${escapeHtml(nick)}</span>`;
  });
}

function processHashtags(text) {
  // Don't double-process tags that are already rendered
  return text.replace(/#(важное|срочно|todo)/gi, (match, tag) => {
    const tagKey = tag.toLowerCase() === 'важное' ? 'important'
                 : tag.toLowerCase() === 'срочно' ? 'urgent' : 'todo';
    return `<span class="msg-tag ${tagKey}">#${escapeHtml(tag)}</span>`;
  });
}

function buildMsgBody(text, myNick) {
  let t = escapeHtml(text);
  t = linkify(t);
  t = processMentions(t, myNick);
  t = processHashtags(t);
  return t;
}

/* ============================================================
   SOCKET INIT
============================================================ */
function initSocket() {
  state.socket = io({ transports: ['websocket', 'polling'], reconnectionAttempts: 10, reconnectionDelay: 1500 });
  const s = state.socket;

  s.on('connect', () => {
    console.log('[WS] Connected:', s.id);
    if (state.nick) s.emit('join_app', { nick: state.nick });
  });
  s.on('disconnect', () => toast('Соединение потеряно. Переподключение...', 'warning'));
  s.on('connect_error', err => console.error('[WS] Error:', err));

  s.on('join_success',          onJoinSuccess);
  s.on('join_error',            onJoinError);
  s.on('rooms_update',          onRoomsUpdate);
  s.on('room_created',          onRoomCreated);
  s.on('room_joined',           onRoomJoined);
  s.on('left_room',             onLeftRoom);
  s.on('join_room_error',       onJoinRoomError);
  s.on('room_deleted',          onRoomDeleted);
  s.on('new_message',           onNewMessage);
  s.on('message_deleted',       onMessageDeleted);
  s.on('message_edited',        onMessageEdited);
  s.on('online_update',         onOnlineUpdate);
  s.on('room_members_update',   onRoomMembersUpdate);
  s.on('role_updated',          onRoleUpdated);
  s.on('emoji_updated',         onEmojiUpdated);
  s.on('kicked',                onKicked);
  s.on('banned',                onBanned);
  s.on('announcement_updated',  onAnnouncementUpdated);
  s.on('error',                 data => toast(data.message || 'Ошибка', 'error'));
  s.on('admin_panel_data',      onAdminPanelData);
  s.on('admin_action_result',   onAdminActionResult);
  s.on('admin_code_result',     onAdminCodeResult);
  s.on('online_users_list',     data => { state.onlineUsers = data.users || []; renderInviteModal(); });
  s.on('invite_notification',   onInviteNotification);
  s.on('reaction_updated',      onReactionUpdated);
  s.on('pin_updated',           onPinUpdated);
  s.on('spam_settings_updated', data => { state.spamDelay = data.delay || 0; });
  s.on('room_expired',          onRoomExpired);
  s.on('custom_roles_update',   onCustomRolesUpdate);
  s.on('leaderboard_data',      onLeaderboardData);
  s.on('custom_role_assigned',  onCustomRoleAssigned);
  // Voice WebRTC signaling
  s.on('voice_offer',           onVoiceOffer);
  s.on('voice_answer',          onVoiceAnswer);
  s.on('voice_ice_candidate',   onVoiceIceCandidate);
  s.on('voice_user_joined',     onVoiceUserJoined);
  s.on('voice_user_left',       onVoiceUserLeft);
  s.on('voice_speaking_update', onVoiceSpeakingUpdate);
  s.on('voice_mute_update',     onVoiceMuteUpdate);
}

/* ============================================================
   EVENT HANDLERS
============================================================ */
function onJoinSuccess(data) {
  state.nick = data.nick;
  state.role = data.role;
  state.emoji = data.emoji;
  state.isAdmin = data.role === 'admin';
  state.isMod = data.role === 'moderator';
  state.customRoles = data.custom_roles || [];
  state.joinTime = Date.now();
  sessionStorage.setItem('vietugram_nick', data.nick);
  updateTopbar();
  renderRooms(data.rooms || []);
  renderOnlineList(data.online_users || []);
  updateAnnouncement(data.global_announcement);
  updateModeratorUI();
  showScreen('screen-lobby');
  toast(`Добро пожаловать, ${data.nick}! 👋`, 'success');
}

function onJoinError(data) {
  const errEl = document.getElementById('login-error');
  errEl.textContent = data.message;
  errEl.classList.remove('hidden');
  document.getElementById('btn-login').innerHTML = 'Войти в Vietugram';
  document.getElementById('btn-login').disabled = false;
}

function onRoomsUpdate(data) {
  state.rooms = data.rooms || [];
  renderRooms(state.rooms);
}

function onRoomCreated(data) {
  closeModal('modal-create-room');
  joinRoom(data.room_id);
}

function onRoomJoined(data) {
  state.currentRoomId = data.room_id;
  state.currentRoomName = data.room_name;
  state.currentRoomIsVoice = data.is_voice || false;
  state.currentRoomIsAnon = data.is_anonymous || false;
  state.currentRoomOwner = data.owner;
  state.spamDelay = data.spam_delay || 0;
  state.pinnedMessageId = data.pinned_message_id || null;
  state.pinnedMessageData = data.pinned_message || null;
  closeModal('modal-room-password');

  if (state.currentRoomIsVoice) {
    enterVoiceRoom(data);
    return;
  }

  showScreen('screen-chat');
  document.getElementById('chat-room-name').textContent = data.room_name
    + (data.is_anonymous ? ' 👻' : '')
    + (data.temp_expires ? ' ⏳' : '');

  const canMod = state.isAdmin || state.isMod;
  const isOwner = data.owner === state.nick;
  const canDelete = canMod || isOwner;
  const canAntiSpam = canMod || isOwner;

  document.getElementById('btn-delete-room').classList.toggle('hidden', !canDelete);
  document.getElementById('btn-spam-settings').classList.toggle('hidden', !canAntiSpam);
  document.getElementById('btn-send-announcement').classList.toggle('hidden', !canMod);
  document.getElementById('announce-row').classList.toggle('hidden', !canMod);
  document.getElementById('tag-selector').classList.toggle('hidden', false);
  document.getElementById('members-sidebar-footer').style.display = canMod ? 'block' : 'none';

  const list = document.getElementById('messages-list');
  list.innerHTML = '';
  (data.messages || []).forEach(msg => renderMessage(msg, false));
  scrollToBottom(false);
  renderMembers(data.members || []);
  updatePinnedBanner(data.pinned_message || null);

  if (data.temp_expires) {
    startRoomTimer(data.temp_expires);
  }

  toast(`Вошли в комнату «${data.room_name}»`, 'success');
}

function onLeftRoom() {
  state.currentRoomId = null;
  state.currentRoomName = '';
  state.searchAuthorFilter = null;
  state.pinnedMessageId = null;
  showScreen('screen-lobby');
}

function onJoinRoomError(data) {
  document.getElementById('join-password-error').textContent = data.message;
  document.getElementById('join-password-error').classList.remove('hidden');
}

function onRoomDeleted(data) {
  if (state.currentRoomId === data.room_id) {
    state.currentRoomId = null;
    showScreen('screen-lobby');
    toast(`Комната «${data.room_name}» была удалена`, 'warning');
  }
}

function onRoomExpired(data) {
  if (state.currentRoomId === data.room_id) {
    state.currentRoomId = null;
    showScreen('screen-lobby');
    toast(`Комната «${data.room_name}» самоуничтожилась`, 'warning');
  }
}

function onNewMessage(msg) {
  // Check mention
  if (msg.text && msg.nick !== state.nick) {
    if (msg.text.includes('@' + state.nick)) {
      toast(`${msg.nick} упомянул вас: "${msg.text.substring(0, 50)}"`, 'mention', 6000);
    }
  }
  // Filter by author if active
  if (state.searchAuthorFilter && msg.nick !== state.searchAuthorFilter) {
    return;
  }
  renderMessage(msg, true);
  scrollToBottom();
}

function onMessageDeleted(data) {
  const msgEl = document.querySelector(`[data-msg-id="${data.message_id}"]`);
  if (msgEl) {
    msgEl.style.opacity = '0';
    msgEl.style.transform = 'scale(0.95)';
    msgEl.style.transition = 'all 0.2s ease';
    setTimeout(() => msgEl.remove(), 200);
  }
  if (state.pinnedMessageId === data.message_id) {
    updatePinnedBanner(null);
    state.pinnedMessageId = null;
  }
}

function onMessageEdited(data) {
  const msgEl = document.querySelector(`[data-msg-id="${data.message_id}"]`);
  if (msgEl) {
    const bodyEl = msgEl.querySelector('.msg-body');
    if (bodyEl) {
      bodyEl.innerHTML = buildMsgBody(data.new_text, state.nick);
      // Add edited badge
      let editedBadge = msgEl.querySelector('.msg-edited');
      if (!editedBadge) {
        editedBadge = document.createElement('span');
        editedBadge.className = 'msg-edited';
        const timeEl = msgEl.querySelector('.msg-time');
        if (timeEl) timeEl.after(editedBadge);
      }
      editedBadge.textContent = '(изменено)';
    }
    // Close edit mode
    const editArea = msgEl.querySelector('.msg-edit-area');
    if (editArea) editArea.remove();
    const editBtns = msgEl.querySelector('.msg-edit-btns');
    if (editBtns) editBtns.remove();
  }
}

function onOnlineUpdate(data) {
  renderOnlineList(data.users || []);
  state.onlineUsers = data.users || [];
}

function onRoomMembersUpdate(data) {
  if (data.room_id === state.currentRoomId) {
    renderMembers(data.members || []);
  }
}

function onRoleUpdated(data) {
  if (data.nick === state.nick) {
    state.role = data.role;
    state.isAdmin = data.role === 'admin';
    state.isMod = data.role === 'moderator';
    state.emoji = data.emoji || state.emoji;
    updateTopbar();
    updateModeratorUI();
    toast(`Ваша роль изменена: ${data.role}`, 'info');
  }
}

function onEmojiUpdated(data) {
  state.emoji = data.emoji;
  updateTopbar();
  toast('Эмодзи обновлён!', 'success');
}

function onKicked(data) {
  state.currentRoomId = null;
  showScreen('screen-lobby');
  toast(`Вы были исключены из комнаты (кик от ${data.by})`, 'warning');
}

function onBanned(data) {
  toast(data.message || 'Вы заблокированы', 'error');
  setTimeout(() => { sessionStorage.clear(); location.reload(); }, 3000);
}

function onAnnouncementUpdated(data) { updateAnnouncement(data.text); }

function onInviteNotification(data) {
  const accept = confirm(`${data.from_nick} приглашает вас в комнату «${data.room_name}». Принять?`);
  if (accept) state.socket.emit('accept_invite', { room_id: data.room_id });
}

function onReactionUpdated(data) {
  const msgEl = document.querySelector(`[data-msg-id="${data.message_id}"]`);
  if (!msgEl) return;
  msgEl.querySelector('.like-count').textContent = data.reactions.like || 0;
  msgEl.querySelector('.dislike-count').textContent = data.reactions.dislike || 0;
  const myReaction = data.reactions.users ? data.reactions.users[state.nick] : null;
  msgEl.querySelector('.like-btn').classList.toggle('active', myReaction === 'like');
  msgEl.querySelector('.dislike-btn').classList.toggle('active', myReaction === 'dislike');
}

function onPinUpdated(data) {
  if (data.room_id === state.currentRoomId) {
    state.pinnedMessageId = data.pinned_message ? data.pinned_message.id : null;
    state.pinnedMessageData = data.pinned_message || null;
    updatePinnedBanner(data.pinned_message || null);
    // Highlight pinned message
    document.querySelectorAll('.msg.pinned-msg').forEach(el => el.classList.remove('pinned-msg'));
    if (data.pinned_message) {
      const msgEl = document.querySelector(`[data-msg-id="${data.pinned_message.id}"]`);
      if (msgEl) msgEl.classList.add('pinned-msg');
    }
  }
}

function onAdminPanelData(data) {
  document.getElementById('admin-only-section').classList.remove('hidden');
  document.getElementById('admin-code-section').classList.add('hidden');
  if (data.stats) {
    document.getElementById('stat-online').textContent = data.stats.online_count ?? 0;
    document.getElementById('stat-rooms').textContent = data.stats.rooms_count ?? 0;
    document.getElementById('stat-messages').textContent = data.stats.total_messages ?? 0;
    document.getElementById('stat-users').textContent = data.stats.total_users_known ?? 0;
  }
  const modList = document.getElementById('moderators-list');
  modList.innerHTML = '';
  (data.moderators || []).forEach(nick => {
    const tag = document.createElement('div');
    tag.className = 'tag tag-mod';
    tag.innerHTML = `🛡️ ${escapeHtml(nick)} <span class="tag-remove" data-action="remove-mod" data-nick="${escapeHtml(nick)}">✕</span>`;
    modList.appendChild(tag);
  });
  const banList = document.getElementById('banned-list');
  banList.innerHTML = '';
  (data.banned_users || []).forEach(nick => {
    const tag = document.createElement('div');
    tag.className = 'tag tag-ban';
    tag.innerHTML = `🚫 ${escapeHtml(nick)} <span class="tag-remove" data-action="unban" data-nick="${escapeHtml(nick)}">✕</span>`;
    banList.appendChild(tag);
  });
  if (data.global_announcement) document.getElementById('global-ann-input').value = data.global_announcement;
  if (data.room_join_message) document.getElementById('join-msg-input').value = data.room_join_message;
  [modList, banList].forEach(list => {
    list.querySelectorAll('.tag-remove').forEach(btn => {
      btn.addEventListener('click', () => {
        if (btn.dataset.action === 'remove-mod') state.socket.emit('set_moderator', { nick: btn.dataset.nick, action: 'remove' });
        else if (btn.dataset.action === 'unban') state.socket.emit('unban_user', { nick: btn.dataset.nick });
      });
    });
  });
  // Observer mode
  const obsBtn = document.getElementById('btn-toggle-observer');
  const obsStatus = document.getElementById('observer-status');
  obsStatus.textContent = state.isObserver ? 'Активен' : '';
  obsBtn.textContent = state.isObserver ? 'Выключить режим наблюдателя' : 'Включить режим наблюдателя';
}

function onAdminActionResult(data) {
  toast(data.message, data.success ? 'success' : 'error');
  if (data.success) state.socket.emit('get_admin_panel', {});
}

function onAdminCodeResult(data) {
  const resultEl = document.getElementById('admin-code-result');
  resultEl.textContent = data.message;
  resultEl.style.color = data.success ? 'var(--green)' : 'var(--red)';
  if (data.success) {
    state.isAdmin = true;
    state.role = 'admin';
    updateTopbar();
    updateModeratorUI();
    state.socket.emit('get_admin_panel', {});
  }
}

function onCustomRolesUpdate(data) {
  state.customRoles = data.roles || [];
  renderCustomRolesList();
}

function onCustomRoleAssigned(data) {
  // Role assigned to user, update UI if it's us
  if (data.nick === state.nick) {
    toast(`Вам выдана роль: ${data.role_name}`, 'info');
  }
}

function onLeaderboardData(data) {
  renderLeaderboard(data);
}

/* ============================================================
   VOICE WEBRTC
============================================================ */
async function enterVoiceRoom(data) {
  showScreen('screen-voice');
  document.getElementById('voice-room-title').textContent = data.room_name;
  state.voiceParticipants = {};
  state.voicePeerConnections = {};
  state.micMuted = false;
  state.deafened = false;

  // Add self
  addVoiceParticipant({ nick: state.nick, emoji: state.emoji, role: state.role, micMuted: false, deafened: false });

  // Request mic
  try {
    state.voiceStream = await navigator.mediaDevices.getUserMedia({ audio: true, video: false });
    setupVoiceActivityDetection(state.voiceStream);
    toast('Микрофон подключён 🎙️', 'success');
  } catch (e) {
    toast('Нет доступа к микрофону. Вы можете слушать.', 'warning');
    state.voiceStream = null;
  }

  state.socket.emit('join_voice_room', { room_id: data.room_id });

  // Add existing members
  (data.members || []).forEach(m => {
    if (m.nick !== state.nick) {
      addVoiceParticipant(m);
    }
  });
  updateVoiceParticipantsUI();
  toast(`Вошли в голосовую комнату «${data.room_name}»`, 'success');
}

function setupVoiceActivityDetection(stream) {
  try {
    const audioCtx = new (window.AudioContext || window.webkitAudioContext)();
    const analyser = audioCtx.createAnalyser();
    const source = audioCtx.createMediaStreamSource(stream);
    source.connect(analyser);
    analyser.fftSize = 512;
    const dataArray = new Uint8Array(analyser.frequencyBinCount);
    let speaking = false;
    setInterval(() => {
      if (state.micMuted || !state.voiceStream) return;
      analyser.getByteFrequencyData(dataArray);
      const avg = dataArray.reduce((a, b) => a + b, 0) / dataArray.length;
      const nowSpeaking = avg > 15;
      if (nowSpeaking !== speaking) {
        speaking = nowSpeaking;
        if (state.socket) state.socket.emit('voice_speaking', { room_id: state.currentRoomId, speaking });
        const el = document.getElementById(`vp-${state.nick}`);
        if (el) el.classList.toggle('speaking', speaking);
      }
    }, 150);
  } catch (e) { console.warn('VAD error:', e); }
}

function addVoiceParticipant(user) {
  state.voiceParticipants[user.nick] = user;
}

function removeVoiceParticipant(nick) {
  delete state.voiceParticipants[nick];
  const pc = state.voicePeerConnections[nick];
  if (pc) { pc.close(); delete state.voicePeerConnections[nick]; }
  updateVoiceParticipantsUI();
}

function updateVoiceParticipantsUI() {
  const container = document.getElementById('voice-participants');
  container.innerHTML = '';
  const participants = Object.values(state.voiceParticipants);
  document.getElementById('voice-room-meta').textContent = `${participants.length} участник${pluralize(participants.length)}`;
  participants.forEach(p => {
    const isMe = p.nick === state.nick;
    const div = document.createElement('div');
    div.className = 'voice-participant';
    if (p.micMuted) div.classList.add('muted-mic');
    div.id = `vp-${p.nick}`;
    const initial = (state.currentRoomIsAnon && !isMe) ? '?' : p.nick.charAt(0).toUpperCase();
    const displayNick = (state.currentRoomIsAnon && !isMe) ? 'Аноним' : escapeHtml(p.nick);
    div.innerHTML = `
      <div class="voice-avatar">
        ${initial}
        <div class="voice-avatar-ring"></div>
      </div>
      <span class="voice-nick ${p.role}">${displayNick}${isMe ? ' (я)' : ''}</span>
      <div class="voice-status-icons">
        ${p.micMuted ? '🔇' : '🎙️'}
        ${p.deafened ? '🙉' : '🔊'}
      </div>
    `;
    container.appendChild(div);
  });
}

function onVoiceUserJoined(data) {
  addVoiceParticipant(data);
  updateVoiceParticipantsUI();
  toast(`${data.nick} присоединился к голосовой комнате`, 'info');
  // Create WebRTC peer connection
  createPeerConnection(data.nick, true);
}

function onVoiceUserLeft(data) {
  removeVoiceParticipant(data.nick);
  toast(`${data.nick} покинул голосовую комнату`, 'info');
}

function onVoiceSpeakingUpdate(data) {
  const el = document.getElementById(`vp-${data.nick}`);
  if (el) el.classList.toggle('speaking', data.speaking);
}

function onVoiceMuteUpdate(data) {
  if (state.voiceParticipants[data.nick]) {
    state.voiceParticipants[data.nick].micMuted = data.micMuted;
    state.voiceParticipants[data.nick].deafened = data.deafened;
    updateVoiceParticipantsUI();
  }
}

async function createPeerConnection(targetNick, isInitiator) {
  const iceServers = [{ urls: 'stun:stun.l.google.com:19302' }, { urls: 'stun:stun1.l.google.com:19302' }];
  const pc = new RTCPeerConnection({ iceServers });
  state.voicePeerConnections[targetNick] = pc;

  if (state.voiceStream) {
    state.voiceStream.getTracks().forEach(track => pc.addTrack(track, state.voiceStream));
  }

  pc.ontrack = (event) => {
    if (state.deafened) return;
    const audio = document.createElement('audio');
    audio.srcObject = event.streams[0];
    audio.autoplay = true;
    audio.id = `audio-${targetNick}`;
    document.body.appendChild(audio);
  };

  pc.onicecandidate = (event) => {
    if (event.candidate) {
      state.socket.emit('voice_ice_candidate', {
        room_id: state.currentRoomId,
        target: targetNick,
        candidate: event.candidate
      });
    }
  };

  if (isInitiator) {
    const offer = await pc.createOffer();
    await pc.setLocalDescription(offer);
    state.socket.emit('voice_offer', {
      room_id: state.currentRoomId,
      target: targetNick,
      offer: pc.localDescription
    });
  }
  return pc;
}

async function onVoiceOffer(data) {
  const pc = await createPeerConnection(data.from, false);
  await pc.setRemoteDescription(new RTCSessionDescription(data.offer));
  const answer = await pc.createAnswer();
  await pc.setLocalDescription(answer);
  state.socket.emit('voice_answer', {
    room_id: state.currentRoomId,
    target: data.from,
    answer: pc.localDescription
  });
}

async function onVoiceAnswer(data) {
  const pc = state.voicePeerConnections[data.from];
  if (pc) await pc.setRemoteDescription(new RTCSessionDescription(data.answer));
}

async function onVoiceIceCandidate(data) {
  const pc = state.voicePeerConnections[data.from];
  if (pc && data.candidate) {
    try { await pc.addIceCandidate(new RTCIceCandidate(data.candidate)); } catch (e) { console.warn(e); }
  }
}

function leaveVoiceRoom() {
  if (state.voiceStream) {
    state.voiceStream.getTracks().forEach(t => t.stop());
    state.voiceStream = null;
  }
  if (state.screenStream) {
    state.screenStream.getTracks().forEach(t => t.stop());
    state.screenStream = null;
  }
  Object.values(state.voicePeerConnections).forEach(pc => pc.close());
  state.voicePeerConnections = {};
  state.voiceParticipants = {};
  document.querySelectorAll('audio[id^="audio-"]').forEach(a => a.remove());
  state.socket.emit('leave_voice_room', { room_id: state.currentRoomId });
  state.socket.emit('leave_room_event', { room_id: state.currentRoomId });
}

/* ============================================================
   RENDERING
============================================================ */
function updateTopbar() {
  const nickEl = document.getElementById('topbar-nick');
  const roleEl = document.getElementById('topbar-role');
  const avatarEl = document.getElementById('topbar-avatar');
  nickEl.textContent = `${state.emoji} ${state.nick}`;
  nickEl.className = `nick-tag ${state.role}`;
  avatarEl.textContent = state.nick.charAt(0).toUpperCase();
  const roleNames = { admin: '👑 Администратор', moderator: '🛡️ Модератор', owner: '🌟 Владелец', user: '👤 Пользователь' };
  roleEl.textContent = roleNames[state.role] || 'Пользователь';
  if (state.isObserver) roleEl.textContent = '👁️ Наблюдатель';
}

function updateModeratorUI() {
  const canMod = state.isAdmin || state.isMod;
  document.getElementById('btn-custom-roles').classList.toggle('hidden', !canMod);
}

function updateAnnouncement(text) {
  const bar = document.getElementById('global-announcement-bar');
  const span = document.getElementById('global-announcement-text');
  if (text) { span.textContent = text; bar.classList.remove('hidden'); }
  else bar.classList.add('hidden');
}

function updatePinnedBanner(msg) {
  const banner = document.getElementById('pinned-banner');
  const canMod = state.isAdmin || state.isMod || state.currentRoomOwner === state.nick;
  if (!msg) {
    banner.classList.add('hidden');
    return;
  }
  banner.classList.remove('hidden');
  document.getElementById('pin-nick').textContent = msg.nick + ': ';
  document.getElementById('pin-text-content').textContent = (msg.text || '').substring(0, 60) + (msg.text && msg.text.length > 60 ? '…' : '');
  document.getElementById('btn-unpin-msg').style.display = canMod ? 'inline-flex' : 'none';
  // Highlight
  document.querySelectorAll('.msg.pinned-msg').forEach(el => el.classList.remove('pinned-msg'));
  const msgEl = document.querySelector(`[data-msg-id="${msg.id}"]`);
  if (msgEl) msgEl.classList.add('pinned-msg');
}

function startRoomTimer(expiresAt) {
  const check = () => {
    const remaining = expiresAt * 1000 - Date.now();
    if (remaining <= 0) return;
    const m = Math.floor(remaining / 60000);
    const s = Math.floor((remaining % 60000) / 1000);
    const meta = document.getElementById('chat-room-meta');
    if (meta) {
      const count = document.querySelectorAll('#members-list .member-item').length;
      meta.textContent = `${count} участник${pluralize(count)} | ⏳ ${m}м ${s}с`;
    }
  };
  check();
  const t = setInterval(check, 1000);
  // Store timer ref for cleanup
  window._roomTimer = t;
}

function renderRooms(rooms) {
  state.rooms = rooms;
  const grid = document.getElementById('rooms-grid');
  const empty = document.getElementById('rooms-empty');
  grid.innerHTML = '';
  if (!rooms || rooms.length === 0) { empty.classList.remove('hidden'); return; }
  empty.classList.add('hidden');
  rooms.forEach(room => {
    const card = document.createElement('div');
    card.className = 'room-card';
    if (room.pinned) card.classList.add('room-pinned');
    card.dataset.roomId = room.id;
    const badges = [];
    if (room.has_password) badges.push(`<span class="room-badge badge-lock">🔒 Пароль</span>`);
    else badges.push(`<span class="room-badge badge-open">🔓 Открытая</span>`);
    if (room.is_voice) badges.push(`<span class="room-badge badge-voice">🎙️ Голос</span>`);
    if (room.is_anonymous) badges.push(`<span class="room-badge badge-anon">👻 Аноним</span>`);
    if (room.temp_expires) badges.push(`<span class="room-badge badge-temp">⏳ Временная</span>`);
    const count = room.members_count || 0;
    const canPin = state.isAdmin || state.isMod;
    const pinBtn = canPin
      ? `<button class="btn btn-ghost btn-sm pin-btn" data-room-id="${room.id}">${room.pinned ? '📌' : '📍'}</button>`
      : '';
    const icon = room.is_voice ? '🎙️' : (room.has_password ? '🔒' : '💬');
    card.innerHTML = `
      <div class="room-card-header">
        <div class="room-card-icon">${icon}</div>
        <div style="flex:1;min-width:0;">
          <div class="room-card-name truncate">${escapeHtml(room.name)}</div>
          <div style="margin-top:4px;display:flex;gap:4px;flex-wrap:wrap;">${badges.join('')}</div>
        </div>
      </div>
      <div class="room-meta">
        <span>👥 ${count} участник${pluralize(count)}</span>
        ${room.owner ? `<span>👤 ${escapeHtml(room.owner)}</span>` : ''}
      </div>
      ${pinBtn}
    `;
    grid.appendChild(card);
  });
}

function renderOnlineList(users) {
  const list = document.getElementById('online-list');
  list.innerHTML = '';
  // Sort by role
  const order = { admin: 0, moderator: 1, owner: 2, user: 3 };
  const sorted = [...users].sort((a, b) => (order[a.role] ?? 3) - (order[b.role] ?? 3));
  let lastGroup = null;
  sorted.forEach(user => {
    const group = user.role === 'admin' ? 'Администраторы'
                : user.role === 'moderator' ? 'Модераторы'
                : 'Пользователи';
    if (group !== lastGroup) {
      lastGroup = group;
      const hdr = document.createElement('div');
      hdr.className = 'role-group-header';
      hdr.textContent = group;
      list.appendChild(hdr);
    }
    const item = document.createElement('div');
    item.className = 'online-item';
    const displayNick = user.nick;
    item.innerHTML = `
      <div class="online-dot"></div>
      <span class="nick-tag ${user.role}">${user.emoji} ${escapeHtml(displayNick)}</span>
      ${user.role !== 'user' ? `<span class="badge-role ${user.role}">${user.role === 'admin' ? 'ADM' : 'MOD'}</span>` : ''}
    `;
    list.appendChild(item);
  });
}

function renderMembers(members) {
  const list = document.getElementById('members-list');
  list.innerHTML = '';
  const canMod = state.isAdmin || state.isMod;
  const isOwner = state.nick === state.currentRoomOwner;
  // Sort by role
  const order = { admin: 0, moderator: 1, owner: 2, user: 3 };
  const sorted = [...members].sort((a, b) => (order[a.role] ?? 3) - (order[b.role] ?? 3));
  let lastGroup = null;
  sorted.forEach(member => {
    const group = member.role === 'admin' ? 'Администраторы'
                : member.role === 'moderator' ? 'Модераторы'
                : 'Пользователи';
    if (group !== lastGroup) {
      lastGroup = group;
      const hdr = document.createElement('div');
      hdr.className = 'role-group-header';
      hdr.textContent = group;
      list.appendChild(hdr);
    }
    const item = document.createElement('div');
    item.className = 'member-item';
    const isMe = member.nick === state.nick;
    const isOwnerMember = member.nick === state.currentRoomOwner;
    const canKickThis = (canMod || isOwner) && !isMe && !(state.isMod && member.role === 'admin');
    const displayNick = state.currentRoomIsAnon && !isMe ? 'Аноним' : member.nick;
    const displayEmoji = state.currentRoomIsAnon && !isMe ? '👻' : member.emoji;
    const kickBtn = canKickThis
      ? `<div class="member-actions"><button class="btn btn-danger btn-sm" onclick="kickUser('${escapeHtml(member.nick)}')">Кик</button></div>`
      : '';
    item.innerHTML = `
      <span class="member-emoji">${displayEmoji}</span>
      <span class="nick-tag ${member.role} flex-1 truncate">
        ${escapeHtml(displayNick)}
        ${isOwnerMember ? '<span style="color:var(--color-owner);font-size:10px;"> 👑</span>' : ''}
        ${isMe ? ' <span style="color:var(--text-muted);font-size:11px;">(я)</span>' : ''}
      </span>
      ${kickBtn}
    `;
    list.appendChild(item);
  });
  const count = members.length;
  document.getElementById('chat-room-meta').textContent = `${count} участник${pluralize(count)}`;
  const canMod2 = state.isAdmin || state.isMod;
  document.getElementById('members-sidebar-footer').style.display = canMod2 ? 'block' : 'none';
}

function renderMessage(msg, isNew = true) {
  const list = document.getElementById('messages-list');
  if (msg.type === 'system' || msg.type === 'system_mod' || msg.type === 'system_admin') {
    const el = document.createElement('div');
    el.className = `msg msg-${msg.type}`;
    el.dataset.msgId = msg.id;
    el.innerHTML = `<span>${escapeHtml(msg.text)}</span>`;
    list.appendChild(el);
    return;
  }
  if (msg.type === 'announcement') {
    const canMod = state.isAdmin || state.isMod;
    const el = document.createElement('div');
    el.className = 'msg msg-announcement';
    el.dataset.msgId = msg.id;
    const deleteBtn = canMod ? `<button class="btn btn-danger btn-sm" onclick="deleteMessage('${msg.id}')">✕</button>` : '';
    const displayNick = state.currentRoomIsAnon ? 'Аноним' : (msg.nick || '');
    const displayEmoji = state.currentRoomIsAnon ? '👻' : (msg.emoji || '👤');
    el.innerHTML = `
      <div class="announcement-label">📢 Объявление ${deleteBtn}</div>
      <div class="msg-header">
        <span class="msg-nick ${msg.role}">${displayEmoji} ${escapeHtml(displayNick)}</span>
        ${msg.role !== 'user' ? `<span class="badge-role ${msg.role}">${msg.role === 'admin' ? 'ADMIN' : 'MOD'}</span>` : ''}
        <span class="msg-time">${msg.formatted_time || formatTime(msg.timestamp)}</span>
      </div>
      ${msg.text ? `<div class="msg-body">${buildMsgBody(msg.text, state.nick)}</div>` : ''}
      ${msg.image_data ? `<img class="msg-image" src="${msg.image_data}" alt="" onclick="openLightbox(this.src)" loading="lazy" />` : ''}
      <div class="msg-reactions">
        <button class="react-btn like-btn" data-type="like">👍 <span class="like-count">${msg.reactions?.like ?? 0}</span></button>
        <button class="react-btn dislike-btn" data-type="dislike">👎 <span class="dislike-count">${msg.reactions?.dislike ?? 0}</span></button>
      </div>
    `;
    list.appendChild(el);
    return;
  }
  // Regular message
  const canMod = state.isAdmin || state.isMod;
  const isOwner = state.nick === state.currentRoomOwner;
  const isMyMsg = msg.nick === state.nick;
  const canDelete = canMod || isOwner;
  const canEdit = isMyMsg;
  const canPin = canMod || isOwner;
  const el = document.createElement('div');
  el.className = 'msg';
  if (state.pinnedMessageId === msg.id) el.classList.add('pinned-msg');
  el.dataset.msgId = msg.id;

  const displayNick = state.currentRoomIsAnon && !isMyMsg ? 'Аноним' : (msg.nick || '');
  const displayEmoji = state.currentRoomIsAnon && !isMyMsg ? '👻' : (msg.emoji || '👤');

  const deleteBtn = canDelete ? `<button class="btn btn-danger btn-sm btn-icon" onclick="deleteMessage('${msg.id}')" title="Удалить">🗑️</button>` : '';
  const editBtn = canEdit ? `<button class="btn btn-ghost btn-sm btn-icon" onclick="startEditMessage('${msg.id}')" title="Редактировать">✏️</button>` : '';
  const pinBtn = canPin ? `<button class="btn btn-ghost btn-sm btn-icon" onclick="pinMessage('${msg.id}')" title="Закрепить">📌</button>` : '';

  const tagsHtml = (msg.tags || []).map(tag => {
    const cls = tag === 'important' ? 'important' : tag === 'urgent' ? 'urgent' : 'todo';
    const label = tag === 'important' ? '#важное' : tag === 'urgent' ? '#срочно' : '#todo';
    return `<span class="msg-tag ${cls}">${label}</span>`;
  }).join('');

  const isOwnerMsg = msg.nick === state.currentRoomOwner;
  const ownerBadge = isOwnerMsg ? `<span class="badge-role owner">OWNER</span>` : (msg.role !== 'user' ? `<span class="badge-role ${msg.role}">${msg.role === 'admin' ? 'ADMIN' : 'MOD'}</span>` : '');

  el.innerHTML = `
    <div class="msg-header">
      <span class="msg-nick ${msg.role}">${displayEmoji} ${escapeHtml(displayNick)}</span>
      ${ownerBadge}
      <span class="msg-time">${msg.formatted_time || formatTime(msg.timestamp)}</span>
      ${msg.edited ? '<span class="msg-edited">(изменено)</span>' : ''}
      <div class="msg-actions">${editBtn}${pinBtn}${deleteBtn}</div>
    </div>
    ${tagsHtml ? `<div style="margin-bottom:4px;">${tagsHtml}</div>` : ''}
    ${msg.text ? `<div class="msg-body">${buildMsgBody(msg.text, state.nick)}</div>` : ''}
    ${msg.image_data ? `<img class="msg-image" src="${msg.image_data}" alt="" onclick="openLightbox(this.src)" loading="lazy" />` : ''}
    <div class="msg-reactions">
      <button class="react-btn like-btn" data-type="like">👍 <span class="like-count">${msg.reactions?.like ?? 0}</span></button>
      <button class="react-btn dislike-btn" data-type="dislike">👎 <span class="dislike-count">${msg.reactions?.dislike ?? 0}</span></button>
    </div>
  `;
  list.appendChild(el);

  // Apply existing reaction state
  if (msg.reactions?.users?.[state.nick]) {
    const r = msg.reactions.users[state.nick];
    el.querySelector(`.${r}-btn`).classList.add('active');
  }
}

/* ============================================================
   EDIT MESSAGE
============================================================ */
function startEditMessage(msgId) {
  const msgEl = document.querySelector(`[data-msg-id="${msgId}"]`);
  if (!msgEl) return;
  // Remove existing edit area if any
  const existing = msgEl.querySelector('.msg-edit-area');
  if (existing) { existing.remove(); msgEl.querySelector('.msg-edit-btns')?.remove(); return; }
  const bodyEl = msgEl.querySelector('.msg-body');
  if (!bodyEl) return;
  // Get original text from server-side or reconstruct
  const originalText = bodyEl.innerText || bodyEl.textContent;
  const textarea = document.createElement('textarea');
  textarea.className = 'msg-edit-area';
  textarea.value = originalText;
  textarea.rows = 2;
  const btnRow = document.createElement('div');
  btnRow.className = 'msg-edit-btns';
  btnRow.innerHTML = `
    <button class="btn btn-primary btn-sm" id="save-edit-${msgId}">Сохранить</button>
    <button class="btn btn-ghost btn-sm" id="cancel-edit-${msgId}">Отмена</button>
  `;
  msgEl.appendChild(textarea);
  msgEl.appendChild(btnRow);
  textarea.focus();
  btnRow.querySelector(`#save-edit-${msgId}`).addEventListener('click', () => {
    const newText = textarea.value.trim();
    if (!newText) { toast('Сообщение не может быть пустым', 'error'); return; }
    state.socket.emit('edit_message', { room_id: state.currentRoomId, message_id: msgId, new_text: newText });
  });
  btnRow.querySelector(`#cancel-edit-${msgId}`).addEventListener('click', () => {
    textarea.remove(); btnRow.remove();
  });
  textarea.addEventListener('keydown', e => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); btnRow.querySelector(`#save-edit-${msgId}`).click(); }
    if (e.key === 'Escape') { textarea.remove(); btnRow.remove(); }
  });
}

/* ============================================================
   PIN MESSAGE
============================================================ */
function pinMessage(msgId) {
  if (!state.currentRoomId) return;
  if (state.pinnedMessageId === msgId) {
    state.socket.emit('unpin_message', { room_id: state.currentRoomId });
  } else {
    state.socket.emit('pin_message', { room_id: state.currentRoomId, message_id: msgId });
  }
}

/* ============================================================
   LEADERBOARD
============================================================ */
function renderLeaderboard(data) {
  const activeTab = document.querySelector('.lb-tab-btn.active')?.dataset.tab || 'messages';
  const container = document.getElementById('lb-content');
  let rows = [];
  if (activeTab === 'messages') {
    rows = (data.by_messages || []).map((u, i) => ({
      rank: i+1, nick: u.nick, role: u.role, value: u.count, label: 'сообщений'
    }));
  } else if (activeTab === 'reactions') {
    rows = (data.by_reactions || []).map((u, i) => ({
      rank: i+1, nick: u.nick, role: u.role, value: u.count, label: 'реакций'
    }));
  } else if (activeTab === 'time') {
    rows = (data.by_time || []).map((u, i) => ({
      rank: i+1, nick: u.nick, role: u.role, value: formatDuration(u.ms), label: ''
    }));
  }
  if (!rows.length) { container.innerHTML = '<p style="color:var(--text-muted);text-align:center;padding:24px;">Нет данных</p>'; return; }
  const rankCls = r => r === 1 ? 'lb-gold' : r === 2 ? 'lb-silver' : r === 3 ? 'lb-bronze' : '';
  container.innerHTML = `
    <table class="lb-table">
      <thead><tr><th>#</th><th>Ник</th><th>Результат</th></tr></thead>
      <tbody>
        ${rows.map(r => `
          <tr>
            <td class="lb-rank ${rankCls(r.rank)}">${r.rank === 1 ? '🥇' : r.rank === 2 ? '🥈' : r.rank === 3 ? '🥉' : r.rank}</td>
            <td><span class="nick-tag ${r.role}">${escapeHtml(r.nick)}</span></td>
            <td style="color:var(--accent);font-weight:600;">${r.value} ${r.label}</td>
          </tr>
        `).join('')}
      </tbody>
    </table>
  `;
}

/* ============================================================
   CUSTOM ROLES
============================================================ */
function renderCustomRolesList() {
  const container = document.getElementById('custom-roles-list');
  const select = document.getElementById('assign-role-select');
  container.innerHTML = '';
  select.innerHTML = '<option value="">Выберите роль...</option>';
  state.customRoles.forEach(role => {
    const item = document.createElement('div');
    item.className = 'custom-role-item';
    item.innerHTML = `
      <div class="role-color-dot" style="background:${escapeHtml(role.color)};"></div>
      <span style="color:${escapeHtml(role.color)};font-weight:600;">${role.emoji} ${escapeHtml(role.name)}</span>
      <span style="font-size:11px;color:var(--text-muted);margin-left:auto;margin-right:8px;">ID: ${role.id}</span>
      <button class="btn btn-danger btn-sm" onclick="deleteCustomRole('${role.id}')">✕</button>
    `;
    container.appendChild(item);
    const opt = document.createElement('option');
    opt.value = role.id;
    opt.textContent = `${role.emoji} ${role.name}`;
    select.appendChild(opt);
  });
  if (!state.customRoles.length) {
    container.innerHTML = '<p style="color:var(--text-muted);font-size:13px;margin-bottom:12px;">Нет кастомных ролей. Создайте первую!</p>';
  }
}

function deleteCustomRole(roleId) {
  state.socket.emit('delete_custom_role', { role_id: roleId });
}

/* ============================================================
   INVITE MODAL
============================================================ */
function renderInviteModal() {
  const container = document.getElementById('invite-online-list');
  container.innerHTML = '';
  state.onlineUsers.forEach(user => {
    if (user.nick === state.nick) return;
    const item = document.createElement('div');
    item.className = 'online-item';
    item.innerHTML = `
      <div class="online-dot"></div>
      <span class="nick-tag ${user.role}">${user.emoji} ${escapeHtml(user.nick)}</span>
      <button class="btn btn-primary btn-sm invite-send-btn" data-nick="${escapeHtml(user.nick)}" style="margin-left:auto;">Пригласить</button>
    `;
    container.appendChild(item);
  });
}

/* ============================================================
   ACTIONS
============================================================ */
function deleteMessage(messageId) {
  if (!state.currentRoomId) return;
  state.socket.emit('delete_message', { room_id: state.currentRoomId, message_id: messageId });
}

function kickUser(nick) {
  if (!state.currentRoomId) return;
  if (!confirm(`Кикнуть пользователя ${nick}?`)) return;
  state.socket.emit('kick_user', { room_id: state.currentRoomId, nick });
}

function openLightbox(src) {
  document.getElementById('lightbox-img').src = src;
  document.getElementById('lightbox').classList.remove('hidden');
}

function canSendMessage() {
  if (!state.spamDelay || state.isAdmin || state.isMod) return true;
  const now = Date.now();
  const elapsed = (now - state.lastMessageTime) / 1000;
  return elapsed >= state.spamDelay;
}

function getRemainingCooldown() {
  const now = Date.now();
  const elapsed = (now - state.lastMessageTime) / 1000;
  return Math.max(0, state.spamDelay - elapsed);
}

function sendMessage() {
  const textarea = document.getElementById('chat-textarea');
  const text = textarea.value.trim();
  const image = state.attachedImage;
  const isAnn = document.getElementById('announce-check').checked;
  if (!text && !image) return;
  if (!state.currentRoomId) return;

  if (!canSendMessage()) {
    const rem = getRemainingCooldown().toFixed(1);
    const warn = document.getElementById('spam-warning');
    warn.style.display = 'block';
    warn.textContent = `⏳ Подождите ${rem}с перед следующим сообщением...`;
    clearTimeout(state.spamCooldownTimer);
    state.spamCooldownTimer = setTimeout(() => { warn.style.display = 'none'; }, 2000);
    return;
  }

  state.lastMessageTime = Date.now();
  state.messageCount++;

  // Veteran check
  if (state.messageCount === 1000) {
    toast('🎖️ Вы достигли звания Ветеран (1000 сообщений)!', 'success', 6000);
    state.socket.emit('check_veteran_badge', {});
  }

  state.socket.emit('send_message', {
    room_id: state.currentRoomId,
    text,
    image_data: image || null,
    is_announcement: isAnn,
    tags: state.activeMessageTags
  });
  textarea.value = '';
  autoResizeTextarea(textarea);
  clearAttach();
  document.getElementById('announce-check').checked = false;
  // Clear tags
  state.activeMessageTags = [];
  document.querySelectorAll('.tag-selector-btn.active').forEach(b => b.classList.remove('active'));
  document.getElementById('spam-warning').style.display = 'none';
}

function clearAttach() {
  state.attachedImage = null;
  document.getElementById('attach-preview').style.display = 'none';
  document.getElementById('attach-preview-img').src = '';
  document.getElementById('file-input').value = '';
}

function handleRoomClick(room) {
  state.pendingRoomId = room.id;
  if (room.has_password && state.role !== 'admin') {
    document.getElementById('join-password-input').value = '';
    document.getElementById('join-password-error').classList.add('hidden');
    openModal('modal-room-password');
  } else {
    joinRoom(room.id);
  }
}

function joinRoom(roomId, password = '') {
  state.socket.emit('join_room_event', { room_id: roomId, password });
}

/* ============================================================
   DRAG & DROP
============================================================ */
function initDragDrop() {
  const area = document.getElementById('messages-area');
  const overlay = document.getElementById('drag-overlay');
  let dragCounter = 0;
  area.addEventListener('dragenter', e => {
    e.preventDefault();
    dragCounter++;
    overlay.classList.add('active');
  });
  area.addEventListener('dragleave', () => {
    dragCounter--;
    if (dragCounter <= 0) { dragCounter = 0; overlay.classList.remove('active'); }
  });
  area.addEventListener('dragover', e => { e.preventDefault(); });
  area.addEventListener('drop', e => {
    e.preventDefault();
    dragCounter = 0;
    overlay.classList.remove('active');
    const files = e.dataTransfer.files;
    if (!files.length) return;
    const file = files[0];
    if (!file.type.startsWith('image/')) { toast('Только изображения поддерживаются', 'error'); return; }
    compressAndSetImage(file);
  });
}

function compressAndSetImage(file) {
  if (file.size > 10 * 1024 * 1024) { toast('Изображение слишком большое (макс. 10MB)', 'error'); return; }
  const img = new Image();
  const reader = new FileReader();
  reader.onload = e => {
    img.onload = () => {
      const canvas = document.createElement('canvas');
      const maxW = 800, maxH = 600;
      let w = img.width, h = img.height;
      if (w > maxW || h > maxH) { const r = Math.min(maxW/w, maxH/h); w *= r; h *= r; }
      canvas.width = w; canvas.height = h;
      canvas.getContext('2d').drawImage(img, 0, 0, w, h);
      const data = canvas.toDataURL('image/jpeg', 0.7);
      state.attachedImage = data;
      document.getElementById('attach-preview-img').src = data;
      document.getElementById('attach-preview').style.display = 'block';
    };
    img.src = e.target.result;
  };
  reader.readAsDataURL(file);
}

/* ============================================================
   UI INIT
============================================================ */
function initUI() {
  const nickInput = document.getElementById('nick-input');
  const btnLogin = document.getElementById('btn-login');
  const saved = sessionStorage.getItem('vietugram_nick');
  if (saved) nickInput.value = saved;

  function doLogin() {
    const nick = nickInput.value.trim();
    if (!nick) { toast('Введите ник', 'error'); return; }
    if (nick.length < 2 || nick.length > 30) { toast('Ник должен быть от 2 до 30 символов', 'error'); return; }
    btnLogin.innerHTML = '<div class="spinner"></div>';
    btnLogin.disabled = true;
    document.getElementById('login-error').classList.add('hidden');
    state.nick = nick;
    state.socket.emit('join_app', { nick });
    setTimeout(() => {
      if (btnLogin.disabled) {
        btnLogin.innerHTML = 'Войти в Vietugram';
        btnLogin.disabled = false;
        toast('Нет ответа от сервера', 'error');
      }
    }, 8000);
  }
  btnLogin.addEventListener('click', doLogin);
  nickInput.addEventListener('keydown', e => { if (e.key === 'Enter') doLogin(); });

  // Close modals
  document.querySelectorAll('[data-close]').forEach(btn => {
    btn.addEventListener('click', () => closeModal(btn.dataset.close));
  });
  document.querySelectorAll('.modal-overlay').forEach(overlay => {
    overlay.addEventListener('click', e => { if (e.target === overlay) closeModal(overlay.id); });
  });

  // Create room
  document.getElementById('btn-create-room').addEventListener('click', () => {
    document.getElementById('room-name-input').value = '';
    document.getElementById('room-password-input').value = '';
    document.getElementById('room-password-toggle').checked = false;
    document.getElementById('room-voice-toggle').checked = false;
    document.getElementById('room-anon-toggle').checked = false;
    document.getElementById('room-temp-toggle').checked = false;
    document.getElementById('room-password-field').classList.add('hidden');
    document.getElementById('room-temp-field').classList.add('hidden');
    openModal('modal-create-room');
  });
  document.getElementById('room-password-toggle').addEventListener('change', function() {
    document.getElementById('room-password-field').classList.toggle('hidden', !this.checked);
  });
  document.getElementById('room-temp-toggle').addEventListener('change', function() {
    document.getElementById('room-temp-field').classList.toggle('hidden', !this.checked);
  });
  document.getElementById('btn-confirm-create-room').addEventListener('click', () => {
    const name = document.getElementById('room-name-input').value.trim();
    const hasPass = document.getElementById('room-password-toggle').checked;
    const password = hasPass ? document.getElementById('room-password-input').value.trim() : '';
    const isVoice = document.getElementById('room-voice-toggle').checked;
    const isAnon = document.getElementById('room-anon-toggle').checked;
    const isTemp = document.getElementById('room-temp-toggle').checked;
    let tempSeconds = 0;
    if (isTemp) {
      const val = parseInt(document.getElementById('room-temp-value').value) || 60;
      const unit = document.getElementById('room-temp-unit').value;
      tempSeconds = unit === 'hours' ? val * 3600 : unit === 'minutes' ? val * 60 : val;
    }
    if (!name) { toast('Введите название комнаты', 'error'); return; }
    if (hasPass && !password) { toast('Введите пароль или отключите защиту', 'error'); return; }
    state.socket.emit('create_room', { name, password, is_voice: isVoice, is_anonymous: isAnon, temp_seconds: tempSeconds });
  });
  document.getElementById('room-name-input').addEventListener('keydown', e => {
    if (e.key === 'Enter') document.getElementById('btn-confirm-create-room').click();
  });

  // Join password
  document.getElementById('btn-confirm-join-password').addEventListener('click', () => {
    const password = document.getElementById('join-password-input').value.trim();
    if (!password) { toast('Введите пароль', 'error'); return; }
    joinRoom(state.pendingRoomId, password);
  });
  document.getElementById('join-password-input').addEventListener('keydown', e => {
    if (e.key === 'Enter') document.getElementById('btn-confirm-join-password').click();
  });

  // Leave room
  document.getElementById('btn-leave-room').addEventListener('click', () => {
    if (window._roomTimer) { clearInterval(window._roomTimer); window._roomTimer = null; }
    state.socket.emit('leave_room_event', { room_id: state.currentRoomId });
  });

  // Delete room
  document.getElementById('btn-delete-room').addEventListener('click', () => {
    document.getElementById('delete-room-name-display').textContent = state.currentRoomName;
    openModal('modal-confirm-delete');
  });
  document.getElementById('btn-confirm-delete-room').addEventListener('click', () => {
    state.socket.emit('delete_room', { room_id: state.currentRoomId });
    closeModal('modal-confirm-delete');
  });

  // Spam settings
  document.getElementById('btn-spam-settings').addEventListener('click', () => {
    document.getElementById('spam-delay-input').value = state.spamDelay || 0;
    openModal('modal-spam-settings');
  });
  document.getElementById('btn-save-spam-settings').addEventListener('click', () => {
    const delay = parseInt(document.getElementById('spam-delay-input').value) || 0;
    state.socket.emit('set_spam_delay', { room_id: state.currentRoomId, delay });
    state.spamDelay = delay;
    closeModal('modal-spam-settings');
    toast(`Антиспам: задержка ${delay}с установлена`, 'success');
  });

  // Send message
  document.getElementById('btn-send').addEventListener('click', sendMessage);
  document.getElementById('chat-textarea').addEventListener('keydown', e => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage(); }
    // Shift+Enter = newline (default textarea behavior, we just don't prevent it)
  });
  document.getElementById('chat-textarea').addEventListener('input', function() {
    autoResizeTextarea(this);
    // Typing indicator
    if (state.currentRoomId) state.socket.emit('typing', { room_id: state.currentRoomId });
  });

  // Attach image
  document.getElementById('btn-attach').addEventListener('click', () => document.getElementById('file-input').click());
  document.getElementById('file-input').addEventListener('change', function() {
    const file = this.files[0];
    if (!file) return;
    if (!file.type.startsWith('image/')) { toast('Выберите изображение', 'error'); return; }
    compressAndSetImage(file);
  });
  document.getElementById('btn-remove-attach').addEventListener('click', clearAttach);

  // Tag selector
  document.getElementById('btn-toggle-tags').addEventListener('click', () => {
    document.getElementById('tag-selector').classList.toggle('hidden');
  });
  document.querySelectorAll('.tag-selector-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const tag = btn.dataset.tag;
      if (btn.classList.contains('active')) {
        btn.classList.remove('active');
        state.activeMessageTags = state.activeMessageTags.filter(t => t !== tag);
      } else {
        btn.classList.add('active');
        state.activeMessageTags.push(tag);
      }
    });
  });

  // Mobile sidebar
  document.getElementById('members-toggle-btn').addEventListener('click', () => {
    document.getElementById('members-sidebar').classList.toggle('open');
  });

  // Lightbox
  document.getElementById('lightbox').addEventListener('click', () => {
    document.getElementById('lightbox').classList.add('hidden');
  });

  // Announcement
  document.getElementById('btn-send-announcement').addEventListener('click', () => {
    document.getElementById('announce-check').checked = true;
    document.getElementById('chat-textarea').focus();
    toast('Включён режим объявления', 'info');
  });

  // Pinned banner
  document.getElementById('btn-goto-pin').addEventListener('click', () => {
    if (state.pinnedMessageId) {
      const msgEl = document.querySelector(`[data-msg-id="${state.pinnedMessageId}"]`);
      if (msgEl) { msgEl.scrollIntoView({ behavior: 'smooth', block: 'center' }); }
    }
  });
  document.getElementById('btn-unpin-msg').addEventListener('click', () => {
    if (state.currentRoomId) state.socket.emit('unpin_message', { room_id: state.currentRoomId });
  });

  // Admin panel
  document.getElementById('btn-admin-panel').addEventListener('click', () => {
    if (state.isAdmin) {
      document.getElementById('admin-code-section').classList.add('hidden');
      document.getElementById('admin-only-section').classList.remove('hidden');
      state.socket.emit('get_admin_panel', {});
    } else {
      document.getElementById('admin-code-section').classList.remove('hidden');
      document.getElementById('admin-only-section').classList.add('hidden');
    }
    openModal('modal-admin');
  });
  document.getElementById('btn-verify-admin-code').addEventListener('click', () => {
    const code = document.getElementById('admin-code-input').value.trim();
    if (!code) return;
    state.socket.emit('verify_admin_code', { code });
    document.getElementById('admin-code-input').value = '';
  });
  document.getElementById('admin-code-input').addEventListener('keydown', e => {
    if (e.key === 'Enter') document.getElementById('btn-verify-admin-code').click();
  });
  document.getElementById('btn-add-mod').addEventListener('click', () => {
    const nick = document.getElementById('mod-nick-input').value.trim();
    if (!nick) { toast('Введите ник', 'error'); return; }
    state.socket.emit('set_moderator', { nick, action: 'add' });
    document.getElementById('mod-nick-input').value = '';
  });
  document.getElementById('btn-ban-user').addEventListener('click', () => {
    const nick = document.getElementById('ban-nick-input').value.trim();
    if (!nick) { toast('Введите ник', 'error'); return; }
    if (!confirm(`Заблокировать пользователя "${nick}"?`)) return;
    state.socket.emit('ban_user', { nick });
    document.getElementById('ban-nick-input').value = '';
  });
  document.getElementById('btn-set-announcement').addEventListener('click', () => {
    const text = document.getElementById('global-ann-input').value.trim();
    state.socket.emit('set_global_announcement', { text });
  });
  document.getElementById('btn-set-join-msg').addEventListener('click', () => {
    const text = document.getElementById('join-msg-input').value.trim();
    state.socket.emit('set_room_join_message', { text });
  });
  document.getElementById('btn-set-emoji').addEventListener('click', () => {
    const emoji = document.getElementById('emoji-input').value.trim();
    state.socket.emit('set_emoji', { emoji });
  });
  document.getElementById('btn-toggle-observer').addEventListener('click', () => {
    state.isObserver = !state.isObserver;
    state.socket.emit('set_observer_mode', { active: state.isObserver });
    document.getElementById('observer-status').textContent = state.isObserver ? 'Активен' : '';
    document.getElementById('btn-toggle-observer').textContent = state.isObserver ? 'Выключить режим наблюдателя' : 'Включить режим наблюдателя';
    toast(state.isObserver ? '👁️ Режим наблюдателя включён' : 'Режим наблюдателя выключен', 'info');
    updateTopbar();
  });

  // Leaderboard
  document.getElementById('btn-leaderboard').addEventListener('click', () => {
    state.socket.emit('get_leaderboard', {});
    openModal('modal-leaderboard');
  });
  document.querySelectorAll('.lb-tab-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.lb-tab-btn').forEach(b => { b.classList.remove('active'); b.className = b.className.replace('btn-primary', 'btn-ghost'); });
      btn.classList.add('active');
      btn.className = btn.className.replace('btn-ghost', 'btn-primary');
      state.socket.emit('get_leaderboard', {});
    });
  });

  // Custom roles
  document.getElementById('btn-custom-roles').addEventListener('click', () => {
    renderCustomRolesList();
    openModal('modal-custom-roles');
  });
  document.getElementById('btn-create-custom-role').addEventListener('click', () => {
    const name = document.getElementById('new-role-name').value.trim();
    const color = document.getElementById('new-role-color').value;
    const emoji = document.getElementById('new-role-emoji').value.trim() || '🏷️';
    if (!name) { toast('Введите название роли', 'error'); return; }
    state.socket.emit('create_custom_role', { name, color, emoji });
    document.getElementById('new-role-name').value = '';
    document.getElementById('new-role-emoji').value = '';
  });
  document.getElementById('btn-assign-custom-role').addEventListener('click', () => {
    const nick = document.getElementById('assign-role-nick').value.trim();
    const roleId = document.getElementById('assign-role-select').value;
    if (!nick || !roleId) { toast('Введите ник и выберите роль', 'error'); return; }
    state.socket.emit('assign_custom_role', { nick, role_id: roleId });
    document.getElementById('assign-role-nick').value = '';
  });

  // Invite
  document.getElementById('btn-open-invite-modal').addEventListener('click', () => {
    state.socket.emit('get_online_users');
    openModal('modal-invite');
  });
  document.getElementById('invite-online-list').addEventListener('click', e => {
    const btn = e.target.closest('.invite-send-btn');
    if (btn) {
      state.socket.emit('invite_player', { nick: btn.dataset.nick, room_id: state.currentRoomId });
      toast(`Приглашение отправлено ${btn.dataset.nick}`, 'info');
    }
  });

  // Search author
  document.getElementById('btn-search-author').addEventListener('click', () => openModal('modal-search-author'));
  document.getElementById('btn-do-search-author').addEventListener('click', () => {
    const nick = document.getElementById('search-author-input').value.trim();
    if (!nick) { toast('Введите ник', 'error'); return; }
    state.searchAuthorFilter = nick;
    document.getElementById('search-author-name').textContent = nick;
    document.getElementById('search-author-panel').classList.remove('hidden');
    closeModal('modal-search-author');
    // Filter visible messages
    filterMessagesByAuthor(nick);
    toast(`Показаны сообщения от ${nick}`, 'info');
  });
  document.getElementById('btn-clear-author-search').addEventListener('click', () => {
    state.searchAuthorFilter = null;
    document.getElementById('search-author-panel').classList.add('hidden');
    // Reload messages (request from server)
    if (state.currentRoomId) state.socket.emit('get_room_messages', { room_id: state.currentRoomId });
    toast('Фильтр снят', 'info');
  });

  // Rooms grid delegation
  document.getElementById('rooms-grid').addEventListener('click', e => {
    if (e.target.closest('.pin-btn')) {
      e.stopPropagation();
      const roomId = e.target.closest('.pin-btn').dataset.roomId;
      const room = state.rooms.find(r => r.id === roomId);
      if (room) state.socket.emit(room.pinned ? 'unpin_room' : 'pin_room', { room_id: roomId });
      return;
    }
    const card = e.target.closest('.room-card');
    if (card) {
      const room = state.rooms.find(r => r.id === card.dataset.roomId);
      if (room) handleRoomClick(room);
    }
  });

  // Messages delegation (reactions)
  document.getElementById('messages-list').addEventListener('click', e => {
    const btn = e.target.closest('.react-btn');
    if (!btn) return;
    const msgEl = btn.closest('.msg');
    if (!msgEl) return;
    const msgId = msgEl.dataset.msgId;
    const type = btn.dataset.type;
    const isActive = btn.classList.contains('active');
    state.socket.emit('react_message', {
      room_id: state.currentRoomId,
      message_id: msgId,
      reaction: isActive ? null : type
    });
  });

  // Mobile sidebar close
  document.addEventListener('click', e => {
    const sidebar = document.getElementById('members-sidebar');
    const toggleBtn = document.getElementById('members-toggle-btn');
    if (sidebar.classList.contains('open') && !sidebar.contains(e.target) && e.target !== toggleBtn) {
      sidebar.classList.remove('open');
    }
  });

  // Escape
  document.addEventListener('keydown', e => {
    if (e.key === 'Escape') {
      document.querySelectorAll('.modal-overlay.open').forEach(m => closeModal(m.id));
      document.getElementById('lightbox').classList.add('hidden');
    }
  });

  // Voice controls
  document.getElementById('voice-btn-mic').addEventListener('click', () => {
    state.micMuted = !state.micMuted;
    if (state.voiceStream) state.voiceStream.getAudioTracks().forEach(t => t.enabled = !state.micMuted);
    const btn = document.getElementById('voice-btn-mic');
    btn.className = `voice-ctrl-btn ${state.micMuted ? 'mic-off' : 'mic-on'}`;
    btn.textContent = state.micMuted ? '🔇' : '🎙️';
    if (state.voiceParticipants[state.nick]) state.voiceParticipants[state.nick].micMuted = state.micMuted;
    updateVoiceParticipantsUI();
    state.socket.emit('voice_mute_update', { room_id: state.currentRoomId, micMuted: state.micMuted, deafened: state.deafened });
  });

  document.getElementById('voice-btn-deaf').addEventListener('click', () => {
    state.deafened = !state.deafened;
    document.querySelectorAll('audio[id^="audio-"]').forEach(a => a.muted = state.deafened);
    const btn = document.getElementById('voice-btn-deaf');
    btn.className = `voice-ctrl-btn ${state.deafened ? 'deaf-off' : 'deaf-on'}`;
    btn.textContent = state.deafened ? '🙉' : '🔊';
    if (state.voiceParticipants[state.nick]) state.voiceParticipants[state.nick].deafened = state.deafened;
    updateVoiceParticipantsUI();
    state.socket.emit('voice_mute_update', { room_id: state.currentRoomId, micMuted: state.micMuted, deafened: state.deafened });
  });

  document.getElementById('voice-btn-screen').addEventListener('click', async () => {
    const btn = document.getElementById('voice-btn-screen');
    if (state.screenSharing) {
      if (state.screenStream) { state.screenStream.getTracks().forEach(t => t.stop()); state.screenStream = null; }
      state.screenSharing = false;
      btn.classList.remove('active');
      toast('Демонстрация экрана остановлена', 'info');
    } else {
      try {
        state.screenStream = await navigator.mediaDevices.getDisplayMedia({ video: true, audio: false });
        state.screenSharing = true;
        btn.classList.add('active');
        toast('Демонстрация экрана запущена 🖥️', 'success');
        state.screenStream.getVideoTracks()[0].onended = () => {
          state.screenSharing = false;
          btn.classList.remove('active');
        };
      } catch (e) { toast('Нет доступа к демонстрации экрана', 'error'); }
    }
  });

  document.getElementById('voice-btn-leave').addEventListener('click', () => {
    leaveVoiceRoom();
  });

  // Drag & Drop
  initDragDrop();

  // Typing indicator (receive)
  state.socket && state.socket.on('user_typing', data => {
    if (data.nick !== state.nick && data.room_id === state.currentRoomId) {
      const el = document.getElementById('typing-indicator');
      el.textContent = `${data.nick} печатает...`;
      clearTimeout(window._typingTimer);
      window._typingTimer = setTimeout(() => { el.textContent = ''; }, 2000);
    }
  });
}

function filterMessagesByAuthor(nick) {
  const list = document.getElementById('messages-list');
  list.querySelectorAll('.msg').forEach(el => {
    const msgNick = el.querySelector('.msg-nick');
    if (!msgNick) return;
    const elNick = msgNick.textContent.replace(/[👑🛡️👤👻]/g, '').trim();
    const visible = elNick === nick || el.classList.contains('msg-system') || el.classList.contains('msg-system-mod') || el.classList.contains('msg-system-admin');
    el.style.display = visible ? '' : 'none';
  });
}

/* ============================================================
   BOOT
============================================================ */
document.addEventListener('DOMContentLoaded', () => {
  initSocket();
  initUI();
  console.log('%c Vietugram v3.0 by Vietu ', 'background:#6c63ff;color:#fff;font-size:14px;padding:4px 8px;border-radius:4px;');
});
</script>
</body>
</html>"""

with open('index.html', 'w', encoding='utf-8') as f:
    f.write(HTML_CONTENT)
print("✅ index.html записан")

# 3. Запись server.py
SERVER_CONTENT = r"""
# =============================================================================
# VIETUGRAM - Flask + SocketIO Server v3.0
# Автор: Vietu
# =============================================================================
import eventlet
eventlet.monkey_patch()

from flask import Flask, request
from flask_socketio import SocketIO, emit, join_room, leave_room
from flask_cors import CORS
from pyngrok import ngrok
import uuid, time, os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'vietugram_secret_key_2024'
CORS(app, cors_allowed_origins="*")
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet', logger=False, engineio_logger=False)

ADMIN_CODE = "GGCheck"

# ── Storage ──────────────────────────────────────────────────────────────────
online_users   = {}   # sid -> {nick, role, room_id, emoji, join_time, observer}
user_roles     = {}   # nick -> role
user_emojis    = {}   # nick -> emoji
banned_users   = set()
rooms          = {}   # room_id -> room dict
custom_roles   = {}   # role_id -> {id, name, color, emoji}
user_custom_roles = {}  # nick -> role_id
leaderboard    = {}   # nick -> {messages, reactions, join_time}
global_announcement = None
room_join_message   = None

# ── Helpers ───────────────────────────────────────────────────────────────────
def get_user_by_sid(sid):
    return online_users.get(sid)

def get_user_by_nick(nick):
    for sid, u in online_users.items():
        if u['nick'] == nick:
            return sid, u
    return None, None

def get_role(nick):
    return user_roles.get(nick, 'user')

def get_emoji(nick):
    role = get_role(nick)
    custom = user_emojis.get(nick)
    if custom: return custom
    if role == 'admin': return '👑'
    if role == 'moderator': return '🛡️'
    return '👤'

def build_user_info(nick, hide_nick=False):
    role = get_role(nick)
    return {
        'nick': 'Аноним' if hide_nick else nick,
        'role': role,
        'emoji': '👻' if hide_nick else get_emoji(nick),
        'color': role
    }

def get_online_list():
    result, seen = [], set()
    for sid, u in online_users.items():
        nick = u['nick']
        if nick in seen or u.get('observer'): continue
        seen.add(nick)
        result.append(build_user_info(nick))
    return result

def get_rooms_list():
    result = []
    for rid, r in rooms.items():
        result.append({
            'id': rid, 'name': r['name'],
            'has_password': bool(r.get('password')),
            'members_count': len(r['members']),
            'owner': r.get('created_by'),
            'is_voice': r.get('is_voice', False),
            'is_anonymous': r.get('is_anonymous', False),
            'temp_expires': r.get('temp_expires'),
            'pinned': r.get('pinned', False),
            'members': [build_user_info(m, r.get('is_anonymous')) for m in r['members']]
        })
    result.sort(key=lambda r: (0 if r['pinned'] else 1, r['name']))
    return result

def get_room_members(room_id):
    r = rooms.get(room_id)
    if not r: return []
    anon = r.get('is_anonymous', False)
    return [build_user_info(nick, anon) for nick in r['members']]

def broadcast_rooms_update():
    socketio.emit('rooms_update', {'rooms': get_rooms_list()})

def broadcast_online_update():
    socketio.emit('online_update', {'users': get_online_list()})

def broadcast_room_members(room_id):
    socketio.emit('room_members_update', {'room_id': room_id, 'members': get_room_members(room_id)}, room=room_id)

def ensure_lb(nick):
    if nick not in leaderboard:
        leaderboard[nick] = {'messages': 0, 'reactions': 0, 'join_time': time.time(), 'role': get_role(nick)}

# ── Routes ────────────────────────────────────────────────────────────────────
@app.route('/')
def index():
    try:
        with open('index.html', 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        return "<h1>index.html not found</h1>", 404

# ── SocketIO Events ───────────────────────────────────────────────────────────
@socketio.on('connect')
def on_connect():
    print(f"[+] {request.sid}")

@socketio.on('disconnect')
def on_disconnect():
    sid = request.sid
    user = online_users.get(sid)
    if not user: return
    nick = user['nick']
    room_id = user.get('room_id')
    if room_id and room_id in rooms:
        rooms[room_id]['members'].discard(nick)
        leave_room(room_id)
        _sys(room_id, f'{nick} покинул комнату (отключился)')
        broadcast_room_members(room_id)
    del online_users[sid]
    broadcast_online_update()
    broadcast_rooms_update()

def _sys(room_id, text, type_='system'):
    msg = {'id': str(uuid.uuid4()), 'type': type_, 'text': text,
           'timestamp': time.time(), 'formatted_time': time.strftime('%H:%M')}
    if room_id in rooms:
        rooms[room_id]['messages'].append(msg)
        socketio.emit('new_message', msg, room=room_id)

@socketio.on('join_app')
def on_join_app(data):
    sid = request.sid
    nick = str(data.get('nick', '')).strip()
    if not nick or len(nick) < 2 or len(nick) > 30:
        return emit('join_error', {'message': 'Ник должен быть от 2 до 30 символов'})
    if nick in banned_users:
        return emit('join_error', {'message': 'Вы заблокированы'})
    for esid, eu in online_users.items():
        if eu['nick'] == nick and esid != sid:
            return emit('join_error', {'message': 'Этот ник уже занят'})
    if nick not in user_roles: user_roles[nick] = 'user'
    role = user_roles[nick]
    online_users[sid] = {'nick': nick, 'role': role, 'room_id': None, 'emoji': get_emoji(nick), 'join_time': time.time(), 'observer': False}
    ensure_lb(nick)
    emit('join_success', {
        'nick': nick, 'role': role, 'emoji': get_emoji(nick),
        'rooms': get_rooms_list(), 'online_users': get_online_list(),
        'global_announcement': global_announcement,
        'custom_roles': list(custom_roles.values())
    })
    broadcast_online_update()

@socketio.on('create_room')
def on_create_room(data):
    sid = request.sid
    user = get_user_by_sid(sid)
    if not user: return emit('error', {'message': 'Не авторизован'})
    name = str(data.get('name', '')).strip()
    if not name or len(name) > 50: return emit('error', {'message': 'Неверное название'})
    for r in rooms.values():
        if r['name'] == name: return emit('error', {'message': 'Комната с таким именем уже существует'})
    password  = str(data.get('password', '')).strip()
    is_voice  = bool(data.get('is_voice', False))
    is_anon   = bool(data.get('is_anonymous', False))
    temp_sec  = int(data.get('temp_seconds', 0))
    room_id   = str(uuid.uuid4())
    room      = {
        'name': name, 'password': password or None,
        'messages': [], 'members': set(),
        'created_by': user['nick'], 'created_at': time.time(),
        'pinned': False, 'is_voice': is_voice, 'is_anonymous': is_anon,
        'temp_expires': time.time() + temp_sec if temp_sec > 0 else None,
        'spam_delay': 0, 'pinned_message': None, 'pinned_message_id': None
    }
    rooms[room_id] = room
    if temp_sec > 0:
        def expire_room():
            eventlet.sleep(temp_sec)
            if room_id in rooms:
                rn = rooms[room_id]['name']
                socketio.emit('room_expired', {'room_id': room_id, 'room_name': rn})
                for u_sid, u_data in list(online_users.items()):
                    if u_data.get('room_id') == room_id:
                        online_users[u_sid]['room_id'] = None
                del rooms[room_id]
                broadcast_rooms_update()
        eventlet.spawn(expire_room)
    emit('room_created', {'room_id': room_id, 'name': name})
    broadcast_rooms_update()

@socketio.on('join_room_event')
def on_join_room(data):
    sid = request.sid
    user = get_user_by_sid(sid)
    if not user: return emit('error', {'message': 'Не авторизован'})
    room_id  = data.get('room_id')
    password = str(data.get('password', '')).strip()
    nick     = user['nick']
    role     = user['role']
    if room_id not in rooms: return emit('error', {'message': 'Комната не найдена'})
    r = rooms[room_id]
    if r.get('password') and role != 'admin' and password != r['password']:
        return emit('join_room_error', {'message': 'Неверный пароль'})
    # Leave old room
    old = user.get('room_id')
    if old and old != room_id and old in rooms:
        rooms[old]['members'].discard(nick)
        leave_room(old)
        _sys(old, f'{nick} покинул комнату')
        broadcast_room_members(old)
    join_room(room_id)
    r['members'].add(nick)
    user['room_id'] = room_id
    online_users[sid]['room_id'] = room_id
    emit('room_joined', {
        'room_id': room_id, 'room_name': r['name'],
        'messages': r['messages'], 'members': get_room_members(room_id),
        'has_password': bool(r.get('password')),
        'is_voice': r.get('is_voice', False),
        'is_anonymous': r.get('is_anonymous', False),
        'owner': r.get('created_by'),
        'temp_expires': r.get('temp_expires'),
        'spam_delay': r.get('spam_delay', 0),
        'pinned_message_id': r.get('pinned_message_id'),
        'pinned_message': r.get('pinned_message')
    })
    # Join message
    if room_join_message:
        _sys(room_id, room_join_message.replace('{nick}', nick))
    else:
        if role == 'admin': _sys(room_id, f'👑 Администратор {nick} вошёл в комнату', 'system_admin')
        elif role == 'moderator': _sys(room_id, f'🛡️ Модератор {nick} вошёл в комнату', 'system_mod')
        else: _sys(room_id, f'{nick} вошёл в комнату')
    broadcast_room_members(room_id)
    broadcast_rooms_update()

@socketio.on('leave_room_event')
def on_leave_room(data):
    sid = request.sid
    user = get_user_by_sid(sid)
    if not user: return
    room_id = data.get('room_id') or user.get('room_id')
    nick = user['nick']
    if room_id and room_id in rooms:
        rooms[room_id]['members'].discard(nick)
        leave_room(room_id)
        online_users[sid]['room_id'] = None
        _sys(room_id, f'{nick} покинул комнату')
        broadcast_room_members(room_id)
    emit('left_room', {'room_id': room_id})
    broadcast_rooms_update()

@socketio.on('send_message')
def on_send_message(data):
    sid = request.sid
    user = get_user_by_sid(sid)
    if not user: return emit('error', {'message': 'Не авторизован'})
    nick       = user['nick']
    role       = user['role']
    room_id    = data.get('room_id') or user.get('room_id')
    text       = str(data.get('text', '')).strip()
    image_data = data.get('image_data')
    is_ann     = bool(data.get('is_announcement', False))
    tags       = data.get('tags', [])
    if is_ann and role not in ('moderator', 'admin'):
        return emit('error', {'message': 'Недостаточно прав'})
    if not room_id or room_id not in rooms: return emit('error', {'message': 'Не в комнате'})
    if nick not in rooms[room_id]['members']: return emit('error', {'message': 'Не участник комнаты'})
    if not text and not image_data: return emit('error', {'message': 'Пустое сообщение'})
    if text and len(text) > 2000: return emit('error', {'message': 'Сообщение слишком длинное'})
    ensure_lb(nick)
    leaderboard[nick]['messages'] += 1
    leaderboard[nick]['role'] = role
    msg = {
        'id': str(uuid.uuid4()),
        'type': 'announcement' if is_ann else 'message',
        'nick': nick, 'role': role, 'emoji': get_emoji(nick),
        'text': text, 'image_data': image_data,
        'timestamp': time.time(), 'formatted_time': time.strftime('%H:%M'),
        'room_id': room_id, 'reactions': {'like': 0, 'dislike': 0, 'users': {}},
        'tags': tags, 'edited': False
    }
    rooms[room_id]['messages'].append(msg)
    socketio.emit('new_message', msg, room=room_id)
    # Veteran badge
    if leaderboard[nick]['messages'] == 1000:
        socketio.emit('new_message', {
            'id': str(uuid.uuid4()), 'type': 'system_admin',
            'text': f'🎖️ {nick} получил звание Ветеран (1000 сообщений)!',
            'timestamp': time.time(), 'formatted_time': time.strftime('%H:%M')
        }, room=room_id)

@socketio.on('edit_message')
def on_edit_message(data):
    sid = request.sid
    user = get_user_by_sid(sid)
    if not user: return
    room_id = data.get('room_id')
    msg_id  = data.get('message_id')
    new_text = str(data.get('new_text', '')).strip()
    if not new_text or not room_id or room_id not in rooms: return
    for msg in rooms[room_id]['messages']:
        if msg['id'] == msg_id and msg['nick'] == user['nick']:
            msg['text'] = new_text
            msg['edited'] = True
            socketio.emit('message_edited', {'room_id': room_id, 'message_id': msg_id, 'new_text': new_text}, room=room_id)
            break

@socketio.on('react_message')
def on_react_message(data):
    sid = request.sid
    user = get_user_by_sid(sid)
    if not user: return
    room_id  = data.get('room_id')
    msg_id   = data.get('message_id')
    reaction = data.get('reaction')
    nick     = user['nick']
    if room_id not in rooms: return
    for msg in rooms[room_id]['messages']:
        if msg['id'] == msg_id:
            r = msg.setdefault('reactions', {'like': 0, 'dislike': 0, 'users': {}})
            users = r.setdefault('users', {})
            old = users.get(nick)
            if old and old in r: r[old] = max(0, r[old] - 1)
            if reaction in ('like', 'dislike'):
                r[reaction] = r.get(reaction, 0) + 1
                users[nick] = reaction
                # Credit reactions to message author
                ensure_lb(msg['nick'])
                leaderboard[msg['nick']]['reactions'] += 1
            else:
                users.pop(nick, None)
            socketio.emit('reaction_updated', {'room_id': room_id, 'message_id': msg_id, 'reactions': r}, room=room_id)
            break

@socketio.on('delete_message')
def on_delete_message(data):
    sid = request.sid
    user = get_user_by_sid(sid)
    if not user: return
    room_id    = data.get('room_id')
    message_id = data.get('message_id')
    nick       = user['nick']
    role       = user['role']
    room_owner = rooms.get(room_id, {}).get('created_by')
    if role not in ('moderator', 'admin') and nick != room_owner: return
    if not room_id or room_id not in rooms: return
    original = len(rooms[room_id]['messages'])
    rooms[room_id]['messages'] = [m for m in rooms[room_id]['messages'] if m['id'] != message_id]
    if len(rooms[room_id]['messages']) < original:
        socketio.emit('message_deleted', {'room_id': room_id, 'message_id': message_id}, room=room_id)

@socketio.on('pin_message')
def on_pin_message(data):
    sid = request.sid
    user = get_user_by_sid(sid)
    if not user: return
    room_id    = data.get('room_id')
    message_id = data.get('message_id')
    nick       = user['nick']
    role       = user['role']
    room_owner = rooms.get(room_id, {}).get('created_by')
    if role not in ('moderator', 'admin') and nick != room_owner: return
    if room_id not in rooms: return
    for msg in rooms[room_id]['messages']:
        if msg['id'] == message_id:
            rooms[room_id]['pinned_message']    = msg
            rooms[room_id]['pinned_message_id'] = message_id
            socketio.emit('pin_updated', {'room_id': room_id, 'pinned_message': msg}, room=room_id)
            break

@socketio.on('unpin_message')
def on_unpin_message(data):
    sid = request.sid
    user = get_user_by_sid(sid)
    if not user: return
    room_id = data.get('room_id')
    nick    = user['nick']
    role    = user['role']
    room_owner = rooms.get(room_id, {}).get('created_by')
    if role not in ('moderator', 'admin') and nick != room_owner: return
    if room_id in rooms:
        rooms[room_id]['pinned_message']    = None
        rooms[room_id]['pinned_message_id'] = None
        socketio.emit('pin_updated', {'room_id': room_id, 'pinned_message': None}, room=room_id)

@socketio.on('kick_user')
def on_kick_user(data):
    sid = request.sid
    user = get_user_by_sid(sid)
    if not user: return
    room_id = data.get('room_id')
    target_nick = data.get('nick')
    nick = user['nick']
    role = user['role']
    room_owner = rooms.get(room_id, {}).get('created_by')
    if role not in ('moderator', 'admin') and nick != room_owner: return
    if role == 'moderator' and get_role(target_nick) == 'admin': return
    target_sid, target_user = get_user_by_nick(target_nick)
    if not target_sid or room_id not in rooms or target_nick not in rooms[room_id]['members']: return
    rooms[room_id]['members'].discard(target_nick)
    if target_user: online_users[target_sid]['room_id'] = None
    socketio.emit('kicked', {'room_id': room_id, 'by': nick}, to=target_sid)
    _sys(room_id, f'{target_nick} был исключён из комнаты')
    broadcast_room_members(room_id)
    broadcast_rooms_update()

@socketio.on('delete_room')
def on_delete_room(data):
    sid = request.sid
    user = get_user_by_sid(sid)
    if not user: return
    room_id = data.get('room_id')
    nick    = user['nick']
    role    = user['role']
    room_owner = rooms.get(room_id, {}).get('created_by')
    if role not in ('moderator', 'admin') and nick != room_owner: return
    if room_id not in rooms: return
    room_name = rooms[room_id]['name']
    socketio.emit('room_deleted', {'room_id': room_id, 'room_name': room_name, 'by': nick}, room=room_id)
    for u_sid in list(online_users):
        if online_users[u_sid].get('room_id') == room_id:
            online_users[u_sid]['room_id'] = None
    del rooms[room_id]
    broadcast_rooms_update()

@socketio.on('set_spam_delay')
def on_set_spam_delay(data):
    sid = request.sid
    user = get_user_by_sid(sid)
    if not user: return
    room_id = data.get('room_id')
    delay   = max(0, min(300, int(data.get('delay', 0))))
    nick    = user['nick']
    role    = user['role']
    room_owner = rooms.get(room_id, {}).get('created_by')
    if role not in ('moderator', 'admin') and nick != room_owner: return
    if room_id in rooms:
        rooms[room_id]['spam_delay'] = delay
        socketio.emit('spam_settings_updated', {'delay': delay}, room=room_id)

@socketio.on('pin_room')
def on_pin_room(data):
    sid = request.sid
    user = get_user_by_sid(sid)
    if not user or user['role'] not in ('moderator', 'admin'): return
    rid = data.get('room_id')
    if rid in rooms: rooms[rid]['pinned'] = True; broadcast_rooms_update()

@socketio.on('unpin_room')
def on_unpin_room(data):
    sid = request.sid
    user = get_user_by_sid(sid)
    if not user or user['role'] not in ('moderator', 'admin'): return
    rid = data.get('room_id')
    if rid in rooms: rooms[rid]['pinned'] = False; broadcast_rooms_update()

@socketio.on('get_online_users')
def on_get_online_users():
    emit('online_users_list', {'users': get_online_list()})

@socketio.on('invite_player')
def on_invite_player(data):
    sid = request.sid
    user = get_user_by_sid(sid)
    if not user or user['role'] not in ('moderator', 'admin'): return
    target_nick = data.get('nick')
    room_id = data.get('room_id') or user.get('room_id')
    if not room_id or room_id not in rooms: return
    target_sid, _ = get_user_by_nick(target_nick)
    if target_sid:
        socketio.emit('invite_notification', {'room_id': room_id, 'room_name': rooms[room_id]['name'], 'from_nick': user['nick']}, to=target_sid)

@socketio.on('accept_invite')
def on_accept_invite(data):
    on_join_room({'room_id': data.get('room_id'), 'password': ''})

@socketio.on('typing')
def on_typing(data):
    sid = request.sid
    user = get_user_by_sid(sid)
    if not user: return
    room_id = data.get('room_id') or user.get('room_id')
    if room_id:
        socketio.emit('user_typing', {'nick': user['nick'], 'room_id': room_id}, room=room_id, skip_sid=sid)

@socketio.on('get_room_messages')
def on_get_room_messages(data):
    sid = request.sid
    user = get_user_by_sid(sid)
    if not user: return
    room_id = data.get('room_id')
    if room_id in rooms and user['nick'] in rooms[room_id]['members']:
        emit('room_messages', {'messages': rooms[room_id]['messages']})

# ── Voice WebRTC ────────────────────────────────────────────────────────────
@socketio.on('join_voice_room')
def on_join_voice_room(data):
    sid = request.sid
    user = get_user_by_sid(sid)
    if not user: return
    room_id = data.get('room_id') or user.get('room_id')
    if room_id not in rooms: return
    voice_data = {
        'nick': user['nick'], 'role': user['role'],
        'emoji': get_emoji(user['nick']), 'micMuted': False, 'deafened': False
    }
    socketio.emit('voice_user_joined', voice_data, room=room_id, skip_sid=sid)

@socketio.on('leave_voice_room')
def on_leave_voice_room(data):
    sid = request.sid
    user = get_user_by_sid(sid)
    if not user: return
    room_id = data.get('room_id') or user.get('room_id')
    if room_id in rooms:
        socketio.emit('voice_user_left', {'nick': user['nick']}, room=room_id, skip_sid=sid)

@socketio.on('voice_offer')
def on_voice_offer(data):
    sid = request.sid
    user = get_user_by_sid(sid)
    if not user: return
    target_sid, _ = get_user_by_nick(data.get('target'))
    if target_sid:
        socketio.emit('voice_offer', {'from': user['nick'], 'offer': data.get('offer')}, to=target_sid)

@socketio.on('voice_answer')
def on_voice_answer(data):
    sid = request.sid
    user = get_user_by_sid(sid)
    if not user: return
    target_sid, _ = get_user_by_nick(data.get('target'))
    if target_sid:
        socketio.emit('voice_answer', {'from': user['nick'], 'answer': data.get('answer')}, to=target_sid)

@socketio.on('voice_ice_candidate')
def on_voice_ice_candidate(data):
    sid = request.sid
    user = get_user_by_sid(sid)
    if not user: return
    target_sid, _ = get_user_by_nick(data.get('target'))
    if target_sid:
        socketio.emit('voice_ice_candidate', {'from': user['nick'], 'candidate': data.get('candidate')}, to=target_sid)

@socketio.on('voice_speaking')
def on_voice_speaking(data):
    sid = request.sid
    user = get_user_by_sid(sid)
    if not user: return
    room_id = data.get('room_id') or user.get('room_id')
    if room_id:
        socketio.emit('voice_speaking_update', {'nick': user['nick'], 'speaking': data.get('speaking', False)}, room=room_id, skip_sid=sid)

@socketio.on('voice_mute_update')
def on_voice_mute_update(data):
    sid = request.sid
    user = get_user_by_sid(sid)
    if not user: return
    room_id = data.get('room_id') or user.get('room_id')
    if room_id:
        socketio.emit('voice_mute_update', {'nick': user['nick'], 'micMuted': data.get('micMuted', False), 'deafened': data.get('deafened', False)}, room=room_id, skip_sid=sid)

# ── Admin ────────────────────────────────────────────────────────────────────
@socketio.on('verify_admin_code')
def on_verify_admin_code(data):
    sid = request.sid
    user = get_user_by_sid(sid)
    if not user: return
    nick = user['nick']
    if data.get('code', '').strip() == ADMIN_CODE:
        user_roles[nick] = 'admin'
        online_users[sid]['role'] = 'admin'
        emit('admin_code_result', {'success': True, 'message': 'Вы теперь администратор!'})
        emit('role_updated', {'nick': nick, 'role': 'admin', 'emoji': get_emoji(nick)})
        broadcast_online_update()
    else:
        emit('admin_code_result', {'success': False, 'message': 'Неверный код'})

@socketio.on('get_admin_panel')
def on_get_admin_panel(data=None):
    sid = request.sid
    user = get_user_by_sid(sid)
    if not user or user['role'] != 'admin': return emit('error', {'message': 'Доступ запрещён'})
    mods = [n for n, r in user_roles.items() if r == 'moderator']
    emit('admin_panel_data', {
        'moderators': mods, 'banned_users': list(banned_users),
        'global_announcement': global_announcement,
        'room_join_message': room_join_message,
        'stats': {
            'online_count': len(set(u['nick'] for u in online_users.values())),
            'rooms_count': len(rooms),
            'total_messages': sum(len(r['messages']) for r in rooms.values()),
            'total_users_known': len(user_roles)
        }
    })

@socketio.on('set_moderator')
def on_set_moderator(data):
    sid = request.sid
    user = get_user_by_sid(sid)
    if not user or user['role'] != 'admin': return
    target = data.get('nick', '').strip()
    action = data.get('action')
    if not target: return
    if action == 'add':
        if user_roles.get(target) == 'admin': return
        user_roles[target] = 'moderator'
        t_sid, _ = get_user_by_nick(target)
        if t_sid:
            online_users[t_sid]['role'] = 'moderator'
            socketio.emit('role_updated', {'nick': target, 'role': 'moderator', 'emoji': get_emoji(target)}, to=t_sid)
        emit('admin_action_result', {'success': True, 'message': f'{target} назначен модератором'})
    elif action == 'remove':
        if user_roles.get(target) == 'moderator':
            user_roles[target] = 'user'
            t_sid, _ = get_user_by_nick(target)
            if t_sid:
                online_users[t_sid]['role'] = 'user'
                socketio.emit('role_updated', {'nick': target, 'role': 'user', 'emoji': get_emoji(target)}, to=t_sid)
            emit('admin_action_result', {'success': True, 'message': f'Права модератора сняты с {target}'})
    on_get_admin_panel()
    broadcast_online_update()

@socketio.on('ban_user')
def on_ban_user(data):
    sid = request.sid
    user = get_user_by_sid(sid)
    if not user or user['role'] != 'admin': return
    target = data.get('nick', '').strip()
    if not target or target == user['nick'] or get_role(target) == 'admin': return
    banned_users.add(target)
    t_sid, _ = get_user_by_nick(target)
    if t_sid: socketio.emit('banned', {'message': 'Вы заблокированы администратором'}, to=t_sid)
    emit('admin_action_result', {'success': True, 'message': f'{target} заблокирован'})
    on_get_admin_panel()

@socketio.on('unban_user')
def on_unban_user(data):
    sid = request.sid
    user = get_user_by_sid(sid)
    if not user or user['role'] != 'admin': return
    target = data.get('nick', '').strip()
    banned_users.discard(target)
    emit('admin_action_result', {'success': True, 'message': f'{target} разблокирован'})
    on_get_admin_panel()

@socketio.on('set_global_announcement')
def on_set_global_announcement(data):
    global global_announcement
    sid = request.sid
    user = get_user_by_sid(sid)
    if not user or user['role'] != 'admin': return
    text = data.get('text', '').strip()
    global_announcement = text or None
    socketio.emit('announcement_updated', {'text': global_announcement})
    emit('admin_action_result', {'success': True, 'message': 'Объявление обновлено'})

@socketio.on('set_room_join_message')
def on_set_room_join_message(data):
    global room_join_message
    sid = request.sid
    user = get_user_by_sid(sid)
    if not user or user['role'] != 'admin': return
    room_join_message = data.get('text', '').strip() or None
    emit('admin_action_result', {'success': True, 'message': 'Сообщение входа обновлено'})

@socketio.on('set_emoji')
def on_set_emoji(data):
    sid = request.sid
    user = get_user_by_sid(sid)
    if not user or user['role'] not in ('moderator', 'admin'): return
    emoji = data.get('emoji', '').strip()
    nick  = user['nick']
    if emoji: user_emojis[nick] = emoji
    else: user_emojis.pop(nick, None)
    emit('emoji_updated', {'emoji': get_emoji(nick)})
    broadcast_online_update()

@socketio.on('set_observer_mode')
def on_set_observer_mode(data):
    sid = request.sid
    user = get_user_by_sid(sid)
    if not user or user['role'] != 'admin': return
    active = bool(data.get('active', False))
    online_users[sid]['observer'] = active
    broadcast_online_update()

# ── Leaderboard ───────────────────────────────────────────────────────────────
@socketio.on('get_leaderboard')
def on_get_leaderboard(data=None):
    by_msg = sorted(leaderboard.items(), key=lambda x: x[1].get('messages', 0), reverse=True)[:20]
    by_react = sorted(leaderboard.items(), key=lambda x: x[1].get('reactions', 0), reverse=True)[:20]
    now = time.time()
    online_nicks = {u['nick']: u for u in online_users.values()}
    by_time_raw = []
    for nick, lb in leaderboard.items():
        u_data = online_nicks.get(nick)
        jt = u_data['join_time'] if u_data else lb.get('join_time', now)
        elapsed_ms = int((now - jt) * 1000)
        by_time_raw.append((nick, lb, elapsed_ms))
    by_time_raw.sort(key=lambda x: x[2], reverse=True)
    emit('leaderboard_data', {
        'by_messages': [{'nick': n, 'role': lb.get('role', 'user'), 'count': lb.get('messages', 0)} for n, lb in by_msg],
        'by_reactions': [{'nick': n, 'role': lb.get('role', 'user'), 'count': lb.get('reactions', 0)} for n, lb in by_react],
        'by_time': [{'nick': n, 'role': lb.get('role', 'user'), 'ms': ms} for n, lb, ms in by_time_raw[:20]]
    })

# ── Custom roles ──────────────────────────────────────────────────────────────
@socketio.on('create_custom_role')
def on_create_custom_role(data):
    sid = request.sid
    user = get_user_by_sid(sid)
    if not user or user['role'] not in ('moderator', 'admin'): return emit('error', {'message': 'Недостаточно прав'})
    name  = str(data.get('name', '')).strip()
    color = str(data.get('color', '#a78bfa'))
    emoji = str(data.get('emoji', '🏷️'))
    if not name: return
    role_id = str(uuid.uuid4())[:8]
    custom_roles[role_id] = {'id': role_id, 'name': name, 'color': color, 'emoji': emoji}
    socketio.emit('custom_roles_update', {'roles': list(custom_roles.values())})

@socketio.on('delete_custom_role')
def on_delete_custom_role(data):
    sid = request.sid
    user = get_user_by_sid(sid)
    if not user or user['role'] not in ('moderator', 'admin'): return
    role_id = data.get('role_id')
    custom_roles.pop(role_id, None)
    socketio.emit('custom_roles_update', {'roles': list(custom_roles.values())})

@socketio.on('assign_custom_role')
def on_assign_custom_role(data):
    sid = request.sid
    user = get_user_by_sid(sid)
    if not user or user['role'] not in ('moderator', 'admin'): return
    target_nick = data.get('nick', '').strip()
    role_id     = data.get('role_id')
    if not target_nick or role_id not in custom_roles: return emit('error', {'message': 'Ник или роль не найдены'})
    user_custom_roles[target_nick] = role_id
    role_data = custom_roles[role_id]
    # Update emoji from custom role
    user_emojis[target_nick] = role_data['emoji']
    t_sid, _ = get_user_by_nick(target_nick)
    socketio.emit('custom_role_assigned', {'nick': target_nick, 'role_name': role_data['name'], 'role_id': role_id, 'color': role_data['color'], 'emoji': role_data['emoji']})
    emit('admin_action_result', {'success': True, 'message': f'Роль «{role_data["name"]}» выдана {target_nick}'})
    broadcast_online_update()

@socketio.on('check_veteran_badge')
def on_check_veteran_badge(data=None):
    sid = request.sid
    user = get_user_by_sid(sid)
    if not user: return
    nick = user['nick']
    ensure_lb(nick)
    if leaderboard[nick].get('messages', 0) >= 1000:
        user_emojis[nick] = '🎖️'
        emit('emoji_updated', {'emoji': '🎖️'})
        broadcast_online_update()

# ── Main ──────────────────────────────────────────────────────────────────────
if __name__ == '__main__':
    print("=" * 60)
    print("  VIETUGRAM v3.0 - Запуск")
    print("=" * 60)
    ngrok.set_auth_token("3EUAvxvni84EnyW0BHobb1cf9s1_22w1T2dnp1UrHno7Ez6G9")
    try:
        public_url = ngrok.connect(5000, "http")
        print(f"\n✅ Публичный URL: {public_url}")
        # Сохраняем URL в файл для чтения из основного скрипта
        with open('ngrok_url.txt', 'w') as f:
            f.write(str(public_url))
    except Exception as e:
        print(f"⚠️  ngrok error: {e}")
    socketio.run(app, host='0.0.0.0', port=5000, debug=False, use_reloader=False)
"""

with open('server.py', 'w', encoding='utf-8') as f:
    f.write(SERVER_CONTENT)
print("✅ server.py записан")

# 4. Запуск сервера в фоновом режиме и получение публичного URL
import subprocess, sys, time, os

# Запускаем сервер как фоновый процесс
proc = subprocess.Popen([sys.executable, "server.py"],
                         stdout=subprocess.DEVNULL,
                         stderr=subprocess.DEVNULL,
                         start_new_session=True)
print("🚀 Сервер запускается в фоновом режиме...")

# Ждём появления файла с URL
for _ in range(20):
    if os.path.exists('ngrok_url.txt'):
        time.sleep(1)
        break
    time.sleep(1)

# Читаем URL
try:
    with open('ngrok_url.txt', 'r') as f:
        url = f.read().strip()
    print(f"\n🌐 ОТКРОЙТЕ В БРАУЗЕРЕ: {url}\n")
except FileNotFoundError:
    print("⚠️ Не удалось получить публичный URL (возможно, ngrok не запустился).")
    print("   Проверьте вывод сервера вручную или запустите server.py отдельно.")
