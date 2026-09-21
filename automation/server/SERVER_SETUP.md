# KYLA server setup

This moves KYLA's n8n, strategy factory, paper trader, and journal onto an always-on server. Keep live trading disabled until every safety check passes.

## 1. Oracle Cloud Always Free ARM VM

1. Create an Oracle Cloud account at https://www.oracle.com/cloud/free/.
2. Create a Compute Instance: Shape VM.Standard.A1.Flex (Ampere ARM), 4 OCPUs and 24 GB RAM, Ubuntu 22.04 or 24.04, Always Free eligible availability domain.
3. During creation generate/upload an SSH key. Download the private key and protect it: chmod 600 ~/Downloads/oracle-kyla.key
4. Copy the public IP and connect: ssh -i ~/Downloads/oracle-kyla.key ubuntu@YOUR_SERVER_IP

Oracle capacity can be temporarily unavailable; retry another availability domain or region instead of creating a paid instance.

## 2. Install the stack

Run on the server:

    sudo bash -c '
    set -e
    apt-get update
    apt-get install -y git python3 python3-pip python3-venv curl build-essential ufw
    curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
    apt-get install -y nodejs
    npm install -g n8n@latest
    adduser --disabled-password --gecos "" kyla || true
    mkdir -p /opt/kyla-quant
    chown -R kyla:kyla /opt/kyla-quant
    sudo -u kyla git clone https://github.com/M3lcharagu/kyla-quant.git /opt/kyla-quant
    cd /opt/kyla-quant
    sudo -u kyla python3 -m venv .venv
    if [ -f requirements.txt ]; then sudo -u kyla .venv/bin/pip install -r requirements.txt; fi
    '

Verify the script paths before enabling cron: find /opt/kyla-quant -type f \( -name "*strategy*" -o -name "paper_trader.py" -o -name "*journal*" \)

Create /opt/kyla-quant/.env owned only by kyla (sudo -u kyla touch /opt/kyla-quant/.env && sudo chmod 600 /opt/kyla-quant/.env) with WEBHOOK_URL=YOUR_WEBHOOK_URL.

Create /etc/systemd/system/kyla-n8n.service:

    [Unit]
    Description=KYLA n8n automation
    After=network-online.target
    Wants=network-online.target

    [Service]
    Type=simple
    User=kyla
    WorkingDirectory=/opt/kyla-quant
    EnvironmentFile=-/opt/kyla-quant/.env
    Environment=NODE_ENV=production
    Environment=N8N_HOST=127.0.0.1
    Environment=N8N_PORT=5678
    ExecStart=/usr/bin/n8n start
    Restart=always
    RestartSec=10

    [Install]
    WantedBy=multi-user.target

Enable: sudo systemctl daemon-reload && sudo systemctl enable --now kyla-n8n && sudo systemctl status kyla-n8n

Add cron jobs for kyla user (sudo -u kyla crontab -e), Nairobi time:

    CRON_TZ=Africa/Nairobi
    0 22 * * * bash -lc 'cd /opt/kyla-quant && set -a && . ./.env && set +a && .venv/bin/python strategy_factory.py backtest && git add docs/STRATEGY_LIBRARY.md && (git diff --cached --quiet || git commit -m "nightly strategy library update") && git push origin main >> /home/kyla/nightly.log 2>&1'
    */15 9-15 * * 1-5 bash -lc 'cd /opt/kyla-quant && set -a && . ./.env && set +a && flock -n /tmp/kyla-paper.lock timeout 14m .venv/bin/python paper_trader.py --loop >> /home/kyla/paper-trader.log 2>&1'
    0 18 * * 0 bash -lc 'cd /opt/kyla-quant && set -a && . ./.env && set +a && .venv/bin/python journal.py --kpi-report >> /home/kyla/journal.log 2>&1'

## 3. Allow GitHub pushes

Preferred: add the server's SSH key as a repository deploy key with write access, then set origin to SSH. Alternative: narrowly scoped GitHub PAT with repo scope stored only in .env. Never commit .env or print the token.

## 4. Send results to a phone

Set WEBHOOK_URL in .env. Use a Telegram bot or Discord webhook. Notify with: curl -fsS -X POST "$WEBHOOK_URL" -H "Content-Type: application/json" --data '{"content":"KYLA result: see the latest journal"}' (Telegram requires chat_id and text fields instead of content).

## 5. Cost

Oracle Always Free ARM VM costs $0 while capacity and account limits permit. Paid alternatives ~$4-6/month: Hetzner CX22 or Contabo VPS S. Confirm current prices.

## 6. Security checklist

    sudo ufw default deny incoming
    sudo ufw default allow outgoing
    sudo ufw allow OpenSSH
    sudo ufw enable

Keep n8n bound to localhost unless a hardened HTTPS reverse proxy is configured. Optional fail2ban. Do not store exchange API keys on this server. Keep paper trading enabled. Before any live action require a kill-switch check. Test the kill switch before enabling any live workflow.
