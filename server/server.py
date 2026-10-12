#!/usr/bin/env python3
"""
Kindle Dashboard Server
A lightweight, modern web app for mobile todo/vocabulary management and Kindle e-ink rendering.
"""

import os
import sys
import json
import time
import uuid
import urllib.request
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler
from datetime import datetime

# Local renderer import
try:
    from renderer import render_dashboard
except ImportError:
    from .renderer import render_dashboard

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
DATA_FILE = os.path.join(DATA_DIR, "data.json")
SCREEN_IMAGE_PATH = os.path.join(DATA_DIR, "screen.png")

os.makedirs(DATA_DIR, exist_ok=True)

# Curated high-frequency English vocabulary database for instant shuffle
BUILTIN_WORDS = [
    {
        "word": "resilience",
        "phonetic": "[rɪˈzɪliəns]",
        "pos": "n.",
        "trans": "恢复力；韧性；适应力",
        "example": "Emotional resilience helps people thrive in challenging environments.",
        "example_cn": "情绪韧性帮助人们在充满挑战的环境中茁壮成长。"
    },
    {
        "word": "serendipity",
        "phonetic": "[ˌserənˈdɪpəti]",
        "pos": "n.",
        "trans": "意外发现珍奇事物的本领；意外的机缘",
        "example": "A series of happy serendipities brought us together.",
        "example_cn": "一连串美妙的机缘巧合让我们相遇。"
    },
    {
        "word": "ubiquitous",
        "phonetic": "[juːˈbɪkwɪtəs]",
        "pos": "adj.",
        "trans": "无所不在的；十分普遍的",
        "example": "Smartphones have become ubiquitous in modern daily life.",
        "example_cn": "智能手机在现代日常生活中已经无处不在。"
    },
    {
        "word": "perseverance",
        "phonetic": "[ˌpɜːrsəˈvɪrəns]",
        "pos": "n.",
        "trans": "坚持不懈；锲而不舍；毅力",
        "example": "Through sheer perseverance, she conquered all obstacles.",
        "example_cn": "凭借顽强的毅力，她克服了所有的艰难险阻。"
    },
    {
        "word": "ephemeral",
        "phonetic": "[ɪˈfemərəl]",
        "pos": "adj.",
        "trans": "短暂的；转瞬即逝的",
        "example": "Fame in the digital era can often be ephemeral.",
        "example_cn": "数字时代的声名往往如昙花一现般短暂。"
    },
    {
        "word": "meticulous",
        "phonetic": "[məˈtɪkjələs]",
        "pos": "adj.",
        "trans": "一丝不苟的；非常严谨细致的",
        "example": "He kept meticulous records of all experimental transactions.",
        "example_cn": "他对所有实验数据进行了细致入微的记录。"
    },
    {
        "word": "pragmatic",
        "phonetic": "[præɡˈmætɪk]",
        "pos": "adj.",
        "trans": "务实的；注重实效的",
        "example": "We adopted a pragmatic approach to solving the engineering bottleneck.",
        "example_cn": "我们采取了一种务实的方法来解决工程瓶颈。"
    },
    {
        "word": "catalyst",
        "phonetic": "[ˈkætəlɪst]",
        "pos": "n.",
        "trans": "催化剂；促成变化的人或因素",
        "example": "The crisis acted as a catalyst for swift regulatory reform.",
        "example_cn": "这场危机成为了迅速推动监管改革的催化剂。"
    },
    {
        "word": "tenacious",
        "phonetic": "[təˈneɪʃəs]",
        "pos": "adj.",
        "trans": "顽强的；坚韧不拔的；执着的",
        "example": "He has a tenacious spirit and never gives up under pressure.",
        "example_cn": "他具有顽强的精神，在压力下从不轻言放弃。"
    },
    {
        "word": "lucid",
        "phonetic": "[ˈluːsɪd]",
        "pos": "adj.",
        "trans": "清晰易懂的；头脑清醒的",
        "example": "She gave a lucid and convincing presentation of the project.",
        "example_cn": "她对该项目进行了清晰透彻且令人信服的阐述。"
    }
]

