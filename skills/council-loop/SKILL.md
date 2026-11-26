---
name: council-loop
description: Review a change with a council of models from different providers, in rounds, until they all approve. Use when Nicolas says "council", "council loop", "loop", or asks for a review loop, and as the review step of finalize-feature.
---

# Council loop

A council reviews the change, you answer every finding, and the council looks again. Stop when every member approves, or when a disagreement needs Nicolas.

The point is a more correct change, not a bigger one. Make the smallest changes that satisfy the reviewers. Push back when they ask for more than the goal needs. Fighting scope creep is your job, not theirs.

## Members

Use the members Nicolas names. Otherwise:

- **Sol**, the newest `gpt-*-sol` on Codex, effort `xhigh`. It finds bugs and broken callers.
- **Opus**, the newest `claude-opus-*` on Claude, effort `xhigh`. It judges design, scope, and taste.
- **Neon**, the newest `gemini-*-neon` on Antigravity, `thought_level` `high`. A second bug finder, from a third company.

Members from different companies is the point: each catches what the others' training misses. "sol loop" means Sol alone. Look up the model IDs with `orchestrator_capabilities` (add `search` for models it leaves out). Never hard-code an ID. If you are one of the named models yourself, a fresh delegate of the same model still counts, because it does not share your context.

If a member cannot run, say so. Do not swap in another model. If Codex or Antigravity is out of usage, run with the members that remain and say in the report who did not review.

## Before round 1

Fix what you already know is wrong: open PR comments, failing checks, known bugs. Give the council the current code, not a list of fixes you plan to make. If Nicolas wants to throw the implementation away and explore, skip fixes to code that is being replaced.

Run `git status --short`. Do not stash, discard, or include unrelated changes. Find the base after `git fetch origin`:

- PR: `gh pr view <n> --json baseRefName,headRefOid`, then `git merge-base HEAD origin/<baseRefName>`. Confirm `HEAD` is the PR head, or ahead only by this change.
- Local branch: `git merge-base HEAD origin/<default-branch>`.
- No remote: a base Nicolas names, or `HEAD` for uncommitted changes.

The change is base to working tree, including untracked files. Use the same diff command in every round. Write the intent and what is out of scope in one or two sentences. Run the checks that cover the change, and note checks that are missing or already failed on the base.

## A round

In T3 Code, start one `delegate_task` per member, in parallel: `role: "review"`, `mode: "async"`, a new `clientRequestId` each round. Every round, including a follow-up, is a new `delegate_task`, never `t3_thread_send`. Outside T3 Code you can only reach your own provider: run with that member alone and say so.

Round 1 brief. Children see none of this conversation, so the brief carries everything:

```
Review only. Do not edit, commit, push, comment on PRs, or start subagents.
Repo: <abs path>  Base: <sha>
Intent: <intent>  Out of scope: <scope>  Checks: <results>
See: git diff <base> [-- <paths>]; git status --short (read untracked files).
Read the surrounding code. Find bugs, broken callers, and mismatches with the intent.
Skip style unless it hides a bug. Hold to the smallest change: flag code, tests,
or guards the intent does not need. Other paths, rare cases, small performance
costs, and extra compatibility are nits.
blocker = the intended case is wrong. should = a real bug callers will hit, within the intent. nit = the rest.
Reply:
VERDICT: APPROVE or CHANGES
SCORE: <n>/10
S1 [blocker|should|nit] <file>:<line> <claim>. Fix: <suggestion>   (keep ids stable)
```

A skill that calls this one may add a question of its own to the brief. Hand the members' answers back to it. This loop does nothing with them.

Do not edit files a member is still reviewing. Do not poll. End your turn and let the completion wake you. When one member's result arrives, check its findings against the code at once while the others run. A timeout, an error, or no reply is not approval.

## Answer the findings

Check each finding and its severity yourself. Another path, a rare case, or a small cost is a nit, whatever label it came with.

- **Agree:** make the smallest fix. Prefer deleting or narrowing code over a new lock, cache, helper, or option. Add one focused test that fails without the fix, if the intent needs it.
- **Disagree:** say why, with evidence: file and line, a test, command output.
- **Nit or out of scope:** decline in one line and list it as a follow-up.

When members contradict each other, decide on the evidence, and note it in the report. Do not agree just to end the loop.

Keep a ledger: id, member, severity, outcome. After answering, rerun the checks and `git diff --shortstat <base>`. If the review made the diff grow, cut first.

## Next round

Start one only if budget remains and a blocker or should is open, or behavior code changed since the approvals. Send each member the round 1 brief, the ledger (`fixed:`, `disagree:`, `declined:`, with evidence), the same base diff, and what changed since their last round. Ask them to look only at open ids and changed code, and to mark each old id `resolved` or `still open: <reason>`.

Budget: 3 rounds. Extend to 5 only for security, permissions, auth, data loss, or concurrency while a blocker or should stays open with evidence, or when Nicolas asks. Stop early when a round returns only nits. Declined nits and comment, doc, or format fixes need no new round.

## Done

**Agreed:** every member approved the current behavior diff, no blocker or should is open, and you have no concern of your own.

**Stuck:** a finding is still disputed after two replies, or the budget ran out. Show both sides in two or three lines each, and let Nicolas decide. Running out of budget is not approval.

Do not push during the loop. Push afterwards only if Nicolas asked you to push or ship, or the skill that called this one says to. If the work has a PR, put the result in its description, above the attribution line. Edit the description; do not post a comment.

```markdown
Council review: 2 rounds.

| Member | Round 1 | Round 2 |
| --- | --- | --- |
| GPT-6.2 Sol | 7/10 | 9/10 |
| Claude Opus 5.5 | 8/10 | 10/10 |
```

Use the model names that actually ran, from each result. Write `no score` when a member gave none. Never invent one.

Report: the members and rounds, what the council changed, the diff size before and after, fixed and declined findings with reasons, and whether you pushed.
