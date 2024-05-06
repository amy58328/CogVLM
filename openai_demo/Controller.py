import paho.mqtt.client as mqtt
import threading
import re

INPUT_COMMAND = None
IMG_PATH = None

def on_connect(client, userdata, flags, rc):
    client.subscribe([("INPUT_COMMAND",2),("IMG_PATH",2)])

# 當接收到從伺服器發送的訊息時要進行的動作
def on_message(client, userdata, msg):
    print(msg.topic+" = "+ str(msg.payload).split('\'')[1])

    if (msg.topic == "INPUT_COMMAND"):
        global INPUT_COMMAND
        INPUT_COMMAND = str(msg.payload).split('\'')[1]

    elif (msg.topic == "IMG_PATH"):
        global IMG_PATH
        IMG_PATH = str(msg.payload).split('\'')[1]
            

client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message
client.username_pw_set("james01","0101xx")
client.connect("140.124.182.78", 1883, 60)

def mqtt_loop():
    client.loop_forever()

mqtt_thread = threading.Thread(target=mqtt_loop)
mqtt_thread.start()

# client.publish("command",INPU)


# INPUT_COMMAND = "[move,[coke can],y"
# IMG_PATH = "../CogVLM testdata/4.png"

from openai_api_request import get_Coordinates

class Command:
    def __init__(self, input_command):
        # verb
        input_command = input_command.split("[")
        self.verb = input_command[1].replace(",","")

        input_command = input_command[2].split("]")

        # direct_list
        # [
        #     {
        #         'name':str,
        #         'coordinate':str,[[x0,y0,x1,y1]]
        #     },
        #     ...
        # ]
        direct_tmp = input_command[0].split(',')
        direct_list= []
        for i in direct_tmp:
            dict = {}
            dict["name"] = i
            dict["coordinate"] = None
            direct_list.append(dict)

        self.direct_list = direct_list
        self.direct_num = len(direct_list)
        

        # indirect_dict
        # {
        #     'assign':bool, 
        #     'name':str,string or ''
        #     'coordinate':str,None or [[x0,y0,x1,y1]]
        # },
        indirect_dict = {}

        indirect_dict['name'] = input_command[1].replace(",","")

        if (indirect_dict['name'] == ''):
            indirect_dict['assign'] = False
        else:
            indirect_dict['assign'] = True

        indirect_dict['coordinate'] = None

        self.indirect_dict = indirect_dict

    def get_direct_coordinate(self,i):
        # get direct object's coordiante
        print(f"name = {i['name']}, coordinate = {i['coordinate']}")

        while not self.check_formate(i['coordinate']):
            coordiante = get_Coordinates(i['name'],IMG_PATH)
            i['coordinate'] = coordiante

    def get_indirect_coordinate(self):
        if not self.indirect_dict['assign']:
            return 
        
        print(f"name = {self.indirect_dict['name']}, coordinate = {self.indirect_dict['coordinate']}")

        while not self.check_formate(self.indirect_dict['coordinate']):
            coordiante = get_Coordinates(self.indirect_dict['name'],IMG_PATH)
            self.indirect_dict['coordinate'] = coordiante

    def check_formate(self, s):
        if (s == None):
            return False
        
        # (-?\d+(\.\d+)?) means number, int or float
        # template = [[x0,y0,x1,y1]]
        template = r'\[\[(-?\d+(\.\d+)?),(-?\d+(\.\d+)?),(-?\d+(\.\d+)?),(-?\d+(\.\d+)?)\]\]'

        return re.match(template,s)

while True:

    while True:
        if INPUT_COMMAND != None and IMG_PATH != None:
            break
    
    command = Command(INPUT_COMMAND)

    for i in command.direct_list: 
        #  get direct coordinate 
        print("get direct coorddinate")
        command.get_direct_coordinate(i)
        print(i)

        print("get indirect coorddinate")
        command.get_indirect_coordinate()
        print(command.indirect_dict)

        # send coordinate to RL
        
        if (command.indirect_dict['assign'] == False):
            send_str = f"({i['coordinate']})"
        else:
            send_str = f"({i['coordinate']},{command.indirect_dict['coordinate']})"

        client.publish('RL',send_str)



    # Destroy command object and refresh the INPUT_COMMAND and IMG_PATH
    print("command done, please enter the next command.")
    print("==============================================")
    del command
    INPUT_COMMAND = None
    IMG_PATH = None

     