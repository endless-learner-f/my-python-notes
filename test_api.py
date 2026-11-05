import requests

# 1. 先登录拿 Token
login_url = "http://127.0.0.1:8000/login"
login_data = {"username": "admin", "password": "123456"}
login_response = requests.post(login_url, json=login_data)

# 提取出 token
token = login_response.json().get("token")
print("拿到的 Token:", token)

# 2. 带着 Token 去请求绝密数据
data_url = "http://127.0.0.1:8000/my_secret_data"
headers = {
    "Authorization": f"Bearer {token}"  # 注意这里是 Bearer + 空格 + token
}

data_response = requests.get(data_url, headers=headers)
print("状态码:", data_response.status_code)
print("返回结果:", data_response.json())