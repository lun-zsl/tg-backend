import os, asyncio, re
from typing import List, Dict
from pydantic import BaseModel
from fastapi import FastAPI, BackgroundTasks, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from telethon import TelegramClient
from telethon.tl.functions.channels import InviteToChannelRequest, JoinChannelRequest
from telethon.errors import UserPrivacyRestrictedError, PeerFloodError, FloodWaitError
from telethon.tl.types import UserStatusOnline, UserStatusRecently

CONFIG = {
    "API_ID": 38906005,                                  
    "API_HASH": "9c4a2467d94a3d88818309c8b80ea183",      
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
    target_link: str      # 您的目的地接收群链接
    pull_count: int       # 限制拉取总数
    source_groups: str    # 采集群列表 (一行一个)

def parse_tg_username(input_str: str) -> str:
    cleaned = input_str.strip()
    if not cleaned: return ""
    match = re.search(r'(?:t\.me/|/joinchat/|@)?([a-zA-Z0-9_]{4,})', cleaned)
    return match.group(1) if match else cleaned

async def core_multi_pulling_engine(target: str, count: int, sources_text: str):
    state.is_running = True
    session_files = [f for f in os.listdir(CONFIG["SESSION_DIR"]) if f.endswith(".session")]
    if not session_files:
        append_log("[安全拦截] 失败：云端无任何已登录账号！")
        state.is_running = False
        return
    
    first_session = session_files[0].replace(".session", "")
    client = TelegramClient(os.path.join(CONFIG["SESSION_DIR"], first_session), CONFIG["API_ID"], CONFIG["API_HASH"])
    
    try:
        await client.connect()
        target_username = parse_tg_username(target)
        
        # =================【全新核心自动化逻辑】=================
        append_log(f"[无人值守] 触发全自动检测：正在控制账号自动潜入您的目的地群组 @{target_username} ...")
        try:
            # 协议级命令：控制操作账号自动加入你的目的地接收群
            await client(JoinChannelRequest(target_username))
            append_log("[无人值守] 成功：账号已在后台全自动成功切入您的群组内部！")
            await asyncio.sleep(3)
        except Exception as e:
            append_log(f"[进群提示] 账号尝试加入您的群组时返回状态: {str(e)}（若已在群内请忽略）")
        
        # 此时账号已在群内，为了拥有管理员拉人权限，请确保您的大号已经手动将该号设为管理员，或使用群主大号直接登录。
        target_entity = await client.get_entity(target_username)
        # ========================================================

        source_lines = [line.strip() for line in sources_text.split("\n") if line.strip()]
        append_log(f"[安全开跑] 多群合并采集任务就绪，源同行群总计: {len(source_lines)} 个。")
        
        successful_pulls = 0
        for idx, current_source in enumerate(source_lines, start=1):
            if not state.is_running or successful_pulls >= count: break
            
            source_username = parse_tg_username(current_source)
            if not source_username: continue
                
            append_log(f"➔ 正在爬取第 [{idx}/{len(source_lines)}] 个源群组: @{source_username} ...")
            try:
                source_entity = await client.get_entity(source_username)
                async for user in client.iter_participants(source_entity):
                    if not state.is_running or successful_pulls >= count: break
                    if not user.username or user.bot or user.deleted: continue
                    
                    if isinstance(user.status, (UserStatusOnline, UserStatusRecently)):
                        try:
                            # 执行邀请强拉指令
                            await client(InviteToChannelRequest(target_entity, [user]))
                            successful_pulls += 1
                            append_log(f"➔ [成功] 活人 @{user.username} 导入成功！当前累计进度: [{successful_pulls}/{count}]")
                            await asyncio.sleep(20) # 控流防封锁间隔
                        except UserPrivacyRestrictedError:
                            pass 
                        except PeerFloodError:
                            append_log("⚠ [频率限制] 触发官方限制，此号今日额度已用尽，请换号。")
                            state.is_running = False
                            return
                        except Exception:
                            await asyncio.sleep(3)
            except Exception as e:
                append_log(f"⚠ 跳过无法解析的源群组 @{source_username}: {str(e)}")
                continue
                
        append_log(f"[大功告成] 多群联合批量拉人任务已彻底大功告成！总计导入: {successful_pulls} 人。")
    except Exception as e:
        append_log(f"[系统异常]: {str(e)}")
    finally:
        await client.disconnect()
        state.is_running = False

@app.get("/", response_class=HTMLResponse)
async def get_index():
    # 保持向前端暴露完美的单页面UI
    return "<h3>Backend is running perfectly. Connecting with your frontend app.</h3>"

@app.post("/api/start_task")
async def start_task(payload: MultiPullTaskSchema, background_tasks: BackgroundTasks):
    if state.is_running: return JSONResponse(status_code=400, content={"message": "已有后台拉人任务在活跃中"})
    state.realtime_logs.clear()
    background_tasks.add_task(core_multi_pulling_engine, payload.target_link, payload.pull_count, payload.source_groups)
    return {"status": "success"}

@app.get("/api/logs")
async def get_realtime_logs(): return {"is_running": state.is_running, "logs": state.realtime_logs}

@app.post("/api/stop_task")
async def stop_task():
    state.is_running = False
    return {"status": "success"}

@app.post("/api/login/send_code")
async def send_phone_code(phone: str = Form(...)):
    session_path = os.path.join(CONFIG["SESSION_DIR"], phone)
    client = TelegramClient(session_path, CONFIG["API_ID"], CONFIG["API_HASH"])
    await client.connect()
    try:
        phone_code_hash = await client.send_code_request(phone)
        state.login_sessions[phone] = {"client": client, "phone_code_hash": phone_code_hash.phone_code_hash}
        return {"status": "success", "message": "验证码已成功发至您的电报！"}
    except Exception as e:
        await client.disconnect()
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/login/verify_code")
async def verify_phone_code(phone: str = Form(...), code: str = Form(...)):
    if phone not in state.login_sessions: raise HTTPException(status_code=400, detail="请先发送验证码")
    session_data = state.login_sessions[phone]
    client, phone_code_hash = session_data["client"], session_data["phone_code_hash"]
    try:
        await client.sign_in(phone=phone, code=code, phone_code_hash=phone_code_hash)
        del state.login_sessions[phone]
        await client.disconnect()
        return {"status": "success", "message": "云端授权并固化完全成功！"}
    except Exception as e: raise HTTPException(status_code=400, detail=str(e))
nano server.py
nano server.py
nano server.py
