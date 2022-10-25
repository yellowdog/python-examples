# YellowDog Installer Script for Amazon Linux 2 (GPU) Image from ECS

Base image:

- Amazon AMI ID (eu-west-2): `ami-03098a0869e59c486`

## Introduction

**`yd_installer_aws_batch_gpu.sh`** is a minimal installer script for installing and setting up the YellowDog agent on systems based on the `Amazon Linux 2 (GPU)` ECS image from AWS Batch. This image is based on Red Hat 7 and includes Docker.

It enables the following Task Types:

- **bash**: Including allowing the `yd-agent` user to use `sudo`
- **python**: Python 3.7 is installed as the system Python version
- **docker**

## Installation Instructions

1. Create a new AWS instance based on the AMI above and login over `SSH` using the key you supplied: `ssh -i <your_private_keyfile> ec2-user@<InstanceIP>`.
2. Switch user to `root` using `sudo su -`
3. To enable the installer script to download the YellowDog agent, create a file `/root/.netrc` containing your YellowDog Nexus username and password in the following format:
```
machine nexus.yellowdog.tech
    login <username>
    password <password>
```
4. Copy the `yd_install.sh` script to `/root`
5. Run the installer script: `bash /root/yd_install.sh`
6. Delete `/root/.netrc` and `/root/yd_install.sh`

Once these steps have been completed, create a new VM image based on the instance.
