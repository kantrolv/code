
import requests

def test_api():
    url = "http://127.0.0.1:5000/analyze"
    data = {"code": "print('hello world')"}

    response = requests.post(url, json=data)
    print(response.json())
