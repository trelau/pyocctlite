---
name: consistency-review
description: Step back and review a whole codebase against its own principles and conventions after features have accumulated, looking for drift, refactors that are getting more expensive, loose ends from earlier work, and the best next step. Use when the user asks for a consistency check or a step back across the code, asks whether things are staying true to form, asks about refactoring opportunities or low-hanging fruit, or asks what to do next after several features. Not for reviewing a single diff or PR for bugs.
---

# Consistency Review

Features added one at a time are each reasonable, but they drift apart. This review looks across them, at the point where a few have landed, and reports what's worth doing. Report first and change nothing until the user has chosen, because they often know why something is the way it is.

## Gather the standard

Read what the project says it wants before reading the code: project instructions, stated principles and patterns, the user's notes and saved memories, and recent commits to see what changed since the last pass. Note anything the user has already decided or deferred, and don't reopen it.

## Look for

- **Exemplars out of step:** start with any code the project names as a model. Agents copy it, so check it against the stated rules first and report conflicts to reconcile.
- **Drift from stated rules:** code that breaks a principle or pattern, or two parts solving the same problem differently. Also rules that the code has outgrown, and decisions that were made but never written down.
- **Inconsistent surface:** similar things named, ordered, or behaving differently. Judge it the way a new user would: could they predict this from one example?
- **Domain conventions:** terms, orientations, and argument meanings that would surprise someone who knows the field.
- **Duplication that compounds:** repetition that the next feature will add to. Repetition a stated pattern calls for isn't a finding unless the pattern itself has become costly. Repetition that's merely untidy matters much less.
- **Layers out of sync:** capability in one layer that another can't reach, and docs, stubs, or examples that no longer match. Compare these with a search, since skimming misses most of it.
- **Loose ends:** stale notes, finished to-dos, documented limitations, and gaps that earlier work had to work around.

## Verify before reporting

Run the project's tests, checks, and any examples; don't write one-off scripts for what they could enforce. When a rule has drifted and a built-in lint or type check could catch it, suggest enabling that. Reproduce behavior claims by running them, isolating anything that could crash the process. For claims about outside conventions, check primary sources and say how strong the evidence is. Label anything you couldn't confirm.

## Report

Lead with the recommended next step, including when that's "nothing here is urgent, build the next feature." Then give one short table, with the most important findings first:

| Finding | Where | Evidence | Suggested fix |
|---|---|---|---|

Sort findings into three groups:

- **Clear:** the right fix is obvious, and it's safe to do on request.
- **Decide:** the user's call, because it breaks callers, trades off principles, or changes behavior. Give a recommendation.
- **Defer:** the design would be a guess until real use shows what's needed. Say what would settle it.

Keep it to what's worth acting on, without listing every nit. If a finding might be intentional, ask rather than assume. For example, unused code may be unfinished intent, so ask whether to finish or remove it.

## After the user chooses

Make only the chosen changes, on a new branch. Probe uncertain behavior before documenting it, and meet the project's definition of done. Call out anything that breaks callers, especially changes that fail silently. When a decision sets a new rule, propose the smallest change to the project's instructions, tightening an existing line where possible, so the next review can check for it. Stop for review before committing.
