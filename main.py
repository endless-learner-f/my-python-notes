from fastapi.responses import HTMLResponse
import os
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Header
import sqlite3
from pydantic import BaseModel
import requests
import json
from fastapi.responses import StreamingResponse
import jwt
import datetime
load_dotenv()
app = FastAPI()
init_conn = sqlite3.connect("school.db")
init_cursor = init_conn.cursor()
init_cursor.execute('''
CREATE TABLE IF NOT EXISTS users(
    id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    username VARCHAR(50) NOT NULL UNIQUE,
    password VARCHAR(100) NOT NULL)
    ''')
init_conn  = sqlite3.connect("school.db")
init_cursor = init_conn.cursor()
init_cursor.execute("""
    CREATE TABLE IF NOT EXISTS chat_logs(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_msg TEXT,
        ai_msg TEXT
    )
""")
init_conn.commit()
init_conn.close()
@app.get("/")
def  read_root():
    return{"message":"测试成功"}
@app.get("/students")
def get_students(min_age: int = 0):
    conn = sqlite3.connect("school.db")
    cursor = conn.cursor()
    if min_age > 0:
       cursor.execute(f"SELECT  * FROM student WHERE age > {min_age}")
    else:
       cursor.execute("SELECT * FROM student")
    results = cursor.fetchall()
    student_list = []
    for row in results:
        student_dict={
            "id": row[0],
            "name":row[1],
            "age":row[2]
        }
        student_list.append(student_dict)
    conn.close()
    return{"students":student_list}
class Student(BaseModel):
    name: str
    age: int

@app.post("/add_student")
def add_student(student: Student):
    conn =  sqlite3.connect("school.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO student (name,age) VALUES (?,?)",(student.name, student.age))
    conn.commit()
    conn.close()

    return {"message": f"成功添加学生: {student.name}, 年龄: {student.age}"}
@app.delete("/students/{student_id}")
def delete_student(student_id: int):
    conn = sqlite3.connect("school.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM student WHERE id = ?", (student_id,))
    row = cursor.fetchone()
    if row is None:
        conn.close()
        raise HTTPException(status_code=404, detail="你要删除的学生不存在！")
    cursor.execute("DELETE FROM student where id = ?", (student_id,))
    conn.commit()
    conn.close()
    return {"message": f"成功删除学号为 {student_id} 的学生"}
@app.put("/students/{student_id}")
def update_student(student_id: int, student: Student):
    conn = sqlite3.connect("school.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM student WHERE id = ?", (student_id,))
    row = cursor.fetchone()
    if row is None:
        conn.close()
        raise HTTPException(status_code=404, detail="你要修改的学生不存在!")
    cursor.execute("UPDATE student SET name = ?,age = ? WHERE id = ?", (student.name,  student.age, student_id))
    conn.commit()
    conn.close()
    return {"message": f"成功更新学号为 {student_id} 的学生信息"}

class Users(BaseModel):
    username: str
    password: str
@app.post("/register")
def make_count(user:Users):
    conn = sqlite3.connect("school.db")
    cursor = init_conn.cursor()
    cursor.execute(
        "INSERT INTO users (username, password) VALUES (?,?)",
        (user.username, user.password)
    )
    conn.commit()
    conn.close()
    return {"message": "注册成功"}

@app.post("/login")
def login(user: Users):
    conn = sqlite3.connect("school.db")
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM users WHERE username = ? AND password = ?",
        (user.username, user.password)
    )
    result = cursor.fetchone()
    conn.close()
    if result is None:
        raise HTTPException(status_code=401, detail="账号和密码错误")
    else:
        payload = {
            "username": user.username,
            "exp": datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=24)
        }
        token = jwt.encode(payload,  "my_secret_key", algorithm="HS256")
        return {"message": "登录成功", "token": token}

