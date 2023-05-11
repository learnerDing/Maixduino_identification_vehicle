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
        # 设置窗户大小固定为初始尺寸
        self.setFixedSize(self.size())

        # 初始化并启动接收线程类
        self.receive_thread = ReceiveThread()
        # 信号与槽函数绑定
        # 接收数据线程绑定
        self.receive_thread.image_data.connect(self.update_image)  # image_data为信号（也是接收到的图片信息）
        self.receive_thread.msg_data.connect(self.display_text)
        self.receive_thread.ip_signal.connect(self.Low_ip_show)  # 用Low_ip_show来接收发送来的地址信息
        self.receive_thread.start()
        # 主线程（窗口线程）绑定
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

    def display_text(self, text):
        # 将收到的文字信息追加展示在QTextBrowser上面
        self.mssg_rec.append(text)

    def Low_ip_show(self, Tpl_Low_ip):
        self.My_low_ip = Tpl_Low_ip  # 将Tql_Low_ip设置为类的属性，其他方法也可以访问到它
        self.Lower_ipED.setText(str(Tpl_Low_ip))  # 展示下位机ip地址和端口

    def on_Sendmssg_clicked(self):
        # 获取 mssg_sed 文本编辑器里的文字
        text_to_send = self.mssg_sed.text()
        # 将获取到的文本发送给接收线程
        self.receive_thread.send_message(text_to_send)


# 接收udp数据线程
class ReceiveThread(QtCore.QThread):
    # 这是信号，用于向主进程发送信息
    image_data = QtCore.pyqtSignal(QtGui.QImage)  # 发送图片信息
    msg_data = QtCore.pyqtSignal(str)  # 发送文字信息
    ip_signal = QtCore.pyqtSignal(tuple)  # 发送下位机ip地址，地址信息是一个tuple eg.('192.168.1.113',9999)
    # 增加一个信号send_text_content
    send_text_content = QtCore.pyqtSignal(str)

    def __init__(self, parent=None):
        super(ReceiveThread, self).__init__(parent)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # 连接信号send_text_content到send_udp_message槽函数
        self.send_text_content.connect(self.send_udp_message)

    def send_message(self, message):
        self.send_text_content.emit(message)

    def judge_pic_or_text(self,data):#用于判断发送的数据是图片还是文本信息
        if data ==b"TE":
            print("接收到文本信息")
    def run(self):
        # 上位机ip地址和端口
        ADDR = ('192.168.1.113', 8080)
        self.sock.bind(ADDR)
        # 开始监听并设置为最多接收一个连接请求
        self.sock.listen(1)
        # 接受一个客户端连接，并获取客户端地址信息
        self.conn, addr = self.sock.accept()#conn是一个新的Socket对象，表示与客户端的连接，可以使用该对象进行通信，发送和接收数据。
        # 将客户端的地址信息发送到主进程
        self.ip_signal.emit(addr)
        self.conn.settimeout(10)#设置conn的超时时间，如果超过十秒没有应答或者发送成功则会产生套接字超时错误
        conn_end = False
        pack_size = 1024 * 5  #图片包大小上限为5个字节

        while True:
            if conn_end:
                break
            img = b""
            tmp = b''
            #尝试先读取2个字节的数据，如果是TE则是文本信息，如果是IM则是图片信息
            try:
                self.begindata = self.conn.recv(2)
            except Exception as e:
                print("Receive data go wrong", e)
            if self.begindata ==b'IM':
                print("开始接收图片信息")
            # 此循环每执行一次会读取一个字节，读取两次之后如果是b'\xFF\xD8'说明这是一张JPEG格式的照片文件
            while True:
                try:
                    client_data = self.conn.recv(1)
                except socket.timeout:
                    conn_end = True
                    break
                if tmp == b'\xFF' and client_data == b'\xD8':
                    img = b'\xFF\xD8'  # 判断完毕，还原图片数据完整性
                    break
                tmp = client_data

            while True:
                try:
                    client_data = self.conn.recv(4096)  # ESP32芯片的SPI总线DMA临时缓冲区大小为4096个字节。
                except socket.timeout:
                    client_data = None
                    conn_end = True
                if not client_data:
                    break
                # print("received data,len:",len(client_data) )
                img += client_data
                if img[-2:] == b'\xFF\xD9':  # 读取到\xFF\xD9字节说明这是一张JEPG图片的结尾部分
                    break
                if len(client_data) > pack_size:  # 超过图片包上限也结束读取
                    break
            print("recive end, pic len:", len(img))
            # 再次检查图片字节串的开始以及结束字符
            if not img.startswith(b'\xFF\xD8') or not img.endswith(b'\xFF\xD9'):
                print("image error")
                continue


            while True:
                # 从客户端接收数据（在TCP协议中，没有事先定义数据长度）
                data = self.conn.recv(2048)
                if not data:
                    break

                # 判断数据类型并进行处理
                if data.startswith(b"IMG:"):
                    img_data = b""
                    data = data[4:]
                    while data != b'end':
                        img_data += data
                        data = self.conn.recv(2048)
                    # 对图片数据进行完整性检查并发送信号
                    try:
                        img = QtGui.QImage.fromData(img_data)
                        if img.isNull():
                            print("Incomplete image data received.")
                            continue
                    except Exception as e:
                        print("Error decoding image data:", e)
                        continue

                    # 发送经过完整性检查的图片信息
                    self.image_data.emit(img)

                # 处理接收到的文本信息
                elif data.startswith(b"TEXT:"):
                    text_msg = data[5:].decode('utf-8')
                    self.msg_data.emit(text_msg)
                    continue

                # 接收到未知数据格式
                else:
                    print("Unknown data format received.")
                    continue
                # 关闭连接
            self.conn.close()
    # 新增一个发送消息的方法
    def send_tcp_message(self, message):
        # 发送数据前，加上"TEXT:"前缀，并编码为字节串
        message = "TEXT:" + message
        message = message.encode('utf-8')
        # 使用连接的套接字发送消息
        self.conn.sendall(message)



if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec_())
