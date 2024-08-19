import requests
import paho.mqtt.client as mqtt
import threading
import re
import time
import os
from word2number import w2n
from openai_api_request import simple_image_chat
import re
from datetime import datetime

MQTT_IP = "140.124.182.78"
MQTT_PORT = 1883

new_filename = None
fp = None
filesize = None
INPUT_COMMAND = None
IMG_PATH = None
repositioning = False
client = None

def __init__():
    global new_filename,fp,filesize,INPUT_COMMAND,IMG_PATH,VQA_sult


    filesize = 0

    INPUT_COMMAND = None
    IMG_PATH = None
    

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
        global filesize,IMG_PATH,fp,new_filename,repositioning,INPUT_COMMAND,start_time

        if (msg.topic == "INPUT_COMMAND" ):
            print("get message")
            # record machine thinking time
            start_time = datetime.now()
            # if (VQA_sult != None):
            #     ori_command = VQA_sult
            # else:
            ori_command = str(msg.payload).split('\'')[1].strip()

            
            print(f"ori_command = {ori_command}")

            command = f"what is the verbs, direct objects, and indirect objects of this sentence:\n{ori_command}\n"
            response = requests.post("http://127.0.0.1:5050/",json={'command':command})
            print(f"llama2 result = {response.json()}")

            INPUT_COMMAND = response.json()
            # VQA_sult = None

        if (msg.topic == "VQA_result"):
            VQA_sult = str(msg.payload).split('\'')[1].strip()
            print(f"VQA_sult = {VQA_sult}")
            
            IMG_PATH = None
            self.client.publish("INPUT_COMMAND",VQA_sult)


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
                    


                    # self.publish("reposition_p",f"{red_center},{blue_center}")
                    print(f"blue center = {blue_center}, red center = {red_center}")
                    location_point = [blue_center,red_center]
                    print("command done, please enter the next command.")
                    print("==============================================")

        elif msg.topic == "IMG_SIZE":
            # __init__()
            new_filename = os.path.join('./IMG.jpg')
            fp = open(new_filename, 'wb') 
            filesize = int(msg.payload)


        # elif msg.topic == "VQA_result":
        #     global VQA_result

        #     VQA_result = str(msg.payload).split('\'')[1]
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
        # split out all commands
        # remove the {} from the beginning and the end
        input_command = input_command.strip('{}')

        # split out the commands from the input_command
        command_list = input_command.split("],[")

        # remove the [] from the beginning and the end of each command
        commands = [i.strip('[]') for i in command_list]

        # Use dict to wrap each command and store it in list
        command_list = []

        for command in commands:
            
            
            command_split = re.split(r"\[|\]",command)

            # verb
            verb = command_split[0].replace(',','')


            # directs
            directs = command_split[1]
            # direct_list
            # [
            #     {
            #         'name':str,
            #         'center_point':str,[[x0,y0,x1,y1]]
            #     },
            #     ...
            # ]
            direct_list = []
            for d in directs.split(','):
                dict = {}
                dict["name"] = d
                dict["center_point"] = None
                direct_list.append(dict)

            # place
            place = {}
            
            # indirect_dict
            # {
            #     'assign':bool, 
            #     'name':str,string or None
            #     'center_point':str,None or [[x0,y0,x1,y1]]
            # },

            #  has a assign place
            if len(command_split) > 2:
                place["name"] = command_split[2].replace(',','')
                place["assign"] = True
            else:
                place["name"] = None
                place["assign"] = False
            place["center_point"] = None

            # assemble command
            for i in direct_list:
                temp_command = {}
                temp_command["verb"] = verb
                temp_command["direct"] = i
                temp_command["place"] = place
                command_list.append(temp_command)

        self.command_list = command_list

    def get_direct_coordinate(self,i):
        print("get direct center_point")
        print(f"i = {i}")
        # get direct object's coordiante
        # print(f"name = {i['name']}, coordinate = {i['coordinate']}")

        if (i['center_point'] == None ):
            coor = Coordinate(i['name'])
            
            # Pixel coordiante
            i['center_point'] = coor.get_center_coordiante()

            if (i['center_point'] == -1):
                print(f"{i['name']} is not in the image")
                return 

            i['center_point'] = coor.chang_pixel_to_word(i['center_point'])

            if (i['center_point'] == -1):
                print(f"{i['name']} pixel to word fail.")
                return 


    def get_indirect_coordinate(self,i):
        if not i['assign']:
            i['center_point'] = -1
            return 
        
        if (i['center_point'] == None):
            coor = Coordinate(i['name'])
            i['center_point'] = coor.get_center_coordiante()

            if (i['center_point'] == -1):
                print(f"{i['name']} is not in the image")
                return 
            
            i['center_point'] = coor.chang_pixel_to_word(i['center_point'])
            
            if (i['center_point'] == -1):
                print(f"{i['name']} pixel to word fail.")
                return


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