@app.get("/my_secret_data")
def get_secret_data(authorization: str =  Header(None)):
    if authorization is None:
        raise HTTPException(status_code=401, detail="缺少 Token，请先登录！")
    try:
        token = authorization.replace("Bearer ","")
        decoded_data = jwt.decode(token, "my_secret_key", algorithms=["HS256"])
        username = decoded_data.get("username")
        return {"message": f"欢迎回来，尊贵的 {username}, 这是你的绝密数据！"}
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token 已过期，请重新登录！")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="无效的 Token，你是黑客吗？")


@app.get("/students/{student_id}")
def get_one_student(student_id: int):
    conn = sqlite3.connect("school.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM student WHERE id = ?", (student_id,))
    row = cursor.fetchone()
    if row is None:
        conn.close()
        raise HTTPException(status_code=404, detail="找不到这个学生")

    return {"id": row[0], "name": row[1], "age": row[2]}
class ChatRequest(BaseModel):
    message: str
    history: list = []
    persona: str = "你现在是一个极其严厉的AI编程教练。"
@app.post("/chat")
def chat_with_ai(request: ChatRequest, authorization: str = Header(None)):
    if authorization is None:
        raise HTTPException(status_code=401, detail="请先登录才能聊天！")
    try:
        token = authorization.split(" ")[-1]

        print(f"👉 收到的 Token: {token[:20]}...")

        jwt.decode(token, "my_secret_key", algorithms=["HS256"])

    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="登录已过期，请重新登录！")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="无效的 Token！")
    except Exception:
        raise HTTPException(status_code=401, detail="未知的 Token 错误！")
    api_key = os.getenv("DEEPSEEK_API_KEY")
    url = "https://api.deepseek.com/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    messages = [{"role": "system", "content": request.persona}]
    messages.extend(request.history)
    messages.append({"role": "user", "content": request.message})
    data = {
        "model": "deepseek-chat",
        "messages": messages,
        "stream": True
    }

    def generate():
        full_ai_reply = ""

        with requests.post(url, headers=headers, json=data, stream=True) as response:
            for line in response.iter_lines():
                if line:
                    raw_text = line.decode('utf-8').strip()
                    if raw_text.startswith("data: "):
                        text = raw_text[6:]
                        if text != "[DONE]":
                            try:
                                json_data = json.loads(text)
                                choices = json_data.get("choices", [])
                                if choices:
                                    delta = choices[0].get("delta", {})
                                    chunk = delta.get("content", "")
                                    if chunk:
                                        # 👈 2. 每吐出一个碎片，就拼接到完整回复里
                                        full_ai_reply += chunk
                                        yield chunk
                            except Exception as e:
                                print(f"\n❌ 解析崩溃：【{text}】")
                                print(f"❌ 报错：{e}\n")
        if full_ai_reply:
            conn = sqlite3.connect("school.db")
            cursor = conn.cursor()
            cursor.execute("INSERT INTO chat_logs (user_msg, ai_msg) VALUES (?, ?)", (request.message, full_ai_reply))
            conn.commit()
            conn.close()
    return StreamingResponse(generate(), media_type="text/event-stream")


