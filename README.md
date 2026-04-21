# Telegram Channel Subscription Monitor

This is a Python-based automation tool utilizing Telethon to emulate and automate Telegram client activities, specifically monitoring channel subscriptions.

## Key Features

- **Automated Monitoring**: Regularly checks for user subscription and unsubscription events on a Telegram channel.
- **Service-Oriented**: Runs as a continuous service on Linux, fetching admin actions every 5 minutes.
- **Efficient Storage**: Actions are hashed based on the date and user ID. Only unique actions are saved to the Firebase Firestore database, preventing duplicates.
- **Real-time Notifications**: Sends detailed alerts of each action to another Telegram channel or group. These alerts include user ID, nickname, first and last name, action date, and the corresponding hash.
- **Sentry Integration (Optional)**: Monitor application health and track potential issues with Sentry.

## Requirements

### System
- **OS**: Linux-based machine.
- **Permissions**: User with `sudo` access.
- **Runtime**: Python **3.12+** (managed by [uv](https://docs.astral.sh/uv/)).
- **Package manager**: [uv](https://docs.astral.sh/uv/getting-started/installation/) — installs Python itself and resolves dependencies from `pyproject.toml` / `uv.lock`.

### Firebase Firestore
1. **Database Setup**: create a collection named `admin_actions` in Firestore. No seed document is required — the app writes on its own.
2. **Private Key**: download your Firebase private key JSON from the [Firebase console](https://console.firebase.google.com/), rename to `serviceAccountKey.json`, and place it in the project root (same directory as `main.py`).

### Telegram
1. **API Credentials**: register on [my.telegram.org](https://my.telegram.org/) to get `api_id` and `api_hash`.
2. **Channel to Monitor**: have the username of the channel you want to watch (e.g. `@channel_name`).
3. **Bot Token**: create a bot via [@BotFather](https://t.me/BotFather).
4. **Notification Receiver ID**: pick a Telegram channel or group to receive notifications and obtain its chat id (e.g. `-1001234567890`). Guide: <https://gist.github.com/mraaroncruz/e76d19f7d61d59419002db54030ebe35>.
5. **Receiver Invite Link**: create an invite link for the receiver (used to verify delivery). Example for private channels: `https://t.me/+IybSNCg_1a2b3c4d5e`.
6. **Bot in Receiver**: add the bot to the receiver channel/group with admin privileges so it can send messages.

### Sentry (Optional)
- **DSN**: obtain a DSN from your Sentry account — used to ship error/trace data.

## Installation (from scratch)

Run on the machine that will host the service.

```bash
# 1. Install uv (one-time)
curl -LsSf https://astral.sh/uv/install.sh | sh
source $HOME/.local/bin/env   # or restart the shell

# 2. Clone
git clone git@github.com:dyvovyzhno/telegram-channel-subs-monitor.git
cd telegram-channel-subs-monitor

# 3. Install Python 3.12 and sync dependencies into .venv
uv python install 3.12
uv sync

# 4. Create .env from the template and fill real values
cp .env.example .env
# edit .env

# 5. Place serviceAccountKey.json in the project root (see Firebase section above)

# 6. Log in to Telegram once interactively to create anon.session
.venv/bin/python main.py
# Enter the SMS code (and 2FA password if set). After you see
# "Fetching new admin actions..." a second time (5 min after the first),
# press Ctrl+C to stop.

# 7. Set up the systemd service
# The unit file (telegram-stats-monitor.service) is already shipped with the
# correct /home/ubuntu/proj/telegram-stats-monitor/ paths. If your
# WorkingDirectory differs, edit it before copying.
sudo cp telegram-stats-monitor.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable telegram-stats-monitor.service
sudo systemctl start telegram-stats-monitor.service
```

## Deploying updates

When new commits land on `main` and you want the server to pick them up:

```bash
# 1. SSH and go to the project
ssh <user>@<server>
cd /home/ubuntu/proj/telegram-stats-monitor/

# 2. Stop the service
sudo systemctl stop telegram-stats-monitor

# 3. Pull latest
git pull origin main

# 4. Re-sync deps (cheap no-op if nothing changed)
uv sync

# 5. If the systemd unit changed in this release, redeploy it
sudo cp telegram-stats-monitor.service /etc/systemd/system/
sudo systemctl daemon-reload

# 6. Start and tail the logs
sudo systemctl start telegram-stats-monitor
sudo journalctl -u telegram-stats-monitor -f
# Look for two "Fetching new admin actions..." lines 5 min apart — that
# confirms a full job cycle completed cleanly.
```

If `.env` gained a new required variable in the release (rare, but check the PR description), add it before starting the service.

## Local development

Dev tooling (`ruff`, `pyright`) lives in the `dev` dependency group and is installed automatically by `uv sync`.

```bash
uv sync                 # installs runtime + dev deps into .venv
.venv/bin/ruff check .  # lint
.venv/bin/ruff format . # format
.venv/bin/pyright .     # type-check (basic mode)
```

Follow-ups that are deferred (hooks, CI, strict typing) are tracked in [TODO.md](TODO.md).

## Operations

```bash
# Status
sudo systemctl status telegram-stats-monitor

# Live logs
sudo journalctl -u telegram-stats-monitor -f

# Restart
sudo systemctl restart telegram-stats-monitor

# Stop
sudo systemctl stop telegram-stats-monitor

# Disable autostart
sudo systemctl disable telegram-stats-monitor
```
