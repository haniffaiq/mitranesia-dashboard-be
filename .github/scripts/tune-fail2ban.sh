#!/bin/bash
set -e
WHITELIST_IP="${1:-112.215.171.70}"
cat > /etc/fail2ban/jail.local <<EOF
[DEFAULT]
bantime  = 10m
findtime = 10m
maxretry = 10
backend  = systemd
ignoreip = 127.0.0.1/8 ::1 ${WHITELIST_IP}

[sshd]
enabled = true
port    = ssh
EOF
systemctl restart fail2ban
sleep 2
fail2ban-client unban --all || true
fail2ban-client status sshd | head -20
echo '---ignoreip---'
grep ignoreip /etc/fail2ban/jail.local
