# 基础镜像使用官方的 Ubuntu 22.04，体积适中且自带 apt
FROM ubuntu:22.04

# 必要工具：wireguard、iptables、dnsutils、curl、procps
RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y \
    wireguard iproute2 iptables nano \
    net-tools ca-certificates curl procps && \
    rm -rf /var/lib/apt/lists/*

# ---------- 安装 udp2raw ----------
ENV UDP2RAW_VER="20200818.0"
RUN curl -L -o /tmp/udp2raw.tar.gz \
    https://github.com/wangyu-/udp2raw/releases/download/${UDP2RAW_VER}/udp2raw_binaries.tar.gz && \
    tar -xzvf /tmp/udp2raw.tar.gz udp2raw_amd64 -C /usr/local/bin && \
    mv /usr/local/bin/udp2raw_amd64 /usr/local/bin/udp2raw && \
    chmod +x /usr/local/bin/udp2raw && \
    rm -f /tmp/udp2raw.tar.gz

# 复制启动脚本并赋权
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# 持久化 WireGuard 配置
VOLUME ["/etc/wireguard"]

# 需要特权 (raw socket) + NET_ADMIN (iptables) 权限
ENTRYPOINT ["/entrypoint.sh"]
