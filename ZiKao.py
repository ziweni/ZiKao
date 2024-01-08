#!/usr/bin/python3
#coding=utf8

import re
import time
import json
import base64
import logging
import requests
import hashlib
from requests import cookies

class ZiKao:

    # 初始化
    def __init__(self, ename, url, proxy=None):
        # 创建Http对象
        self.s = requests.session()
        # 设置全局Http协议头
        self.s.headers.update(
            {
                'Accept': "*/*",
                'Accept-Language': "zh-Hans-CN;q=1",
                'Connection': "keep-alive",
                'Accept-Encoding': "gzip, deflate, br",
                'User-Agent': "hnzikao/5.3.0 (iPhone; iOS 13.3.1; Scale/2.00)"
            })
        # 设置目标学校
        self.ename = ename
        # 设置服务器地址
        self.url = url
        # 初始化变量
        self.token = None
        # 使用代理访问
        if proxy != None:
            self.s.proxies.update({
                "http": proxy,
                "https": proxy
            })

    # 登陆
    def login(self, u_name, u_pass):
        try:
            r = self.s.get("{0}/WebApiZK/LoginInfo/Login?ename={1}&username={2}&Password={3}".format(self.url, self.ename, u_name, u_pass))
            o = json.loads(r.text)
            if o['success']:
                self.token = o['data']['token']
            return o['success']
        except Exception as a:
            logging.error(a)
            return False
    
    # Token 取 Cookies
    def loginShow(self):
        try:
            r = self.s.get("{0}/WebApiZK/LoginInfo/LoginShow?token={1}&ename={2}".format(self.url, self.token, self.ename))
            o = json.loads(r.text)
            return o['success']
        except Exception as a:
            logging.error(a)
            return False
        
    # 获取专业列表
    def getMajorList(self):
        try:
            r = self.s.get("{0}/WebApiZK/MajorInfo/Semesters?token={1}&ename={2}".format(self.url, self.token, self.ename))
            o = json.loads(r.text)
            if o['success']:
                return o['data']
            else:
                return []
        except Exception as a:
            logging.error(a)
            return []

    # 获取课程列表
    def getCourseList(self, majorId):
        try:
            r = self.s.get("{0}/WebApiZK/CourseInfo/getCourseList?token={1}&ename={2}&majorID={3}".format(self.url, self.token, self.ename, majorId))
            o = json.loads(r.text)
            if o['success']:
                return o['data']
            else:
                return []
        except Exception as a:
            logging.error(a)
            return []

    # 获取课程详细信息
    def getDetaiList(self, majorId, TypeID, courseId, Type, examType=1):
        try:
            if Type == 1:
                uri = "{0}/WebApiZK/CourseInfoList/getCourseDetailList?ID={1}&ProceduralTypeID={2}&ename={3}&majorID={4}&token={5}".format(self.url, courseId, TypeID, self.ename, self.ename, self.token)
            elif Type == 2:
                uri = "{0}/WebApiZK/ExamInfoList/getExamDetailList?ID={1}&ProceduralTypeID={2}&ename={3}&majorID={4}&examType={5}&token={6}".format(self.url, courseId, TypeID, self.ename, self.ename, examType, self.token)
            r = self.s.get(uri)
            o = json.loads(r.text)
            if o['success']:
                return o['data']
            else:
                return []
        except Exception as a:
            logging.error(a)
            return []

    # 上传人脸信息
    def uploadFace(self, username, faceConfig):
        headers = {
            'Content-Type': "application/json; charset=utf-8",
            'Accept-Encoding': "gzip, deflate, br",
        }
        try:
            faceImage = self.s.get(faceConfig['imageURL']).content
            data = {
	            'ename': self.ename,
	            'FaceType': '1',
                'TypeName': faceConfig['TypeName'],
	            'UploadType': faceConfig['UploadType'],
	            'token': self.token,
                'ProceduralTypeID': faceConfig['ProceduralTypeID'],
	            'ID': str(faceConfig['ID']),
                'SourseImgBase64': str(base64.b64encode(faceImage), "utf-8"),
            }
            r = self.s.post("{0}/WebApiZK/LoginInfo/FaceCompare".format(self.url), data=json.dumps(data), headers=headers)
            o = json.loads(r.text)
            if o['success']:
                return True
            else:
                return False
        except Exception as a:
            logging.error(a)
            return False

    # 获取试题地址
    def getExamInfo(self, url):
        while True:
            try:
                r = self.s.get(url)
                o = json.loads(r.text)
                if not o['success']:
                    return []
                url = o['url']
                if 'userExam' in o:
                    return o  
            except Exception as a:
                logging.error(a)
                return False

    # 解析试题
    def analysisExam(self, url):
        try:
            ret = []
            r = self.s.get(url)
            questionList = re.findall(r'<div class="ui-question ui-question-(.*?)</ul>', r.text, re.DOTALL)
            if len(questionList) == 0:
                questionList = re.findall(r'<div class="ui-question (.*?)</ul>', r.text, re.DOTALL)
            for question in questionList:
                try:
                    question = question + "</ul>"
                    q = re.findall(r'id="q_(.*?)"', question)[0]
                    psq = re.findall(r'code="psq_(.*?)"', question)[0]
                    q_text = re.findall(r'<div class="ui-question-content-wrapper">(.*?)</div>', question, re.DOTALL)[0].replace("\n","").strip();
                    a = re.findall(r'<ul class="ui-question-options">(.*?)</ul>', question, re.DOTALL)
                    if len(a) > 0:
                        a_text = re.findall(r'<div class="ui-question-content-wrapper">(.*?)</div>', a[0], re.DOTALL)
                    else:
                        a_text = []
                except IndexError:
                    continue
                options = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm']
                a = {}
                for k,v in enumerate(a_text):
                    a[options[k]] = v.replace("\n","").strip()
                ret.insert(len(ret), {
                    'q': int(q),
                    'psq': int(psq),
                    'q_text': q_text,
                    'a': a
                })
            return ret
        except Exception as a:
            logging.error(a)
            return []

    # 获取做题记录
    def getExamRecord(self, url):
        try:
            r = self.s.get(url)
            o = json.loads(r.text)
            if o['success']:
                r = self.s.get(o['url'])
                o = json.loads(r.text)
                if o['success']:
                    return o['records']
            return []
        except Exception as a:
            logging.error(a)
            return []

    # 上报试题信息
    def saveAnswer(self, context, userExamId, psq, q, a):

        headers = {
            'Content-Type': "application/x-www-form-urlencoded",
            'Accept-Encoding': "gzip, deflate, br",
        }

        stime = int(time.time()*1000)

        data = f"answer={a}&psqId={psq}&questionId={q}&right=false&score=0&stime={stime}"
        m = hashlib.md5((f"{data}&key={q}{userExamId}").encode("utf-8")).hexdigest()
        data = f"{data}&attach=&m={m}"
        try:
            r = self.s.post(f"{context}/student/exam/myanswer/newSave/{userExamId}/{q}", headers=headers, data=data)
            o = json.loads(r.text)
            return o['success']
        except Exception as a:
            logging.error(a)
            return False

    # 试题提交
    def submitAnswer(self, context, userExamId):

        headers = {
            'Content-Type': "application/x-www-form-urlencoded",
            'Accept-Encoding': "gzip, deflate, br",
        }

        try:
            r = self.s.post("{0}/student/exam/submit/{1}".format(context, userExamId), headers=headers)
            o = json.loads(r.text)
            return o['success']
        except Exception as a:
            logging.error(a)
            return False

    # 获取试题成绩
    def getAnswerResult(self, context, userExamId):

        try:
            r = self.s.get("{0}/student/exam/finished/json/{1}".format(context, userExamId))
            o = json.loads(r.text)
            if o['success']:
                r = self.s.get(o['seeScoreUrl'])
                o = json.loads(r.text)
                if o['success']:
                    return o['score']
            return -1
        except Exception as a:
            logging.error(a)
            return -1

    # 查询试卷答案
    def getExamAnswer(self, context, userExamId):
        try:
            r = self.s.get("{0}/student/exam/answer/{1}".format(context, userExamId))
            o = json.loads(r.text)
            if o['success']:
                return o['answers']
            return []
        except Exception as a:
            logging.error(a)
            return []

    # 验证码验证; 用于做题
    def verify(self, courseId, code):
        try:
            r = self.s.get("{0}/WebApiZK/ExamVerificate/Verificate?ID={1}&VerificateCode={2}&ename={3}&token={4}".format(self.url, courseId, code, self.ename, self.token))
            o = json.loads(r.text)
            if o['success']:
                return o['data']['IsSuccess']
            return False
        except Exception as a:
            logging.error(a)
            return False

    # 获取视频列表
    def getVideoList(self, param):

        headers = {
            'Content-Type': "application/json; charset=utf-8",
            'Accept-Encoding': "gzip, deflate, br",
        }

        try:
            data = json.dumps({
                'maxTimePerDay': param['maxTimePerDay'],
    	        'accumulativeTime': param['accumulativeTime'],
                'serverUrl': param['serverUrl'],
    	        'lastTime': param['lastTime'],
                'maxTimePerTime': param['maxTimePerTime'],
    	        'timestamp': param['timestamp'],
                'hintPoint': param['hintPoint'],
    	        'businessLineCode': param['businessLineCode'],
    	        'clientCode': param['clientCode'],
    	        'userId': param['userId'],
    	        'userName': param['userName'],
    	        'isQuestion': param['isQuestion'],
    	        'videoTime': param['videoTime'],
    	        'coursewareCode': param['coursewareCode'],
    	        'courseCodeN': param['courseCodeN'],
    	        'catalogId': param['catalogId'],
    	        'clientKey': param['clientKey'],
    	        'publicKey': param['publicKey']
            })

            r = self.s.post("http://cws.edu-edu.com/appApi/catalogs", data=data, headers=headers)
            o = json.loads(r.text)
            if o['success']:
                return o['data']
            return []
        except Exception as a:
            logging.error(a)
            return []

    # 获取视频详情
    def getVideoInfo(self, id, param):

        headers = {
            'Content-Type': "application/json; charset=utf-8",
            'Accept-Encoding': "gzip, deflate, br",
            'User-Agent': "hnzikao/1.9.1 (iPhone; iOS 13.3.1; Scale/2.00)"
        }
        try:
            data = json.dumps({
                'maxTimePerDay': param['maxTimePerDay'],
	            'accumulativeTime': param['accumulativeTime'],
                'serverUrl': param['serverUrl'],
	            'lastTime': param['lastTime'],
	            'maxTimePerTime': param['maxTimePerTime'],
	            'timestamp': param['timestamp'],
	            'hintPoint': param['hintPoint'],
	            'businessLineCode': param['businessLineCode'],
	            'clientCode': param['clientCode'],
	            'userId': param['userId'],
	            'userName': param['userName'],
	            'isQuestion': param['isQuestion'],
	            'videoTime': param['videoTime'],
	            'coursewareCode': param['coursewareCode'],
	            'courseCodeN': param['courseCodeN'],
	            'catalogId': param['catalogId'],
	            'clientKey': param['clientKey'],
	            'publicKey': param['publicKey']
            })
            r = self.s.post("https://cws.edu-edu.com/appApi/catalogInfo/{0}".format(id), data=data, headers=headers)
            o = json.loads(r.text)
            if o['code'] == 0:
                return o['data']
            return None
        except Exception as a:
            logging.error(a)
            return None

    # 数据上报
    def updataVideo(self, catalogId, param, lastTime, accumulativeTime, videoTime, examinePoint, questionId, isPass, learnRecordId=None):

        headers = {
            'Content-Type': "application/json; charset=utf-8",
            'Accept-Encoding': "gzip, deflate, br",
            'User-Agent': "hnzikao/1.9.1 (iPhone; iOS 13.3.1; Scale/2.00)"
        }
        try:
            data = {
            	"coursewareCode": param['coursewareCode'],
            	"maxTimePerDay": param['maxTimePerDay'],
            	"learnRecordId": learnRecordId,
            	"catalogId": catalogId,
            	"clientCode": param['clientCode'],
            	"lastTime": str(lastTime),
            	"hintPoint": 1,
            	"isQuestion": True,
            	"courseCodeN": "",
            	"clientKey": param['clientKey'],
            	"isPass": isPass,
            	"maxTimePerTime": param['maxTimePerTime'],
            	"serverUrl": param['serverUrl'],
            	"questionId": questionId,
            	"accumulativeTime": accumulativeTime,
            	"videoTime": str(videoTime),
            	"publicKey": param['publicKey'],
            	"timestamp": str(int(time.time() * 1000)),
            	"examinePoint": examinePoint,
            	"businessLineCode": "",
            	"userName": param['userName'],
            	"userId": param['userId']
            }

            r = self.s.put("http://cws.edu-edu.com/appApi/learnRecords", data=json.dumps(data), headers=headers)
            o = json.loads(r.text)
            if not o['success']:
                return False
                
            r = self.s.post(o['data']['backUrl'], data=json.dumps(o['data']), headers=headers)
            o2 = json.loads(r.text)

            if o2['success']:
                return o['data']
            return False
        except Exception as a:
            logging.error(a)
            return False
    
    # 获取用户信息
    def getInfo(self):
        try:        
            r = self.s.get("{0}/WebApiZK/StuInfo/getInfo?ename={1}&token={2}".format(self.url, self.ename, self.token))
            o = json.loads(r.text)
            if o['success']:
                return o['data']
            return None
        except Exception as a:
            logging.error(a)
            return None

    # 获取视频测验
    def getVideoLang(self, courseId, TypeId):
        try:        
            r = self.s.get("{0}/WebApiZK/CourseInfoList/getCourseLanguageList?ID={1}&ProceduralTypeID={2}&ename={3}&token={4}".format(self.url, courseId, TypeId, self.ename, self.token))
            o = json.loads(r.text)
            if o['success']:
                return o['data']
            return []
        except Exception as a:
            logging.error(a)
            return []
        
    # 查询课程学习报告
    def getCourseInfo(self, courseId, ProceduralTypeID, courseSource):
        try:        
            r = self.s.get("{0}/WebApiZK/CourseInfoDetail/Show?ProceduralTypeID={1}&courseSource={2}&ename={3}&id={4}&token={5}".format(self.url, ProceduralTypeID, courseSource, self.ename, courseId, self.token))
            o = json.loads(r.text)
            if o['success']:
                return o['data']
            return []
        except Exception as a:
            logging.error(a)
            return []