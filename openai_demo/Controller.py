import requests
import paho.mqtt.client as mqtt
import threading
import re
import numpy as np
import cv2
import time
import os
from word2number import w2n
from openai_api_request import simple_image_chat


MQTT_IP = "140.124.182.78"
MQTT_PORT = 1883

new_filename = None
fp = None
filesize = None
INPUT_COMMAND = None
IMG_PATH = None
repositioning = False


def __init__():
    global new_filename,fp,filesize,INPUT_COMMAND,IMG_PATH,repositioning

    new_filename = os.path.join('./IMG.jpg')
    fp = open(new_filename, 'wb') 
    filesize = 0

    INPUT_COMMAND = None
    IMG_PATH = None
    repositioning = False
    

class Client:
    def __init__(self,IP,PORT,AC,PW,sub_list):
        self.client = mqtt.Client()
        self.client.username_pw_set(AC,PW)
        self.client.connect(IP,PORT)

        self.sub_list = sub_list
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message

    def on_connect(self, client, userdata, flags, rc):
        self.client.subscribe(self.sub_list)

    def on_message(self, client, userdata, msg):
        global filesize,IMG_PATH,repositioning,fp

        if (msg.topic == "INPUT_COMMAND"):
            print("get message")
            __init__()

            ori_command = str(msg.payload).split('\'')[1]
            print(f"ori_command = {ori_command}")

            info = {'command':ori_command}
            response = requests.post("http://127.0.0.1:5050/",json=info)
            print(f"llama2 result = {response.json()}")

            global INPUT_COMMAND
            INPUT_COMMAND = response.json()

        elif msg.topic == "IMG":
            fp.write(msg.payload)

            # IMG reception completed
            if fp.tell() >= filesize:


                print('get IMG')
                fp.close()
                time.sleep(1)

                IMG_PATH = new_filename
                
                if repositioning == True:
                    repositioning = False

                    # __init__()
                    coor = Coordinate()

                    input_question = F"Where is one of the the red point? answer in [[x0,y0,x1,y1]] format."
                    red_position = coor.Grounding(input_question)
                    red_center = coor.Cal_center_point(red_position)

                    input_question = F"Where is one of the the blue point? answer in [[x0,y0,x1,y1]] format."
                    blue_position = coor.Grounding(input_question)
                    blue_center = coor.Cal_center_point(blue_position)
                    


                    self.publish("reposition_p",f"{red_center},{blue_center}")
                    print(f"red center = {red_center}, blue center = {blue_center}")
                  




        elif msg.topic == "IMG_SIZE":
            filesize = int(msg.payload)

            # __init__()


        elif msg.topic == "Repositioning":
            __init__()

            repositioning = True
            print("Respositioning")
            


    def publish(self,topic,send_str):
        self.client.publish(topic,send_str)

    def loop(self):
        self.client.loop_forever()

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
            dict["center_point"] = None
            direct_list.append(dict)

        self.direct_list = direct_list
        # self.direct_num = len(direct_list)
        

        # indirect_dict
        # {
        #     'assign':bool, 
        #     'name':str,string or ''
        #     'coordinate':str,None or [[x0,y0,x1,y1]]
        # },
        indirect_dict = {}

        indirect_dict['name'] = self.wordTonumber(input_command[1].replace(",",""))

        if (indirect_dict['name'] == ''):
            indirect_dict['assign'] = False
        else:
            indirect_dict['assign'] = True

        indirect_dict['center_point'] = None

        self.indirect_dict = indirect_dict

    def get_direct_coordinate(self,i):
        print("get direct center_point")
        # get direct object's coordiante
        # print(f"name = {i['name']}, coordinate = {i['coordinate']}")

        if (i['center_point'] == None):
            coor = Coordinate(i['name'])
            i['center_point'] = coor.get_center_coordiante()

            if (i['center_point'] == -1):
                print(f"{i['name']} is not in the image")

        # while not self.check_formate(i['coordinate']):


        #     coordiante = self.get_coordinate(i['name'])

        #     i['coordinate'] = coordiante

        #     if (coordiante == -1):
        #         print(f"{i['name']} is not in the image")
        #         break


    def get_indirect_coordinate(self):
        if not self.indirect_dict['assign']:
            return 
        
        if (self.indirect_dict['center_point'] == None):
            coor = Coordinate(self.indirect_dict['name'])
            self.indirect_dict['center_point'] = coor.get_center_coordiante()

            if (self.indirect_dict['center_point'] == -1):
                print(f"{self.indirect_dict['name']} is not in the image")

        # while not self.check_formate(self.indirect_dict['coordinate']):

        #     coordiante = self.get_coordinate(self.indirect_dict['name'])

        #     self.indirect_dict['coordinate'] = coordiante

        #     if (coordiante == -1):
        #         print(f"{self.indirect_dict['name']} is not in the image")
        #         break

    # def check_formate(self, s):
    #     if (s == None):
    #         return False
        
    #     # (-?\d+(\.\d+)?) means number, int or float
    #     # template = [[x0,y0,x1,y1]]
    #     template = r'\[\[(-?\d+(\.\d+)?),(-?\d+(\.\d+)?),(-?\d+(\.\d+)?),(-?\d+(\.\d+)?)\]\]'

    #     return re.match(template,s)

    def wordTonumber(self,ori_str):
        if (ori_str == ""):
            return ""
        
        ori_str = ori_str.replace("add","+")
        ori_str = ori_str.replace("minus","-")
        ori_str = ori_str.replace("times","*")
        ori_str = ori_str.replace("divided by","/")

        temp_list = []
        for i in ori_str.split(' '):
            try:
                temp_list.append(str(w2n.word_to_num(i)))
            except ValueError:
                temp_list.append(i)

        return " ".join(temp_list) + "."
    
    # def get_coordinate(self,ori_narrate):
    #     #  need reasoning or not
    #     if len(ori_narrate)> 15:
    #         VQA_result = simple_image_chat(img_path=IMG_PATH, question=ori_narrate,PORT = "8080")

    #         VQA_result = VQA_result.split('is')[-1].split(".")[0]
    #     else:
    #         VQA_result = ori_narrate
    #     print(f"the VQA_result is : {VQA_result}")

    #     # check if exist
    #     input_question = f"is there any {VQA_result} in the image?"
    #     Exist_result = simple_image_chat(img_path=IMG_PATH, question=input_question,PORT = "8080")
    #     if ("No" in Exist_result):
    #         return -1
    #     print(f"the Exist_result is : {Exist_result}")
        
        
    #     # Grounding
    #     if (" is " in Exist_result):
    #         input_question = F"Where is {VQA_result}? answer in [[x0,y0,x1,y1]] format."
    #     else:
    #         input_question = F"Where is one of the {VQA_result}? answer in [[x0,y0,x1,y1]] format."

    #     Grounding_result = simple_image_chat(img_path=IMG_PATH, question=input_question,PORT = "3030")
    #     print(f"the Grounding_result is : {Grounding_result}")

    #     return Grounding_result
    
    # def Cal_center_point(self,coordantes):
    #     coordantes = coordantes.replace("[","").replace("]","")
    #     a = [int(i) for i in coordantes.split(',')]
    #     c_x = int((a[0]+a[2])/2)
    #     c_y = int((a[1]+a[3])/2)
    #     return f"({c_x},{c_y})"

