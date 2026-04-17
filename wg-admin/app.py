import os
import subprocess
import sqlite3
from flask import Flask, request, jsonify, render_template, redirect, url_for
from flask_httpauth import HTTPBasicAuth

app = Flask(__name__)
auth = HTTPBasicAuth()

# ----------- 简单的用户名密码（从环境变量读取） -----------
USERS = {
    os.getenv("ADMIN_USER", "admin"): os.getenv("ADMIN_PASSWORD", "admin")
}

@auth.verify_password
def verify(username, password):
    return USERS.get(username) == password

# ----------- WireGuard 配置路径 ----------- 
WG_CONF = "/etc/wireguard/wg0.conf"

# ----------- 辅助函数 ----------
def run_cmd(cmd: str) -> str:
    """执行系统命令并返回 stdout，异常时报错"""
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, check=True)
    return result.stdout.strip()

def get_peers():
    """返回 [{pubkey, tx, rx, ip}] 列表"""
    # 通过 wg show 获取已连接的 peer 公钥
    peers = run_cmd("wg show wg0 peers").splitlines()
    # 通过 wg show wg0 transfer 获取流量统计
    stats_raw = run_cmd("wg show wg0 transfer").splitlines()
    stats = {}
    for line in stats_raw:
        pk, tx, rx = line.split()
        stats[pk] = {"tx": int(tx), "rx": int(rx)}
    out = []
    for pk in peers:
        out.append({
            "public_key": pk,
            "tx": stats.get(pk, {}).get("tx", 0),
            "rx": stats.get(pk, {}).get("rx", 0)
        })
    return out

def get_next_ip():
    """在 10.10.0.0/24 中找下一个未使用的 /32 地址"""
    used = set()
    with open(WG_CONF) as f:
        for line in f:
            if line.strip().startswith("AllowedIPs"):
                ip = line.split("=")[1].strip().split("/")[0]
                used.add(ip)
    for i in range(2, 255):
        ip = f"10.10.0.{i}"
        if ip not in used:
            return ip
    raise RuntimeError("IP pool exhausted")

def add_peer(name: str):
    """生成密钥、写入 wg0.conf、并同步到运行中的 wg 接口"""
    # 1️⃣ 生成密钥
    priv = run_cmd("wg genkey")
    pub = run_cmd(f"echo {priv} | wg pubkey")
    # 2️⃣ 为 peer 分配 IP
    ip = get_next_ip()
    # 3️⃣ 追加到配置文件（保留换行，方便管理）
    peer_block = f"""

# {name}
[Peer]
PublicKey = {pub}
AllowedIPs = {ip}/32
"""
    with open(WG_CONF, "a") as f:
        f.write(peer_block)
    # 4️⃣ 同步到内核（不需要重启 wg-quick）
    run_cmd("wg syncconf wg0 <(wg-quick strip wg0)")
    return {
        "name": name,
        "private_key": priv,
        "public_key": pub,
        "address": f"{ip}/32"
    }

def delete_peer(pubkey: str):
    """从 wg0.conf 移除对应 peer（连同注释块）并同步"""
    lines = []
    skip = False
    with open(WG_CONF) as f:
        for line in f:
            if line.strip().startswith("[Peer]"):
                skip = False  # 进入新的 peer 区块，先不决定是否跳过
                current_peer = ""
            if line.strip().startswith("PublicKey"):
                current_peer = line.split("=")[1].strip()
                if current_peer == pubkey:
                    skip = True   # 找到要删除的 peer，整块跳过
            if not skip:
                lines.append(line)
    # 写回
    with open(WG_CONF, "w") as f:
        f.writelines(lines)
    # 同步
    run_cmd("wg syncconf wg0 <(wg-quick strip wg0)")

# ----------- Flask 路由 ----------
@app.route("/")
@auth.login_required
def index():
    peers = get_peers()
    return render_template("index.html", peers=peers)

@app.route("/api/peer", methods=["POST"])
@auth.login_required
def api_add_peer():
    name = request.json.get("name", "unnamed")
    info = add_peer(name)
    return jsonify(info), 201

@app.route("/api/peer/<pubkey>", methods=["DELETE"])
@auth.login_required
def api_del_peer(pubkey):
    delete_peer(pubkey)
    return "", 204

if __name__ == "__main__":
    # 开发模式直接运行
    app.run(host="0.0.0.0", port=5000)
