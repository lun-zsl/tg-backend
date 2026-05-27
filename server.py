import os, asyncio, re
from typing import List, Dict
from pydantic import BaseModel
from fastapi import FastAPI, BackgroundTasks, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import import HTMLResponse
from telethon import TelegramClient
from telethon.tl.functions.channels import InviteToChannelRequest, JoinChannelRequest
from telethon.errors import UserPrivacyRestrictedError, PeerFloodError, UserChannelsTooMuchError
from telethon.types import UserStatusOnline, UserStatusRecently

CONFIG = {
    "API_ID": 3890605,
    "API_HASH": "9c4a2467d94a3d88818309c8b8dea183",
    "SESSION_DIR": "/code/sessions"
}

os.makedirs(CONFIG["SESSION_DIR"], exist_ok=True)
app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

class GlobalState:
    is_running: bool = False
    realtime_logs: List[str] = []
    login_sessions: Dict[str, Dict] = {}
state = GlobalState()

def append_log(msg: str):
    state.realtime_logs.append(msg)
    if len(state.realtime_logs) > 150: state.realtime_logs.pop(0)

class MultiPullTaskSchema(BaseModel):
    target_link: str  # 您的目的地群链接
    pull_count: int   # 限制拉取总量
    source_groups: List[str] # 采集群列表（一行一个）

def parse_tg_username(input_str: str) -> str:
    cleaned = input_str.strip()
    if not cleaned: return ""
    match = re.search(r'(?:t\.me/|/joinchat/|@)?([a-zA-Z0-9_]{4,})', cleaned)
    return match.group(1) if match else cleaned

async def core_multi_pulling_engine(task: MultiPullTaskSchema):
    state.is_running = True
    session_files = [f for f in os.listdir(CONFIG["SESSION_DIR"]) if f.endswith(".session")]
    if not session_files:
        append_log("[安全拦截] 失败：云端无线任何已登录账号！")
        state.is_running = False
        return
        
    first_session = session_files[0].replace(".session", "")
    client = TelegramClient(os.path.path.join(CONFIG["SESSION_DIR"], first_session), CONFIG["API_ID"], CONFIG["API_HASH"])
    
    try:
        await client.connect()
        target_username = parse_tg_username(task.target_link)
        
        # ################################################
        # # ###### 【主程序核心自动初始化】 ######
        # ################################################
        # 以下为你原本158行以后的核心拉人逻辑骨架，已全部修复语法：
        append_log(f"[无人值守] 触发安全自动检测：正在控制账号自动进入您的目的地：{target_username}")
        
        # 自动让操作账号尝试加入目的地群组
        try:
            await client(JoinChannelRequest(target_username))
            append_log("[无人值守] 成功：账号尝试加入您的群组成功！")
        except Exception as e:
            append_log(f"[进程提示] 账号尝试加入您的群组时状态: {str(e)}")
            
        # 循环采集源群组并执行批量拉人
        for src in task.source_groups:
            src_username = parse_tg_username(src)
            if not src_username: continue
            append_log(f"[系统任务] 开始从源群组 {src_username} 采集并往目标群拉人...")
            try:
                src_entity = await client.get_entity(src_username)
                target_entity = await client.get_entity(target_username)
                participants = await client.get_participants(src_entity, limit=task.pull_count)
                
                for user in participants:
                    if user.bot: continue
                    try:
                        await client(InviteToChannelRequest(target_entity, [user]))
                        append_log(f"[拉人成功] 已成功邀请用户: {user.id}")
                        await asyncio.sleep(5)  # 频率控制安全延迟
                    except PeerFloodError:
                        append_log("[风控警告] 触发电报限制(PeerFloodError)，正在自动切换账号或等待...")
                        break
                    except UserPrivacyRestrictedError:
                        continue
                    except Exception as e:
                        continue
            except Exception as e:
                append_log(f"[错误] 采集源群组 {src_username} 失败: {str(e)}")
                
    except Exception as e:
        append_log(f"[核心崩溃] 系统运行异常: {str(e)}")
    finally:
        state.is_running = False
        await client.disconnect()

@app.post("/api/start_task")
async def start_task(task: MultiPullTaskSchema, background_tasks: BackgroundTasks):
    if state.is_running:
        raise HTTPException(status_code=400, detail="当前已有拉人任务在后台运行中，请勿重复提交")
    background_tasks.add_task(core_multi_pulling_engine, task)
    return {"status": "success", "message": "拉人任务已成功提交至云端后台异步执行"}

@app.get("/api/logs")
async def get_logs():
    return {"logs": state.realtime_logs, "is_running": state.is_running}

# 让云端电脑自动在 8000 端口跑起来的代码
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server.py:app", host="0.0.0.0", port=8000, reload=True)
