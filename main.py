# /usr/bin/python3
# coding=utf8

import os
import sys
import yaml
import time
import random
import logging
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
            print("❌ 未提供配置文件!")
            exit(-1)
        # 加载配置
        with open(sys.argv[1], "r", encoding='utf-8') as f:
            data = f.read()
        # 读取配置文件
        config = yaml.safe_load(data)
    except IOError:
        print("❌ 初始化时出现错误：没找到配置文件！")
        exit(-1)
    except yaml.YAMLError as exc:
        print("❌ 初始化时出现错误：配置文件异常！")
        exit(-2)

    # 初始化网课操作对象
    obj = ZiKao(config['member']['ename'], config['member']['url'])

    log("\n⏳ 开始登陆……")

    if obj.login(str(config['member']['user']), str(config['member']['pass'])):
        obj.loginShow()
        print("✅ 账号密码登陆成功!")
    else:
        print("❌ 登陆失败！")
        exit(-1)

    try:
        log("⏳ 正在获取专业信息……")
        # 获取专业信息
        major = obj.getMajorList()

        majorId = major['majorid']
        majorName = major['majorname']
        # 获取账号信息
        account = obj.getInfo()
        log("⚡️  %s - %s" % (account['bkSchoolName'], account['name']))

        os.system("title %s %s" % (account['name'], str(config['member']['user'])))

        log("📖 专业名称：《%s》\n" % majorName)
        if not 'imgURL' in account or account['imgURL'] == '':
            print("❌ 未上传头像无法执行刷课！")
            exit(-1)
        log("⏳ 正在获取课程列表……\n")
        # 获取专业课程列表
        course = obj.getCourseList(majorId)

        # 遍历课程； 分别处理
        for item in course:
            # 判断课程是否已经达到 100
            if not item['score'] < 100:
                continue

            log("📖 执行课程《%s》" % item['name'])
            log("⏳ 正在查询完成状态……")

            # 提取视频
            if item['courseware']:
                video = obj.getDetaiList(majorId, item['ProceduralTypeID'], item['id'], 1)
            
            if 'video' in dir():
                for item2 in video:
                    if item2['cws_param']['accumulativeTime'] >= item2['cws_param']['videoTime']:
                        # 取测验列表
                        videoLangList = obj.getVideoLang(item['id'], item['ProceduralTypeID'])
                        # 判断测验是否完成
                        contini = False
                        # 未完成的测验
                        questionIdList = []

                        for value in videoLangList:
                            if value['isPass'] != 1:
                                contini = True
                                questionIdList.insert(0, value['questionId'])
                        if not contini:
                            break
                        log("⏳ 正在自动完成测验……")
                        # 可有可无的人脸识别
                        if not obj.uploadFace(config['member']['user'], item2['faceConfig']):
                            log("❌ 请注意，人脸识别出现异常！")
                        # 获取视频列表
                        videoList = obj.getVideoList(item2['cws_param'])
                        # 遍历视频完成测验
                        for videoItem in videoList:
                            # 防频繁
                            time.sleep(2)
                            # 没完成; 就获取详情
                            videoInfo = obj.getVideoInfo(videoItem['id'], item2['cws_param'])
                            # 没题目就跳过
                            if videoInfo == None or len(videoInfo['questions']) == 0:
                                continue
                            # 判断没完成的题目是否在本视频中
                            for questions in videoInfo['questions']:
                                contini = False
                                if questions['questionId'] in questionIdList:
                                    contini = True
                                    break
                            if not contini:
                                continue
                            # 获取总时长
                            videoTime = int(videoItem['mediaDuration'])
                            # 数据进度Key
                            learnRecordId = None
                            # 试题测验上报
                            for questions in videoInfo['questions']:
                                res = obj.updataVideo(videoItem['id'], item2['cws_param'], questions['mediaTime'], random.randint(1, 60), videoTime, questions['examinePoint'], questions['questionId'], True, learnRecordId)
                                if res != False:
                                    learnRecordId = res['learnRecordId']
                        continue
                    # 防频繁
                    time.sleep(1)
                    # 可有可无的人脸识别
                    if not obj.uploadFace(config['member']['user'], item2['faceConfig']):
                        log("❌ 请注意，人脸识别出现异常！")

                    log("⏳ 正在获取视频列表……")

                    # 获取视频列表
                    videoList = obj.getVideoList(item2['cws_param'])
                    # 遍历并完成
                    for videoItem in videoList:
                        # 判断是否是视频
                        if not videoItem['isMedia']:
                            continue
                        # 防频繁延迟
                        time.sleep(1.5)
                        # 如果已经完成; 就跳过
                        if int(videoItem['validTime']) >= int(videoItem['mediaDuration']):
                            continue
                        # 没完成; 就获取详情
                        videoInfo = obj.getVideoInfo(videoItem['id'], item2['cws_param'])
                        # 获取总时长
                        videoTime = int(videoItem['mediaDuration'])
                        # 有效时间
                        validTime = 0 # int(videoItem['validTime'])
                        # 累计时长
                        accumulativeTime = 0
                        if videoInfo['learnRecord'] != None and 'accumulativeTime' in videoInfo['learnRecord']:
                            accumulativeTime = int(videoInfo['learnRecord']['accumulativeTime'])
                        # 进度
                        index = 0
                        # 数据进度Key
                        learnRecordId = None

                        log("\n📺 视频《%s》" % videoInfo['title'])
                        log("⏰ 时长：%.2f 分钟" % (videoTime / 60))
                        log("⏳ 正在自动完成……")
                        # 开启进度条
                        with alive_bar(videoTime) as bar:
                            # 进度恢复
                            for i in range(validTime):
                                bar()
                            # 视频播放模拟
                            while True:
                                # 延迟一秒
                                time.sleep(1)

                                # 试题测验上报
                                for questions in videoInfo['questions']:
                                    if int(questions['mediaTime']) == index + validTime:
                                        res = obj.updataVideo(videoItem['id'], item2['cws_param'], index + validTime, index, videoTime, questions['examinePoint'], questions['questionId'], True, learnRecordId)
                                        if res:
                                            learnRecordId = res['learnRecordId']

                                # 上报判断
                                if index % 60 == 0 and index != 0:
                                    res = obj.updataVideo(videoItem['id'], item2['cws_param'], index + validTime, index, videoTime, "0", "0", "0", learnRecordId)
                                    if res:
                                        learnRecordId = res['learnRecordId']
                                if index + validTime >= videoTime:
                                    res = obj.updataVideo(videoItem['id'], item2['cws_param'], videoTime, index, videoTime, "0", "0", "0", learnRecordId)
                                    break

                                # 上报结果异常判断
                                if 'res' in dir():
                                    if res == None:
                                        break

                                # 叠加计数器
                                index = index + 1

                                # 更新进度
                                bar()
                        if res != None:
                            log("✅ 已完成《%s》" % videoInfo['title'])
                        else:
                            log("❌ 上报失败《%s》" % videoInfo['title'])
            
            # 提取作业、考试
            if item['assignment']:
                info = { }
                info[1] = obj.getDetaiList(majorId, item['ProceduralTypeID'], item['id'], 2)
            if item['exam'] and (item['examMessage'] == None or item['examMessage'].find("未开启") == -1):
                if not 'info' in dir():
                    info = { }
                info[2] = obj.getDetaiList(majorId, item['ProceduralTypeID'], item['id'], 2, 2)

            if 'info' in dir():
                for key, value in info.items():
                    for item2 in value:
                        # 判断是否要验证码验证; 一个可有可无的功能
                        if item2['IsVerification']:
                            # 进行验证码验证
                            if not obj.verify(item['id'], config['member']['code']):
                                log("❌ 请注意，验证码验证失败！")
                        # 防频繁
                        time.sleep(1)
                        # 可有可无的人脸识别
                        if not obj.uploadFace(config['member']['user'], item2['faceConfig']):
                            log("❌ 请注意，人脸识别出现异常！")
                        # 获取提交记录
                        record = obj.getExamRecord(item2['test_url'])

                        # 判断是否已经满足要求
                        back = False
                        for rec in record:
                            if 'score' in rec and rec['score'] != None and rec['score'] >= 90:
                                back = True
                                break
                        if back:
                            continue

                        # 查询做题记录是否可以继续
                        for recordItem in record:
                            continueExam = False
                            if 'continueExamUrl' in recordItem and recordItem['score'] != None:
                                continueExam = True
                                break
                        # 不可继续做题，并且无可做题次数
                        if not ('continueExam' in dir() and continueExam) and item2['restExamTimes'] == 0:
                            continue
                        # 判断是否已经做过，且分数达到90+
                        if len(record) == 0 or not ('continueExam' in dir() and continueExam):
                            pass
                            # 没做过，就开始做题，再获取答案
                            exam = obj.getExamInfo(item2['stu_study'])
                            # 更新记录
                            record = obj.getExamRecord(item2['test_url'])


                        # 如果做过，但是未达到90+
                        # 则保存答案
                        try:
                            examAnswer = obj.getExamInfo(record[0]['viewPaperUrl'])
                            userExamId = examAnswer['userExam']['id']
                        except TypeError:
                            if key == 1:
                                # 重新做
                                exam = obj.getExamInfo(record[0]['continueExamUrl'])
                                userExamId = exam['userExam']['userExamId']
                                # 答案提交
                                obj.submitAnswer(exam['context'], userExamId)
                                # 重新获取
                                examAnswer = obj.getExamInfo(record[0]['viewPaperUrl'])
                                userExamId = examAnswer['userExam']['id']
                        # 读取答案
                        answer = obj.getExamAnswer(examAnswer['context'], userExamId)

                        # 答案信息
                        answerList = {}
                        for ans in answer:
                            answerList[ans['questionId']] = ans

                        # 重新做
                        exam = obj.getExamInfo(record[0]['continueExamUrl'])
                        userExamId = exam['userExam']['userExamId']

                        # 解析试题
                        examList = obj.analysisExam(exam['url'])

                        log("📃 试题《%s》" % item2['examName'])
                        log("📄 数目 %d 道" % len(examList))
                        log("⏳ 正在自动完成……")
                        # 进度条
                        with alive_bar(len(examList)) as bar:
                            # 遍历试题; 并提交答案
                            for examItem in examList:
                                # 模拟延迟
                                time.sleep(3)
                                # 读取答案
                                answer = answerList[examItem['q']]
                                # 保存答案
                                obj.saveAnswer(exam['context'], userExamId, examItem['psq'], examItem['q'], answer['answer'])
                                # 更新进度
                                bar()
                        log("⏳ 正在提交试题……")
                        # 提交延迟
                        time.sleep(5)
                        # 可有可无的人脸识别
                        if not obj.uploadFace(config['member']['user'], item2['faceConfig']):
                            log("❌ 请注意，人脸识别出现异常！")
                        # 答案提交
                        if obj.submitAnswer(exam['context'], userExamId):
                            log("✅ 提交成功!\n")
                        else:
                            log("❌ 提交失败!")
                            log("⚠️  已自动跳过!\n")
            log("🎉 已完成本课程所有任务！\n")
        log("\n🎉 你已完成了本专业的所有任务！")
        input()
    except Exception as e:
        logging.error(e)
        input()