from fastapi.responses import HTMLResponse, StreamingResponse, FileResponse
import bcrypt
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
    cursor = conn.cursor()
    hashed_password = bcrypt.hashpw(user.password.encode('utf-8'), bcrypt.gensalt())
    try:
        cursor.execute(
            "INSERT INTO users (username, password) VALUES (?,?)",
            (user.username, hashed_password.decode('utf-8'))
        )
        conn.commit()
        return {"message": "注册成功"}
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=400, detail="该用户名已被注册！")
    finally:
        conn.close()



@app.post("/login")
def login(user: Users):
    conn = sqlite3.connect("school.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username = ?", (user.username,))
    result = cursor.fetchone()
    conn.close()
    if result is None:
        raise HTTPException(status_code=401, detail="账号不存在")
    db_hashed_password = result[2]
    if not bcrypt.checkpw(user.password.encode('utf-8'), db_hashed_password.encode('utf-8')):
        raise HTTPException(status_code=401, detail="密码错误！")
    payload = {
        "username":user.username,
        "exp": datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=24)
    }
    token = jwt.encode(payload, "my_secret_key", algorithm="HS256")
    return {"message": "登录成功", "token": token}

@app.get("/my_secret_data")
def get_secret_data(authorization: str =  Header(None)):
    if authorization is None:
        raise HTTPException(status_code=401, detail="缺少 Token，请先登录！")
    try:
        token = authorization.split(" ")[-1]
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
    return FileResponse("index.html")