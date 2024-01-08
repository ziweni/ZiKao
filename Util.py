# /usr/bin/python3
# coding=utf8

"""
工具集
"""

import time

# 获取时间戳
def get_timestamp():
    timestamp = time.time()
    return int(timestamp * 1000)

# json转字符
def obj2str(obj):
    ret = ""
    for key in obj:
        if ret == "":
            ret = key + "=" + str(obj[key])
        else:
            ret = ret + "&" + key + "=" + str(obj[key])
    return ret