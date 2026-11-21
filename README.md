# nstack

The agent skills I use to get work finished without watching it. They work in Claude Code and Codex, and use [T3 Code](https://github.com/pingdotgg/t3code) features where they exist.

Largely inspired by [tstack](https://github.com/t3dotgg/tstack) by Theo Browne. `modernize` is his, almost unchanged.

| Skill | Say | What it does |
|---|---|---|
| `finalize-feature` | "finalize feature" | Takes a change to a tested, reviewed pull request. Fixes merge on their own. Anything that adds to the product is finished and then held for me, with a before and after. |
| `council-loop` | "council", "sol loop" | Two models from two companies review a change in rounds until both approve. |
| `modernize` | "modernize" | Rebases an old pull request and says honestly whether it should still exist. |
| `hetzner` | (automatic) | Manages a Hetzner account with the `hcloud` CLI, and asks before anything that deletes or costs money. |

The idea behind `finalize-feature`: a model is good at making a broken thing work, and bad at deciding what a product should have. It finds a good reason for every addition. So fixes go through, and additions wait for a person.

[AGENTS.md](AGENTS.md) is the instruction file every agent on my machine reads. It is here as an example, not as something to install.

To install, copy the folders in `skills/` to `~/.claude/skills/` for Claude Code or `~/.agents/skills/` for Codex. `finalize-feature` needs `council-loop`. Do not run `install.sh` unless you want my whole setup: it also links my `AGENTS.md` as your global instructions.

`hetzner` reads the API token from `~/.config/hetzner/api-token` and the account's private details from `~/.config/hetzner/account.env`. Nothing private is in this repo.

You need an authenticated [GitHub CLI](https://cli.github.com). `council-loop` needs a harness that can run a model from another provider as a subagent. T3 Code does this with `delegate_task`.

The skills are written for me. They say "Nicolas" and name the models I trust. Change both.

[MIT](LICENSE)
