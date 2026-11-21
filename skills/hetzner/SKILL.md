---
name: hetzner
description: Work in Nicolas's Hetzner account with the `hcloud` CLI. Use when a task touches Hetzner, a server he hosts, or DNS for one of his domains.
---

`hcloud` is on `PATH` and already authenticated. It reads its token from `~/.config/hetzner/api-token`. Everything is in one project: servers, firewalls, DNS zones and storage boxes.

The account's private details are in `~/.config/hetzner/account.env`: `HETZNER_LOGIN`, `HETZNER_PROJECT_ID` and `HETZNER_SSH_KEY`. Load the file in the command that needs them:

```sh
# SSH into a server
. ~/.config/hetzner/account.env && ssh -i "$HETZNER_SSH_KEY" root@"$(hcloud server ip <name>)"

# Password for accounts.hetzner.com, for what the API cannot do
. ~/.config/hetzner/account.env && secret-tool lookup service hetzner-console username "$HETZNER_LOGIN"
```

Never put the token, the password or these values into chat or another file. If the sign-in asks for a 2FA code, ask Nicolas.

Reading is always fine. Ask Nicolas before you delete or rebuild something, change a DNS record or firewall rule, spend money, or touch the sign-in or payment settings, unless he asked for exactly that.
