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

CONFIG = {
    "API_ID": 38906005,                                  
    "API_HASH": "9c4a2467d94a3d88818309c8b80ea183",      
    "SESSION_DIR": "./sessions"                          
}
os.makedirs(CONFIG["SESSION_DIR"], exist_ok=True)
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class GlobalState:
    is_running: bool = False             
    realtime_logs: List[str] = []        
    login_sessions: Dict[str, Dict] = {} 
state = GlobalState()

def append_log(msg: str):
    print(msg) 
    state.realtime_logs.append(msg)
    if len(state.realtime_logs) > 100: state.realtime_logs.pop(0)

class MultiPullTaskSchema(BaseModel):
    target_link: str      
    pull_count: int       
    source_groups: str    

def parse_tg_username(input_str: str) -> str:
    if not input_str: return ""
    cleaned = input_str.strip().replace(" ", "")
    if "t.me/" in cleaned: cleaned = cleaned.split("t.me/")[-1]
    if "joinchat/" in cleaned: cleaned = cleaned.split("joinchat/")[-1]
    if "/" in cleaned: cleaned = cleaned.split("/")[-1]
    return cleaned.replace("@", "").split("?")[0]

async def core_multi_pulling_engine(target: str, count: int, sources_text: str):
    state.is_running = True
    session_files = [f for f in os.listdir(CONFIG["SESSION_DIR"]) if f.endswith(".session")]
    if not session_files:
        append_log("[安全拦截] 失败：云端未检测到登录账号，请先完成第一步登录！")
        state.is_running = False; return
    
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
        except Exception as e: append_log(f"[进群状态] {str(e)}（若已在群内请忽略）")
        
        target_entity = await client.get_entity(target_username)
        source_lines = [line.strip() for line in sources_text.split("\n") if line.strip()]
        append_log(f"[安全开跑] 多群合并采集就绪，源同行群共: {len(source_lines)} 个。")
        
        successful_pulls = 0
        for idx, current_source in enumerate(source_lines, start=1):
            if not state.is_running or successful_pulls >= count: break
            source_username = parse_tg_username(current_source)
            if not source_username: continue
                
            append_log(f"➔ 正在深度扫描第 [{idx}/{len(source_lines)}] 个源群组: @{source_username} ...")
            try:
                source_entity = await client.get_entity(source_username)
                async for user in client.iter_participants(source_entity):
                    if not state.is_running or successful_pulls >= count: break
                    if not user.username or user.bot or user.deleted: continue
                    
                    if isinstance(user.status, (UserStatusOnline, UserStatusRecently)):
                        try:
                            await client(InviteToChannelRequest(target_entity, [user]))
                            successful_pulls += 1
                            append_log(f"➔ [成功] 活人 @{user.username} 导入成功！当前进度: [{successful_pulls}/{count}]")
                            await asyncio.sleep(20) 
                        except UserPrivacyRestrictedError: pass
                        except PeerFloodError:
                            append_log("⚠ [频率限制] 触发官方频控。此号今日额度已尽，请明天换号冲锋。")
                            state.is_running = False; return
                        except Exception: await asyncio.sleep(3)
            except Exception as e: append_log(f"⚠ 跳过无法解析的群组 @{source_username}: {str(e)}"); continue
                
        append_log(f"[大功告成] 多群拉人任务已彻底完成！总计导入: {successful_pulls} 人。")
    except Exception as e: append_log(f"[系统异常]: {str(e)}")
    finally: await client.disconnect(); state.is_running = False

@app.get("/", response_class=HTMLResponse)
async def get_index():
if (!nodes.code.value) return alert("请输入验证码！");
try {
const formData = new FormData(); formData.append("phone", nodes.phone.value); formData.append("code", nodes.code.value);
if (nodes.pwd2fa.value) formData.append("password", nodes.pwd2fa.value);
const res = await fetch(`${API_BASE}/api/login/verify_code`, { method: "POST", body: formData });
const data = await res.json(); alert(data.message);
if (res.ok) { nodes.step2.classList.add('hidden'); nodes.step1.classList.remove('hidden'); }
} catch (err) { alert("验证失败"); }
};
nodes.btnBack.onclick = () => { nodes.step2.classList.add('hidden'); nodes.step1.classList.remove('hidden'); };
</script>
</body>
</html>
