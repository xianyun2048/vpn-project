# 基础镜像：Ubuntu 22.04（内置 WireGuard 内核模块）
FROM ubuntu:22.04

# -------------------------------------------------
# 只装 WireGuard 的用户空间工具
# -------------------------------------------------
RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y \
    wireguard-tools            \
    iptables ca-certificates   \
    wget                       \
    && rm -rf /var/lib/apt/lists/*

# -------------------------------------------------
# 安装 udp2raw（使用最近的官方发行版）
# -------------------------------------------------
ARG UDP2RAW_VER=20230206.0          # ← 更换为最新可用的 tag
RUN set -eux && \
    wget -O /tmp/udp2raw.tar.gz \
        "https://github.com/wangyu-/udp2raw/releases/download/${UDP2RAW_VER}/udp2raw_binaries.tar.gz" && \
    # 解压我们关心的两个二进制
    tar -xzvf /tmp/udp2raw.tar.gz -C /usr/local/bin/ udp2raw_amd64 udp2raw_amd64_hw_aes && \
    # 优先使用硬件加速版；若不存在则回退到普通版
    if [ -f /usr/local/bin/udp2raw_amd64_hw_aes ]; then \
        mv /usr/local/bin/udp2raw_amd64_hw_aes /usr/local/bin/udp2raw; \
    else \
        mv /usr/local/bin/udp2raw_amd64 /usr/local/bin/udp2raw; \
    fi && \
    chmod +x /usr/local/bin/udp2raw && \
    rm -f /tmp/udp2raw.tar.gz

# 运行入口（实际启动脚本在容器外 `entrypoint.sh` 调用）
ENTRYPOINT ["udp2raw"]
