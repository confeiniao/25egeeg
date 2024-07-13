# coding=utf-8
import urllib.request
import urllib.parse
import configparser
import datetime
import pywencai
import json
import sys

def send_weixin(text):
    url = 'https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=%s' % webhook_key
    headers = {'Content-Type': 'application/json'}
    data = {'msgtype': 'text', 'text': {'content': text}}
    data_json = json.dumps(data).encode('utf-8')
    req = urllib.request.Request(url, data=data_json, headers=headers, method='POST')
    with urllib.request.urlopen(req) as response:
        response_data = response.read()
        cuowu = json.loads(response_data)
    if cuowu['errcode'] == 0:
        print('微信推送成功')
    elif cuowu['errcode'] == 93000:
        gh_tuisong('群推送失败', '错误信息：', 'webhook_key错误')
        print('微信推送是失败，webhook_key错误')
    else:
        gh_tuisong('群推送失败', '错误代码：', cuowu['errcode'])
        print('微信推送是失败，错误代码：%s' % cuowu['errcode'])

def gh_tuisong(biaoti, neirong, canshu):
    bt = urllib.parse.quote(biaoti, safe='')
    nr = urllib.parse.quote('%s%s----%s' % (neirong, canshu, datetime.datetime.now()), safe='')
    with urllib.request.urlopen('http://www.pushplus.plus/send?token=%s&title=%s&content=%s&template=html' % (token, bt, nr)) as response:
        response_data = response.read().decode('utf-8')
        response_json = json.loads(response_data)
        if response_json['code'] == 200:
            print('公号提醒错误成功')
        else:
            print('公号提醒失败，错误提示：%s' % response_json['msg'])

webhook_key = '0ecd045f-082d-4c8c-b5cd-b5d62b3f9a38'
token = '7700b291a13d4d1eaefdf7fc29c48267'
wenju = '非ST；54天内的3天3板；'

with open('./%s' % wenju, 'r', encoding='utf-8') as file:
    data = file.read()
if data:
    print('条件：%s' % data)
else:
    send_weixin('条件配置为空（py）')
    print('条件配置为空，已退出程序')
    sys.exit()

try:
    pywencai_res = pywencai.get(query=data, loop=True, sleep=3)
    gupiao_res = pywencai_res['股票代码'].tolist()
    now = datetime.datetime.now()
    fw_sj = now.strftime('%H:%M')
    if gupiao_res:
        pass
    else:
        send_weixin('----获取到空列表----\n已退出pywen程序\n访问时间：%s\n条件：%s' % (fw_sj, data))
        print('获取到0条信息，已退出程序')
        sys.exit()
    with open('/root/workspace/st/gupiaochi.txt', 'w', encoding='utf-8') as file:
        for code in gupiao_res:
            pure_number = code.split('.')[0]
            file.write(pure_number + '\n')
    send_weixin('----访问成功----\n访问时间：%s\n共索引到%s条信息\n条件：%s' % (fw_sj, len(gupiao_res), data))
    print('共索引到%s条信息'%len(gupiao_res))
except Exception as e:
    send_weixin('----访问失败----\n访问时间：%s\n错误提示：%s' % (fw_sj, e))