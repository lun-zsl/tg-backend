import os, asyncio, re
from typing import List, Dict
from pydantic import BaseModel
from fastapi import FastAPI, BackgroundTasks, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from telethon import TelegramClient
from telethon.tl.functions.channels import InviteToChannelRequest, JoinChannelRequest
from telethon.errors import UserPrivacyRestrictedError, PeerFloodError, FloodWaitError, SessionPasswordNeededError
from telethon.tl.types import UserStatusOnline, UserStatusRecently

# 1. 核心配置与目录初始化
CONFIG = {
    "SESSION_DIR": "./sessions"
}
os.makedirs(CONFIG["SESSION_DIR"], exist_ok=True)

# 2. 初始化 FastAPI 服务
app = FastAPI()

# ======= 完美融入：拦截并忽略浏览器自带的 favicon 请求，消除终端红字 404 报错 =======
@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return Response(status_code=204)  # 返回 204 No Content
# =================================

# 3. 开启跨域支持
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 4. 全局状态控制
class GlobalState:
    is_running: bool = False
    realtime_logs: List[str] = []
    login_clients: Dict[str, TelegramClient] = {}

state = GlobalState()

# 5. 日志记录辅助函数
def append_log(msg: str):
    print(msg)
    state.realtime_logs.append(msg)
    if len(state.realtime_logs) > 100:
        state.realtime_logs.pop(0)

# 6. 请求数据结构定义
class SendCodeSchema(BaseModel):
    phone: str
    api_id: int
    api_hash: str

class VerifyCodeSchema(BaseModel):
    phone: str
    code: str
    password: str = None

class MultiPullTaskSchema(BaseModel):
    target_link: str
    pull_count: int
    source_groups: List[str]
    api_id: int
    api_hash: str

# 7. Telegram 用户名清洗规则
def parse_tg_username(input_str: str) -> str:
    if not input_str:
        return ""
    cleaned = input_str.strip().replace(" ", "")
    if "t.me/" in cleaned:
        cleaned = cleaned.split("t.me/")[-1]
    if "joinchat/" in cleaned:
        cleaned = cleaned.split("joinchat/")[-1]
    if "/" in cleaned:
        cleaned = cleaned.split("/")[-1]
    res = cleaned.replace("@", "")
    if "?" in res:
        res = res.split("?")[0]
    return res

# 8. 核心全自动多群拉人引擎
async def core_multi_pulling_engine(target: str, count: int, source_lines: List[str], api_id: int, api_hash: str):
    state.is_running = True
    session_files = [f for f in os.listdir(CONFIG["SESSION_DIR"]) if f.endswith(".session")]
    if not session_files:
        append_log("[安全拦截] 失败：云端未检测到登录账号，请先完成第一步登录！")
        state.is_running = False
        return
        
    first_session = session_files[0].replace(".session", "")
    client = TelegramClient(os.path.join(CONFIG["SESSION_DIR"], first_session), api_id, api_hash)
    
    try:
        await client.connect()
        target_username = parse_tg_username(target)
        append_log(f"[检测] 正在控制账号自动潜入目的地群组: @{target_username} ...")
        try:
            await client(JoinChannelRequest(target_username))
            append_log("[成功] 账号已全自动成功切入目的地群组内部！")
            await asyncio.sleep(3)
        except Exception as e:
            append_log(f"[进群状态] {str(e)}（若已在群内请忽略）")
            
        target_entity = await client.get_entity(target_username)
        append_log(f"[安全开跑] 多群合并采集就绪，源同行群共: {len(source_lines)} 个。\n")
        
        successful_pulls = 0
        for idx, current_source in enumerate(source_lines, start=1):
            if not state.is_running or successful_pulls >= count:
                break
            source_username = parse_tg_username(current_source)
            if not source_username:
                continue
            append_log(f"➔ 正在深度扫描第 [{idx}/{len(source_lines)}] 个源群组: @{source_username} ...")
            
            try:
                source_entity = await client.get_entity(source_username)
                async for user in client.iter_participants(source_entity):
                    if not state.is_running or successful_pulls >= count:
                        break
                    if not user.username or user.bot or user.deleted:
                        continue
                    if isinstance(user.status, (UserStatusOnline, UserStatusRecently)):
                        try:
                            await client(InviteToChannelRequest(target_entity, [user]))
                            successful_pulls += 1
                            append_log(f"[成功] 已成功邀请用户 @{user.username} 进入目的地群组 ({successful_pulls}/{count})")
                            await asyncio.sleep(5)  # 频率控制安全延迟
                        except UserPrivacyRestrictedError:
                            append_log(f"[拦截] 用户 @{user.username} 开启了隐私限制，无法强制拉入")
                        except PeerFloodError:
                            append_log("[警告] 触发官方频控限制(Flood)，当前账号需要休息！换群中...")
                            break
                        except Exception:
                            pass
            except Exception as e:
                append_log(f"[扫描错误] 无法读取群组 @{source_username}: {str(e)}")
    finally:
        if client.is_connected():
            await client.disconnect()
        state.is_running = False
        append_log("[结束] 任务运行完毕或已被手动停止。")

