#!/bin/bash

#
# YellowDog agent installer script for use with 'Amazon Linux 2 (GPU)' AMI
# from AWS Batch.
#

######## Run as root ###########################################################

# Fail immediately on error; print script steps
set -euxo pipefail

# Set up Nexus credentials for YD Agent download
# *** EDIT LOGIN NAME & PASSWORD BELOW ***
cat > /root/.netrc << EOF
machine nexus.yellowdog.tech
    login     <insert_nexus_login_name>
    password  <insert_nexus_password>
EOF

# Install Java 11 & set as default
yum install -y java-11-amazon-corretto-headless && \
alternatives --set java /usr/lib/jvm/java-11-amazon-corretto.x86_64/bin/java

# Install AWS CLI to enable gathering ECR credentials if required
yum install -y unzip
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
./aws/install
rm -rf aws*

# Create 'yd-agent' user and directories
mkdir -p /opt/yellowdog
adduser yd-agent --home-dir /opt/yellowdog/agent
mkdir -p /var/opt/yellowdog/agent/data/actions
mkdir -p /var/opt/yellowdog/agent/data/workers
chown -R yd-agent:yd-agent /opt/yellowdog/agent
chown -R yd-agent:yd-agent /var/opt/yellowdog/agent/data

# Download the latest version of the YD Agent
curl -Lno "/opt/yellowdog/agent/agent.jar" \
  "http://nexus.yellowdog.tech/service/rest/v1/search/assets/download?sort=version&repository=maven-public&maven.groupId=co.yellowdog.platform&maven.artifactId=agent&maven.extension=jar"

chown yd-agent:yd-agent /opt/yellowdog/agent/agent.jar

# Set up the Agent's config file
cat > /opt/yellowdog/agent/application.yaml << EOF
yda.taskTypes:
  - name: "bash"
    run: "/bin/bash"
  - name: "python"
    run: "/usr/bin/python3"
  - name: "docker"
    run: "/opt/yellowdog/agent/docker-run.sh"
EOF

# Set up the agent start script
cat > /opt/yellowdog/agent/start.sh << EOF
#!/bin/bash
. ~/.bash_profile
/usr/bin/java -jar /opt/yellowdog/agent/agent.jar
EOF

chown -R yd-agent:yd-agent /opt/yellowdog/agent
chmod ug+x /opt/yellowdog/agent/start.sh

# Set up the Docker run script
cat > /opt/yellowdog/agent/docker-run.sh << 'EOF'
#!/bin/bash

# Run docker login if environment variables are set
[[ ! -z "$DOCKER_PASSWORD" && ! -z "$DOCKER_USERNAME" ]] && docker login -u $DOCKER_USERNAME -p $DOCKER_PASSWORD $DOCKER_REGISTRY

# Default YD_WORKING if not set
[ -z "$YD_WORKING" ] && export YD_WORKING="/yd_working"

# Run docker command
docker run -e YD_WORKING=$YD_WORKING -v `pwd`:$YD_WORKING $@
EOF

chown yd-agent:yd-agent /opt/yellowdog/agent/docker-run.sh
chmod ug+x /opt/yellowdog/agent/docker-run.sh

# Set up the systemd configuration
cat > /etc/systemd/system/yd-agent.service << EOF
[Unit]
Description=YellowDog Agent
After=cloud-final.service

[Service]
User=yd-agent
WorkingDirectory=/opt/yellowdog/agent
ExecStart=/opt/yellowdog/agent/start.sh
SuccessExitStatus=143
TimeoutStopSec=10
Restart=on-failure
RestartSec=5

[Install]
WantedBy=cloud-init.target
EOF

mkdir -p /etc/systemd/system/yd-agent.service.d

cat > /etc/systemd/system/yd-agent.service.d/yd-agent.conf << EOF
[Service]
Environment="YD_AGENT_HOME=/opt/yellowdog/agent"
Environment="YD_AGENT_DATA=/var/opt/yellowdog/agent/data"
EOF

mkdir -p /lib/systemd/system/cloud-final.service.d

cp /etc/systemd/system/yd-agent.service.d/yd-agent.conf \
   /lib/systemd/system/cloud-final.service.d/yd-agent.conf

systemctl enable yd-agent.service && systemctl start yd-agent

# Add yd-agent to sudoers, with no password required
usermod -aG wheel yd-agent
echo -e "yd-agent\tALL=(ALL)\tNOPASSWD: ALL" > /etc/sudoers.d/020-yd-agent

# Add yd-agent to the docker group
usermod -a -G docker yd-agent

# Ensure that the Nvidia runtime is the Docker default
(grep -q ^OPTIONS=\"--default-runtime /etc/sysconfig/docker && \
 echo '/etc/sysconfig/docker needs no changes') || \
 (sed -i 's/^OPTIONS="/OPTIONS="--default-runtime nvidia /' /etc/sysconfig/docker && \
 echo '/etc/sysconfig/docker updated to have nvidia runtime as default' \
 && systemctl restart docker && echo 'Restarted docker')
