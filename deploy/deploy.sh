#!/bin/bash
# MUNITY OS 一键部署脚本
# 在云服务器上执行：bash deploy.sh

set -e

echo "=============================="
echo "  MUNITY OS 一键部署脚本"
echo "=============================="

# 1. 创建部署用户
echo "[1/7] 创建部署用户..."
if ! id "deploy" &>/dev/null; then
    sudo useradd -m -s /bin/bash deploy
    echo "  用户 deploy 已创建"
else
    echo "  用户 deploy 已存在"
fi

# 2. 安装依赖
echo "[2/7] 安装系统依赖..."
sudo apt update -qq
sudo apt install -y -qq python3 python3-pip python3-venv nginx curl

# 3. 复制项目文件
echo "[3/7] 复制项目文件..."
sudo mkdir -p /home/deploy/mun-os
sudo cp -r ../backend /home/deploy/mun-os/
sudo cp -r ../frontend /home/deploy/mun-os/

# 4. 安装 Python 依赖
echo "[4/7] 安装 Python 依赖..."
cd /home/deploy/mun-os/backend
pip3 install -r requirements.txt --break-system-packages -q

# 5. 构建前端（用当前用户，不用 sudo）
echo "[5/7] 构建前端..."
cd /home/deploy/mun-os/frontend
npm install --silent
npm run build

# 6. 修改权限
echo "[6/7] 设置权限..."
chown -R deploy:deploy /home/deploy/mun-os

# 7. 配置 Nginx 和服务
echo "[7/7] 配置 Nginx 和服务..."
cp /home/deploy/mun-os/deploy/nginx.conf /etc/nginx/sites-available/munity
ln -sf /etc/nginx/sites-available/munity /etc/nginx/sites-enabled/munity
rm -f /etc/nginx/sites-enabled/default
nginx -t && systemctl reload nginx

cp /home/deploy/mun-os/deploy/munity.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable munity
systemctl start munity

echo ""
echo "=============================="
echo "  部署完成！"
echo "=============================="
echo ""
echo "访问地址：http://$(curl -s ifconfig.me 2>/dev/null || echo '你的服务器IP')"
echo ""
echo "常用命令："
echo "  查看后端状态：systemctl status munity"
echo "  重启后端：    systemctl restart munity"
echo "  查看日志：    journalctl -u munity -f"
echo "  重启 Nginx：  systemctl reload nginx"
echo ""
echo "默认管理员：admin / admin123"
echo "请登录后立即修改密码！"