# 9. 首页核心集成：直接返回黑金前端管理控制台界面
@app.get("/", response_class=HTMLResponse)
async def serve_frontend():
    return """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>云端多群联合采集拉人系统 (通用商用版)</title>
<style>
:root { --bg-color: #121212; --panel-bg: #1e1e1e; --input-bg: #2d2d2d; --text-color: #e0e0e0; --primary-green: #00e676; --danger-red: #ff5252; --warning-orange: #ff9100; }
body { margin: 0; padding: 15px; background-color: var(--bg-color); color: var(--text-color); font-family: -apple-system, sans-serif; }
.container { max-width: 600px; margin: 0 auto; background: var(--panel-bg); border-radius: 12px; padding: 20px; box-shadow: 0 4px 20px rgba(0,0,0,0.5); }
h2 { text-align: center; margin-top: 0; color: #fff; font-size: 18px; border-bottom: 1px solid #333; padding-bottom: 15px; letter-spacing: 1px; }
.section { margin-bottom: 20px; padding: 15px; background: rgba(255,255,255,0.02); border-radius: 8px; border: 1px solid #333; }
.section-title { font-size: 14px; color: #fff; margin-bottom: 12px; font-weight: bold; }
.form-group { margin-bottom: 15px; }
label { display: block; font-size: 14px; margin-bottom: 8px; color: #bbb; font-weight: bold; }
input, textarea { width: 100%; padding: 14px; background: var(--input-bg); border: 1px solid #333; border-radius: 8px; color: #fff; box-sizing: border-box; margin-bottom: 10px; font-size: 15px; transition: all 0.3s; }
input:focus, textarea:focus { outline: none; border-color: var(--primary-green); background: #333; }
textarea { height: 140px; resize: none; line-height: 1.5; }
.btn-group { display: flex; gap: 12px; width: 100%; box-sizing: border-box; margin-top: 10px; }
.btn { flex: 1; padding: 14px; border: none; border-radius: 8px; font-size: 15px; font-weight: bold; cursor: pointer; display: flex; align-items: center; justify-content: center; gap: 6px; box-sizing: border-box; }
.btn-green { background-color: var(--primary-green); color: #000; }
.btn-red { background-color: var(--danger-red); color: #fff; }
.hidden { display: none !important; }
.log-panel { background: #0a0a0a; border: 1px solid #222; border-radius: 8px; height: 180px; overflow-y: auto; padding: 12px; font-family: monospace; font-size: 13px; line-height: 1.6; margin-top: 10px; }
.log-line { margin: 0 0 5px 0; white-space: pre-wrap; word-break: break-all; }
.log-success { color: #4caf50; }
.log-warning { color: var(--warning-orange); }
.log-error { color: var(--danger-red); }
</style>
</head>
<body>
<div class="container">
<h2>云端多群联合采集拉人系统 (通用商用版)</h2>
<div class="section">
<div class="section-title">🔑 专属开发者凭证配置</div>
<div id="login-step-1" class="form-group">
<label>API_ID</label>
<input type="number" id="api_id" value="38906005">
<label>API_HASH</label>
<input type="text" id="api_hash" value="9c4a2467d94a3d88818309c8b80ea183">
<label>操作号手机号</label>
<input type="text" id="phone" value="+2347064991293">
<button style="margin-top: 8px;" class="btn btn-green" id="btn-send-code">🚀 发送验证码</button>
</div>
<div id="login-step-2" class="form-group hidden">
<input type="text" id="code" placeholder="输入 5 位验证码">
<input type="password" id="2fa-pwd" placeholder="两步验证密码 (若无则不填)" style="margin-top:8px;">
<div class="btn-group">
<button class="btn" style="background-color:#444; color:#fff;" id="btn-back">返回</button>
<button class="btn btn-green" id="btn-verify">确认验证登录</button>
</div>
</div>
</div>
<div class="section">
<div class="section-title">🎯 拉人任务分配</div>
<div class="form-group">
<label>你的目的地群组链接</label>
<input type="text" id="target_group" value="https://t.me">
</div>
<div class="form-group">
<label>要拉取的数量</label>
<input type="number" id="pull_count" value="100">
</div>
<div class="form-group">
<label>采集群 (一行放一个群)</label>
<textarea id="source_groups" placeholder="https://t.me"></textarea>
</div>
<div class="btn-group">
<button id="btn-start" class="btn btn-green">🔥 开始运行</button>
<button id="btn-stop" class="btn btn-red">🛑 停止运行</button>
</div>
</div>
<div class="section">
<div class="section-title">📊 实时监控流日志面板：</div>
<div class="log-panel" id="log-container">
<div id="log-empty" style="color: #555; text-align: center; margin-top: 70px;">后端挂载就绪，等待下发开跑指令...</div>
</div>
</div>
</div>
<script>
const API_BASE = window.location.origin;
const nodes = {
step1: document.getElementById('login-step-1'), step2: document.getElementById('login-step-2'),
apiId: document.getElementById('api_id'), apiHash: document.getElementById('api_hash'),
phone: document.getElementById('phone'), code: document.getElementById('code'), pwd2fa: document.getElementById('2fa-pwd'),
targetGroup: document.getElementById('target_group'), pullCount: document.getElementById('pull_count'), sources: document.getElementById('source_groups'),
btnSendCode: document.getElementById('btn-send-code'), btnVerify: document.getElementById('btn-verify'), btnBack: document.getElementById('btn-back'),
"""
