# MUNITY OS 部署指南

## 快速部署（推荐）

```bash
# 1. 上传项目到服务器
scp -r /home/cyw2007/mun-os root@你的服务器IP:/home/deploy/mun-os

# 2. SSH 登录服务器
ssh root@你的服务器IP

# 3. 执行部署脚本
cd /home/deploy/mun-os/deploy
bash deploy.sh
```

部署完成后访问 `http://你的服务器IP`

## 系统要求

- Ubuntu 22.04 LTS
- 1核1G 内存以上
- 脚本会自动安装：Python3、Node.js 20、Nginx

## 绑定域名（可选）

```bash
# 1. 修改 Nginx 配置
sudo nano /etc/nginx/sites-available/munity
# 把 server_name _ 改成你的域名

# 2. 重启 Nginx
sudo systemctl reload nginx

# 3. 安装 HTTPS 证书
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d 你的域名
```

## 常用命令

```bash
# 查看后端状态
sudo systemctl status munity

# 重启后端
sudo systemctl restart munity

# 查看日志
sudo journalctl -u munity -f

# 重启 Nginx
sudo systemctl reload nginx
```

## 自动恢复机制

- 服务崩溃后 3 秒自动重启
- 每 30 秒自动保存会议状态
- 服务器重启后自动恢复上次状态
