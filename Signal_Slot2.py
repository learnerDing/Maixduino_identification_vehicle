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

    def update_image(self, img_data):
        # 将收到的img_data转换为QPixmap并显示在QLabel上
        pixmap = QtGui.QPixmap.fromImage(img_data)
        self.PIC_Show.setPixmap(pixmap.scaled(self.PIC_Show.size(), QtCore.Qt.KeepAspectRatio))
    def display_text(self,text):
        #将收到的文字信息追加展示在QTextBrowser上面
        self.mssg_rec.append(text)
    def Low_ip_show(self,Tpl_Low_ip):
        self.My_low_ip = Tpl_Low_ip  #将Tql_Low_ip设置为类的属性，其他方法也可以访问到它
        self.Lower_ipED.setText(str(Tpl_Low_ip))#展示下位机ip地址和端口



#接收udp数据线程
class ReceiveThread(QtCore.QThread):

    #这是信号，用于向主进程发送信息
    image_data = QtCore.pyqtSignal(QtGui.QImage)#发送图片信息
    msg_data = QtCore.pyqtSignal(str)#发送文字信息
    ip_signal = QtCore.pyqtSignal(tuple)#发送下位机ip地址，地址信息是一个tuple eg.('192.168.1.113',9999)


    def __init__(self, parent=None):
        super(ReceiveThread, self).__init__(parent)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    def run(self):
        # 上位机ip地址和端口
        ADDR = ('192.168.1.113', 9999)
        self.sock.bind(ADDR)

        while True:
            data, self.Low_addr = self.sock.recvfrom(2048)
            self.ip_signal.emit(self.Low_addr)#将Low_addr信号发送给主进程
            if data.startswith(b"IMG:"):
                img_data = b""
                data = data[4:]  # 去掉“IMG:”标志
                while data != b'end':
                    img_data += data
                    data, self.Low_addr = self.sock.recvfrom(2048)
                # 对图片数据进行完整性检查
                try:
                    img = QtGui.QImage.fromData(img_data)
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


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec_())
