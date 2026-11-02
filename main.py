from fastapi.responses import HTMLResponse
import os
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
import sqlite3
from pydantic import BaseModel
import requests
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
    messages = [
        {"role": "system", "content": "你现在是个极其严厉的AI编程教练。说话一针见血，绝不废话。如果用户问低级问题，直接嘲讽他，然后再告诉他正确答案。"}
    ]
    messages.extend(request.history)
    messages.append({"role": "user", "content": request.message})
    data = {
        "model": "deepseek-chat",
        "messages": messages
    }
    response = requests.post(url, headers=headers, json=data)
    if response.status_code == 200:
        result = response.json()
        ai_reply = result["choices"][0]["message"]["content"]
        conn = sqlite3.connect("school.db")
        cursor = conn.cursor()
        cursor.execute("INSERT INTO chat_logs (user_msg, ai_msg) VALUES (?,?)", (request.message, ai_reply))
        conn.commit()
        conn.close()
        return {"reply": ai_reply}
    else:
        return {"状态码": response.status_code, "化验单": response.text}
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
                    // 1. 在函数最外面建一个全局数组，用来存历史记录
        let chatHistory = [];

        async function sendMessage() {
            const input = document.getElementById("msg-input");
            const chatBox = document.getElementById("chat-box");
            const msg = input.value;
            if (!msg) return;

            // 2. 把你说的话，先装进历史记录里
            chatHistory.push({"role": "user", "content": msg});

            // 显示在屏幕上
            chatBox.innerHTML += `<div class="user-msg">我: ${msg}</div>`;
            input.value = ""; 
            chatBox.scrollTop = chatBox.scrollHeight;

            // 3. 发送给后端（看这里！body 里加上了 history！）
            const response = await fetch("/chat", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ 
                    message: msg, 
                    history: chatHistory // 👈 就是这个！把历史记录一起发过去
                })
            });

            const data = await response.json();
            
            // 4. 拿到 AI 的回复后，也把它装进历史记录里
            chatHistory.push({"role": "assistant", "content": data.reply});

            // 显示在屏幕上
            chatBox.innerHTML += `<div class="ai-msg">AI: ${data.reply}</div>`;
            chatBox.scrollTop = chatBox.scrollHeight;
        }
        </script>
    </body>
    </html>
    """
    return html_content