@app.get("/chat_ui", response_class=HTMLResponse)
def chat_ui():
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>我的专属 AI 助手</title>
        <!-- 引入 Markdown 渲染库 -->
        <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
        <style>
            body { font-family: sans-serif; max-width: 500px; margin: 50px auto; background: #f0f2f5; }
            #chat-box { background: white; padding: 20px; border-radius: 10px; height: 400px; overflow-y: scroll; margin-bottom: 10px; }
            .user-msg { text-align: right; color: blue; margin: 10px 0; }
            .ai-msg { text-align: left; color: green; margin: 10px 0; }
            input { width: 80%; padding: 10px; }
            button { padding: 10px; cursor: pointer; }
        </style>
    </head>
    <body>
        <h2>我的专属 AI 助手</h2>

        <!-- 登录面板 -->
        <div id="login-panel" style="margin-bottom: 20px; text-align: center;">
            <input type="text" id="username" placeholder="请输入账号" style="padding: 10px; margin: 5px;">
            <input type="password" id="password" placeholder="请输入密码" style="padding: 10px; margin: 5px;">
            <button onclick="login()" style="padding: 10px; background: blue; color: white;">登录</button>
        </div>

        <!-- 聊天面板（默认隐藏） -->
        <div id="chat-panel" style="display: none;">
            <button onclick="logout()" style="background: gray; color: white; margin-bottom: 10px;">退出登录</button>
            <select id="persona-select" style="margin-bottom: 10px; padding: 5px; width: 100%;">
                <option value="你现在是一个极其严厉的AI编程教练。">暴躁老哥</option>
                <option value="你现在是一个温柔可爱的AI助手。">温柔助手</option>
            </select>

            <div id="chat-box"></div>

            <input type="text" id="msg-input" placeholder="输入你想说的话...">
            <button onclick="sendMessage()">发送</button>
            <button onclick="clearChat()" style="background: red; color: white;">清空</button>
        </div>

        <script>
            let chatHistory = [];

            // 页面加载时，检查本地有没有 Token
            window.onload = function() {
                const token = localStorage.getItem("token");
                if (token) {
                    document.getElementById("login-panel").style.display = "none";
                    document.getElementById("chat-panel").style.display = "block";
                }
            };

            // 登录功能
            async function login() {
                const u = document.getElementById("username").value;
                const p = document.getElementById("password").value;
                const res = await fetch("/login", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ username: u, password: p })
                });

                if (res.ok) {
                    const data = await res.json();
                    localStorage.setItem("token", data.token); 
                    alert("登录成功！");
                    document.getElementById("login-panel").style.display = "none";
                    document.getElementById("chat-panel").style.display = "block";
                } else {
                    alert("账号或密码错误！");
                }
            }

            // 退出登录功能
            function logout() {
                localStorage.removeItem("token");
                location.reload(); // 刷新页面
            }

            // 清空聊天
            function clearChat() {
                chatHistory = [];
                document.getElementById("chat-box").innerHTML = "";
            }

            // 发送消息（流式打字机）
            async function sendMessage() {
                const input = document.getElementById("msg-input");
                const chatBox = document.getElementById("chat-box");
                const msg = input.value;
                if (!msg) return;

                chatHistory.push({"role": "user", "content": msg});
                chatBox.innerHTML += `<div class="user-msg">我: ${msg}</div>`;
                input.value = ""; 
                chatBox.scrollTop = chatBox.scrollHeight;

                const token = localStorage.getItem("token");

                const response = await fetch("/chat", {
                    method: "POST",
                    headers: { 
                        "Content-Type": "application/json",
                        "Authorization": `Bearer ${token}` // 带上 Token
                    },
                    body: JSON.stringify({ 
                        message: msg, 
                        history: chatHistory,
                        persona: document.getElementById("persona-select").value 
                    })
                });

                if (response.status === 401) {
                    alert("登录已过期或无效，请重新登录！");
                    logout();
                    return;
                }

                const aiMsgDiv = document.createElement("div");
                aiMsgDiv.className = "ai-msg";
                aiMsgDiv.innerText = "AI: ";
                chatBox.appendChild(aiMsgDiv);

                const reader = response.body.getReader();
                const decoder = new TextDecoder("utf-8");
                let aiReply = ""; 

                while (true) {
                    const { done, value } = await reader.read();
                    if (done) break;

                    const chunk = decoder.decode(value, { stream: true });
                    aiReply += chunk;

                    aiMsgDiv.innerText = "AI: " + aiReply; // 流式过程纯文本
                    chatBox.scrollTop = chatBox.scrollHeight;
                }

                // 接收完毕后，用 marked 渲染成漂亮的 Markdown
                aiMsgDiv.innerHTML = "AI: " + marked.parse(aiReply);
                chatHistory.push({"role": "assistant", "content": aiReply});
            }
        </script>
    </body>
    </html>
    """
    return html_content