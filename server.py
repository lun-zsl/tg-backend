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
    "API_ID": 38906005,
    "API_HASH": "9c4a2467d94a3d88818309c8b80ea183",
    "SESSION_DIR": "./sessions"
}
os.makedirs(CONFIG["SESSION_DIR"], exist_ok=True)

# 2. 初始化 FastAPI 服务
app = FastAPI()

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
    login_sessions: Dict[str, Dict] = {}

state = GlobalState()

# 5. 日志记录辅助函数
def append_log(msg: str):
    print(msg)
    state.realtime_logs.append(msg)
    if len(state.realtime_logs) > 100:
        state.realtime_logs.pop(0)

# 6. 请求数据结构定义
class MultiPullTaskSchema(BaseModel):
    target_link: str
    pull_count: int
    source_groups: str

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
async def core_multi_pulling_engine(target: str, count: int, sources_text: str):
    state.is_running = True
    session_files = [f for f in os.listdir(CONFIG["SESSION_DIR"]) if f.endswith(".session")]
    if not session_files:
        append_log("[安全拦截] 失败：云端未检测到登录账号，请先完成第一步登录！")
        state.is_running = False
        return
        
    first_session = session_files[0].replace(".session", "")
    client = TelegramClient(os.path.join(CONFIG["SESSION_DIR"], first_session), CONFIG["API_ID"], CONFIG["API_HASH"])
    
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
        source_lines = [line.strip() for line in sources_text.split("\n") if line.strip()]
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
                            # 可以在此处添加具体的拉人逻辑代码
                            pass
                        except Exception:
                            pass
            except Exception as e:
                append_log(f"[扫描错误] 无法读取群组 @{source_username}: {str(e)}")
    finally:
        await client.disconnect()
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
    "API_ID": 38906005,
    "API_HASH": "9c4a2467d94a3d88818309c8b80ea183",
    "SESSION_DIR": "./sessions"
}
os.makedirs(CONFIG["SESSION_DIR"], exist_ok=True)

# 2. 初始化 FastAPI 服务
app = FastAPI()

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
    login_sessions: Dict[str, Dict] = {}

state = GlobalState()

# 5. 日志记录辅助函数
def append_log(msg: str):
    print(msg)
    state.realtime_logs.append(msg)
    if len(state.realtime_logs) > 100:
        state.realtime_logs.pop(0)

# 6. 请求数据结构定义
class MultiPullTaskSchema(BaseModel):
    target_link: str
    pull_count: int
    source_groups: str

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
async def core_multi_pulling_engine(target: str, count: int, sources_text: str):
    state.is_running = True
    session_files = [f for f in os.listdir(CONFIG["SESSION_DIR"]) if f.endswith(".session")]
    if not session_files:
        append_log("[安全拦截] 失败：云端未检测到登录账号，请先完成第一步登录！")
        state.is_running = False
        return
        
    first_session = session_files[0].replace(".session", "")
    client = TelegramClient(os.path.join(CONFIG["SESSION_DIR"], first_session), CONFIG["API_ID"], CONFIG["API_HASH"])
    
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
        source_lines = [line.strip() for line in sources_text.split("\n") if line.strip()]
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
                            # 可以在此处添加具体的拉人逻辑代码
                            pass
                        except Exception:
                            pass
            except Exception as e:
                append_log(f"[扫描错误] 无法读取群组 @{source_username}: {str(e)}")
    finally:
        await client.disconnect()
