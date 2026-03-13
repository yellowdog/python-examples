#!/bin/bash

cd /root || exit
echo "Downloading the Agent installer script"
wget https://raw.githubusercontent.com/yellowdog/resources/refs/heads/main/agent-install/linux/yd-agent-installer.sh

# Install/update the Agent
bash yd-agent-installer.sh

echo "Restarting the Agent Service"
systemctl --no-block restart yd-agent.service