def load_data():
    if not os.path.exists(DATA_FILE):
        initial = {
            "note": "保持专注与热爱，每天进步一点点！",
            "words": [BUILTIN_WORDS[0]],
            "todos": [
                {"id": str(uuid.uuid4())[:8], "text": "早晨完成考研/雅思生词背诵", "done": False},
                {"id": str(uuid.uuid4())[:8], "text": "检查服务器运行状态与每日备份", "done": True},
                {"id": str(uuid.uuid4())[:8], "text": "整理今晚阅读书单与洗漱", "done": False}
            ]
        }
        save_data(initial)
        return initial
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"note": "", "words": [], "todos": []}

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    # Trigger re-rendering
    try:
        render_dashboard(data, SCREEN_IMAGE_PATH)
    except Exception as e:
        print(f"Render error: {e}", file=sys.stderr)

def fetch_word_definition(word):
    """Fetches word phonetic, translation, and example via public dict API."""
    clean_word = word.strip().lower()
    # Try Youdao public API
    try:
        url = f"https://dict.youdao.com/suggest?q={urllib.parse.quote(clean_word)}&num=1&doctype=json"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=3) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            entries = data.get("data", {}).get("entries", [])
            if entries:
                entry = entries[0]
                explain = entry.get("explain", "")
                from renderer import clean_trans
                return {
                    "word": clean_word,
                    "phonetic": "",
                    "pos": "",
                    "trans": clean_trans(explain),
                    "example": "",
                    "example_cn": ""
                }
    except Exception:
        pass
    
    # Fallback to local built-in words if matched
    for w in BUILTIN_WORDS:
        if w["word"].lower() == clean_word:
            return w

    return {
        "word": clean_word,
        "phonetic": "",
        "pos": "",
        "trans": "",
        "example": "",
        "example_cn": ""
    }

# Ensure screen image exists on launch
if not os.path.exists(SCREEN_IMAGE_PATH):
    save_data(load_data())

