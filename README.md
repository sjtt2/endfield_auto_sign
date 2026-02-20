# endfield-auto-sign终末地森空岛自动签到

适用于青龙面板的终末地森空岛签到脚本

- 支持多账号
- 支持国服 & 国际服
- 支持青龙面板多平台推送

![Python](https://img.shields.io/badge/Python-3.7+-blue?logo=python&logoColor=white)
![Platform](https://img.shields.io/badge/Platform-青龙面板-blue?logo=linux)
![Game](https://img.shields.io/badge/Game-终末地-orange?logo=arknights)
![Last Commit](https://img.shields.io/github/last-commit/sjtt2/endfield_auto_signin)


此脚本在原项目的基础上进行了以下改进：

- ✅ 适配终末地的签到接口
- ✅ 优化了签到结果的格式化打印
- ✅ 添加了国际服支持

**原项目**: https://github.com/Zerolouis/skyland_auto_sign_qinglong

**原项目的原项目**：https://gitee.com/FancyCabbage/skyland-auto-sign
`(这个项目1.4起版本已支持终末地)`


## 快速开始

### 步骤 1：青龙面板添加订阅

| 项目 | 值 |
| :--- | :--- |
| 名称 | `终末地签到` |
| 地址 | `https://github.com/sjtt2/endfield_auto_sign.git` |
| 分支 | `master` |
| 定时 | `0 0 23 * * *` |

### 步骤 2：添加环境变量

在青龙面板中添加环境变量：

| 服务器 | 环境变量名 | 示例值 |
| :---: | :--- | :--- |
| 国服 | `SKYLAND_TOKEN` | `token1;token2;token3` |
| 国际服 | `SKPORT_TOKEN` | `token1;token2` |

> 💡 多账号使用英文分号 `;` 分隔，单账号不需要分号

Token获取方式：[如何获取 Token？](#获取token)

### 步骤 3：运行脚本

- 默认定时：`0 30 8 * * *` （每天上午8:30自动签到）
- 也可以手动点击"运行"立即测试

## 获取Token

### 国服
1. 登录[森空岛](https://www.skland.com/)

2. 访问这个网址 https://web-api.skland.com/account/info/hg

   会返回如下信息

   ```json
   {
     "code": 0,
     "data": {
       "content": "Token"
     },
     "msg": "接口会返回您的鹰角网络通行证账号的登录凭证，此凭证可以用于鹰角网络账号系统校验您登录的有效性。泄露登录凭证属于极度危险操作，为了您的账号安全，请勿将此凭证以任何形式告知他人！"
   }
   ```

   data.content即为token

### 国际服
1. 登录[skport](https://www.skport.com/)

2. 访问这个网址 https://web-api.skport.com/cookie_store/account_token

   会返回如下信息

   ```json
   {
      "code":0,
      "data":{
         "content":"Token"
         },
         "msg":""}
   ```

   data.content即为token
## 通知(可选)

适配了青龙面板的多平台推送

1. **在青龙面板添加环境变量**
   
   名称: `SKYLAND_NOTIFY`

   值:`true`(设置为`false`或不添加此变量则不推送)


2. **配置推送渠道**

   在青龙面板`配置文件`中的`config.sh`中填入相对应的推送API的环境变量即可

### 支持的推送方式
以下内容在`config.sh`中配置，不需要自己创建环境变量

| 推送方式 | 需要配置的核心环境变量 |
| :--- | :--- |
| **Server 酱** | `PUSH_KEY` |
| **Bark (iOS)** | `BARK_PUSH` |
| **Telegram** | `TG_BOT_TOKEN`, `TG_USER_ID` |
| **钉钉机器人** | `DD_BOT_TOKEN`, `DD_BOT_SECRET` |
| **企业微信机器人** | `QYWX_KEY` |
| **企业微信应用** | `QYWX_AM` |
| **iGot 聚合** | `IGOT_PUSH_KEY` |
| **Push Plus** | `PUSH_PLUS_TOKEN` |
| **微加机器人** | `WE_PLUS_BOT_TOKEN` |
| **go-cqhttp** | `GOBOT_URL`, `GOBOT_TOKEN` |
| **Gotify** | `GOTIFY_URL`, `GOTIFY_TOKEN` |
| **PushDeer** | `DEER_KEY` |
| **Synology Chat** | `CHAT_URL`, `CHAT_TOKEN` |
| **智能微秘书** | `AIBOTK_KEY` |
| **CHRONOCAT** | `CHRONOCAT_URL`, `CHRONOCAT_TOKEN` |
| **SMTP 邮件** | `SMTP_SERVER`, `SMTP_EMAIL`, `SMTP_PASSWORD` |
| **PushMe** | `PUSHME_KEY` |
| **飞书机器人** | `FSKEY` |
| **Qmsg 酱** | `QMSG_KEY` |
| **Ntfy** | `NTFY_TOPIC`, `NTFY_URL` |
| **wxPusher** | `WXPUSHER_APP_TOKEN`, `WXPUSHER_UIDS` |
| **自定义 Webhook** | `WEBHOOK_URL`, `WEBHOOK_METHOD` |

仅测试了`钉钉`的推送，如有问题请反馈

> [!TIP]
> 详细的变量名称和渠道支持，请直接参考 `config.sh` 

---

## 其他说明

### 1. 代理配置（国际服用户可能需要）

如果无法直接访问国际服接口，可以在青龙面板添加代理环境变量：

| 环境变量 | 示例值 |
| :--- | :--- |
| `http_proxy` | `http://127.0.0.1:7890` |
| `https_proxy` | `http://127.0.0.1:7890` |

> 💡 Docker 容器内访问宿主机代理时，将 `127.0.0.1` 改为宿主机局域网 IP（如 `192.168.x.x`）
> 
> ⚠️ 注意：环境变量名使用**小写** `http_proxy` / `https_proxy`

### 2. 依赖安装

本脚本运行需要 `requests` 库，青龙面板一般自带。若缺失：

1. 进入 `依赖管理` -> `Python3`
2. 点击 `创建依赖`
3. 输入 `requests` 并保存

### 3. 自定义消息（Webhook）

如果你使用自定义 Webhook，可以在 URL 或 Body 中使用以下占位符：

- `$title`: 邮件/消息标题（如：终末地每日签到结果）
- `$content`: 详细的签到状态汇总