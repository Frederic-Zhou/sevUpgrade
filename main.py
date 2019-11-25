import paramiko
import os
import datetime


class EndPoint:
    def __init__(self, host='localhost', user='root', pwd='', port=22, timeout=30):
        super().__init__()
        self.host = host
        self.port = port
        self.timeout = timeout
        self.user = user
        self.password = pwd

        self.t = None
        self.ssh = None

        self.open()
        pass

    def open(self):
        try:
            self.ssh = paramiko.SSHClient()
            self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            self.ssh.connect(self.host, self.port, self.user, self.password)
        except Exception as e:
            self.ssh = None
            PrintAndExit(e)

        try:
            self.t = paramiko.Transport((self.host, self.port))
            self.t.connect(username=self.user, password=self.password)
            self.sftp = paramiko.SFTPClient.from_transport(self.t)
        except Exception as e:
            self.t = None
            PrintAndExit(e)

    def Exec(self, command):
        try:
            std_in, std_out, std_err = self.ssh.exec_command(command)
            for line in std_out:
                print(line.strip("\n"))
        except Exception as e:
            PrintAndExit(e)
        pass

    def Upload(self, local_path, server_path):
        try:
            print('upload file start %s ' % datetime.datetime.now())
            self.sftp.put(local_path, server_path)
        except Exception as e:
            if "Is a directory" in str(e):
                try:
                    print('upload dir start %s ' % datetime.datetime.now())
                    if local_path[-1] == '/' or local_path[-1] == '\\':
                        local_path = local_path[0:-1]

                    if server_path[-1] == '/' or server_path[-1] == '\\':
                        server_path = server_path[0:-1]

                    for root, dirs, files in os.walk(local_path):
                        for filespath in files:
                            local_file = os.path.join(root, filespath)
                            a = local_file.replace(local_path+"/", '')
                            remote_file = os.path.join(server_path+"/", a)
                            try:
                                self.sftp.put(local_file, remote_file)
                                pass
                            except Exception as e:
                                print("may be not dir:", e)
                                self.sftp.mkdir(os.path.split(remote_file)[0])
                                self.sftp.put(local_file, remote_file)
                            print("upload %s to remote %s" %
                                  (local_file, remote_file))
                        for name in dirs:
                            local_dir = os.path.join(root, name)
                            a = local_dir.replace(local_path, '')
                            remote_path = os.path.join(server_path, a)
                            try:
                                self.sftp.mkdir(remote_path)
                                print("mkdir path %s" % remote_path)
                            except Exception as e:
                                print(e)

                except Exception as e:
                    PrintAndExit(e)
                pass
            else:
                PrintAndExit(e)

    # def Download(self, local_path, server_path):
    #     try:
    #         self.sftp.get(server_path, local_path)
    #     except Exception as e:
    #         PrintAndExit(e)

    def close(self):
        if self.t:
            self.t.close()
        if self.ssh:
            self.ssh.close()
        pass

    def __del__(self):
        self.close()
        print("over!!")


def PrintAndExit(obj):
    print("exception:", obj)
    print("process exit")
    exit()


if __name__ == '__main__':

    ############# 配置区域开始 #######################
    # 配置服务器列表
    ServerList = [
        {
            "host": "example.com",  # 测试
            "port": 22,  # 端口
            "user": "root",  # 登录名
            "password": "yourpassword",  # 登录密码
            "rootdir": "/home/root/",  # 上传根目录
            "screenName": "serverScreen"  # 创建的screen的名称
        },

    ]

    # 本地可执行文件名
    localExeName = "server"
    # 本地目录
    localRoot = "/Users/zeta/project/"

    # 远端可执行文件名
    remoteExeName = "server001"

    uploadClean = False  # 是否上传清理脚本
    uploadExe = True  # 是否上传可执行文件
    uploadView = False  # 是否上传视图目录
    uploadConfig = False  # 是否上传配置目录
    uploadStatic = False  # 是否上传静态文件目录

    ############# 配置区域结束 #######################

    if localRoot[-1] != "/":
        localRoot += "/"

    for server in ServerList:

        print("upgrade... at", server["host"])
        remoteRoot = server["rootdir"]
        screenName = server["screenName"]

        if remoteRoot[-1] != "/":
            remoteRoot += "/"

        ep = EndPoint(server["host"], server["user"],
                      server["password"], server["port"])

        # 上传views目录
        if uploadView:
            print("upload View==================")
            ep.Upload("%sviews" % localRoot, "%sviews" % remoteRoot)
            pass
        # 上传config目录
        if uploadConfig:
            print("upload Config==================")
            ep.Upload("%sconfig" % localRoot, "%sconfig" % remoteRoot)
            pass
        # 上传static目录
        if uploadStatic:
            print("upload Static==================")
            ep.Upload("%sstatic" % localRoot, "%sstatic" % remoteRoot)
            pass

         # 上传执行文件
        if uploadExe:
            print("upload Exe==================")
            ep.Upload(localRoot+localExeName, remoteRoot+remoteExeName)

            # 设置权限
            ep.Exec("echo %s | sudo -S chmod +x %s" %
                    (server["password"], remoteRoot+remoteExeName))
            ep.Exec("screen -S %s -X quit" % screenName)  # 关闭预设 的screen
            ep.Exec("screen -dmS %s" % screenName)  # 创建一个叫预设 的screen
            # 用screen执行代码
            ep.Exec(
                'screen -x -S %s -p 0 -X stuff "cd %s && echo %s|sudo -S ./%s -env prod \n"' % (screenName, remoteRoot, server["password"], remoteExeName))
            pass

        # 上传清理脚本
        if uploadClean:
            print("upload Clean==================")
            ep.Upload(localRoot+"clean.sh", remoteRoot+"clean.sh")
            ep.Exec("echo %s | sudo -S chmod +x %s" %
                    (server["password"], remoteRoot+"clean.sh"))
            pass

        # 执行清理脚本
        ep.Exec("cd %s && echo %s| sudo -S ./clean.sh" %
                (remoteRoot, server["password"]))
        pass

    pass
