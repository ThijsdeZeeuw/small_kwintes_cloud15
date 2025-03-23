# Setup Steps for Kwintes Cloud on Ubuntu VPS

This guide provides step-by-step instructions for setting up Kwintes Cloud (including Puter integration) on an Ubuntu VPS.

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
ufw allow 8501  # Archon Streamlit UI (if using)
ufw allow 5001  # DocLing Serve (if using)
ufw reload
```

## 3. Clone and Configure

```bash
# Clone the repository
git clone https://github.com/ThijsdeZeeuw/small_kwintes_cloud.git
cd small_kwintes_cloud

# Create Puter data directory
mkdir -p puter-data
sudo chown -R 1000:1000 puter-data

# Edit .env file with your configuration
# Make sure to set these important values:
# - POSTGRES_PASSWORD
# - JWT_SECRET
# - N8N_ENCRYPTION_KEY
# - N8N_USER_MANAGEMENT_JWT_SECRET
# - NGROK_AUTHTOKEN (if using Ngrok)
# - TELEGRAM_BOT_TOKEN (if using Telegram)
nano .env
```

## 4. Start Services

```bash
# Start all services (including Puter)
python3 start_services.py --profile cpu

# If you have NVIDIA GPU available:
# python3 start_services.py --profile gpu-nvidia

# If you have AMD GPU available:
# python3 start_services.py --profile gpu-amd
```

The script will:
1. Clone the Supabase repository
2. Configure environment settings
3. Start Supabase services
4. Start all other services (including Puter)
5. Configure Ngrok for webhook access (if configured)

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

## 6. Set Up System Service (Optional)

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

## 7. Update Your System

When you need to update:

```bash
# Stop all services
docker compose -p localai -f docker-compose.yml -f supabase/docker/docker-compose.yml down

# Pull latest versions
docker compose -p localai -f docker-compose.yml -f supabase/docker/docker-compose.yml pull

# Start services again
python3 start_services.py --profile cpu
```

## 8. Troubleshooting

If you encounter issues:

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

# If Docker daemon isn't running
sudo systemctl start docker
sudo systemctl enable docker

# Permission issues
sudo chmod 666 /var/run/docker.sock
```

## Additional Configuration

### Configuring Ngrok (for Webhooks)

If you need your n8n webhooks accessible from the internet:

1. Register at https://ngrok.com/
2. Get your auth token from the dashboard
3. Add to `.env`: `NGROK_AUTHTOKEN=your-ngrok-auth-token`
4. Run `./update_ngrok_url.sh` after services are started

### Telegram Integration

For Telegram login:

1. Create a bot via BotFather on Telegram
2. Get your bot token and set in the `.env` file:
   ```
   TELEGRAM_BOT_TOKEN=your-telegram-bot-token
   TELEGRAM_BOT_USERNAME=your_bot_username
   ```
3. Configure your domain in BotFather under Login Widget settings

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

### Setting Up WebUI

1. Access WebUI at `http://YOUR_SERVER_IP:3000/`
2. Configure Workspace Functions:
   - Go to Admin Settings -> Workspace -> Functions -> Add Function
   - URL: `http://host.docker.internal:5678/webhook/invoke_n8n_agent`
   - Enable the function 