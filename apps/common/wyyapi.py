#-*- coding:utf-8 –*-
import hashlib,requests,json,time
import sys


AppKey = '0151eb211fb26ebf020684cfd8125624'
AppSecret = '269163c64b9e'

apiurl = {
	'send_code': 'https://api.netease.im/sms/sendcode.action',
 	'check_code': 'https://api.netease.im/sms/verifycode.action',
}

#状态码 http://dev.netease.im/docs/product/IM%E5%8D%B3%E6%97%B6%E9%80%9A%E8%AE%AF/%E6%9C%8D%E5%8A%A1%E7%AB%AFAPI%E6%96%87%E6%A1%A3/code%E7%8A%B6%E6%80%81%E8%A1%A8


# 验证码发送
def sendcode(mobile):
	TEMPLATEID = "9374242"
	CODELEN = "6"
	body = ('templateid=%s&mobile=%s&codeLen=%s' % (TEMPLATEID, mobile, CODELEN)).encode("utf-8")
	nonce = '575728120'  # 随机数（最大长度128个字符）
	curTime = str(int(time.time()))
	checkSum = AppSecret + nonce + curTime
	checkSum = hashlib.sha1(checkSum.encode("utf-8")).hexdigest()
	headers = {'content-type': 'application/x-www-form-urlencoded;charset=utf-8',
			   'AppKey': AppKey,
			   'Nonce': nonce,
			   'CurTime': curTime,
			   'CheckSum': checkSum}
	response = requests.post(apiurl['send_code'], data=body, headers=headers)
	if response.status_code == 200:
		try:
			jsonData = json.loads(response.text)
			print(jsonData)
			if jsonData['code'] == 200:
				print(jsonData['obj'])
				return jsonData['obj']
		except ValueError:
			jsonData = None
	return None
# 验证码校验
def checkcode(mobile, code):
	body = ('mobile=%s&code=%s' % (mobile, code)).encode("utf-8")
	nonce = '575728120'  # 随机数（最大长度128个字符）
	curTime = str(int(time.time()))
	checkSum = AppSecret + nonce + curTime
	checkSum = hashlib.sha1(checkSum.encode("utf-8")).hexdigest()
	headers = {'content-type': 'application/x-www-form-urlencoded;charset=utf-8',
			   'AppKey': AppKey,
			   'Nonce': nonce,
			   'CurTime': curTime,
			   'CheckSum': checkSum}
	response = requests.post(apiurl['check_code'], data=body, headers=headers)
	if response.status_code == 200:
		try:
			jsonData = json.loads(response.text)
			if jsonData['code'] == 200:
				return True
		except ValueError:
			jsonData = None
	return None

