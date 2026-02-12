#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
File: auto_sign.py(终末地签到)
Author: sjtt2
cron: 0 30 8 * * *
new Env('终末地签到');
Update: 2026/2/12
"""
import hashlib
import hmac
import json
import os
import time
from urllib import parse
import requests
import notify

# 全局配置
skyland_tokens = os.getenv('SKYLAND_TOKEN') or ''
skyland_notify = os.getenv('SKYLAND_NOTIFY') or ''
run_message: str = ''
account_num: int = 1
sign_token = ''

# 接口地址
SIGN_URL = "https://zonai.skland.com/api/v1/game/endfield/attendance"
BINDING_URL = "https://zonai.skland.com/api/v1/game/player/binding"
CRED_CODE_URL = "https://zonai.skland.com/api/v1/user/auth/generate_cred_by_code"
GRANT_CODE_URL = "https://as.hypergryph.com/user/oauth2/v2/grant"
APP_CODE = '4ca99fa6b56cc2ba'

# 请求头配置
BASE_HEADER = {
    'cred': '',
    'User-Agent': 'Skland/1.0.1 (com.hypergryph.skland; build:100001014; Android 31; ) Okhttp/4.11.0',
    'Accept-Encoding': 'gzip',
    'Connection': 'close'
}
LOGIN_HEADER = {
    'User-Agent': 'Skland/1.0.1 (com.hypergryph.skland; build:100001014; Android 31; ) Okhttp/4.11.0',
    'Accept-Encoding': 'gzip',
    'Connection': 'close'
}
SIGN_HEADER_TPL = {
    'platform': '',
    'timestamp': '',
    'dId': '',
    'vName': ''
}

def send_notify(title, content):
    if not skyland_notify:
        return
    nt = skyland_notify.strip()
    if nt == 'TG':
        notify.telegram_bot(title, content)
    elif nt == 'BARK':
        notify.bark(title, content)
    elif nt == 'PUSHPLUS':
        notify.pushplus_bot(title, content)
    elif nt == 'SERVERJ':
        notify.serverJ(title, content)
    elif nt == 'QYWXBOT':
        notify.wecom_bot(title, content)
    elif nt == 'DD':
        notify.dingding_bot(title, content)

def generate_sign(token, path, body):
    """生成接口签名"""
    t = str(int(time.time()) - 2)
    token = token.encode('utf-8')
    sign_header = json.loads(json.dumps(SIGN_HEADER_TPL))
    sign_header['timestamp'] = t
    sign_header_str = json.dumps(sign_header, separators=(',', ':'))
    sign_str = path + body + t + sign_header_str
    hmac_hex = hmac.new(token, sign_str.encode('utf-8'), hashlib.sha256).hexdigest()
    md5_sign = hashlib.md5(hmac_hex.encode('utf-8')).hexdigest()
    return md5_sign, sign_header

def get_sign_header(url, method, body, base_header):
    """组装带签名的请求头"""
    header = json.loads(json.dumps(base_header))
    parse_url = parse.urlparse(url)
    if method.lower() == 'get':
        sign, sign_header = generate_sign(sign_token, parse_url.path, parse_url.query)
    else:
        sign, sign_header = generate_sign(sign_token, parse_url.path, json.dumps(body))
    header['sign'] = sign
    header.update(sign_header)
    return header

def get_grant_code(token):
    """通过token获取grant code"""
    resp = requests.post(GRANT_CODE_URL, json={'appCode': APP_CODE, 'token': token, 'type': 0}, headers=LOGIN_HEADER, timeout=10).json()
    if resp['status'] != 0:
        raise Exception(f'获取grant code失败：{resp["msg"]}')
    return resp['data']['code']

def get_cred(grant_code):
    """通过grant code获取cred和sign token"""
    resp = requests.post(CRED_CODE_URL, json={'code': grant_code, 'kind': 1}, headers=LOGIN_HEADER, timeout=10).json()
    if resp['code'] != 0:
        raise Exception(f'获取cred失败：{resp["message"]}')
    global sign_token
    sign_token = resp['data']['token']
    return resp['data']['cred']

def login(token):
    """森空岛登录核心逻辑"""
    try:
        t = json.loads(token)
        token = t['data']['content']
    except:
        pass
    grant = get_grant_code(token)
    cred = get_cred(grant)
    return cred

def get_endfield_roles(cred):
    """获取终末地绑定角色"""
    header = get_sign_header(BINDING_URL, 'get', None, BASE_HEADER)
    header['cred'] = cred
    resp = requests.get(BINDING_URL, headers=header, timeout=10).json()
    if resp['code'] != 0:
        raise Exception(f'获取角色失败：{resp["message"]}')
    roles = []
    for app in resp['data']['list']:
        if app.get('appCode') == 'endfield':
            roles.extend(app.get('bindingList', []))
    if not roles:
        raise Exception('未绑定终末地角色')
    return roles

def do_daily_sign(cred):
    """执行签到"""
    global run_message, account_num
    roles = get_endfield_roles(cred)
    for role in roles:
        try:
            role_name = role.get('defaultRole', {}).get('nickname', '未知角色')
            channel = role.get('channelName', '未知渠道')
            # 组装签到POST参数
            sign_body = {
                'uid': role.get('uid'),
                'gameId': 3,  # 终末地固定gameId
                'roleId': role.get('defaultRole', {}).get('roleId'),
                'serverId': role.get('defaultRole', {}).get('serverId')
            }
            # 参数校验
            if not all([sign_body['roleId'], sign_body['serverId']]):
                msg = f'[账号{account_num}] {role_name}({channel}) - 缺少角色参数，无法签到'
                run_message += msg + '\n'
                print(msg)
                account_num += 1
                continue
            # 生成签名头并发送POST签到请求
            sign_header = get_sign_header(SIGN_URL, 'post', sign_body, BASE_HEADER)
            sign_header['cred'] = cred
            resp = requests.post(SIGN_URL, headers=sign_header, json=sign_body, timeout=10).json()
            # 处理签到结果
            if resp['code'] == 0:
                # 获取奖励ID列表和奖励详情映射
                award_ids = resp['data'].get('awardIds', [])
                resource_map = resp['data'].get('resourceInfoMap', {})

                if award_ids and resource_map:
                    # 遍历奖励ID，匹配详情并拼接奖励文本
                    award_text = []
                    for award in award_ids:
                        award_id = award.get('id')
                        if award_id and award_id in resource_map:
                            res = resource_map[award_id]
                            award_text.append(f'{res["name"]}x{res.get("count", 1)}')

                    if award_text:
                        msg = f'[账号{account_num}] {role_name}({channel}) - 每日签到成功！获得：{"、".join(award_text)}'
                    else:
                        msg = f'[账号{account_num}] {role_name}({channel}) - 每日签到成功（未识别到奖励信息）'
                else:
                    msg = f'[账号{account_num}] {role_name}({channel}) - 每日签到成功（无奖励信息）'
            else:
                # 错误处理逻辑（保持不变）
                error_msg = resp.get("message", "未知错误")
                if "请勿重复签到" in error_msg:
                    msg = f'[账号{account_num}] {role_name}({channel}) - 今日已签到，请勿重复签到'
                else:
                    msg = f'[账号{account_num}] {role_name}({channel}) - 签到失败：{error_msg}'

            run_message += msg + '\n'
            print(msg)
        except Exception as e:
            msg = f'[账号{account_num}] 角色处理失败：{str(e)}'
            run_message += msg + '\n'
            print(msg)
        finally:
            account_num += 1

def main():
    """脚本主入口"""
    global run_message
    print(f"终末地每日签到脚本启动 - {time.strftime('%Y-%m-%d %H:%M:%S')}")
    if not skyland_tokens.strip():
        run_message = '错误：未配置SKYLAND_TOKEN环境变量'
        print(run_message)
        send_notify('终末地每日签到', run_message)
        return
    # 处理多账号
    tokens = [t.strip() for t in skyland_tokens.split(';') if t.strip()]
    for idx, token in enumerate(tokens, 1):
        print(f"\n===== 处理第{idx}个账号 =====")
        try:
            cred = login(token)
            do_daily_sign(cred)
        except Exception as e:
            err_msg = f'[账号{account_num}] 账号处理失败：{str(e)}'
            run_message += err_msg + '\n'
            print(err_msg)
            account_num += 1
        if idx < len(tokens):
            time.sleep(10)
    # 发送通知并输出结果
    if run_message:
        send_notify('终末地每日签到结果', run_message)
    print(f"\n脚本执行结束 - {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"\n签到结果汇总：\n{run_message}")

if __name__ == "__main__":
    main()