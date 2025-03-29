# Setup Steps for Kwintes Cloud on Ubuntu VPS

This guide provides step-by-step instructions for setting up Kwintes Cloud (including Puter and Telegram integration) on an Ubuntu VPS.

## System Requirements
- Ubuntu 24.04 LTS
- Minimum 4GB RAM (8GB+ recommended)
- 20GB+ free disk space
- CPU with AVX2 support for optimal performance

## 1. Pre-Installation Setup

```bash
# SSH to your VPS
ssh root@your-vps-ip

# Update System
sudo apt update && sudo apt install -y nano git docker.io python3 python3-pip

# Install Docker
sudo apt install -y ca-certificates curl gnupg
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg

echo \
  "deb [arch="$(dpkg --print-architecture)" signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  "$(. /etc/os-release && echo "$VERSION_CODENAME")" stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Add current user to docker group
sudo usermod -aG docker $USER
newgrp docker

# Start and enable Docker service
sudo systemctl start docker
sudo systemctl enable docker
sudo systemctl status docker

# If you see permission issues, try:
sudo chmod 666 /var/run/docker.sock

# Verify Docker is working
docker --version
docker ps
```

## 2. Configure Firewall

```bash
sudo apt install -y ufw
ufw enable
ufw allow ssh
ufw allow 80
ufw allow 443
ufw allow 3000  # WebUI
ufw allow 5678  # n8n workflow
ufw allow 8080  # SearXNG 
ufw allow 11434 # Ollama
ufw allow 7000  # Puter
ufw allow 3001  # Archon Streamlit UI (if using)
ufw reload
```

## 3. Clone and Configure

```bash
# Clone the repository
git clone https://github.com/ThijsdeZeeuw/small_kwintes_cloud15.git
cd small_kwintes_cloud

# Create Puter data directory with proper permissions
mkdir -p puter-data
sudo chown -R 1000:1000 puter-data

# Create n8n backup directories to prevent import errors
mkdir -p n8n/backup/credentials n8n/backup/workflows
touch n8n/backup/credentials/.keep n8n/backup/workflows/.keep

# Edit .env file with your configuration
# Make sure to set these important values:
# - POSTGRES_PASSWORD
# - JWT_SECRET
# - N8N_ENCRYPTION_KEY
# - N8N_USER_MANAGEMENT_JWT_SECRET
# - NGROK_AUTHTOKEN (if using Ngrok)
# - TELEGRAM_BOT_TOKEN (if using Telegram)
# - PUTER_HOSTNAME (for Puter integration)
nano .env
```

## 4. Start Services

The improved `start_services.py` script has been enhanced to:
- Properly setup Puter directories
- Check and configure Telegram integration
- Fix n8n-import issues
- Continue running even if some services encounter problems
- Display detailed status information

```bash
# Start all services (including Puter and Telegram)
python3 start_services.py --profile cpu

# If you have NVIDIA GPU available:
# python3 start_services.py --profile gpu-nvidia

# If you have AMD GPU available:
# python3 start_services.py --profile gpu-amd
```

The script will:
1. Clone the Supabase repository
2. Prepare the Puter data directory
3. Check Telegram configuration
4. Prepare n8n directories to prevent import errors
5. Start Supabase services
6. Start all other services (including Puter)
7. Update ngrok URL for webhook access (if configured)
8. Configure Telegram webhook (if configured)
9. Check which services are running and report their status

## 5. Access Your Services

- WebUI: `http://YOUR_SERVER_IP:3000/`
- n8n workflow: `http://YOUR_SERVER_IP:5678/`
- Puter: `http://YOUR_SERVER_IP:7000/`
- SearXNG: `http://YOUR_SERVER_IP:8080/`
- Flowise: `http://YOUR_SERVER_IP:3001/`

If you've configured domain names in your .env file and DNS is set up properly, you can access via:
- `https://puter.yourdomain.com/`
- `https://n8n.yourdomain.com/`
- `https://webui.yourdomain.com/`
- etc.

## 6. Puter Configuration and Usage

Puter provides a web-based cloud operating system that's integrated with your other services:

1. **Initial Access**
   - Access Puter at `http://YOUR_SERVER_IP:7000/` or `https://puter.yourdomain.com/`
   - Create an administrator account on first login

