#!/usr/bin/env python3
"""
start_services.py

This script starts the Supabase stack first, waits for it to initialize, and then starts
the local AI stack with support for Puter and Telegram. Both stacks use the same Docker 
Compose project name ("localai") so they appear together in Docker Desktop.
"""

import os
import subprocess
import shutil
import time
import argparse
import platform
import sys

def run_command(cmd, cwd=None):
    """Run a shell command and print it."""
    print("Running:", " ".join(cmd))
    subprocess.run(cmd, cwd=cwd, check=True)

def clone_supabase_repo():
    """Clone the Supabase repository using sparse checkout if not already present."""
    if not os.path.exists("supabase"):
        print("Cloning the Supabase repository...")
        run_command([
            "git", "clone", "--filter=blob:none", "--no-checkout",
            "https://github.com/supabase/supabase.git"
        ])
        os.chdir("supabase")
        run_command(["git", "sparse-checkout", "init", "--cone"])
        run_command(["git", "sparse-checkout", "set", "docker"])
        run_command(["git", "checkout", "master"])
        os.chdir("..")
    else:
        print("Supabase repository already exists, updating...")
        os.chdir("supabase")
        run_command(["git", "pull"])
        os.chdir("..")

def prepare_supabase_env():
    """Copy .env to .env in supabase/docker."""
    env_path = os.path.join("supabase", "docker", ".env")
    env_example_path = os.path.join(".env")
    print("Copying .env in root to .env in supabase/docker...")
    shutil.copyfile(env_example_path, env_path)

def check_puter_setup():
    """Check and prepare the Puter data directory."""
    print("Checking Puter configuration...")
    if not os.path.exists("puter-data"):
        print("Creating Puter data directory...")
        os.makedirs("puter-data", exist_ok=True)
        
        # Set appropriate permissions on Unix-like systems
        if platform.system() != "Windows":
            try:
                # UID 1000 is the standard user ID in many Docker containers
                run_command(["sudo", "chown", "-R", "1000:1000", "puter-data"])
                print("Set permissions for Puter data directory")
            except Exception as e:
                print(f"Warning: Could not set permissions for Puter data directory: {e}")
                print("You may need to manually run: sudo chown -R 1000:1000 puter-data")
    else:
        print("Puter data directory exists")

def check_telegram_setup():
    """Check Telegram configuration and setup webhook if needed."""
    print("Checking Telegram configuration...")
    
    # Check if Telegram bot token is configured
    with open(".env", "r") as file:
        env_contents = file.read()
        
    if "TELEGRAM_BOT_TOKEN=your-telegram-bot-token" in env_contents or "TELEGRAM_BOT_TOKEN=" in env_contents:
        print("Warning: Telegram bot token not configured in .env file")
        print("If you want to use Telegram integration, set TELEGRAM_BOT_TOKEN in your .env file")
    elif "TELEGRAM_BOT_TOKEN" in env_contents:
        print("Telegram bot token found in .env file")
        
        # Make update_telegram_webhook.sh executable if it exists
        if os.path.exists("update_telegram_webhook.sh"):
            try:
                os.chmod("update_telegram_webhook.sh", 0o755)
                print("Made update_telegram_webhook.sh executable")
            except Exception as e:
                print(f"Warning: Could not make update_telegram_webhook.sh executable: {e}")

def prepare_n8n_directories():
    """Prepare n8n backup directories to avoid import errors."""
    print("Preparing n8n backup directories...")
    os.makedirs("n8n/backup/credentials", exist_ok=True)
    os.makedirs("n8n/backup/workflows", exist_ok=True)
    
    # Create empty files to ensure directories aren't empty
    cred_file = os.path.join("n8n", "backup", "credentials", ".keep")
    wf_file = os.path.join("n8n", "backup", "workflows", ".keep")
    
    if not os.path.exists(cred_file):
        with open(cred_file, 'w') as f:
            f.write("")
    
    if not os.path.exists(wf_file):
        with open(wf_file, 'w') as f:
            f.write("")
    
    print("n8n backup directories prepared")

def stop_existing_containers():
    """Stop and remove existing containers for our unified project ('localai')."""
    print("Stopping and removing existing containers for the unified project 'localai'...")
    run_command([
        "docker", "compose",
        "-p", "localai",
        "-f", "docker-compose.yml",
        "-f", "supabase/docker/docker-compose.yml",
        "down"
    ])

def start_supabase():
    """Start the Supabase services (using its compose file)."""
    print("Starting Supabase services...")
    run_command([
        "docker", "compose", "-p", "localai", "-f", "supabase/docker/docker-compose.yml", "up", "-d"
    ])

def start_local_ai(profile=None):
    """Start the local AI services (using its compose file)."""
    print("Starting local AI services...")
    cmd = ["docker", "compose", "-p", "localai"]
    if profile and profile != "none":
        cmd.extend(["--profile", profile])
    cmd.extend(["-f", "docker-compose.yml", "up", "-d"])
    
    # Use non-checking run to prevent script termination if n8n-import fails
    try:
        run_command(cmd)
    except subprocess.CalledProcessError as e:
        print(f"Warning: Some services may have failed to start: {e}")
        print("Checking which services are running...")
        subprocess.run(["docker", "ps", "--format", "table {{.Names}}\t{{.Status}}"])
        print("\nContinuing with script execution...")

