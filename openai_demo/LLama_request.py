import requests


while True:
    input_type = input("please enter the question type. 1: sentence split, 2:word reasoning.\n")
    
    input_str = input("please enter sentence:")
    PORT = None

    if input_type == '1':
        input_str = f"what is the verbs, direct objects, and indirect objects of this sentence:\n{input_str}\n"
        PORT = 5050
    # elif input_type == '2':
    #     input_str  =  f"What is the point of this paragraph:{input_str}?\n"

    elif input_type == '2':
        input_str  =  f"Is the sentence {input_str} a sentence describing objects?\n"
        PORT = 2020
    else: 
        print("wrong question type")
        continue

    # input_str = f"what are the verbs, direct objects, and indirect objects of this text:\n{input_str}\n"
    # input_str = f"Is the sentence \"{input_str}\" a description of a specific object?\n"

    info = {'command':input_str}

    response = requests.post(f"http://127.0.0.1:{PORT}/",json=info)
    print(f"llama2 result = {response.json()}")