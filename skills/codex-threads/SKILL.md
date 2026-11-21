---
name: codex-threads
description: Run `codex exec` threads from Claude Code without silent waits, lost threads or stalls — launch in the background, watch progress in the chat, detect hangs and deaths, resume. Use when you run Codex from Claude Code outside T3 Code, or when a review needs a hard read-only sandbox.
---

# Codex threads

`scripts/cx` wraps `codex exec`. It runs one thread per name, logs compact
progress from Codex's JSON events, keeps a state file, enforces a timeout, and
makes sure every thread ends as `done`, `failed`, `timeout` or `killed`, never
in limbo.

    CX=~/.claude/skills/codex-threads/scripts/cx

## The pattern

1. **Write the brief to a file.** Codex does not see this conversation.
2. **Launch every thread with Bash `run_in_background: true`**, one call each:

       $CX run NAME --brief FILE --model MODEL --effort xhigh \
           --sandbox workspace-write --cd /repo --timeout 45

   `cx run` blocks until Codex ends, so the harness notifies you when it
   exits. That notification is your guaranteed wake-up. Codex's own life is
   tied to the wrapper, so killing the wrapper stops the thread.
3. **Arm one Monitor on the watch**, so the user sees progress in the chat:

       $CX watch

   Without names it follows every running thread, and picks up threads
   launched later, so one Monitor covers the whole session. Name threads
   (`$CX watch A B`) only to watch a subset.

   It prints starts, errors and endings at once, one combined summary line
   every 3 minutes, and a `[silent N min]` flag for a thread that has gone
   quiet. After 25 minutes it prints "re-arm the watch" and exits, before
   Monitor's 30-minute limit. Re-arm it when that line arrives and threads are
   still running. The watch only observes: its expiry never touches a thread.
4. **Tell the user in one line what is running**, then keep working on
   something else or end the turn. Ending the turn is safe because the
   background `cx run` will wake you.
5. **When a thread ends**, read `$CX result NAME`. Check the diff and run
   the tests yourself before accepting the work.

Other commands:

- `$CX status` shows one line per thread: state, minutes, commands, edits and
  the last action.
- `$CX resume NAME "message"` continues the same Codex session with its
  context. Use it for follow-ups, fixes after review, or after a timeout.
  Launch it in the background too.
- Files live in `/tmp/cx-threads/NAME/`: `progress.log`, `events.jsonl`,
  `stderr.log`, `state.json`, `result.md`.

## Rules learned the hard way

- **Never wait in the foreground.** Don't use `sleep` loops, `until` loops or
  a blocking `codex exec`. A foreground wait caps at 10 minutes and freezes
  the conversation.
- **Never find threads with `pgrep -f <pattern>`.** The waiting shell's own
  command line contains the pattern, so it matches itself and "waits"
  forever. It once hid a thread that had finished an hour earlier. Use
  `cx status`.
- **Never end a turn with threads running unless each one runs under a
  background `cx run`.** Otherwise nothing wakes you, and to the user it looks
  like you stalled.
- **Always feed stdin from a file or `/dev/null`.** `codex exec` reads extra
  input from stdin even when given a prompt, and can hang on it. `cx` does
  this for you.
- **A killed or failed run leaves no `result.md`.** Only `state.json` is
  reliable. Exit 0 plus a result file is still not success: read it.
- **Unattended runs use `approval_policy="never"`** (cx sets it), so a request
  for approval is refused instead of waiting forever.
- **Parallel writers** get disjoint files or `--worktree`. Integrate one at a
  time.
- **Keep 2–4 threads at once.** More multiplies notifications and integration
  work faster than it saves time.

## Briefs that finish

Give each thread a stopping condition, not just a topic:

- **Goal:** one or two sentences, with the product context it needs.
- **Owns:** exact files or directories. **Must not touch:** everything else.
- **Constraints:** style, dependencies, platform, and what it cannot verify.
- **Done means:** the checks to run and pass. For example: "stop when
  `pytest -q` passes. After two failed approaches, stop and report blocked,
  with evidence."
- **Final message:** what changed, what was verified, what was not, open
  questions.

For machine-readable reports, `codex exec --output-schema FILE` also works.
Validate the report yourself: valid JSON doesn't prove the work is done.
Don't use `--ephemeral`: it prevents `resume`.

## Failure signals

| Seen | Meaning | Do |
|---|---|---|
| `failed`, `error: ... usage limit` | quota exhausted | Stop launching Codex; route to Opus/Fable agents |
| `failed`, other error | model, config or network | Read `stderr.log`; fix and rerun |
| `timeout` | too slow or stuck | `cx resume NAME "summarise where you are and finish X"` with a new `--timeout` |
| `killed` | the wrapper died | Inspect the files it changed; resume or rerun |
| `[silent N min]` | long reasoning or a stuck tool | Check `progress.log`; wait, or let the timeout act |

`scripts/test_cx.py` holds regression tests against a fake `codex`. Run them
with `python3 test_cx.py` after changing `cx`.
