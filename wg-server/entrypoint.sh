#!/usr/bin/env bash
set -e

# 环境变量（在 .env 中可以自行覆盖）
: "${UDP2RAW_PASSWORD:=VerySecretPass}"   # udp2raw 共享密钥
: "${WG_IFACE:=wg0}"                      # WireGuard 接口名
: "${WG_PORT:=51820}"                     # WireGuard 监听的本地 UDP 端口
: "${UDP2RAW_LISTEN:=443}"                 # 对外暴露的 TCP 端口（伪装成 HTTPS）

# 1️⃣ 启动 WireGuard（wg‑quick 读取 /etc/wireguard/wg0.conf）
echo ">>> Starting WireGuard interface $WG_IFACE ..."
wg-quick up $WG_IFACE

# 2️⃣ 启动 udp2raw（服务端模式）
#    -s                : server mode
#    -l 0.0.0.0:443    : 监听 TCP 443
#    -r 127.0.0.1:51820: 把收到的 TCP 流量转发到本地 wg0 UDP 端口
#    -k "$UDP2RAW_PASSWORD" : 对称密码
#    --raw-mode faketcp    : 伪装成普通 TCP（可被防火墙认作 HTTPS）
#    -a                    : 自动添加/删除 iptables 规则（需要 NET_ADMIN）
echo ">>> Starting udp2raw (Fake‑TCP on TCP $UDP2RAW_LISTEN) ..."
udp2raw -s \
    -l 0.0.0.0:${UDP2RAW_LISTEN} \
    -r 127.0.0.1:${WG_PORT} \
    -k "${UDP2RAW_PASSWORD}" \
    --raw-mode faketcp -a \
    > /var/log/udp2raw.log 2>&1 &

# 3️⃣ 保持容器前台运行（Docker 需要主进程存活）
tail -f /var/log/udp2raw.log
