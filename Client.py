from socket import socket, AF_INET, SOCK_STREAM
from threading import Thread, Lock
import os, argparse, time


class Client(Thread):
    def __init__(self, lock, remote_host, port, file_name, user_name, family=AF_INET, type=SOCK_STREAM):
        super().__init__()
        self.lock = lock
        self.remote_host = remote_host
        self.port = port
        self.file_name = file_name
        self.user_name = user_name
        self.client = socket(family=family, type=type)
        # self._start()
        pass


    def run(self):
        self.client.connect((self.remote_host, self.port))
        try:
            with open(self.file_name, "rb") as fb:      # 修改为rb模式, 即可以读图片等二进制文件, 也可以读字符文件
                # 首先获得文件的大小
                file_size = fb.seek(0, 2)       # 将指针移动到文件末尾, 获得文件的大小(字节)
                # 如果self.file_name是一个路径
                idx = self.file_name.rfind("/") # 查找路径的方法, 只是用于linux系统
                if idx != -1:
                    fname = self.file_name[idx+1:]
                    pass
                else:
                    fname = self.file_name
                # 发送文件的元数据: "用户名:文件名:文件大小", 路径的话, 只传文件名, 不包含路径
                self.client.send("{}:{}:{}".format(self.user_name, fname, file_size).encode(encoding="utf8"))
                while True:
                    # 等待远程主机的确认信息: ding-dong
                    answer = self.client.recv(1024).decode(encoding="utf8").strip()
                    if answer == "ding-dong":
                        break

                print("收到远程主机的响应")
                # 开始发送文件
                fb.seek(0, 0)       # 移动文件指针到开始的位置
                for data in fb.readlines():
                    print("{}".format(data))  # 不再显示数据了
                    # self.client.send(data.encode(encoding="utf8"))    # 如果是rb模式, 就不需要在编码了
                    self.client.send(data)
                    self.client.recv(10)
                    # time.sleep(0.05)   # 去除了
                pass
        except OSError as e:
            print("OSError=> {}".format(e))
            exit(1)
        else:
            print("文件读取完毕, 也传送完毕...")
            self.client.send("bye".encode(encoding="utf8"))     # bye 表示要断开连接了
            time.sleep(1)
        pass

    def _get_file_size(self):
        pass

    pass

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="")
    parser.add_argument("--username", dest="user_name", required=True)
    parser.add_argument("--filename", dest="file_name", required=True)
    parser.add_argument("--host", dest="remote_host", required=False)
    parser.add_argument("--port", dest="port", required=False)

    args = parser.parse_args()

    if args.remote_host is None:
        args.remote_host = "127.0.0.1"
    if args.port is None:
        args.port = 8080

    lock = Lock()

    client = Client(lock, args.remote_host, int(args.port), args.file_name, args.user_name)
    client.start()

    pass