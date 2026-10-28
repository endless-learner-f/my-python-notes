import sqlite3

# 1. 连上数据库（建仓库，文件名叫 school.db）
conn = sqlite3.connect("school.db")
cursor = conn.cursor()

# 2. 建表 （学校今天交的逻辑，设主键，自增，不能为空）
cursor.execute("""
    CREATE TABLE IF NOT EXISTS student (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(20) NOT NULL,
    age INT
    )
""")

# 3. INSERT (增): 赛三个同学进去
cursor.execute("INSERT INTO student (name, age) VALUES ('张三', 18)")
cursor.execute("INSERT INTO student (name, age) VALUES ('李四', 19)")
cursor.execute("INSERT INTO student (name, age) VALUES ('王五', 20)")
conn.commit()

# 4. SELECT (查): 把刚才塞进去的人全部查出来
cursor.execute("SELECT * FROM  student")
results = cursor.fetchall()
print("---- 查到的所有学生----")
for row in results:
    print(f"学号: {row[0]}, 姓名: {row[1]}, 年龄: {row[2]}")

#  5. UPDATE (改): 把李四的年龄改成 25
cursor.execute("UPDATE student SET age = 25 WHERE  name = '李四'")
conn.commit()

# 6. 再次查: 单独查一下李四，看看改了没
cursor.execute("SELECT * FROM student WHERE name = '李四'")
lisi = cursor.fetchone()
print("----李四的最新消息----")
print(f"姓名: {lisi[1]}, 修改后的年龄: {lisi[2]}")

# 7. 关闭连接
conn.close()
