<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>云端多群联合采集拉人系统</title>
<style>
:root {
--bg-color: #121212;
--panel-bg: #1e1e1e;
--input-bg: #2d2d2d;
--text-color: #e0e0e0;
--primary-green: #00e676;
--danger-red: #ff5252;
--warning-orange: #ff9100;
}
body { margin: 0; padding: 15px; background-color: var(--bg-color); color: var(--text-color); font-family: -apple-system, sans-serif; }
.container { max-width: 600px; margin: 0 auto; background: var(--panel-bg); border-radius: 12px; padding: 20px; box-shadow: 0 4px 20px rgba(0, 0, 0, 0.5); }
h2 { text-align: center; margin-top: 0; color: #fff; font-size: 18px; border-bottom: 1px solid #333; padding-bottom: 15px; letter-spacing: 1px; }
.section { margin-bottom: 20px; padding: 15px; background: rgba(255, 255, 255, 0.02); border-radius: 8px; border: 1px solid #333; }
.section-title { font-size: 14px; color: #fff; margin-bottom: 12px; font-weight: bold; }
.form-group { margin-bottom: 15px; }
label { display: block; font-size: 14px; margin-bottom: 8px; color: #bbb; font-weight: bold; }
input, textarea { width: 100%; padding: 14px; background: var(--input-bg); border: 1px solid #333; border-radius: 8px; color: #fff; box-sizing: border-box; margin-bottom: 10px; font-size: 15px; transition: all 0.3s; }
input:focus, textarea:focus { outline: none; border-color: var(--primary-green); background: #333; }
textarea { height: 140px; resize: none; line-height: 1.5; }
.hint-text { font-size: 13px; color: #888; margin: -5px 0 15px 0; }
.btn-group { display: flex; gap: 12px; width: 100%; box-sizing: border-box; margin-top: 10px; }
.btn { flex: 1; padding: 14px; border: none; border-radius: 8px; font-size: 15px; font-weight: bold; cursor: pointer; display: flex; align-items: center; justify-content: center; gap: 6px; box-sizing: border-box; }
.btn-green { background-color: var(--primary-green); color: #000; }
.btn-red { background-color: var(--danger-red); color: #fff; }
.btn-secondary { background-color: #333; color: #fff; width: 100%; font-size: 15px; border: 1px solid #444; }
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
<h2>云端多群联合采集拉人系统</h2>
<div class="section">
<div class="section-title">🔑 账号在线鉴权</div>
<div id="login-step-1" class="form-group">
<input type="text" id="phone" value="+2347064991293" placeholder="操作号手机号(带国家码如 +234...)">
<button style="margin-top: 8px;" class="btn btn-green" id="btn-send-code">🚀 发送验证码</button>
</div>
<div id="login-step-2" class="form-group hidden">
<input type="text" id="code" placeholder="输入 5 位验证码">
<input type="password" id="2fa-pwd" placeholder="两步验证密码(若无则不填)" style="margin-top:8px;">
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
<label>要拉取的数量 (最少 100)</label>
<input type="number" id="pull_count" value="100">
<div class="hint-text">最少下单: 100 - 最大下单: 10 000</div>
</div>
<div class="form-group">
<label>采集群 (支持完整链接，一行放一个群)</label>
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
// 使用通用回路自动直连
const API_BASE = window.location.origin;
const nodes = {
step1: document.getElementById('login-step-1'), step2: document.getElementById('login-step-2'),
phone: document.getElementById('phone'), code: document.getElementById('code'), pwd2fa: document.getElementById('2fa-pwd'),
targetGroup: document.getElementById('target_group'), pullCount: document.getElementById('pull_count'), sources: document.getElementById('source_groups'),
btnSendCode: document.getElementById('btn-send-code'), btnVerify: document.getElementById('btn-verify'), btnBack: document.getElementById('btn-back'),
btnStart: document.getElementById('btn-start'), btnStop: document.getElementById('btn-stop'), logContainer: document.getElementById('log-container'), logEmpty: document.getElementById('log-empty')
};
nodes.btnSendCode.onclick = async () => {
if (!nodes.phone.value) return alert("请输入手机号！");
try {
const formData = new FormData(); formData.append("phone", nodes.phone.value);
const res = await fetch(`${API_BASE}/api/login/send_code`, { method: "POST", body: formData });
const data = await res.json(); alert(data.message || "成功");
if (res.ok) { nodes.step1.classList.add('hidden'); nodes.step2.classList.remove('hidden'); }
} catch (err) { alert("连接超时"); }
};
nodes.btnVerify.onclick = async () => {
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