class Coordinate:
    global IMG_PATH

    def __init__(self,item_name=None):
        self.item_name = item_name
        print(F"item name = {item_name}")
    
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

        command = f"Is the sentence {self.item_name} a sentence describing objects?\n"
        describing_object = requests.post("http://127.0.0.1:2020/",json={'command':command}).json()
        print(f"describing_object = {describing_object}")

        need_reasoning = False
        if describing_object == "no":
            need_reasoning = True

        VQA_result = self.item_name
        #  need reasoning or not
        if need_reasoning == True:
            VQA_result = self.VQA(self.item_name.replace(".",""))
            
            if ("divided" in VQA_result):
                VQA_result = VQA_result.split("is")[-1]
                VQA_result = VQA_result.split(".")[0]
                VQA_result = VQA_result.replace("approximately","")

            print(f"the VQA_result is : {VQA_result}")
        # else:
        #     input_question = f"is there any {self.item_name} in the image?"
        #     VQA_result = self.VQA(input_question)

        
        # if ("No" in VQA_result):
        #     return -1
        
        VQA_result = VQA_result.replace("Yes,",'')
        
        # Grounding
        # if need_reasoning == False:
        #     input_question = F"Where is {self.item_name}? answer in [[x0,y0,x1,y1]] format."
        # else:
        input_question = F"Where is {VQA_result}? answer in [[x0,y0,x1,y1]] format."

        Grounding_result = self.Grounding(input_question)
        print(f"the Grounding_result is : {Grounding_result}")

        return Grounding_result
    
    def VQA(self,input_str):
        # print(f"VQA_COMMAND = {input_str}")
        # client.publish("VQA_COMMAND",input_str)
        VQA_result = simple_image_chat(img_path=IMG_PATH, question=input_str,PORT = "8080")

        return VQA_result
    
    def Grounding(self,input_str):
        Grounding_result = simple_image_chat(img_path=IMG_PATH, question=input_str,PORT = "3030")

        return Grounding_result

                  
    def check_formate(self, s):
        if (s == None ):
            return False
        
        if (s == -1):
            return True
        
        # (-?\d+(\.\d+)?) means number, int or float
        # template = [[x0,y0,x1,y1]]
        template = r'\[\[(-?\d+(\.\d+)?),(-?\d+(\.\d+)?),(-?\d+(\.\d+)?),(-?\d+(\.\d+)?)\]\]'

        return re.match(template,s)
    
    def chang_pixel_to_world(self,p):
        p = [int(i) for i in p.strip("()").split(',')]

        imgx = p[0]
        imgy = p[1]


        # blue        
        p1x = 583
        p1y = 413

        # red
        p2x = 705
        p2y = 656

        # blue        
        r1x = 0.55975
        r1y = 0.28234

        # red
        r2x = 0.45706
        r2y = 0.20859

        # defeul
        d_x = 1.5
        d_y = 1.15

        wx = ((imgx-p1x) * (((r2y - r1y)/(p2x - p1x)) * d_x)) + r1y
        wy = ((imgy-p1y) * (((r2x - r1x)/(p2y - p1y)) * d_y)) + r1x

        return f"({wx},{wy})"


def __main__():

    global INPUT_COMMAND,IMG_PATH,client

    client = Client(MQTT_IP,MQTT_PORT,"james01","0101xx",[("INPUT_COMMAND",2),("IMG",2),("IMG_SIZE",2),("Repositioning",2),("VQA_result",2)])
    mqtt_thread = threading.Thread(target=client.loop)
    mqtt_thread.start()

    while True:
        __init__()
        while True:
            if INPUT_COMMAND != None and IMG_PATH != None:
                break


        command = Command(INPUT_COMMAND)

        for single_command in command.command_list:
            print(f"single_command = {single_command}")

            # for i in single_command["direct_list"]: 
                #  get direct coordinate 
                # print("get direct coorddinate")
            command.get_direct_coordinate(single_command['direct'])
            print(single_command['direct'] , "\n")

            if (single_command['direct']['center_point'] == -1):
                print("direct not found, Command Fail.")
                continue
            #client.publish('RL_target_location',)


            # print("get indirect coorddinate")
            command.get_indirect_coordinate(single_command["place"])
            print(single_command["place"], "\n")
            if (single_command['place']['assign'] == True and single_command['place']['center_point'] == -1):
                print("Indirect not found, Command Fail.")
                continue

            client.publish('RL_target_location',f"({single_command['direct']['center_point']},{single_command['place']['center_point']})")
       
        stop_time = datetime.now()
        different_time = (stop_time - start_time).total_seconds()
        client.publish("machine thinking time",f"{different_time}")



        # Destroy command object and refresh the INPUT_COMMAND and IMG_PATH
        print("command done, please enter the next command.")
        print("==============================================")
        del command
        INPUT_COMMAND = None
        IMG_PATH = None

__main__()
