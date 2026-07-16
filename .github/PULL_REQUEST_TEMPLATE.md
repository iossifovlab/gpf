## Background

Provide enough information for people to have context for your changes.
What problems the code is solving now, why have we picked this solution historically, etc.

## Aim

Provide a short summary of the changes. Try to include answers to the **Why?** questions,
e.g. **Why are we introducing this change?**, **Why now?**, etc.

If your changes make UI changes, consider providing before and after screenshots.
You can also include a video demonstrating the old vs. the new UX.

## Implementation

Explain why things are done the way they are in this PR.
Highlight the most important and/or controversial design decisions you have taken.
**Why it's implemented the way it is? What alternative implementations have you
considered and why you chose this one?**

The description is a good place to include questions that came up during development like
**Is this name the best one?**, *Could approach B be more applicable in this case?*, etc.

This is also a good place to talk about performance and security considerations if any.

## Related issues

Link issues which concern/are resolved by this PR.

If this PR resolves an issue **in this repository**, write `Closes #NNN` here —
GitHub then closes the issue automatically when the PR merges. Without it the
issue stays open after the work has landed, and the tracker starts lying about
what's left to do.

Auto-closing is **same-repo only**. For an issue in another repository
(`iossifovlab/gain`, `seqpipe/infra`, ...) reference it as
`iossifovlab/gain#NNN` — that creates a backlink but does **not** close it.
Close those by hand once this merges.