HTML_PAGE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
  <title>Kindle 同步看板 · 手机管理中心</title>
  <style>
    :root {
      --bg: #f4f6f8;
      --card-bg: #ffffff;
      --text-main: #1f2937;
      --text-sub: #6b7280;
      --primary: #111827;
      --primary-hover: #374151;
      --border: #e5e7eb;
      --accent: #2563eb;
      --radius: 14px;
      --danger: #ef4444;
      --success: #10b981;
    }
    * { box-sizing: border-box; -webkit-tap-highlight-color: transparent; }
    body {
      margin: 0;
      padding: 0;
      background: var(--bg);
      color: var(--text-main);
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", sans-serif;
      padding-bottom: 70px;
    }
    .header {
      background: #111827;
      color: #fff;
      padding: 18px 20px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      box-shadow: 0 2px 10px rgba(0,0,0,0.08);
    }
    .header h1 { margin: 0; font-size: 19px; font-weight: 700; display: flex; align-items: center; gap: 8px; }
    .header .badge { background: #374151; font-size: 12px; padding: 3px 8px; border-radius: 20px; color: #9ca3af; }
    
    .container { max-width: 600px; margin: 0 auto; padding: 16px; }
    
    .card {
      background: var(--card-bg);
      border-radius: var(--radius);
      padding: 18px;
      margin-bottom: 16px;
      box-shadow: 0 1px 3px rgba(0,0,0,0.05);
      border: 1px solid var(--border);
    }
    .card-title {
      font-size: 16px;
      font-weight: 700;
      margin-bottom: 14px;
      display: flex;
      justify-content: space-between;
      align-items: center;
    }
    .card-title .action-btn {
      font-size: 13px;
      font-weight: 500;
      color: var(--accent);
      cursor: pointer;
      background: none;
      border: none;
      padding: 4px 8px;
    }

    /* Input group */
    .input-row { display: flex; gap: 8px; margin-bottom: 12px; }
    input[type="text"] {
      flex: 1;
      padding: 12px 14px;
      border: 1px solid var(--border);
      border-radius: 10px;
      font-size: 15px;
      outline: none;
      transition: border 0.2s;
    }
    input[type="text"]:focus { border-color: var(--primary); }
    .btn {
      padding: 12px 16px;
      background: var(--primary);
      color: #fff;
      border: none;
      border-radius: 10px;
      font-size: 14px;
      font-weight: 600;
      cursor: pointer;
      display: flex;
      align-items: center;
      gap: 4px;
      white-space: nowrap;
    }
    .btn-secondary { background: #e5e7eb; color: #374151; }
    .btn-outline { background: transparent; border: 1px solid var(--border); color: #374151; }
    
    /* Todo items */
    .todo-item {
      display: flex;
      align-items: center;
      padding: 12px 4px;
      border-bottom: 1px solid #f3f4f6;
      gap: 12px;
    }
    .todo-item:last-child { border-bottom: none; }
    .todo-checkbox {
      width: 24px;
      height: 24px;
      border-radius: 6px;
      border: 2px solid #d1d5db;
      display: flex;
      align-items: center;
      justify-content: center;
      cursor: pointer;
      transition: all 0.2s;
      flex-shrink: 0;
    }
    .todo-checkbox.checked {
      background: var(--primary);
      border-color: var(--primary);
      color: #fff;
    }
    .todo-text {
      flex: 1;
      font-size: 15px;
      line-height: 1.4;
      word-break: break-all;
    }
    .todo-text.done {
      text-decoration: line-through;
      color: var(--text-sub);
    }
    .todo-delete {
      color: #9ca3af;
      cursor: pointer;
      background: none;
      border: none;
      padding: 6px;
      font-size: 16px;
    }
    .todo-delete:hover { color: var(--danger); }

    /* Word card */
    .word-card {
      background: #f9fafb;
      border-radius: 10px;
      padding: 14px;
      margin-bottom: 10px;
      border: 1px solid #e5e7eb;
      position: relative;
    }
    .word-header { display: flex; align-items: baseline; gap: 8px; margin-bottom: 6px; }
    .word-title { font-size: 20px; font-weight: 700; color: #111827; }
    .word-phonetic { font-size: 14px; color: #6b7280; font-family: monospace; }
    .word-trans { font-size: 15px; color: #1f2937; margin-bottom: 6px; font-weight: 500; }
    .word-example { font-size: 13px; color: #4b5563; line-height: 1.4; }
    .word-example-cn { font-size: 13px; color: #6b7280; }
    .word-delete {
      position: absolute;
      top: 10px;
      right: 10px;
      color: #9ca3af;
      background: none;
      border: none;
      font-size: 16px;
      cursor: pointer;
    }

    /* Preview section */
    .preview-box {
      text-align: center;
      padding: 10px 0;
    }
    .preview-img {
      max-width: 100%;
      height: auto;
      border-radius: 8px;
      border: 2px solid #374151;
      box-shadow: 0 4px 12px rgba(0,0,0,0.15);
      background: #fff;
    }
    
    .toast {
      position: fixed;
      top: 20px;
      left: 50%;
      transform: translateX(-50%);
      background: rgba(17, 24, 39, 0.9);
      color: #fff;
      padding: 10px 20px;
      border-radius: 30px;
      font-size: 14px;
      z-index: 1000;
      opacity: 0;
      transition: opacity 0.3s;
      pointer-events: none;
    }
    .toast.show { opacity: 1; }
  </style>
</head>
<body>
  <div class="header">
    <h1>📖 Kindle 同步看板</h1>
    <span class="badge" id="syncStatus">实时同步已开启</span>
  </div>

  <div class="container">
    <!-- 1. 待办事项模块 -->
    <div class="card">
      <div class="card-title">
        <span>📋 今日待办事项</span>
        <button class="action-btn" onclick="clearCompleted()">清理已完成</button>
      </div>
      <div class="input-row">
        <input type="text" id="todoInput" placeholder="输入新的待办事项..." onkeydown="if(event.key==='Enter') addTodo()">
        <button class="btn" onclick="addTodo()">添加</button>
      </div>
      <div id="todoList">
        <!-- Rendered by JS -->
      </div>
    </div>

    <!-- 2. 今日背单词模块 -->
    <div class="card">
      <div class="card-title">
        <span>🔤 重点生词管理</span>
        <div style="display: flex; gap: 8px;">
          <button class="action-btn" onclick="addRandomWord()">🎲 随机抽词</button>
        </div>
      </div>
      <div class="input-row">
        <input type="text" id="wordInput" placeholder="输入英文单词 (自动查释义)..." onkeydown="if(event.key==='Enter') addWord()">
        <button class="btn" onclick="addWord()">添加</button>
      </div>
      <div id="wordList">
        <!-- Rendered by JS -->
      </div>
    </div>

    <!-- 3. 便签与提醒 -->
    <div class="card">
      <div class="card-title">
        <span>💡 随手便签 / 鼓励语</span>
        <button class="action-btn" onclick="saveNote()">保存便签</button>
      </div>
      <div class="input-row">
        <input type="text" id="noteInput" placeholder="写一句鼓励、目标或倒计时...">
        <button class="btn btn-secondary" onclick="saveNote()">更新</button>
      </div>
    </div>

    <!-- 4. Kindle 墨水屏实时效果预览 -->
    <div class="card">
      <div class="card-title">
        <span>📱 Kindle 墨水屏实时呈现效果</span>
        <button class="action-btn" onclick="refreshPreview()">刷新预览图</button>
      </div>
      <div class="preview-box">
        <img id="screenPreview" class="preview-img" src="./screen.png" alt="Kindle 墨水屏预览">
        <div style="font-size: 13px; color: #4b5563; margin-top: 12px; line-height: 1.6;">
          Kindle 拉取地址：<code id="pullUrlText">http://&lt;your-server-ip&gt;:8085/screen.png</code><br>
          分辨率：<b>1072 × 1448</b> (KPW3 原生高清灰阶)
        </div>
        <div style="margin-top: 14px;">
          <a href="./kindle-files.zip" class="btn btn-secondary" style="display: inline-flex; text-decoration: none; justify-content: center; width: 100%;">
            📥 下载 Kindle 端一键配置包 (kindle-files.zip)
          </a>
        </div>
      </div>
    </div>
  </div>

  <div id="toast" class="toast">操作成功</div>

  <script>
    let appData = { todos: [], words: [], note: "" };

    function showToast(msg) {
      const toast = document.getElementById('toast');
      toast.innerText = msg;
      toast.classList.add('show');
      setTimeout(() => toast.classList.remove('show'), 2000);
    }

    async function loadData() {
      try {
        const res = await fetch('./api/data');
        appData = await res.json();
        renderUI();
      } catch (e) {
        console.error(e);
      }
    }

    function renderUI() {
      // 1. Render Todos
      const todoList = document.getElementById('todoList');
      if (!appData.todos || appData.todos.length === 0) {
        todoList.innerHTML = '<div style="color:#9ca3af; font-size:14px; text-align:center; padding:16px 0;">当前暂无待办事项</div>';
      } else {
        todoList.innerHTML = appData.todos.map(t => `
          <div class="todo-item">
            <div class="todo-checkbox ${t.done ? 'checked' : ''}" onclick="toggleTodo('${t.id}')">
              ${t.done ? '✓' : ''}
            </div>
            <div class="todo-text ${t.done ? 'done' : ''}">${escapeHtml(t.text)}</div>
            <button class="todo-delete" onclick="deleteTodo('${t.id}')">✕</button>
          </div>
        `).join('');
      }

      // 2. Render Words
      const wordList = document.getElementById('wordList');
      if (!appData.words || appData.words.length === 0) {
        wordList.innerHTML = '<div style="color:#9ca3af; font-size:14px; text-align:center; padding:16px 0;">暂无生词，点击右上角“随机抽词”或输入单词添加</div>';
      } else {
        wordList.innerHTML = appData.words.map((w, index) => `
          <div class="word-card">
            <button class="word-delete" onclick="deleteWord(${index})">✕</button>
            <div class="word-header">
              <span class="word-title">${escapeHtml(w.word)}</span>
              <span class="word-phonetic">${escapeHtml(w.phonetic || '')}</span>
            </div>
            <div class="word-trans">${escapeHtml(w.pos || '')} ${escapeHtml(w.trans || '')}</div>
            ${w.example ? `<div class="word-example">${escapeHtml(w.example)}</div>` : ''}
            ${w.example_cn ? `<div class="word-example-cn">${escapeHtml(w.example_cn)}</div>` : ''}
          </div>
        `).join('');
      }

      // 3. Render Note
      document.getElementById('noteInput').value = appData.note || '';

      // 4. Refresh preview
      refreshPreview();
    }

    async function addTodo() {
      const input = document.getElementById('todoInput');
      const text = input.value.trim();
      if (!text) return;
      input.value = '';
      const res = await fetch('./api/todo', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ action: 'add', text })
      });
      appData = await res.json();
      renderUI();
      showToast('已添加待办并同步');
    }

    async function toggleTodo(id) {
      const res = await fetch('./api/todo', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ action: 'toggle', id })
      });
      appData = await res.json();
      renderUI();
      showToast('状态已更新');
    }

    async function deleteTodo(id) {
      const res = await fetch('./api/todo', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ action: 'delete', id })
      });
      appData = await res.json();
      renderUI();
      showToast('已删除待办');
    }

    async function clearCompleted() {
      const res = await fetch('./api/todo', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ action: 'clear_done' })
      });
      appData = await res.json();
      renderUI();
      showToast('已清理已完成事项');
    }

    async function addWord() {
      const input = document.getElementById('wordInput');
      const word = input.value.trim();
      if (!word) return;
      input.value = '';
      showToast('正在联网解析单词...');
      const res = await fetch('./api/word', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ action: 'add', word })
      });
      appData = await res.json();
      renderUI();
      showToast('单词添加成功');
    }

    async function addRandomWord() {
      const res = await fetch('./api/word', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ action: 'random' })
      });
      appData = await res.json();
      renderUI();
      showToast('已抽取新单词');
    }

    async function deleteWord(index) {
      const res = await fetch('./api/word', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ action: 'delete', index })
      });
      appData = await res.json();
      renderUI();
      showToast('生词已移除');
    }

    async function saveNote() {
      const note = document.getElementById('noteInput').value.trim();
      const res = await fetch('./api/note', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ note })
      });
      appData = await res.json();
      renderUI();
      showToast('便签已保存');
    }

    function refreshPreview() {
      const img = document.getElementById('screenPreview');
      img.src = './screen.png?t=' + new Date().getTime();
    }

    function escapeHtml(str) {
      if (!str) return '';
      return String(str).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
    }

    try {
      const fullUrl = window.location.origin + window.location.pathname.replace(/\/$/, '') + '/screen.png';
      const el = document.getElementById('pullUrlText');
      if (el) el.innerText = fullUrl;
    } catch(e) {}

    loadData();
  </script>