class Coordinate:
    global IMG_PATH

    def __init__(self,item_name=None):
        self.item_name = item_name
    
    def get_center_coordiante(self):
        bounding_coordinate = None

        #  get the two coordinate of the selected object
        while not self.check_formate(bounding_coordinate):
            bounding_coordinate = self.get_item_Bounding_coordinate()

        if (bounding_coordinate == -1):
            return -1
        
        # get the center point of two coordiante
        center_point = self.Cal_center_point(bounding_coordinate)

        return center_point
        
    def Cal_center_point(self,coordantes):
        coordantes = coordantes.strip('[]')
        a = [int(i) for i in coordantes.split(',')]
        c_x = int((a[0]+a[2])/2)
        c_y = int((a[1]+a[3])/2)
        return f"({c_x},{c_y})"
    
    def get_item_Bounding_coordinate(self):

        ori_narrate = self.item_name

        #  need reasoning or not
        if len(ori_narrate)> 15:
            VQA_result = self.VQA(ori_narrate)

            VQA_result = VQA_result.split('is')[-1].split(".")[0]
        else:
            VQA_result = ori_narrate
        print(f"the VQA_result is : {VQA_result}")

        # check if exist
        input_question = f"is there any {VQA_result} in the image?"
        Exist_result = self.VQA(input_question)
        if ("No" in Exist_result):
            return -1
        print(f"the Exist_result is : {Exist_result}")
        
        
        # Grounding
        if (" is " in Exist_result):
            input_question = F"Where is {VQA_result}? answer in [[x0,y0,x1,y1]] format."
        else:
            input_question = F"Where is one of the {VQA_result}? answer in [[x0,y0,x1,y1]] format."

        Grounding_result = self.Grounding(input_question)
        print(f"the Grounding_result is : {Grounding_result}")

        return Grounding_result
    
    def VQA(self,input_str):
        VQA_result = simple_image_chat(img_path=IMG_PATH, question=input_str,PORT = "8080")

        return VQA_result
    
    def Grounding(self,input_str):
        Grounding_result = simple_image_chat(img_path=IMG_PATH, question=input_str,PORT = "3030")

        return Grounding_result

                  
    def check_formate(self, s):
        if (s == None):
            return False
        
        # (-?\d+(\.\d+)?) means number, int or float
        # template = [[x0,y0,x1,y1]]
        template = r'\[\[(-?\d+(\.\d+)?),(-?\d+(\.\d+)?),(-?\d+(\.\d+)?),(-?\d+(\.\d+)?)\]\]'

        return re.match(template,s)

def __main__():

    __init__()
    global INPUT_COMMAND,IMG_PATH,client

    client = Client(MQTT_IP,MQTT_PORT,"james01","0101xx",[("INPUT_COMMAND",2),("IMG",2),("IMG_SIZE",2),("Repositioning",2)])
    mqtt_thread = threading.Thread(target=client.loop)
    mqtt_thread.start()
    while True:

        while True:
            if INPUT_COMMAND != None and IMG_PATH != None:
                break
        
        command = Command(INPUT_COMMAND)

        for i in command.direct_list: 
            #  get direct coordinate 
            # print("get direct coorddinate")
            command.get_direct_coordinate(i)
            print(i , "\n")

            # print("get indirect coorddinate")
            command.get_indirect_coordinate()
            print(command.indirect_dict, "\n")

            # send coordinate to RL
            if (command.indirect_dict['assign'] == False):
                send_str = f"({i['center_point']})"
            else:
                send_str = f"({i['center_point']},{command.indirect_dict['center_point']})"

            client.publish('RL',send_str)



        # Destroy command object and refresh the INPUT_COMMAND and IMG_PATH
        print("command done, please enter the next command.")
        print("==============================================")
        del command
        INPUT_COMMAND = None
        IMG_PATH = None

__main__()
