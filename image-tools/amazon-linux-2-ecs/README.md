# YellowDog Installer Script for Amazon Linux 2 (GPU) Image from ECS

Base image:

- Amazon AMI ID (eu-west-2): `ami-03098a0869e59c486`

## Introduction

**`yd_install.sh`** is a minimal installer script for installing and setting up the YellowDog agent on systems based on the `Amazon Linux 2 (GPU)` ECS image from AWS Batch. This image is based on Red Hat 7 and includes Docker.

It enables the following Task Types:

- **bash**: Including allowing the `yd-agent` user to use `sudo`
- **python**: Python 3.7 is installed as the system Python version
- **docker**

## Creating a YellowDog-Specialised Image

1. Edit the Nexus login and password in the `yd_install.sh` script (lines 17 and 18) to insert your YellowDog Nexus credentials.
1. Create a new AWS instance based on the AMI ID above and login over `SSH` using the key you supplied: `ssh -i <your_private_keyfile> ec2-user@<InstanceIP>`.
1. Switch user to `root` using `sudo su -`.
1. Update the image to pick up the latest versions of all installed packages by running: `yum update`.
1. Copy the [`yd_install.sh`](yd_install.sh) script to `/root`.
1. Run the installer script: `bash /root/yd_install.sh` and check for successful completion.
1. Delete the script: `rm -f /root/yd_install.sh`.

Once these steps have been completed, create a new VM image based on the instance.
