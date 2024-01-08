# /usr/bin/python3
# coding=utf8

import os
import sys
import yaml
from ZiKao import ZiKao
from alive_progress import alive_bar

# 全局配置
config = { }

# 日志输出
def log(info):
    print(info)

if __name__ == "__main__":

    try:
        if len(sys.argv) <= 1:
            print("error: 未提供配置文件!")
            input()
            exit(-1)
        # 加载配置
        with open(sys.argv[1], "r", encoding='utf-8') as f:
            data = f.read()
        # 读取配置文件
        config = yaml.safe_load(data)
    except IOError:
        print("error: 初始化时出现错误：没找到配置文件！")
        input()
        exit(-1)
    except yaml.YAMLError as exc:
        print("error: 初始化时出现错误：配置文件异常！")
        input()
        exit(-2)

    # 初始化网课操作对象
    obj = ZiKao(config['member']['ename'], config['member']['url'])

    log("\n开始登陆……")

    if obj.login(str(config['member']['user']), str(config['member']['pass'])):
        obj.loginShow()
        print("账号密码登陆成功!")
    else:
        print("登陆失败！")
        input()
        exit(-1)
 

    log("正在获取专业信息……")
    # 获取专业信息
    major = obj.getMajorList()

    majorId = major['majorid']
    majorName = major['majorname']
    # 获取账号信息
    account = obj.getInfo()
    log("%s - %s" % (account['bkSchoolName'], account['name']))

    os.system("title %s %s" % (account['name'], str(config['member']['user'])))

    log("专业名称：《%s》\n" % majorName)
    if not 'imgURL' in account or account['imgURL'] == '':
        print("❌ 未上传头像无法执行刷课！")
        exit(-1)
    log("正在获取课程列表……\n")
    # 获取专业课程列表
    course = obj.getCourseList(majorId)

    TotalVideo = 0

    # 遍历课程，打印输出
    for item in course:
        info = obj.getCourseInfo(item['id'], item['ProceduralTypeID'], item['courseSource'])
        print("课程《%s》 总分：%s" % (item['name'], info['finalScore']))
        for item2 in info['kjInfo']:
            TotalVideo = TotalVideo + item2['totalTime']
            print(" - 课件《%s》 总时长：%d 分钟 | 已完成：%d 分钟" % (item2['courseName'], item2['totalTime'], item2['learnTime']))
        print(" - 测验《%s》 总数：%d | 答对：%d" % (info['cpInfo']['courseName'], info['cpInfo']['totalCount'], info['cpInfo']['getCount']))
        for item2 in info['zyInfo']:
            print(" - 作业《%s》 总分：%d 得分：%s" % (item2['courseName'], item2['totalScore'], item2['getScore']))
        print(" - 期末《%s》 总分：%d 得分：%s" % (info['qmInfo']['courseName'], info['qmInfo']['totalScore'], info['qmInfo']['getScore']))
        print(" - 表现《%s》 总分：%d 得分：%s" % (info['xxbcInfo']['courseName'], info['xxbcInfo']['cpRate'], info['xxbcInfo']['cpScore']))
    
    # 价格计算器
    d1 = 6
    d2 = 4
    d3 = 2
    money = 0
    if TotalVideo > 200:
        if TotalVideo > 600:
            money = (200 * d1) + (400 * d2) + ((TotalVideo - 600) * d3)
        else:
            money = (200 * d1) + ((TotalVideo - 200) * d2)
    else:
        money = TotalVideo * 6
    print("总时长为: %d Min - 预计金额：%.2f CNY" % (TotalVideo, money / 100))
    
    input()