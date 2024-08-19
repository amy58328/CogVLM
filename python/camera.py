# from openni import openni2
import numpy as np
import cv2
import paho.mqtt.client as mqtt
import threading
import time
import os

MQTT_IP = "140.124.182.78"
MQTT_PORT = 1883


# def mousecallback(event,x,y,flags,param):
#      if event==cv2.EVENT_LBUTTONDBLCLK:
#          print(y, x, dpt[y,x])

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

    def on_message(self,client, userdata, msg):
        global frame

        print(msg.topic+" = "+ str(msg.payload).split('\'')[1])

        if (msg.topic == "INPUT_COMMAND"  or msg.topic == "Repositioning" or msg.topic == "VQA_COMMAND"):
            global frame,depth

            cv2.imwrite("./temp.jpg",frame)
            # cv2.imwrite("./temp_dpeth.jpg",depth)
            sendIMG()


    def publish(self,topic,send_str):
        self.client.publish(topic,send_str)
    
    def loop(self):
        self.client.loop_forever()
    
    
def sendIMG():
    filepath = "temp.jpg"
    fp = open(filepath, 'rb')
    filesize=os.stat(filepath).st_size
    client.publish('IMG_SIZE', filesize)
    time.sleep(3)

    re_size=0
    while 1:
        if filesize - re_size >= 1024:  #文件切片，大小可自定义，视情况而定
            data = fp.read(1024)
            re_size += 1024
        else:
            data = fp.read(filesize -  re_size)
            print(len(data))
        if not data:
            print ('{0} file send over...'.format(filepath))
            print('')
            break
        print("send to mqtt")
        client.publish('IMG', data)

def RBG_camera():
    global frame
    ret,frame = cap.read()

    cv2.imshow("Camera",frame)

def Depth_camera():
    global depth
    frame = depth_stream.read_frame()
    dframe_data = np.array(frame.get_buffer_as_triplet()).reshape([480, 640, 2])
    dpt1 = np.asarray(dframe_data[:, :, 0], dtype='float32')
    dpt2 = np.asarray(dframe_data[:, :, 1], dtype='float32')
    
    dpt2 *= 255
    depth = dpt1 + dpt2
    
    cv2.imshow('depth', depth)
    

if __name__ == "__main__": 
    ## MQTT
    client = Client(MQTT_IP,MQTT_PORT,"james01","0101xx",[("INPUT_COMMAND",2),("VQA_COMMAND",2),("Repositioning",2)])
    mqtt_thread = threading.Thread(target=client.loop)
    mqtt_thread.daemon = True
    mqtt_thread.start()


    # RBG
    # camera_number = input("please input the number of camera:")
    cap = cv2.VideoCapture(0)

    # Depth
    # openni2.initialize()

    # dev = openni2.Device.open_any()
    # print(dev.get_device_info())

    # depth_stream = dev.create_depth_stream()
    # depth_stream.start()

    # cv2.namedWindow('depth')
    # cv2.setMouseCallback('depth',mousecallback)
    i = 1
    while True:
        RBG_camera()
        # Depth_camera()


        key = cv2.waitKey(1)
        if int(key) == ord('q'):
            break

        if int(key) == ord("s"):
            cv2.imwrite(f"./img{i}.jpg",frame)
            print(f"save img{i}.jpg")
            i += 1

    cap.release()
    cv2.destroyAllWindows()