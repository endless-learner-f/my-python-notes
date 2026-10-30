from fastapi import FastAPI
import sqlite3
from pydantic import BaseModel
app = FastAPI()
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
    cursor.execute("DELETE FROM student where id = ?", (student_id,))
    conn.commit()
    conn.close()
    return {"message": f"成功删除学号为 {student_id} 的学生"}
@app.put("/students/{student_id}")
def update_student(student_id: int, student: Student):
    conn = sqlite3.connect("school.db")
    cursor = conn.cursor()
    cursor.execute("UPDATE student SET name = ?,age = ? WHERE id = ?", (student.name,  student.age, student_id))
    conn.commit()
    conn.close()

    return {"message": f"成功更新学号为 {student_id} 的学生信息"}