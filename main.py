from fastapi.responses import HTMLResponse
import os
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
import sqlite3
from pydantic import BaseModel
import requests
import json
from fastapi.responses import StreamingResponse
load_dotenv()
app = FastAPI()
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
@app.post("/chat")
def chat_with_ai(request: ChatRequest):
    api_key = os.getenv("DEEPSEEK_API_KEY")
    url = "https://api.deepseek.com/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    messages = [{"role": "system", "content": "你现在是个极其严厉的AI编程教练。说话一针见血，绝不废话。如果用户问低级问题，直接嘲讽他，然后再告诉他正确答案。"}]
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
        <div id="chat-box"></div>
        <input type="text" id="msg-input" placeholder="输入你想说的话...">
        <button onclick="sendMessage()">发送</button>

                <script>
            // 1. 建个全局数组，当记忆库
            let chatHistory = [];

            async function sendMessage() {
                const input = document.getElementById("msg-input");
                const chatBox = document.getElementById("chat-box");
                const msg = input.value;
                if (!msg) return;

                // 2. 把你发的话存进记忆库，并显示在屏幕上
                chatHistory.push({"role": "user", "content": msg});
                chatBox.innerHTML += `<div class="user-msg">我: ${msg}</div>`;
                input.value = ""; 
                chatBox.scrollTop = chatBox.scrollHeight;

                // 3. 发送请求给后端
                const response = await fetch("/chat", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ 
                        message: msg, 
                        history: chatHistory 
                    })
                });

                // 4. 建一个空的 AI 聊天气泡，先不打字
                const aiMsgDiv = document.createElement("div");
                aiMsgDiv.className = "ai-msg";
                aiMsgDiv.innerText = "AI: ";
                chatBox.appendChild(aiMsgDiv);
                
                // 5. 像吸管一样，接收流式数据
                const reader = response.body.getReader();
                const decoder = new TextDecoder("utf-8");
                let aiReply = ""; // 用来存最终完整的回复

                while (true) {
                    const { done, value } = await reader.read();
                    if (done) break;
                    
                    // 解码吐出来的字，拼接到总回复里
                    const chunk = decoder.decode(value, { stream: true });
                    aiReply += chunk;
                    
                    // 实时更新到网页上，这就产生了“打字机”效果
                    aiMsgDiv.innerText = "AI: " + aiReply;
                    chatBox.scrollTop = chatBox.scrollHeight;
                }

                // 6. 全部接收完后，把 AI 的完整回复存进记忆库
                chatHistory.push({"role": "assistant", "content": aiReply});
            }
        </script>
    </body>
    </html>
    """
    return html_content