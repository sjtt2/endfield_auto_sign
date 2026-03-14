#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
File: auto_sign.py
Author: sjtt2
cron: 0 30 8 * * *
new Env('终末地签到');
Update: 2026/2/20
"""
import hashlib
import hmac
import json
import os
import random
import time
from urllib import parse
import requests
import notify


# ========== 防封号配置 ==========
# 请求间隔范围（秒）：随机等待以模拟人类行为
REQUEST_DELAY_MIN = 2
REQUEST_DELAY_MAX = 8
# 账号之间的额外等待时间
ACCOUNT_DELAY_MIN = 15
ACCOUNT_DELAY_MAX = 45
# 签到请求前的等待时间
SIGN_DELAY_MIN = 3
SIGN_DELAY_MAX = 10

# User-Agent 池（模拟不同设备）
USER_AGENTS = [
    'Skland/1.0.0 (com.skland.grass; Android; SDK_INT 33; Build/TQ3A.230901.001)',
    'Skland/1.0.0 (com.skland.grass; Android; SDK_INT 34; Build/UP1A.231005.004)',
    'Skland/1.0.0 (com.skland.grass; Android; SDK_INT 35; Build/AP2A.240405.002)',
    'Skland/1.0.1 (skport; Android; SDK_INT 33; Build/TQ3A.230901.001)',
    'Skland/1.0.1 (skport; Android; SDK_INT 34; Build/UP1A.231005.004)',
]



# 初始化变量
skyland_notify = os.getenv('SKPORT_NOTIFY') or os.getenv('SKYLAND_NOTIFY') or ''
run_message: str = ''
account_num: int = 1
sign_token = ''
PLATFORM = '3'
VNAME = '1.0.0'
# ========== 配置 ==========
SERVER_CONFIG = {
    "cn": {
        "name": "国服",
        "ENV_TOKEN": "SKYLAND_TOKEN",
        "MANUAL_TOKENS": "",  # 如果你想直接写token就在这里填，多个用 ; 分隔
        "APP_CODE": "4ca99fa6b56cc2ba",
        "GRANT_URL": "https://as.hypergryph.com/user/oauth2/v2/grant",
        "CRED_URL": "https://zonai.skland.com/api/v1/user/auth/generate_cred_by_code",
        "BIND_URL": "https://zonai.skland.com/api/v1/game/player/binding",
        "SIGN_URL": "https://zonai.skland.com/api/v1/game/endfield/attendance",
    },
    "global": {
        "name": "国际服",
        "ENV_TOKEN": "SKPORT_TOKEN",
        "MANUAL_TOKENS": "",  # 如果你想直接写token就在这里填，多个用 ; 分隔
        "APP_CODE": "6eb76d4e13aa36e6",
        "GRANT_URL": "https://as.gryphline.com/user/oauth2/v2/grant",
        "CRED_URL": "https://zonai.skport.com/web/v1/user/auth/generate_cred_by_code",
        "BIND_URL": "https://zonai.skport.com/api/v1/game/player/binding",
        "SIGN_URL": "https://zonai.skport.com/web/v1/game/endfield/attendance",
    }
}

# 请求头配置（优化，防封号）
BASE_HEADER = {
    'cred': '',
    'User-Agent': random.choice(USER_AGENTS),
    'Accept-Encoding': 'gzip',
    'Connection': 'keep-alive',
    'Accept': '*/*',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
}


def get_random_header():
    """获取随机化的请求头"""
    return {
        **BASE_HEADER,
        'User-Agent': random.choice(USER_AGENTS)
    }


def random_delay(min_sec=REQUEST_DELAY_MIN, max_sec=REQUEST_DELAY_MAX):
    """随机延迟，模拟人类操作"""
    delay = random.uniform(min_sec, max_sec)
    time.sleep(delay)

def send_notify(title, content):
    """
    消息推送，使用青龙推送脚本
    """
    if not skyland_notify or skyland_notify.strip().lower() == 'false':
        return
    notify.send(title, content)

    
def generate_sign(token, path, body):
    """生成接口签名"""
    t = str(int(time.time()))
    token = token.encode('utf-8')
    sign_header = {
        "platform": PLATFORM,
        "timestamp": t,
        "dId": "",
        "vName": VNAME
    }
    sign_header_str = json.dumps(sign_header, separators=(',', ':'))
    sign_str = path + body + t + sign_header_str
    hmac_hex = hmac.new(
        token,
        sign_str.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    md5_sign = hashlib.md5(hmac_hex.encode('utf-8')).hexdigest()
    return md5_sign, sign_header

def get_grant_code(token,cfg):
    """通过token获取grant code"""
    random_delay(1, 3)  # 请求前随机延迟
    try:
        t = json.loads(token)
        token = t['data']['content']
    except:
        pass
    resp = requests.post(
        cfg["GRANT_URL"],
        json={'appCode': cfg["APP_CODE"], 'token': token, 'type': 0},
        headers=get_random_header(),
        timeout=15
    ).json()
    if resp.get('status') != 0:
        raise Exception(f'获取grant code失败：{resp.get("msg", resp.get("message"))}')
    return resp['data']['code']

def get_cred(grant_code,cfg):
    """通过grant code获取cred和sign token"""
    global sign_token
    random_delay(1, 3)
    resp = requests.post(
        cfg["CRED_URL"],
        json={'code': grant_code, 'kind': 1},
        headers=get_random_header(),
        timeout=15
    ).json()
    if resp['code'] != 0:
        raise Exception(f'获取cred失败：{resp["message"]}')
    global sign_token
    sign_token = resp['data']['token']
    return resp['data']['cred']

def login(token,cfg):
    """森空岛登录逻辑"""
    grant = get_grant_code(token,cfg)
    cred = get_cred(grant,cfg)
    return cred

def get_endfield_roles(cred,cfg):
    """获取终末地绑定角色"""
    random_delay(2, 5)
    # 生成签名头
    parse_url = parse.urlparse(cfg["BIND_URL"])
    sign, sign_header = generate_sign(sign_token, parse_url.path, '')
    header = {
        'cred': cred,
        'platform': PLATFORM,
        'vName': VNAME,
        'timestamp': sign_header['timestamp'],
        'sk-language': 'en',
        'sign': sign,
        'Content-Type': 'application/json'
    }
    resp = requests.get(cfg["BIND_URL"], headers=header, timeout=15).json()
    if resp['code'] != 0:
        raise Exception(f'获取角色失败：{resp["message"]}')
    binding = None
    for app in resp['data']['list']:
        if app.get('appCode') == 'endfield' and app.get('bindingList'):
            binding = app['bindingList'][0]
            break
    if not binding:
        raise Exception('未绑定终末地角色')
    return binding

def do_daily_sign(cred,cfg):
    """执行签到"""
    global run_message, account_num
    try:
        roles = get_endfield_roles(cred,cfg)
        role = roles.get('defaultRole') or (roles.get('roles') and roles['roles'][0])
        role_str = f"3_{role['roleId']}_{role['serverId']}"
        # 签到前随机延迟，模拟人类行为
        random_delay(SIGN_DELAY_MIN, SIGN_DELAY_MAX)
        # 生成签到签名
        parse_url = parse.urlparse(cfg["SIGN_URL"])
        sign, sign_header = generate_sign(sign_token, parse_url.path, '')
        # 组装签到头
        header = {
            'cred': cred,
            'platform': PLATFORM,
            'vName': VNAME,
            'timestamp': sign_header['timestamp'],
            'sk-language': 'en',
            'sign': sign,
            'sk-game-role': role_str,
            'Content-Type': 'application/json'
        }
        # 发送签到请求（body为空）
        resp = requests.post(cfg["SIGN_URL"], headers=header, json=None, timeout=15).json()
        # 结果处理
        role_name = roles.get('defaultRole', {}).get('nickname', '未知角色')
        channel = roles.get('defaultRole', {}).get('serverName', '未知服务器')
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
            if "请勿重复签到" in error_msg or "Please do not sign in again!" in error_msg:
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
    global run_message, account_num
    print(f"终末地签到启动 {time.strftime('%Y-%m-%d %H:%M:%S')}")
    for cfg in SERVER_CONFIG.values():
        token_env = cfg.get("MANUAL_TOKENS") or os.getenv(cfg["ENV_TOKEN"], "")
        tokens = [t.strip() for t in token_env.split(";") if t.strip()]
        err_msg = ""
        if not tokens:
            err_msg = f"{cfg['name']} 没有配置 token，跳过..."
            run_message += err_msg + '\n'
            print(err_msg)
            continue
        for idx, token in enumerate(tokens, 1):
            print(f"\n===== 处理第{idx}个账号 =====")
            try:
                cred = login(token,cfg)
                do_daily_sign(cred,cfg)
            except Exception as e:
                err_msg = f"[{cfg['name']}] 账号{account_num} 异常：{str(e)}"
                run_message += err_msg + '\n'
                print(err_msg)
                account_num += 1
            # 账号之间增加随机延迟，避免高频请求被检测
            if idx < len(tokens):
                account_delay = random.uniform(ACCOUNT_DELAY_MIN, ACCOUNT_DELAY_MAX)
                print(f"等待 {account_delay:.1f} 秒后处理下一个账号...")
                time.sleep(account_delay)
    if run_message:
        send_notify('终末地签到结果', run_message)
    print(f"\n脚本执行结束 - {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"\n签到结果汇总：\n{run_message}")

if __name__ == "__main__":
    main()