</body>
</html>
"""

class KindleDashboardHandler(BaseHTTPRequestHandler):
    def do_HEAD(self):
        self.do_GET()

    def log_message(self, format, *args):
        # Keep logs concise
        sys.stderr.write("%s - - [%s] %s\n" % (self.address_string(), self.log_date_time_string(), format % args))

    def do_GET(self):
        url = urllib.parse.urlparse(self.path)
        raw_path = url.path
        if raw_path.startswith("/kindle/"):
            path = raw_path[len("/kindle"):]
        elif raw_path == "/kindle":
            path = ""
        else:
            path = raw_path
        path = path.rstrip("/")

        if path in ("", "/index.html"):
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Cache-Control", "no-cache")
            self.end_headers()
            self.wfile.write(HTML_PAGE.encode("utf-8"))
            return

        elif path in ("/view", "/k"):
            # Pure browser display mode (for un-jailbroken Kindles using Experimental Browser)
            view_html = """<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>Kindle Board</title>
  <style>
    html, body { margin:0; padding:0; width:100%; height:100%; background:#fff; overflow:hidden; }
    img { width:100%; height:100%; object-fit:contain; display:block; }
  </style>
</head>
<body>
  <img id="screen" src="./screen.png">
  <script>
    setInterval(function() {
      document.getElementById('screen').src = './screen.png?t=' + new Date().getTime();
    }, 60000);
  </script>
</body>
</html>"""
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Cache-Control", "no-cache")
            self.end_headers()
            self.wfile.write(view_html.encode("utf-8"))
            return

        elif path in ("/screen.png", "/dashboard.png"):
            # Ensure file exists
            if not os.path.exists(SCREEN_IMAGE_PATH):
                save_data(load_data())
            try:
                with open(SCREEN_IMAGE_PATH, "rb") as f:
                    content = f.read()
                self.send_response(200)
                self.send_header("Content-Type", "image/png")
                self.send_header("Content-Length", str(len(content)))
                self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
                self.end_headers()
                self.wfile.write(content)
            except Exception as e:
                self.send_error(500, f"Image read error: {e}")
            return

        elif path == "/kindle-files.zip":
            zip_path = os.path.join(DATA_DIR, "kindle-files.zip")
            if not os.path.exists(zip_path):
                zip_path = os.path.join(BASE_DIR, "kindle-files.zip")
            if os.path.exists(zip_path):
                with open(zip_path, "rb") as f:
                    content = f.read()
                self.send_response(200)
                self.send_header("Content-Type", "application/zip")
                self.send_header("Content-Disposition", 'attachment; filename="kindle-files.zip"')
                self.send_header("Content-Length", str(len(content)))
                self.end_headers()
                self.wfile.write(content)
            else:
                self.send_error(404, "Zip Not Found")
            return

        elif path == "/api/data":
            data = load_data()
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Cache-Control", "no-cache")
            self.end_headers()
            self.wfile.write(json.dumps(data, ensure_ascii=False).encode("utf-8"))
            return

        else:
            self.send_error(404, "Not Found")

    def do_POST(self):
        url = urllib.parse.urlparse(self.path)
        raw_path = url.path
        if raw_path.startswith("/kindle/"):
            path = raw_path[len("/kindle"):]
        elif raw_path == "/kindle":
            path = ""
        else:
            path = raw_path
        path = path.rstrip("/")

        content_len = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_len).decode("utf-8")
        try:
            req_json = json.loads(body) if body else {}
        except Exception:
            req_json = {}

        data = load_data()

        if path == "/api/todo":
            action = req_json.get("action")
            if action == "add":
                text = req_json.get("text", "").strip()
                if text:
                    data["todos"].insert(0, {
                        "id": str(uuid.uuid4())[:8],
                        "text": text,
                        "done": False
                    })
            elif action == "toggle":
                tid = req_json.get("id")
                for t in data["todos"]:
                    if t["id"] == tid:
                        t["done"] = not t["done"]
                        break
            elif action == "delete":
                tid = req_json.get("id")
                data["todos"] = [t for t in data["todos"] if t["id"] != tid]
            elif action == "clear_done":
                data["todos"] = [t for t in data["todos"] if not t.get("done", False)]

            save_data(data)
            self._send_json(data)
            return

        elif path == "/api/word":
            action = req_json.get("action")
            if action == "add":
                raw_word = req_json.get("word", "").strip()
                if raw_word:
                    # Look up definition
                    parsed = fetch_word_definition(raw_word)
                    # Put at top, max 6 active words on dashboard
                    data["words"].insert(0, parsed)
                    data["words"] = data["words"][:6] # Up to 6 words for 3x2 grid
            elif action == "random":
                import random
                chosen = random.choice(BUILTIN_WORDS)
                data["words"].insert(0, chosen)
                data["words"] = data["words"][:6]
            elif action == "delete":
                idx = req_json.get("index", 0)
                if 0 <= idx < len(data["words"]):
                    data["words"].pop(idx)

            save_data(data)
            self._send_json(data)
            return

        elif path == "/api/note":
            note = req_json.get("note", "").strip()
            data["note"] = note
            save_data(data)
            self._send_json(data)
            return

        self.send_error(404, "Not Found")

    def _send_json(self, data):
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode("utf-8"))

def run_server(port=8085):
    server = HTTPServer(("127.0.0.1", port), KindleDashboardHandler)
    print(f"Kindle Dashboard Server listening on 127.0.0.1:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()

if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8085
    run_server(port)