def generate_searxng_secret_key():
    """Generate a secret key for SearXNG based on the current platform."""
    print("Checking SearXNG settings...")
    
    # Define paths for SearXNG settings files
    settings_path = os.path.join("searxng", "settings.yml")
    settings_base_path = os.path.join("searxng", "settings-base.yml")
    
    # Check if settings-base.yml exists
    if not os.path.exists(settings_base_path):
        print(f"Warning: SearXNG base settings file not found at {settings_base_path}")
        return
    
    # Check if settings.yml exists, if not create it from settings-base.yml
    if not os.path.exists(settings_path):
        print(f"SearXNG settings.yml not found. Creating from {settings_base_path}...")
        try:
            shutil.copyfile(settings_base_path, settings_path)
            print(f"Created {settings_path} from {settings_base_path}")
        except Exception as e:
            print(f"Error creating settings.yml: {e}")
            return
    else:
        print(f"SearXNG settings.yml already exists at {settings_path}")
    
    print("Generating SearXNG secret key...")
    
    # Detect the platform and run the appropriate command
    system = platform.system()
    
    try:
        if system == "Windows":
            print("Detected Windows platform, using PowerShell to generate secret key...")
            # PowerShell command to generate a random key and replace in the settings file
            ps_command = [
                "powershell", "-Command",
                "$randomBytes = New-Object byte[] 32; " +
                "(New-Object Security.Cryptography.RNGCryptoServiceProvider).GetBytes($randomBytes); " +
                "$secretKey = -join ($randomBytes | ForEach-Object { \"{0:x2}\" -f $_ }); " +
                "(Get-Content searxng/settings.yml) -replace 'ultrasecretkey', $secretKey | Set-Content searxng/settings.yml"
            ]
            subprocess.run(ps_command, check=True)
            
        elif system == "Darwin":  # macOS
            print("Detected macOS platform, using sed command with empty string parameter...")
            # macOS sed command requires an empty string for the -i parameter
            openssl_cmd = ["openssl", "rand", "-hex", "32"]
            random_key = subprocess.check_output(openssl_cmd).decode('utf-8').strip()
            sed_cmd = ["sed", "-i", "", f"s|ultrasecretkey|{random_key}|g", settings_path]
            subprocess.run(sed_cmd, check=True)
            
        else:  # Linux and other Unix-like systems
            print("Detected Linux/Unix platform, using standard sed command...")
            # Standard sed command for Linux
            openssl_cmd = ["openssl", "rand", "-hex", "32"]
            random_key = subprocess.check_output(openssl_cmd).decode('utf-8').strip()
            sed_cmd = ["sed", "-i", f"s|ultrasecretkey|{random_key}|g", settings_path]
            subprocess.run(sed_cmd, check=True)
            
        print("SearXNG secret key generated successfully.")
        
    except Exception as e:
        print(f"Error generating SearXNG secret key: {e}")
        print("You may need to manually generate the secret key using the commands:")
        print("  - Linux: sed -i \"s|ultrasecretkey|$(openssl rand -hex 32)|g\" searxng/settings.yml")
        print("  - macOS: sed -i '' \"s|ultrasecretkey|$(openssl rand -hex 32)|g\" searxng/settings.yml")
        print("  - Windows (PowerShell):")
        print("    $randomBytes = New-Object byte[] 32")
        print("    (New-Object Security.Cryptography.RNGCryptoServiceProvider).GetBytes($randomBytes)")
        print("    $secretKey = -join ($randomBytes | ForEach-Object { \"{0:x2}\" -f $_ })")
        print("    (Get-Content searxng/settings.yml) -replace 'ultrasecretkey', $secretKey | Set-Content searxng/settings.yml")