2. **File Management**
   - Upload files directly through the web interface
   - Files are stored persistently in the `puter-data` directory
   - Organize content using the familiar desktop interface

3. **Integration with n8n and other services**
   - Puter can communicate with n8n workflows
   - Store, process, and retrieve files from your Puter instance
   - Use in conjunction with your AI services

## 7. Telegram Integration

Kwintes Cloud includes a Telegram integration for authentication and bot interactions:

1. **Setup Telegram Bot**
   - Create a bot via @BotFather on Telegram
   - Update `.env` with your bot token and username:
     ```
     TELEGRAM_BOT_TOKEN=your-telegram-bot-token
     TELEGRAM_BOT_USERNAME=your_bot_username
     ```

2. **Configure Webhook**
   - The `update_telegram_webhook.sh` script is executed automatically during startup
   - It configures your bot to receive notifications through n8n
   - Telegram login widget will use this communication channel

3. **Access Login Page**
   - Use the Telegram login widget at `https://login.yourdomain.com/`
   - The login page securely authenticates users via Telegram

## 8. Set Up System Service (Optional)

To run as a system service that starts automatically on boot:

```bash
sudo nano /etc/systemd/system/localai.service
```

Add the following content:
```
[Unit]
Description=Kwintes Cloud
After=docker.service
Requires=docker.service

[Service]
Type=simple
User=YOUR_USERNAME
WorkingDirectory=/path/to/small_kwintes_cloud
ExecStart=/usr/bin/python3 start_services.py --profile cpu
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Replace `YOUR_USERNAME` and `/path/to/small_kwintes_cloud` with your actual values.

Enable and start the service:
```bash
sudo systemctl daemon-reload
sudo systemctl enable localai.service
sudo systemctl start localai.service
```

## 9. Update Your System

When you need to update:

```bash
# Stop all services
docker compose -p localai -f docker-compose.yml -f supabase/docker/docker-compose.yml down

# Pull latest versions
docker compose -p localai -f docker-compose.yml -f supabase/docker/docker-compose.yml pull

# Start services again
python3 start_services.py --profile cpu
```

## 10. Troubleshooting

### Common Issues

1. **n8n-import Failures**
   - If `n8n-import` service fails, check that you have created the necessary directories:
     ```bash
     mkdir -p n8n/backup/credentials n8n/backup/workflows
     touch n8n/backup/credentials/.keep n8n/backup/workflows/.keep
     ```
   - The enhanced script handles this automatically

2. **Puter Not Starting**
   - Check permissions on the puter-data directory:
     ```bash
     sudo chown -R 1000:1000 puter-data
     ```
   - Check Puter logs:
     ```bash
     docker logs puter
     ```

3. **Telegram Integration Not Working**
   - Verify your bot token in .env
   - Check ngrok URL is correctly updated
   - Run webhook update manually:
     ```bash
     chmod +x update_telegram_webhook.sh
     ./update_telegram_webhook.sh
     ```

4. **General Troubleshooting Commands**
   ```bash
   # Check Docker service
   sudo systemctl status docker

   # Check logs for all services
   docker compose -p localai logs

   # Check logs for specific service
   docker logs puter
   docker logs n8n
   docker logs open-webui

   # Check system resources
   htop

   # Check container status
   docker ps

   # Restart a specific container
   docker restart puter
   docker restart n8n
   ```

## 11. Additional Configuration

### Configuring Ngrok (for Webhooks)

If you need your n8n webhooks accessible from the internet:

1. Register at https://ngrok.com/
2. Get your auth token from the dashboard
3. Add to `.env`: `NGROK_AUTHTOKEN=your-ngrok-auth-token`
4. Run `./update_ngrok_url.sh` after services are started

### Local Ollama Setup (Optional)

If you prefer to use Ollama locally instead of from Docker:

```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Pull required models
ollama pull nomic-embed-text
ollama pull qwen2.5:7b-instruct-q4_K_M

# Start Ollama service
systemctl --user enable ollama
systemctl --user start ollama
```

### WebUI Configuration

1. Access WebUI at `http://YOUR_SERVER_IP:3000/`
2. Configure Workspace Functions:
   - Go to Admin Settings -> Workspace -> Functions -> Add Function
   - URL: `http://host.docker.internal:5678/webhook/invoke_n8n_agent`
   - Enable the function 