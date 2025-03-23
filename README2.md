# System Architecture Overview

This document describes the architecture and component interactions of our Docker-based system, which integrates n8n, Ollama, Puter, Redis, and other services.

## Core Components

### Configuration Files

| File | Description |
|------|-------------|
| `docker-compose.yml` | Central configuration defining all containers and their relationships |
| `.env` | Environment variables used throughout the system |
| `.env.template` | Template with default values for creating `.env` |
| `start_services.py` | Main entry script that orchestrates system startup |
| `update_ngrok_url.sh` | Helper script to update dynamic ngrok URLs |

## Key Processes

### 1. Redis-Based Telegram Integration

1. Redis container acts as a central message broker and session store
2. Telegram Bot API webhooks are configured to send messages to n8n endpoints
3. Authentication data is stored in Redis with appropriate expiration times
4. User sessions are maintained securely across service restarts
5. n8n workflows can subscribe to Redis channels for real-time event processing
6. Authentication verification uses the bot token hash for security

### 2. Dynamic URL Configuration Process

1. The ngrok container starts and creates a tunnel
2. `update_ngrok_url.sh` queries the ngrok API to get the public URL
3. The script updates the `.env` file with the URL variables
4. It then updates the n8n container environment variables
5. Webhooks are configured with the new URL
6. Admin notification is sent via Telegram if configured

### 3. Container Networking Process

1. Docker Compose creates a custom network `kwintes_net`
2. All services are attached to this network
3. Services communicate using their container names as hostnames
4. The Caddy service uses `network_mode: host` to bind directly to host ports
5. Some services use `extra_hosts` to communicate with the host machine

### 4. Service Configuration Process

1. `start_services.py` loads the `.env` file or creates it from template
2. It detects hardware capabilities and selects an appropriate profile
3. The script invokes Docker Compose with the profile flag
4. Docker Compose reads the configuration file and environment variables
5. Containers are created and started with the specified configuration
6. Service information is displayed to the user

### 5. Ollama Model Configuration Process

1. `.env` specifies which models to pull via the `OLLAMA_MODELS` variable
2. The `ollama-pull-models` container is initialized with this variable
3. The container pulls the specified models during startup
4. The Ollama service is configured to expose the API on the specified port
5. Other services like OpenWebUI are configured to communicate with Ollama

### 6. Puter Cloud OS Integration

1. Puter container joins the `kwintes_net` network for integration with other services
2. Persistent storage is configured through mapped volumes to `/etc/puter` and `/var/puter`
3. The container is accessible via the configured port (default: 4100)
4. Access control is managed through the same network policies as other services
5. Provides a complete web-based operating system environment
6. File management and applications are accessible through the web interface

## Variable Flow and Dependencies

| Process | Source File | Source Variable | Target File | Target Variable | Description |
|---------|-------------|-----------------|------------|-----------------|-------------|
| Telegram Integration | `.env` | TELEGRAM_BOT_TOKEN | `docker-compose.yml` | environment.TELEGRAM_BOT_TOKEN | Bot token passed to n8n container |
| Telegram Integration | `.env` | TELEGRAM_BOT_USERNAME | `docker-compose.yml` | environment.TELEGRAM_BOT_USERNAME | Bot username for API calls |
| Telegram Integration | `.env` | REDIS_PASSWORD | `docker-compose.yml` | environment.REDIS_PASSWORD | Secure Redis connection |
| Telegram Integration | `.env` | REDIS_HOST | `docker-compose.yml` | environment.REDIS_HOST | Redis connection config |
| URL Configuration | `update_ngrok_url.sh` | NGROK_URL | `.env` | NGROK_URL | Dynamic URL from ngrok |
| URL Configuration | `update_ngrok_url.sh` | NGROK_URL | `.env` | WEBHOOK_TUNNEL_URL | Webhook URL for n8n |
| URL Configuration | `update_ngrok_url.sh` | NGROK_URL | `.env` | WEBHOOK_URL | Alternative webhook URL |
| URL Configuration | `.env` | NGROK_URL | `docker-compose.yml` | environment.WEBHOOK_TUNNEL_URL | Webhook URL in container |
| URL Configuration | `.env` | NGROK_URL | `docker-compose.yml` | environment.WEBHOOK_URL | Alternate webhook URL in container |
| Container Configuration | `.env` | N8N_VERSION | `docker-compose.yml` | image (n8n) | Container image version |
| Container Configuration | `.env` | N8N_PORT | `docker-compose.yml` | ports.n8n | Container port mapping |
| Container Configuration | `.env` | OLLAMA_MODELS | `docker-compose.yml` | command (ollama-pull-models) | Models to pull at init |
| Container Configuration | `.env` | OLLAMA_PORT | `docker-compose.yml` | ports.ollama | Container port mapping |
| Container Configuration | `.env` | PUTER_PORT | `docker-compose.yml` | ports.puter | Container port mapping for Puter |
| Container Configuration | `.env` | REDIS_PORT | `docker-compose.yml` | ports.redis | Redis port mapping |
| Service Orchestration | `start_services.py` | profile | `docker-compose.yml` | --profile | Hardware profile selection |
| Network Configuration | `docker-compose.yml` | kwintes_net | All services | networks | Service communication network |
| Environment Variables | `.env.template` | All variables | `.env` | All variables | Template for configuration |
| Environment Variables | `.env` | All variables | `start_services.py` | os.environ | Loaded at runtime |

