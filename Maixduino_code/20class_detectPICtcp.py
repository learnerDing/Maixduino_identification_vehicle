import sensor,image,lcd,time
import KPU as kpu
import socket
import time

########################################################
#network configuration
SSID = "403"
PASW = "zuishuai403"

def enable_esp32():
    from network_esp32 import wifi
    if wifi.isconnected() == False:
        for i in range(5):
            try:
                # Running within 3 seconds of power-up can cause an SD load error
                # wifi.reset(is_hard=False)
                wifi.reset(is_hard=True)
                print('try AT connect wifi...')
                wifi.connect(SSID, PASW)
                if wifi.isconnected():
                    break
            except Exception as e:
                print(e)
    print('network state:', wifi.isconnected(), wifi.ifconfig())

enable_esp32()

ADDR = ("192.168.1.113", 6687)

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect(ADDR)
#sock.settimeout(1)
lcd.init(type=2)
lcd.rotation(2)
#客户端服务端之间建立连接初次对话
while 1:
    try:
        sock.send(b'TE'+"Try to build connection\n")
        data = sock.recv(1024)   #等待回复
    except Exception as e:
        print("receive error:", e)
        continue
    print("addr:", ADDR, "data:", data)
    #lcd.draw_string(0,0,"Connection done!")
    sock.send(b"TE"+"Connection done!\n")  #成功通信之后退出循环进入下一步
    break
######################################################

send_len, count, err = 0, 0, 0
sensor.reset()
sensor.set_pixformat(sensor.RGB565)
sensor.set_framesize(sensor.QVGA)  #分辨率为320*240
#sensor.set_vflip(1) #flip camera; maix go use sensor.set_hmirror(0)
sensor.set_hmirror(1)
sensor.set_vflip(1)
sensor.run(1)
clock = time.clock()
classes = ['aeroplane', 'bicycle', 'bird', 'boat', 'bottle', 'bus', 'car', 'cat', 'chair', 'cow', 'diningtable', 'dog', 'horse', 'motorbike', 'person', 'pottedplant', 'sheep', 'sofa', 'train', 'tvmonitor']
task = kpu.load(0x800000)
anchor = (1.08, 1.19, 3.42, 4.41, 6.63, 11.38, 9.42, 5.11, 16.62, 10.52)
a = kpu.init_yolo2(task, 0.5, 0.3, 5, anchor)

while(True):
    clock.tick()
    if err >= 10:
        print("Too many send failure")
        break
    img = sensor.snapshot()
    code = kpu.run_yolo2(task, img)
    '''返回值说明： 是以下的形式 类型为Python中的list xy表示 矩形框左上角的元素位置，wh表示矩形的宽度和高度
    {"x":158, "y":65, "w":83, "h":111, "value":0.829885, "classid":0, "index":0, "objnum":1}
    识别物体相似度，物体种类（从0开始，比如，人脸，动物脸），物体种类索引（0开始，比如第一张脸，第二张脸），
    一帧图像中检测到物体的数量（图像中几个人脸）
    '''
    if code:
        for i in code:
            a = img.draw_rectangle(i.rect())
            a = lcd.display(img)
            for i in code:
                lcd.draw_string(i.x(), i.y(), classes[i.classid()], lcd.RED, lcd.WHITE)
                lcd.draw_string(i.x(), i.y()+12, '%f1.3'%i.value(), lcd.RED, lcd.WHITE)
    else:
        a = lcd.display(img)
#udp图传，发送的是bytes
    img = img.compress(quality = 60)
    img_bytes = img.to_bytes(img)
    print("send len:",len(img_bytes))
    try:
        block = int(len(img_bytes)/2048)
        send_first = sock.send(b'IM'+img_bytes[0:2048])
        for i in range(1,block):#分包发送
            send_len = sock.send(img_bytes[i*2048:(i+1)*2048])#发送整数段
        send_len2 = sock.send(img_bytes[block*2048:]+b'end')#发送剩下的,end字符表示图片发送结束
        #for i in range(block):#分包发送
            #send_len = sock.sendto(img_bytes[i*2048:(i+1)*2048],ADDR)#发送整数段
        #send_len2 = sock.sendto(img_bytes[block*2048:],ADDR)#发送剩下的,end字符表示图片发送结束
        #send_end = sock.sendto(b'end',ADDR)#发送字节串end代表一张图片发送完毕
        if send_first == 0: #sock.sendto()返回值为发送的字节数
            raise Exception("send fail")
    except OSError as e:
        if e.args[0] == 128:
           print("connection closed")
    except Exception as e:
        print("send fail:",e)
        time.sleep(1)
        err+=1
        continue
    count+=1
    print("send:",count)
    print("fps:",clock.fps())
a = kpu.deinit(task)
print("Sock is going to close...")
sock.close()
