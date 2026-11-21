---
name: hetzner
description: Manage Nicolas's Hetzner account — servers, firewalls, IPs, volumes, DNS zones and records, storage boxes — with the authenticated `hcloud` CLI or the Hetzner API, SSH into the servers, and sign in to the Hetzner website for what the API cannot do. Use whenever a task touches Hetzner, a server Nicolas hosts, or DNS for one of his domains.
---

Nicolas's Hetzner account has one Cloud project, `Default`. Ask Hetzner what exists instead of trusting a list written here: `hcloud server list`, `hcloud zone list`, `hcloud firewall list`, `hcloud primary-ip list`, `hcloud storage-box list`.

This skill is public, so the private details of the account are not in it. They live in `~/.config/hetzner/account.env`: `HETZNER_LOGIN` (the sign-in email), `HETZNER_PROJECT_ID`, and `HETZNER_SSH_KEY` (the path of the SSH key). Load them in the same command that uses them, as in the examples below. Never write their values into this skill or any other file tracked by git.

`hcloud` is on `PATH` and already authenticated. The wrapper `~/agents/bin/hcloud` reads the token from `~/.config/hetzner/api-token`. Add `-o json` when you need to parse output. `hcloud <command> --help` is accurate and current.

For the raw API, send the same token: `curl -H "Authorization: Bearer $(cat ~/.config/hetzner/api-token)" https://api.hetzner.cloud/v1/servers`. Never print the token, paste it into chat, commit it, or put it in a file outside `~/.config/hetzner/`.

SSH into a server as root with `. ~/.config/hetzner/account.env && ssh -i "$HETZNER_SSH_KEY" root@"$(hcloud server ip <name>)"`. The key has no passphrase, so this works without an SSH agent.

DNS lives in the same API. Use `hcloud zone` and `hcloud zone rrset` to read and change records.

The token has Read & Write access to the whole project. Reading is always fine. Ask Nicolas first before anything that deletes, replaces, or can lock him out: deleting or rebuilding a server, changing or deleting DNS records, deleting zones, IPs, volumes or snapshots, changing firewall rules, or disabling protection. Creating resources costs money, so do it only when the task calls for it, and say what you created and what it costs per month.

Some things only work on the website: account settings and 2FA, invoices and payment, limit increases, support tickets, creating API tokens, Robot (dedicated servers), and konsoleH (web hosting). Prefer the API whenever it can do the job. Use whatever browser your harness gives you. The browser may already be signed in, so check the open tabs before you navigate, and work in a tab of your own rather than one Nicolas is using. If you need to sign in, go to `https://accounts.hetzner.com` and use `$HETZNER_LOGIN` with the password from `. ~/.config/hetzner/account.env && secret-tool lookup service hetzner-console username "$HETZNER_LOGIN"`. Type it only into that sign-in page, and never print it, log it, or save it anywhere else. If Hetzner asks for a 2FA code, ask Nicolas for it.

The website can do more than the token, so the bar is higher there. Ask Nicolas before anything that costs money or cannot be undone: ordering or cancelling products, changing payment or billing details, deleting a project, removing members, and changing the password, email or 2FA.

To rotate the token, create a new Read & Write token in the Console under Default → Security → API tokens, write it to `~/.config/hetzner/api-token` with mode 600, check that `hcloud server list` works, then delete the old token in the Console.