## Key Features

- **Centralized Configuration**: All configuration is centralized in the `.env` file
- **Hardware-Aware Deployment**: Automatically selects appropriate profile based on available hardware
- **Dynamic URL Handling**: Automatically updates URLs and configurations when ngrok changes
- **Redis-Based Authentication**: Secure Telegram login with session persistence
- **Containerized Architecture**: All components run in isolated containers with defined relationships
- **Persistent Storage**: Data is preserved through mapped volumes
- **Cloud OS Environment**: Puter provides a web-based operating system for file management and application access

## Installation Guide for Ubuntu VPS

### Prerequisites

1. Update your system:
   ```bash
   sudo apt update && sudo apt upgrade -y
   ```

2. Install Docker and Docker Compose:
   ```bash
   # Install required packages
   sudo apt install -y apt-transport-https ca-certificates curl software-properties-common

   # Add Docker's official GPG key
   curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

   # Add Docker repository
   echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

   # Install Docker Engine
   sudo apt update
   sudo apt install -y docker-ce docker-ce-cli containerd.io

   # Install Docker Compose
   sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.3/docker-compose-linux-$(uname -m)" -o /usr/local/bin/docker-compose
   sudo chmod +x /usr/local/bin/docker-compose

   # Add your user to the docker group to run Docker without sudo
   sudo usermod -aG docker $USER
   
   # Apply the changes to current session
   newgrp docker
   ```

3. Install Python and Git:
   ```bash
   sudo apt install -y nano python3 python3-pip git
   ```

### Setting up the System

1. Clone the repository:
   ```bash
   git clone https://github.com/ThijsdeZeeuw/small_kwintes_cloud15.git
   cd small_kwintes_cloud15
   ```

2. Create directories for Puter and Redis:
   ```bash
   mkdir -p puter/config puter/data
   mkdir -p redis/data
   sudo chown -R 1000:1000 puter
   sudo chown -R 1000:1000 redis
   ```

3. Create or modify the `.env` file:
   ```bash
   cp .env.template .env
   nano .env
   ```
   
   Add or update the Puter and Redis-related configurations:
   ```
   # Puter Configuration
   PUTER_PORT=4100
   PUTER_CONFIG_PATH=./puter/config
   PUTER_DATA_PATH=./puter/data
   
   # Redis Configuration
   REDIS_PORT=6379
   REDIS_PASSWORD=your_secure_password_here
   REDIS_DATA_PATH=./redis/data
   
   # Telegram Configuration
   TELEGRAM_BOT_TOKEN=your_bot_token_here
   TELEGRAM_BOT_USERNAME=your_bot_username_here
   ```

4. Update the `docker-compose.yml` file to include Puter and Redis:
   ```bash
   nano docker-compose.yml
   ```
   
   Add the following service configurations:
   ```yaml
   puter:
     container_name: puter
     image: ghcr.io/heyputer/puter:latest
     restart: unless-stopped
     networks:
       - kwintes_net
     volumes:
       - ${PUTER_CONFIG_PATH}:/etc/puter
       - ${PUTER_DATA_PATH}:/var/puter
     ports:
       - "${PUTER_PORT}:4100"
     profiles:
       - local_ai
       
   redis:
     container_name: redis
     image: redis:7-alpine
     restart: unless-stopped
     command: redis-server --requirepass ${REDIS_PASSWORD}
     networks:
       - kwintes_net
     volumes:
       - ${REDIS_DATA_PATH}:/data
     ports:
       - "${REDIS_PORT}:6379"
     profiles:
       - local_ai
   ```

