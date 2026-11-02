import sqlite3
conn = sqlite3.connect("school.db")
cursor  = conn.cursor()
cursor.execute("SELECT * FROM chat_logs")
results = cursor.fetchall()
print("----历史聊天记录----")
for row in results:
    print(f"编号: {row[0]} | 用户: {row[1]} | AI: {row[2]} ")
    conn.close()