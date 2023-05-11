# 导入模块
import sys
import socket
import threading
from PyQt5 import QtWidgets, QtGui, QtCore
from PyQt5.QtWidgets import QMainWindow

# 假设您的图形界面类为Ui_MainWindow，将其导入
from UI_myui import Ui_MainWindow


# 更新的MainWindow类
class MainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)
        self.setupUi(self)
        #设置窗户大小固定为初始尺寸
        self.setFixedSize(self.size())

        # 初始化并启动接收线程类
        self.receive_thread = ReceiveThread()
        #信号与槽函数绑定
        #接收数据线程绑定
        self.receive_thread.image_data.connect(self.update_image)#image_data为信号（也是接收到的图片信息）
        self.receive_thread.msg_data.connect(self.display_text)
        self.receive_thread.ip_signal.connect(self.Low_ip_show)#用Low_ip_show来接收发送来的地址信息
        self.receive_thread.start()
        #主线程（窗口线程）绑定
        self.Sendmssg.clicked.connect(self.on_Sendmssg_clicked)

    def update_image(self, img_data):
        # 将收到的img_data转换为QPixmap并显示在QLabel上
        pixmap = QtGui.QPixmap.fromImage(img_data)
        self.PIC_Show.setPixmap(pixmap.scaled(self.PIC_Show.size(), QtCore.Qt.KeepAspectRatio))

        '''首先，使用QtGui.QPixmap.fromImage(img_data)将img_data转换为QtGui.QPixmap对象，并将结果赋值给变量pixmap。
        QtGui.QPixmap.fromImage()是一个静态方法，接受一个QtGui.QImage对象作为输入，并返回对应的QtGui.QPixmap对象。
        
        接下来，通过调用pixmap.scaled(self.PIC_Show.size(), QtCore.Qt.KeepAspectRatio)对pixmap进行缩放操作。
        pixmap.scaled()方法接受一个目标大小和缩放模式作为参数，并返回一个按照指定大小和模式缩放后的新的QtGui.QPixmap对象。
        
        在这里，目标大小为self.PIC_Show.size()，即self.PIC_Show控件的大小，而缩放模式为QtCore.Qt.KeepAspectRatio，表示保持图像的纵横比进行缩放。
        最后,通过调用self.PIC_Show.setPixmap(pixmap)，将缩放后的图像设置为self.PIC_Show控件的Pixmap，从而在界面上显示出来。'''

    def display_text(self,text):
        #将收到的文字信息追加展示在QTextBrowser上面
        self.mssg_rec.append(text)
    def Low_ip_show(self,Tpl_Low_ip):
        self.My_low_ip = Tpl_Low_ip  #将Tql_Low_ip设置为类的属性，其他方法也可以访问到它
        self.Lower_ipED.setText(str(Tpl_Low_ip))#展示下位机ip地址和端口

    def on_Sendmssg_clicked(self):
        # 获取 mssg_sed 文本编辑器里的文字
        text_to_send = self.mssg_sed.text()
        # 将获取到的文本发送给接收线程
        self.receive_thread.send_message(text_to_send)




#接收udp数据线程
class ReceiveThread(QtCore.QThread):

    #这是信号，用于向主进程发送信息
    image_data = QtCore.pyqtSignal(QtGui.QImage)#发送图片信息
    msg_data = QtCore.pyqtSignal(str)#发送文字信息
    ip_signal = QtCore.pyqtSignal(tuple)#发送下位机ip地址，地址信息是一个tuple eg.('192.168.1.113',9999)
    #增加一个信号send_text_content
    send_text_content = QtCore.pyqtSignal(str)

    def __init__(self, parent=None):
        super(ReceiveThread, self).__init__(parent)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        #连接信号send_text_content到send_udp_message槽函数
        self.send_text_content.connect(self.send_udp_message)

    def send_message(self,message):
        self.send_text_content.emit(message)

    def run(self):
        # 上位机ip地址和端口
        ADDR = ('192.168.1.113', 8080)
        self.sock.bind(ADDR)
        while True:
            data, self.Low_addr = self.sock.recvfrom(2048)
            self.ip_signal.emit(self.Low_addr)#将Low_addr信号发送给主进程
            if data.startswith(b"IMG:"):
                img_data = b""
                print("接收到IMG:作为开头的信息")
                data = data[4:]  # 去掉“IMG:”标志
                while data != b'end':
                    img_data += data
                    data, self.Low_addr = self.sock.recvfrom(2048)#如果不是以end结尾，则继续接收
                # 对图片数据进行完整性检查
                try:
                    img = QtGui.QImage.fromData(img_data)
                    #QtGui.QImage.fromData()是一个静态方法，它接受一个字节流作为输入，并返回一个QtGui.QImage对象。
                    if img.isNull():
                        print("Incomplete image data received.")
                        continue
                except Exception as e:
                    print("Error decoding image data:", e)
                    continue

                # 发送img_data信号到主窗口类
                self.image_data.emit(img)
            #TEXT开头的说明是文字信息
            elif data.startswith(b"TEXT:"):
                # print("I have receive massage!")
                print(type(data))
                text_msg = data[5:].decode('utf-8')
                self.msg_data.emit(text_msg)
                continue

            else:
                print("Unknown data format received.")
                continue
 # 新增一个发送消息的方法
    def send_udp_message(self, message):
        # 发送数据前，加上"TEXT:"前缀，并编码为字节串
        message = "TEXT:" + message
        message = message.encode('utf-8')

        # 设置目标IP地址和端口
        target_addr = self.Low_addr # 设置为下位机目标IP和端口

        # 发送 UDP 消息
        self.sock.sendto(message, target_addr)

if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec_())