5. Create a Telegram bot authentication workflow for n8n:

   Create a file named `n8n_telegram_auth.json` with a workflow that:
   - Listens for webhook requests from Telegram
   - Verifies authentication data using the bot token
   - Stores user sessions in Redis
   - Handles session management and token refreshing
   - Implements secure data verification

   You can import this workflow into n8n after setting up the system.

6. Start the services:
   ```bash
   python3 start_services.py --profile local_ai
   ```

### Accessing the Services

- **Puter Cloud OS**: http://your-server-ip:4100
- **n8n Automation**: http://your-server-ip:${N8N_PORT}
- **Ollama LLM Interface**: http://your-server-ip:${OLLAMA_PORT}
- **Redis Commander** (if added): http://your-server-ip:8081

### Setting Up Telegram Bot Integration

1. **Create a Telegram Bot**:
   - Contact BotFather on Telegram
   - Create a new bot with `/newbot` command
   - Save the bot token in your `.env` file

2. **Configure Login Widget**:
   - Set up the domain allowlist with BotFather
   - Configure webhook URL to point to your n8n instance

3. **Configure n8n Workflows**:
   - Import the `n8n_telegram_auth.json` workflow
   - Set up credentials for Redis and Telegram
   - Activate the workflow

4. **Verify Integration**:
   - Check Redis connection with: `docker exec -it redis redis-cli -a ${REDIS_PASSWORD} ping`
   - Test webhook is receiving events
   - Verify user sessions are being stored in Redis

### Puter Cloud OS Configuration

1. **Initial Access**:
   - Access Puter Cloud OS using your browser at http://your-server-ip:4100
   - Create an administrator account on first login

2. **File Management**:
   - Upload files directly through the web interface
   - Organize content using the familiar desktop interface
   - Share files with other users in your organization

3. **Application Integration**:
   - Install applications from the Puter App Store
   - Configure applications to work with other services in your stack
   - Create custom workflows between Puter and n8n

4. **Customization**:
   - Modify the desktop environment to match your organization's needs
   - Create custom shortcuts to frequently used services
   - Set up user permissions and access controls

### Implementing Authentication Verification

For secure Telegram authentication, n8n will use this verification approach (automatically included in the workflow):

```javascript
// This runs inside n8n workflow
function verifyTelegramAuth(authData) {
  const crypto = require('crypto');
  const { hash, ...data } = authData;
  
  // Create secret key from bot token
  const secretKey = crypto.createHash('sha256')
    .update(process.env.TELEGRAM_BOT_TOKEN)
    .digest();
  
  // Create data check string
  const dataCheckString = Object.keys(data)
    .sort()
    .map(k => `${k}=${data[k]}`)
    .join('\n');
  
  // Generate HMAC
  const hmac = crypto.createHmac('sha256', secretKey)
    .update(dataCheckString)
    .digest('hex');
  
  // Verify hash matches
  return hmac === hash;
}
```

### Troubleshooting

1. **Port Availability**: Ensure the configured ports are not in use by other services and are allowed through your firewall:
   ```bash
   sudo ufw allow 4100/tcp  # For Puter
   sudo ufw allow ${N8N_PORT}/tcp
   sudo ufw allow ${OLLAMA_PORT}/tcp
   sudo ufw allow ${REDIS_PORT}/tcp  # Only if accessing Redis externally
   ```

2. **Permission Issues**: If you encounter permission problems with volumes:
   ```bash
   sudo chown -R 1000:1000 puter
   sudo chown -R 1000:1000 redis
   ```

3. **Docker Service**: If Docker isn't running:
   ```bash
   sudo systemctl start docker
   sudo systemctl enable docker
   ```

4. **Memory Constraints**: Ensure your VPS has at least 2GB RAM (4GB recommended) for all services to run smoothly.

5. **Network Issues**: If services can't communicate with each other:
   ```bash
   docker network inspect kwintes_net
   ```

6. **Redis Connection Issues**:
   ```bash
   docker logs redis
   docker exec -it redis redis-cli -a ${REDIS_PASSWORD} ping
   ```

7. **Puter Specific Issues**: If Puter isn't starting properly:
   ```bash
   docker logs puter
   ```

These interlinked processes create a dynamic, flexible system that's easy to deploy and manage in different environments. 