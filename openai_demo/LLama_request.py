import requests


while True:
    input_str = input("please enter sentence:")
    info = {'command':input_str}

    response = requests.post("http://127.0.0.1:5050/",json=info)
    print(f"llama2 result = {response.json()}")