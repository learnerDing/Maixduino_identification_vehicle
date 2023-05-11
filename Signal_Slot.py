from PyQt5 import QtWidgets, QtGui, QtCore
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtWidgets import *
from PyQt5.QtCore import QThread
from UI_myui import Ui_MainWindow
import sys, cv2, socket,serial
import numpy as np

ip = "192.168.1.113"
port = 9999

class ReceiverThread(QThread):
    def __init__(self, sock, display_received_message, receive_picture, set_low_ip_port):
        super().__init__()
        self.sock = sock
        self.display_received_message = display_received_message
        self.receive_picture = receive_picture
        self.set_low_ip_port = set_low_ip_port
        self.flag_run = 0

    def run(self):
        buffer = b""
        while True:
            try:
                data, addr = self.sock.recvfrom(4096)  # 接收数据
                self.set_low_ip_port(addr)  # 设置发送方的ip和端口信息

                if data[-3:] == b'end':
                    buffer += data[:-3]
                    if self.flag_run:
                        self.receive_picture(buffer)  # 调用 receive_picture 方法处理图像数据
                        buffer = b""  # 清空缓冲区以便接收下一张图片
                elif data[:4] == b'\xff\xd8' and data[-2:] == b'\xff\xd9':#此时说明图片包是完整的
                    self.receive_picture(data)
                else:
                    try:
                        text_data = data.decode("utf-8")
                        self.display_received_message(text_data, addr[0], addr[1])
                    except UnicodeDecodeError:
                        buffer += data
            except socket.timeout:
                pass
            except Exception as e:
                print(f"Error while receiving data: {e}")
                break


class MainWindow(QtWidgets.QMainWindow, Ui_MainWindow):
    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)
        self.setupUi(self)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # Start the receiver thread
        self.receive_data_thread = ReceiverThread(
            self.sock, self.display_received_message, self.receive_picture, self.set_low_ip_port)
        self.receive_data_thread.start()
        self.sock.bind((ip, port))

        # 设置窗口属性
        self.setFixedSize(self.size())  # 使窗口大小固定为设计时的大小
        self.setWindowIcon(QtGui.QIcon("Resource/Icon/跑车.png"))  # 设置窗口图标
        self.setWindowTitle("识别小车上位机")  # 设置窗口标题



        # Connect signals to slots
        self.Sendmssg.clicked.connect(self.send_message)
        self.save_pic.clicked.connect(self.save_picture)
        self.btn_suspend.clicked.connect(self.stop_display)
        self.Run_model.clicked.connect(self.Run_flag)
        # 修改QDial组件的信号与move_steer槽函数相连接
        self.dial.valueChanged.connect(lambda value: self.move_steer(value))
        # Initialize other variables and settings
        self.low_ip = ""
        self.low_port = 0

    def Run_flag(self):
        self.receive_data_thread.flag_run = True

    def display_received_message(self, message, sender_ip, sender_port):
        self.mssg_rec.setText(message)
        self.Lower_ipED.setText(f"{sender_ip}:{sender_port}")

    def set_low_ip_port(self, addr):
        self.low_ip = addr[0]
        self.low_port = addr[1]

    def send_message(self):
        message = self.mssg_sed.text()
        address = (self.low_ip, self.low_port)
        try:
            # 向下位机发送消息
            self.sock.sendto(message.encode(), address)
            print("Message sent:", message)
        except Exception as e:
            print("Error sending message:", e)

    def receive_picture(self, buffer):
        # 在PIC_show中显示图片
        # 将字节串数据解码为 QImage 对象
        qimage = QImage.fromData(buffer, "JPEG")

        # 如果解码成功，将 QImage 对象转换为 QPixmap 并在 Pic_show 标签上显示图像
        if not qimage.isNull():
            pixmap = QPixmap.fromImage(qimage)
            self.PIC_Show.setPixmap(pixmap)
            self.PIC_Show.setScaledContents(True)
        else:
            print("Failed to decode image data.")

    def save_picture(self):
        # 保存当前显示的图片到指定文件夹
        # ...
        pass

    def stop_display(self):
        # flag_run置0
        # 停止图片显示
        self.receive_data_thread.flag_run = False

    #以下是控制stm32小车运动的代码
    def keyPressEvent(self, event):
        key = event.key()
        if key == QtCore.Qt.Key_Up:
            self.move_up()
        elif key == QtCore.Qt.Key_Down:
            self.move_down()
        elif key == QtCore.Qt.Key_Left:
            self.move_left()
        elif key == QtCore.Qt.Key_Right:
            self.move_right()

    def move_up(self):
        # 发送向上移动的指令
        command = "Mu"
        self.send_command_to_stm32(command)

    def move_down(self):
        # 发送向下移动的指令
        command = "Md"
        self.send_command_to_stm32(command)

    def move_left(self):
        # 发送向左移动的指令
        command = "Ml"
        self.send_command_to_stm32(command)

    def move_right(self):
        # 发送向右移动的指令
        command = "Mr"
        self.send_command_to_stm32(command)
    #控制舵机组件转动
    def move_steer(self, angle):
        data = f"a{angle}"
        # 向下位机发送角度
        self.ser.write((data + "\r\n").encode())
        print("Steer angle sent:", angle)

    def SerialInit(self):
        self.ser = serial.Serial()
        self.ser.baudrate = 115200
        self.ser.port = 'COM1'
        self.ser.open()
        #先发送一个命令让舵机回正  angle180度
        self.ser.write("a180\r\n".encode())

    def send_command_to_stm32(self, command):
        # 通过串口发送指令给STM32单片机
        # 替换为您的串口通信实现
        # 示例:
        # stm32_serial.write((command + "\r\n").encode())  # 发送指令为字符串
        self.SerialInit()
        try:
            self.ser.write(command+"\r\n".encode())#发送指令
        except Exception as e:
            print("Error sending command",e)

if __name__ == "__main__":
    app = QtWidgets.QApplication([])
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())