def check_and_fix_docker_compose_for_searxng():
    """Check and modify docker-compose.yml for SearXNG first run."""
    docker_compose_path = "docker-compose.yml"
    if not os.path.exists(docker_compose_path):
        print(f"Warning: Docker Compose file not found at {docker_compose_path}")
        return
    
    try:
        # Read the docker-compose.yml file
        with open(docker_compose_path, 'r') as file:
            content = file.read()
        
        # Default to first run
        is_first_run = True
        
        # Check if Docker is running and if the SearXNG container exists
        try:
            # Check if the SearXNG container is running
            container_check = subprocess.run(
                ["docker", "ps", "--filter", "name=searxng", "--format", "{{.Names}}"],
                capture_output=True, text=True, check=True
            )
            searxng_containers = container_check.stdout.strip().split('\n')
            
            # If SearXNG container is running, check inside for uwsgi.ini
            if any(container for container in searxng_containers if container):
                container_name = next(container for container in searxng_containers if container)
                print(f"Found running SearXNG container: {container_name}")
                
                # Check if uwsgi.ini exists inside the container
                container_check = subprocess.run(
                    ["docker", "exec", container_name, "sh", "-c", "[ -f /etc/searxng/uwsgi.ini ] && echo 'found' || echo 'not_found'"],
                    capture_output=True, text=True, check=True
                )
                
                if "found" in container_check.stdout:
                    print("Found uwsgi.ini inside the SearXNG container - not first run")
                    is_first_run = False
                else:
                    print("uwsgi.ini not found inside the SearXNG container - first run")
                    is_first_run = True
            else:
                print("No running SearXNG container found - assuming first run")
        except Exception as e:
            print(f"Error checking Docker container: {e} - assuming first run")
        
        if is_first_run and "cap_drop: - ALL" in content:
            print("First run detected for SearXNG. Temporarily removing 'cap_drop: - ALL' directive...")
            # Temporarily comment out the cap_drop line
            modified_content = content.replace("cap_drop: - ALL", "# cap_drop: - ALL  # Temporarily commented out for first run")
            
            # Write the modified content back
            with open(docker_compose_path, 'w') as file:
                file.write(modified_content)
                
            print("Note: After the first run completes successfully, you should re-add 'cap_drop: - ALL' to docker-compose.yml for security reasons.")
        elif not is_first_run and "# cap_drop: - ALL  # Temporarily commented out for first run" in content:
            print("SearXNG has been initialized. Re-enabling 'cap_drop: - ALL' directive for security...")
            # Uncomment the cap_drop line
            modified_content = content.replace("# cap_drop: - ALL  # Temporarily commented out for first run", "cap_drop: - ALL")
            
            # Write the modified content back
            with open(docker_compose_path, 'w') as file:
                file.write(modified_content)
    
    except Exception as e:
        print(f"Error checking/modifying docker-compose.yml for SearXNG: {e}")

def update_ngrok_url():
    """Run the script to update the ngrok URL."""
    print("Updating ngrok URL...")
    try:
        # Make sure the script is executable
        os.chmod("update_ngrok_url.sh", 0o755)
        run_command(["./update_ngrok_url.sh"])
    except Exception as e:
        print(f"Error updating ngrok URL: {e}")
        print("You may need to manually run: ./update_ngrok_url.sh")

def configure_telegram_webhook():
    """Set up Telegram webhook after services are started."""
    print("Configuring Telegram webhook...")
    if os.path.exists("update_telegram_webhook.sh"):
        try:
            os.chmod("update_telegram_webhook.sh", 0o755)
            run_command(["./update_telegram_webhook.sh"])
            print("Telegram webhook configured successfully")
        except Exception as e:
            print(f"Error configuring Telegram webhook: {e}")
            print("You may need to manually run: ./update_telegram_webhook.sh")
    else:
        print("Warning: update_telegram_webhook.sh not found")

def check_required_services():
    """Check if all core services are running."""
    print("Checking service status...")
    services = ["n8n", "ollama", "puter", "open-webui", "searxng"]
    
    for service in services:
        try:
            result = subprocess.run(
                ["docker", "ps", "--filter", f"name={service}", "--format", "{{.Status}}"],
                capture_output=True, text=True, check=True
            )
            if result.stdout.strip():
                print(f"✅ {service} is running")
            else:
                print(f"❌ {service} is not running")
        except Exception as e:
            print(f"Error checking {service}: {e}")

def main():
    parser = argparse.ArgumentParser(description='Start the local AI and Supabase services.')
    parser.add_argument('--profile', choices=['cpu', 'gpu-nvidia', 'gpu-amd', 'none'], default='cpu',
                      help='Profile to use for Docker Compose (default: cpu)')
    args = parser.parse_args()

    # Prepare all services
    clone_supabase_repo()
    prepare_supabase_env()
    check_puter_setup()
    check_telegram_setup()
    prepare_n8n_directories()
    
    # Generate SearXNG secret key and check docker-compose.yml
    generate_searxng_secret_key()
    check_and_fix_docker_compose_for_searxng()
    
    stop_existing_containers()
    
    # Start Supabase first
    start_supabase()
    
    # Give Supabase some time to initialize
    print("Waiting for Supabase to initialize...")
    time.sleep(10)
    
    # Then start the local AI services
    start_local_ai(args.profile)
    
    # Give services some time to start up
    print("Waiting for services to start...")
    time.sleep(10)
    
    # Update ngrok URL after services are started
    update_ngrok_url()
    
    # Configure Telegram webhook after ngrok URL is updated
    configure_telegram_webhook()
    
    # Check service status
    check_required_services()
    
    print("\n🚀 All services started successfully!")
    print("\n📊 Access your services at:")
    print(" - WebUI: http://localhost:3000")
    print(" - n8n: http://localhost:5678")
    print(" - Puter: http://localhost:7000")
    print(" - SearXNG: http://localhost:8080")
    print(" - Flowise: http://localhost:3001")
    
    print("\n🔄 If you're using ngrok, you can check the public URL with:")
    print("  docker logs ngrok")
    print("  or check your .env file under NGROK_URL\n")

if __name__ == "__main__":
    main()