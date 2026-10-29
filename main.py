from fastapi import FastAPI
import sqlite3

app = FastAPI()

@app.get("/")
def  read_root():
    return {"message":  "测试成功"}

@app.get("/student")
def get_students():
    conn = sqlite3.connect("school.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM student")
    results = cursor.fetchall()
    student_list = []
    for row in results:
        student_dict  = {
            "id": row[0],
            "name": row[1],
            "age": row[2]
        }
        student_list.append(student_dict)
    conn.close()
    return{"students": student_list}