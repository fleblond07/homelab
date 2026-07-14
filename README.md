# Homelab Ansible

## Bootstrap prerequisites

Before running the bootstrap playbook, the target host must already have an
Ansible-capable admin user. This repository expects that user to be
`homelab_admin`.

On the host, create the user and install the basics:

```bash
sudo adduser --disabled-password --gecos "" homelab_admin
sudo apt update
sudo apt install -y sudo python3 openssh-server
```

Add the controller SSH public keys to the admin user:

```bash
sudo install -d -m 0700 -o homelab_admin -g homelab_admin /home/homelab_admin/.ssh
sudo editor /home/homelab_admin/.ssh/authorized_keys
sudo chown homelab_admin:homelab_admin /home/homelab_admin/.ssh/authorized_keys
sudo chmod 0600 /home/homelab_admin/.ssh/authorized_keys
```

Grant passwordless sudo for Ansible:

```bash
sudo visudo -f /etc/sudoers.d/90-homelab-admin
```

Add:

```sudoers
homelab_admin ALL=(ALL:ALL) NOPASSWD:ALL
```

Validate the sudoers file:

```bash
sudo visudo -cf /etc/sudoers.d/90-homelab-admin
```

From the Ansible controller, verify access before running any playbook:

```bash
ssh homelab_admin@192.168.1.47
sudo -n id
```

`sudo -n id` should print `uid=0(root)` without prompting for a password.

## Running the SSH bootstrap

```bash
ansible-playbook playbooks/bootstrap.yml
```
