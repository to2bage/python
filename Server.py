import selectors
import argparse
from socket import socket, AF_INET, SOCK_STREAM
import types, os

class Server:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.family = AF_INET
        self.type = SOCK_STREAM
        self.server = socket(family=self.family, type=self.type)
        self.selector = selectors.DefaultSelector()
        # self.root = "/root"             # remote_host
        self.root = "/users/apple"      # local_host
        self.fb = None
        self.start()
        pass

    def start(self):
        self.server.setblocking(False)      # 设置非阻塞模式
        self.server.bind((self.host, self.port))
        self.server.listen()
        print("服务器开始监听端口{}".format(self.port))

        self.selector.register(self.server, selectors.EVENT_READ, data=None)    # 注册事件
        pass

    def run_for_ever(self):
        """
            事件循环
            key.data is None: 表示是处理连接到请求
            key.data is not None and key.data.info == "file_info": 表示处理文件的名称, 大小, 用户等信息
            key.data is not None and key.data.info == "upload_file": 表示处理文件的上传
        """
        try:
            while True:
                events = self.selector.select(timeout=None)
                for key, mask in events:
                    if key.data is None:
                        # 客户端连接事件
                        self._accept_client(key.fileobj)
                    elif key.data is not None and key.data.info == "file_info":
                        # 处理文件的名称, 大小, 用户等信息
                        self._handle_file_info(key, mask)
                    elif key.data is not None and key.data.info == "upload_file":
                        # 处理文件的上传
                        self._handle_upload_file(key, mask)
                    pass
            pass
        except KeyboardInterrupt as e:
            print(e)
        finally:
            self.selector.unregister(self.server)
            self.selector.close()
        pass

    def _accept_client(self, server_sock):
        """ 处理客户端连接事件 """
        client, addr = server_sock.accept()
        print("欢迎远道而来的朋友: [{}]".format(addr))
        client.setblocking(False)       # 非阻塞
        data = types.SimpleNamespace(info="file_info", addr=addr)
        events = selectors.EVENT_READ | selectors.EVENT_WRITE

        self.selector.register(client, events, data=data)       # 注册处理文件信息的事件 ***
        pass

    def _handle_file_info(self, key, mask):
        """ 处理文件的名称, 大小, 用户等信息 """
        try:
            client = key.fileobj
            data = key.data

            if mask & selectors.EVENT_READ:
                dt = client.recv(1024).decode("utf8")         # 文件信息格式: "用户名:文件名:文件大小"
                client.send("ding-dong".encode("utf8"))

                username, filename, filesize = self._get_file_info(dt)  # filename包含路径
                events = selectors.EVENT_READ | selectors.EVENT_WRITE
                data = types.SimpleNamespace(info="upload_file", username=username, filename=filename, filesize=filesize, bytes_num=0)
                print("data: {}".format(data))

                # os.chdir(self.root)  # 改变当前目录至self.root定义的目录, 即 cd /root, 且这个目录一定是存在的
                # if not os.path.exists(username):
                #     # 以username命名的目录不存在
                #     os.mkdir(username)  # 并在当前目录, 创建新目录
                #     pass
                #
                # os.chdir(username)  # 并改变当前目录为 self.root/username
                self.fb = open(filename, "wb")      #  以wb模式打开文件filename


                self.selector.unregister(client)                        # 取消注册处理文件信息的事件 ***  特别注意哦
                self.selector.register(client, events, data=data)       # 注册处理文件上传的事件
                print("完成注册处理文件上传的事件")
                pass
            else:
                pass
            pass
        except:
            pass


    def _handle_upload_file(self, key, mask):
        """ 处理文件的上传 """
        # print("upload fils......")
        try:
            client = key.fileobj
            username = key.data.username
            filename = key.data.filename
            filesize = key.data.filesize

            # print(data)             #  用于测试
            # os.chdir(self.root)         # 改变当前目录至self.root定义的目录, 即 cd /root
            # os.mkdir(username)          # 并在当前目录, 创建新目录
            # os.chdir(username)          # 并改变当前目录为 self.root/username
            if mask & selectors.EVENT_READ:
                # print("准备上传文件: {}, 文件大小: {}".format(filename, filesize), end="\r", flush=True)
                # bytes_num = 0
                # with open(filename, "wb") as fb:
                #     while True:
                #         # data = client.recv(1024).decode("utf8")   # 模式由a, 修改为wb
                #         data = client.recv(1024)
                #         if data == b"bye":
                #             break
                #         # print(data)
                #         bytes_num += len(data)
                #         print("已经上传了: {:.2f}%".format(bytes_num / filesize * 100), end="\r",flush=True)  # 始终在同一行第一列开始打印, flush要求不要缓存
                #         fb.write(data)
                #         client.send("ok".encode(encoding="utf8"))
                #         pass
                data = client.recv(1024)
                if data != b"bye":
                    print(data)
                    self.fb.write(data)
                    client.send("ok".encode(encoding="utf8"))
                    pass
                else:
                    print()
                    print("文件上传完毕了!!!")
                    self.fb.flush()             # 强迫写入文件
                    self.selector.unregister(client)  # 文件上传完毕, 即取消注册文件上传事件
                    client.close()
                pass
            pass
        except:
            pass


    def _get_file_info(self, data):
        if data is None:
            return None

        file_info_list = data.split(":") # 文件名不包含目录, 只是单纯的文件名
        user_name = file_info_list[0]
        # 可以建立目录了
        # os.chdir(self.root)  # 改变当前目录至self.root定义的目录, 即 cd /root, 且这个目录一定是存在的
        # if not os.path.exists(user_name):
        #     # 以username命名的目录不存在
        #     os.mkdir(user_name)  # 并在当前目录, 创建新目录
        #     pass
        #
        # os.chdir(user_name)  # 并改变当前目录为 self.root/username    ++++++++注意:  改变了当前目录**********
        # print("当前目录: ", os.getcwd())
        file_path = os.path.join(self.root, user_name)
        if not os.path.exists(file_path):
            os.mkdir(file_path)
            pass


        file_name = self._get_nums_of_same_file_name(file_info_list[1], file_path)
        file_name = os.path.join(file_path, file_name)          # 这时的file_name是包含路径的文件名
        file_size = file_info_list[2]

        return (user_name, file_name, file_size)
        pass

    def _file_name(self, file_dir):
        for root, dirs, files in os.walk(file_dir):
            # print(root)  # 当前目录路径
            # print(dirs)  # 当前路径下所有子目录
            # print(files)  # 当前路径下所有非目录子文件
            # for file in files:
            #     yield file
            yield from files

    def _get_nums_of_same_file_name(self, file_name, file_path):
        """
        上传文件, 如果是同名的就在文件名(不包含扩展名)后加入_X, 例如 Server.py Server_1.py Server_2.py Server_3.py
        """
        # idx = file_name.rfind("/")
        # if idx != -1:
        #     # 表示上传到文件是一个路径
        #     pass

        flag = False    # 判断是否有同名的文件存在
        count = 0       # 记录同名文件的个数
        arr1 = file_name.split(".")
        fn1 = arr1[0]       # 文件名
        en1 = arr1[1]       # 扩展名
        for name in self._file_name(file_path):  # 在指定的目录下(即当前目录), 查找所有的文件
            arr2 = name.split(".")
            fn2 = arr2[0]
            en2 = arr2[1]
            if en1 == en2:
                # 扩展名相同
                if fn1 == fn2:
                    # 文件名相同
                    count += 1
                else:
                    # 文件名不相同, 要按照"-"拆分文件名
                    arr3 = fn2.split("_")
                    if fn1 == arr3[0]:
                        # 文件名相同
                        count += 1
                        pass
                    else:
                        pass
                pass
            else:
                # 扩展名不一样, 根本不可能是重复文件
                pass
            pass

        if count == 0:
            return fn1 + "." + en1
        else:
            return fn1 + "_" + str(count) + "." + en1
        pass

    pass


if __name__ == '__main__':
    parse = argparse.ArgumentParser(description="文件上传服务器")
    parse.add_argument("--host", dest="host", required=False)
    parse.add_argument("--port", dest="port", required=False)

    args = parse.parse_args()       # return Namespace

    if args.host is None:
        args.host = "192.168.1.234"
        args.host = "0.0.0.0"
    if args.port is None:
        args.port = 8080

    server = Server(host=args.host, port=int(args.port))
    server.run_for_ever()
    pass