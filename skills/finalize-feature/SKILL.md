---
name: finalize-feature
description: Take the current work to a proven, council-reviewed pull request and merge it. Fixes merge on their own, visible ones too. Anything that adds to the product, or reworks a lot at once, is finished and then held for Nicolas with a before and after. Use when Nicolas says "finalize feature", "finalize this", "finalize and merge", or asks to finish work end to end.
---

# Finalize feature

Nicolas is probably not watching. Own the work from where it is now to a merged PR, or to a finished PR that is held for his yes.

## Merge or hold

Nicolas is the gate for what gets added to his product. A model finds a good reason for every addition, and a product gets worse one reasonable addition at a time. Models are good at making a broken thing work. So fixes go through, and additions wait for him.

- **Merge: a fix.** Something was wrong and now it is right, also when it is visible: a crash, a button that does nothing or is too small to hit, a cut-off label, a broken layout. Upkeep that leaves the product as it is merges too: tests, CI, docs, a contained cleanup.
- **Hold: an addition.** Anything the product did not have before: a feature, screen, button, option, setting, message, or step in a flow. Hold it also when he asked for it by name. He decides whether it stays once he can see it.
- **Hold: a drastic change.** Reworking a lot at once, even with nothing new in it: a redesigned screen, a large refactor, a change to the architecture or to stored data.

A fix that brings a new option or a "while I was here" improvement is an addition. Take it out and merge the fix alone.

These are examples, not a checklist. You make the call and give your reason in one sentence. Do not hold a plain fix to be safe. If he said in this request to merge without showing him, do that.

The council votes too. Add this to each member's round 1 brief, without your own call:

```
Also answer on its own line:
HOLD FOR NICOLAS: yes or no, <one-line reason>
Nicolas decides what gets added to his product. Say yes if this change adds anything the
product did not have before (a feature, screen, button, option, setting, message, or step
in a flow), also when it comes inside a bug fix, or if it reworks a lot at once. Say no for
a fix that only makes existing behavior correct, also a visible one, and for upkeep.
```

Any member's yes holds the merge. No vote releases a merge you decided to hold.

## Steps

This request lets you do all of it without asking. That includes test methods a project rule says to ask about first (running the app, emulators and devices, the browser, computer use), force-pushing this task's own branch with `--force-with-lease`, and a merge that starts the repo's usual automatic deploy.

1. **Set up.** Work on a branch. Use a worktree of your own if the main checkout has uncommitted work or another session is using it.
2. **Finish the change** with the smallest change that works. Fix the case that happened, not every case that could.
3. **Prove it.** See "Proof".
4. **Review it** with the `council-loop` skill, with the hold question added.
5. **Open the PR**, after rebasing onto the latest default branch. Start the description with the problem in plain words, then what the change does, how you proved it, and whether the merge is held. Check it for secrets and private details. Not a draft.
6. **Get the checks green.** Wait with one watcher, never a `sleep` or polling loop: `watch_pull_request` in T3 Code, `gh pr checks <pr> --watch --fail-fast` in the background elsewhere. Fix real failures and prove each fix. Rerun a suspected flake once. A check counts as required even where GitHub cannot enforce it.
7. **Merge, or hold.** Right before a merge, fetch and check again: green, up to date with the default branch, and the council's approval covers the current diff. Merge the way the repo usually does, never with `--admin`. Then delete the branch and the worktree. For a hold, see "A held merge".

Do not end your turn while checks are pending unless a watcher will wake you.

## Proof

Proof is something you observed yourself in this session:

- Reproduce the failure, apply the fix, and watch the same reproduction pass.
- Run the checks the repo's CI runs, and read the actual results.
- Add one focused test when the behavior has none, and confirm it fails without the fix.
- For UI, run the app and look. Take a screenshot of the same view before and after.

Never take a device or emulator another session is using. A test that also fails on the base branch is not yours: leave it out and report it as found work.

## A held merge

Finish everything first: proof, council, PR, green checks. Do not stop earlier to ask whether he wants it. He can only judge it once he can see it.

Then end with a message that leads with the decision. In T3 Code, call `unwatch_pull_request` first.

- What is new, in one or two plain sentences, from the user's side.
- Before and after as images inline. For a drastic change with nothing to see, say what was reworked and how big it is.
- Why it is held: your call, or which council member's.
- The PR link, and that it is proven, approved by the council, and green.
- Last, the question: do we want this?

On his yes, merge. If he wants it changed, take the change through proof, the council, and the checks again. If he drops it, close the PR and delete the branch.

## When you cannot go on

Decide everything else yourself, and list those decisions in the report. Stop only when you cannot prove the change, the checks cannot go green, the goal is ambiguous in a way that changes the result, another PR makes this one obsolete, or the next step deletes data, touches production, or changes things outside the repo. Leave the PR open, and start your final message with what stops you and your recommendation.

## Report

For a merged change: the PR link and merge commit, what the merge started, why it needed no hold, how you proved it, the council result, your decisions, found work, and the risks that remain. Say plainly what is left open, or that nothing is.
