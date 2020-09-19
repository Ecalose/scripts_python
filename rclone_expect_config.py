#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# @Author : bajins https://www.bajins.com
# @File : rclone_expect_config.py
# @Version: 1.1.0
# @Time : 2020/7/26 11:00
# @Project: tool-gui-python
# @Package:
# @Software: PyCharm

import json
# 如果import urllib，则在使用urllib.request时会报错
import urllib.request
import subprocess
import os
import time
import sys
# 自动执行命令，pip install pexpect
import pexpect


def daemon():
    """
    Daemon（守护进程）
    :return:
    """
    # 将当前进程fork为一个守护进程
    pid = os.fork()
    if pid > 0:
        # 父进程退出
        os._exit(0)


def call_cmd(cmd, log_path="rclone.log"):
    """
    执行命令不输出回显并输出日志到文件
    :param cmd: 执行的命令
    :param log_path: 日志文件路径
    :return:
    """
    call = subprocess.call(f'nohup {cmd} >{log_path} &', shell=True)
    if call != 0:
        print(f"执行失败，请查看{log_path}中的日志")


def popen_cmd(cmd, charset="utf8"):
    """
    执行shell命令并实时输出回显
    :param cmd: 执行的命令
    :param charset: 字符集
    :return:
    """
    # universal_newlines=True, bufsize=1
    process = subprocess.Popen(cmd, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    # 判断子进程是否结束
    while process.poll() is None:
        line = process.stdout.readline()
        line = line.strip()
        if line:
            print(line.decode(charset, 'ignore'))


def download_rclone():
    """
    通过GitHub的api下载rclone最新版本
    :return:
    """
    # 判断系统架构位数
    if sys.maxsize > 2 ** 32:
        maxbit = "linux-amd64.zip"
    else:
        maxbit = "linux-386.zip"
    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.105 Safari/537.36"
    # 请求GitHub api
    req = urllib.request.Request("https://api.github.com/repos/rclone/rclone/releases/latest",
                                 headers={"User-Agent": user_agent}, method='GET')
    res = urllib.request.urlopen(req, timeout=30)
    # 获取到GitHub返回的release详情
    res_json = json.loads(res.read().decode("utf-8"))

    for asset in res_json["assets"]:
        # 如果系统架构在当前name中
        if maxbit in asset["name"]:
            # 获取当前系统架构的下载链接
            download_url = asset["browser_download_url"]
            # rclone压缩包名
            zip_name = asset["name"]
            # 删除同名压缩包
            os.system(f"find . -type f -name '{zip_name}*' | xargs rm")
            # 解压后目录名
            dir_name = zip_name.replace(".zip", "")
            # 删除同名目录，防止目录中的文件已被删除
            os.system(f"rm -rf {dir_name}")
            # 下载当前系统架构的文件
            subprocess.call(['wget', download_url])
            # 解压
            subprocess.call(['unzip', zip_name])
            return dir_name


def one_drive(rclone_dir, drive_name, access_token=None):
    """
    One Drive 配置
    :param rclone_dir:  rclone运行目录
    :param drive_name:  自定义远程配置名称
    :param access_token:  授权token，为执行 rclone authorize "onedrive" 获取到的token
    :return:
    """
    child = pexpect.spawn(f'./{rclone_dir}/rclone config')
    # print(child)
    # 如果返回0说明匹配到了异常
    index = child.expect([pexpect.EOF, 'New remote'])
    if index == 1:
        # n新建远程
        child.sendline('n')

    index = child.expect([pexpect.EOF, 'name'])
    if index == 1:
        child.sendline(drive_name)

    try:
        index = child.expect([pexpect.EOF, 'already exists'])
        if index == 1:
            print("该远程配置已经存在：", drive_name)
            time.sleep(5)
            return None
    except:
        pass

    index = child.expect([pexpect.EOF, 'Storage'])
    if index == 1:
        # Microsoft OneDrive:23 , Google Drive:13
        child.sendline('23')

    index = child.expect([pexpect.EOF, 'client_id'])
    if index == 1:
        child.sendline('')

    index = child.expect([pexpect.EOF, 'client_secret'])
    if index == 1:
        child.sendline('')

    index = child.expect([pexpect.EOF, 'Edit advanced config'])
    if index == 1:
        # 是否配置高级设置，这里我们直接No，选择n
        child.sendline('n')

    index = child.expect([pexpect.EOF, 'Use auto config'])
    if index == 1:
        # 是否使用自动设置，同样直接NO，选择n
        child.sendline('n')

    index = child.expect([pexpect.EOF, 'result'])
    if index == 1:
        # 如果传入的授权为空，就在文件中获取
        if access_token is None:
            # 创建空文件，把授权后的代码保存到此文件中第一行
            # echo 授权代码 >one_drive_access_token.txt
            os.mknod("one_drive_access_token.txt")
            # 等待用户操作时间，秒为单位
            time.sleep(240)
            # 读取文件中第一行内容
            with open("one_drive_access_token.txt", "r")as f:
                access_token = f.readlines()
            if access_token == "":
                raise Exception("读取到授权文件为空，如果操作时间过长，请调整time.sleep")
        # 这里输入在Windows下CMD中获取的access_token
        child.sendline(access_token)

    index = child.expect([pexpect.EOF, 'Your choice'])
    if index == 1:
        # 这里选择1，onedrive个人版或是商业版
        child.sendline('1')

    index = child.expect([pexpect.EOF, 'Chose drive to use'])
    if index == 1:
        # 提示找到一个驱动器，输入找到的序号0
        child.sendline('0')

    index = child.expect([pexpect.EOF, "Found drive 'root' of type 'business'"])
    if index == 1:
        # 找到类型为“business”的驱动器 "root"，输入y
        child.sendline('y')

    index = child.expect([pexpect.EOF, 'Yes this is OK'])
    if index == 1:
        # 确认配置
        child.sendline('y')

    index = child.expect([pexpect.EOF, 'Quit config'])
    if index == 1:
        # 输入q，退出配置；n新建；d删除；r重命名；c复制；s设置密码
        child.sendline('q')
    #     print(subprocess.getoutput(f'./{dir_name}/rclone config show'))
    time.sleep(5)


def google_drive(rclone_dir, drive_name):
    """
    Google Drive 远程配置
    :param drive_name: 自定义远程配置名称
    :return:
    """
    child = pexpect.spawn(f'./{rclone_dir}/rclone config')
    # print(child)
    # 如果返回0说明匹配到了异常
    index = child.expect([pexpect.EOF, 'New remote'])
    if index == 1:
        # n新建远程
        child.sendline('n')

    index = child.expect([pexpect.EOF, 'name'])
    if index == 1:
        child.sendline(drive_name)

    try:
        index = child.expect([pexpect.EOF, 'already exists'])
        if index == 1:
            print("该远程配置已经存在：", drive_name)
            time.sleep(5)
            return None
    except:
        pass

    index = child.expect([pexpect.EOF, 'Storage'])
    if index == 1:
        # Microsoft OneDrive:23 , Google Drive:13
        child.sendline('13')

    index = child.expect([pexpect.EOF, 'client_id'])
    if index == 1:
        child.sendline('')

    index = child.expect([pexpect.EOF, 'client_secret'])
    if index == 1:
        child.sendline('')

    index = child.expect([pexpect.EOF, 'scope'])
    if index == 1:
        child.sendline('1')

    index = child.expect([pexpect.EOF, 'root_folder_id'])
    if index == 1:
        child.sendline('')

    index = child.expect([pexpect.EOF, 'service_account_file'])
    if index == 1:
        child.sendline('')

    index = child.expect([pexpect.EOF, 'Edit advanced config'])
    if index == 1:
        child.sendline('n')

    index = child.expect([pexpect.EOF, 'Use auto config'])
    if index == 1:
        child.sendline('n')

    index = child.expect([pexpect.EOF, 'Enter verification code'])
    print(child.before)
    if index == 1:
        # 创建空文件，把授权后的代码保存到此文件中第一行
        # echo 授权代码 >google_drive_verification_code.txt
        os.mknod("google_drive_verification_code.txt")
        # 等待用户操作时间，秒为单位
        time.sleep(120)
        # 读取文件中第一行内容
        with open("google_drive_verification_code.txt", "r")as f:
            google_drive_verification_code = f.readlines()
        if google_drive_verification_code == "":
            raise Exception("读取到授权文件为空，如果操作时间过长，请调整time.sleep")
        child.sendline(google_drive_verification_code)

    index = child.expect([pexpect.EOF, 'Configure this as a team drive'])
    if index == 1:
        child.sendline('n')

    index = child.expect([pexpect.EOF, 'Yes this is OK'])
    if index == 1:
        child.sendline('y')

    index = child.expect([pexpect.EOF, 'Quit config'])
    if index == 1:
        # 输入q，退出配置；n新建；d删除；r重命名；c复制；s设置密码
        child.sendline('q')
    #     print(subprocess.getoutput(f'./{dir_name}/rclone config show'))
    time.sleep(5)


def write_google_drive_config(rclone_dir, name, token=None, drive_type="drive", scope="drive", team_drive=None,
                              root_folder_id=None, shared_with_me=None, service_account_file=None, saf=None):
    """
    此函数是为了方便写入在其他地方已经授权复制过来的Google Drive配置，而不需要重新创建配置
    :param name: 自定义远程配置名称
    :param token: 授权token
    :param drive_type: drive类型，一般默认即可
    :param scope: rclone从驱动器请求访问时应使用的范围，对应--drive-scope参数
    :param team_drive: 团队驱动器的ID，对应--drive-team-drive参数
    :param root_folder_id: 根文件夹的ID，对应--drive-root-folder-id参数
    :param shared_with_me: 只显示与我共享的文件，对应--drive-shared-with-me参数
    :param saf: 服务帐户凭据JSON文件内容，此参数有值且service_account_file为空时默认saf.json
    :param service_account_file: 服务帐户凭据JSON文件路径，对应--drive-service-account-file参数
    :return:
    """
    import configparser
    conf = configparser.ConfigParser()
    # 获取rclone配置文件的路径
    file = subprocess.getoutput(f"./{rclone_dir}/rclone config file")
    file = file.split("\n")[1]
    # 读取配置
    conf.read(file, encoding="utf-8")
    # 获取配置中的远程节点
    node_array = conf.sections()
    # 如果远程节点不存在
    if name not in node_array:
        # 添加远程节点
        conf.add_section(name)
        conf.set(name, 'type', drive_type)
        conf.set(name, 'scope', scope)
        if token is not None:
            conf.set(name, 'token', token)
        if team_drive is not None:
            conf.set(name, 'team_drive', team_drive)
        if root_folder_id is not None:
            conf.set(name, 'root_folder_id', root_folder_id)
        if shared_with_me is not None:
            # "true" 或 ”false"
            conf.set(name, 'shared_with_me', shared_with_me)
        if saf is not None:
            if service_account_file is None:
                service_account_file = "saf.json"
            with open(service_account_file, 'w') as f:
                f.write(saf)
        if service_account_file is not None:
            # 服务账户授权json文件路径 https://rclone.org/drive/#service-account-support
            conf.set(name, 'service_account_file ', service_account_file)
        with open(file, 'w') as f:
            conf.write(f)


rclone_dir = download_rclone()

"""
以下为执行rclone自动配置
"""

one_drive_access_token = """授权"""
one_drive(rclone_dir, "onedrive", one_drive_access_token)

google_drive_token = """授权"""
write_google_drive_config(rclone_dir, "gdrive", google_drive_token)
# 团队盘配置
write_google_drive_config(rclone_dir, "gdrive_team", google_drive_token, team_drive="0AFZsAUl3VSwzUk9PVA")
# 分享链接配置
write_google_drive_config(rclone_dir, "gdrive_stared", google_drive_token,
                          root_folder_id="10USshsyfY01grYZzSHMq60lo1H_WVVZH")

service_account_json = r"""
{
  "type": "service_account",
  "project_id": "elated-emitter-287202",
  "private_key_id": "4fcf7adfcfb7ee765170156d5dd9807aa5801e65",
  "private_key": "-----BEGIN PRIVATE KEY-----\nMIIEvAIBADANBgkqhkiG9w0BAQEFAASCBKYwggSiAgEAAoIBAQDB0NtpAb6/DImE\n9u9FWOzftzQY3T1OR/pRixGIvtL/VAOQ3ui5O/lXPkQJ5+bB/zrb8YQmhL5Zd0Yp\npUkJ7XFLbQRKWHU3jvW+1DMcRUW/B5uhnuEIyYjBpCH+/wCO6w1rdxAVpudnJF7P\n7mCELH3b8dJ9bEYms7UVHtxuGOud+YnAZolRTYo9tfaFYHg4wJIJmAKPamzf2XkA\nefKUptrRC6sM4FnLnr3w4jGNGlMogOeARY/5MTiImeXFaJ5o67c6KgLjEBumMSuq\n6pvE3S7aWnUEVKYASaz49vBDGuquFCrxZSgS4R5sOxyLOABiPMhKhppTQ+C1zIaz\najEBG9cFAgMBAAECggEAVqDQGPCvPbxQUS6ABsp24Y2EyyJD7xPL5huXJDxKmdYG\n2/9OHNEaIu0RQy40XXyDZeBe1Uqau+lMYnvemAHZlEFvW/2KsuECpR86kwXBZV90\np/oYEjHmHssKaOu4Z6jW8DQg69SUdGz0tdKRsDIktSSylN3KwyyqoPyQwOMBmTMz\nPp71Y+n5ILH8ECMKjmgQJazLZIoCMRarItFqryMkkIfv/rtSd8cgsh7yJIwsBorR\nbKXOVrSobgW700wCmPqU1/X9cwEphHMLJ1/lL7CcvEB0Qaea1P6c0cRNK/waCGml\niJK9QgOjwMcwpbzy1WjtOl7mQ0MOI38WTKd3XNDDZwKBgQDjCoo6lok4h94gfCGr\nPyrn0mKEteSohr8VEZwqnZfMT9Cep4R5hpzZcycEJ23VsZF7PvOTMcvUE6/nelK8\niDGK2N8yYUgkT3mZ8BCTp1QFTocL7uSlOYj0NwTCeVAD8z+fisOcXM4osGejHBUg\nRWx/meFRXEzHetDzb+BM0DgnwwKBgQDaiW1wXUlisIhtYng+SnwMlJBrpZtUXCv+\ndsS8/OTWyzJmiHQl6cwi8OTU4TvMfBaoq9NmsSm35RiuRTbJiMNi4zbVIVKtp9Kp\nHgodlUNz64VhXalUWcta2DsDjWsMBnW0YfCgQ6CtIavu9Dg1MTWNDTrqiJ5I7get\nQdYkkC7hlwKBgAi0scI3XYGmbBUQzXW0kV+cSJzQILl5mUAkkblsm5KBCP3cbI8A\nY2lPKhLVtDd6fJqeOlbNlQRH0PnuTdfe3Q9263ASHOMPjRkjBG+0/drKPRFvEqNn\nRmIe7fbLEg9kt27VslR/loQm54JwpDq9jsCB1Qr6oBMSGYsMIiyv20djAoGAdi/K\nivE4hfH45kdRxkZcDiWucTkv5xCuDkFHJvoR/IQJ7t+vCO4HI4JqDyL8Rxt42aGL\ng8ceS8DPdzghaB7ZpDpDZkJOR3IygJmpWNRnlWJzUPPpZp/lVW0JhWNO2EMKFxK8\nor/QPrGuHV3gpAvH7U+RZFOcXs60QiQP3thHMmMCgYB0QClTCzvF9oqhbIA3K/R4\nteW/NFp+OMx+vExNA9mzI8vfjqgEeTeo1FmvCz8zid0r+3NFY4cSmuZ0Fw1PuPoM\n4i5bAJ+PrqV+qytGZh/M7O0g93jHDA2UspYNR4f2esbO8n+plTMbD7TPQEnZda4J\nMQqwjNFjkAdKIDFuAS8zQA==\n-----END PRIVATE KEY-----\n",
  "client_email": "rclone@elated-emitter-287202.iam.gserviceaccount.com",
  "client_id": "105227418884970409788",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/rclone%40elated-emitter-287202.iam.gserviceaccount.com"
}
"""
write_google_drive_config(rclone_dir, "gservicedrive", saf=service_account_json)


print(subprocess.getoutput(f'./{rclone_dir}/rclone config show'))

"""
以下为执行rclone命令，执行命令不输出回显可使用call_cmd函数执行命令或调用daemon函数
"""

params = " --multi-thread-cutoff 50M --multi-thread-streams 50 --transfers 100 --checkers 100 --buffer-size 50M"
params += " --cache-chunk-size 50M --tpslimit-burst 2 --ignore-errors -P"
# --fast-list 如果可用，请使用递归列表。使用更多的内存，但更少的事务
# --drive-server-side-across-configs 允许Google Drive服务器端操作跨不同的驱动器，不走本地流量
# --drive-V2-download-min-size 指定最小大小文件使用驱动器v2 API下载

# 复制分享的链接文件或目录到团队盘
gdrive_stared_copy = f'./{rclone_dir}/rclone copy --drive-server-side-across-configs gdrive_stared: gdrive_team: {params}'
# 我的云盘同步到团队盘
gdrive_team_sync = f'./{rclone_dir}/rclone sync --drive-server-side-across-configs gdrive: gdrive_team: {params}'
# 查看目录大小，可使用--drive-root-folder-id参数指定其他分享链接ID
gdrive_size = f'./{rclone_dir}/rclone size gdrive_stared: '

# 同步
cmd = f'./{rclone_dir}/rclone sync gdrive:/ onedrive:/ {params}'
# 去重
# cmd = f'./{rclone_dir}/rclone dedupe --dedupe-mode oldest gdrive:/ {params}'

# call_cmd(cmd)

# daemon()
# popen_cmd(gdrive_stared_copy)
# popen_cmd(gdrive_team_sync)
# popen_cmd(gdrive_size)
popen_cmd(cmd)