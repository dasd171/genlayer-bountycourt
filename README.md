# BountyCourt — open-source bounties judged by GenLayer validators

BountyCourt is an Intelligent Contract that turns GenLayer into a **neutral judge for open-source bounties**.
A maintainer posts a bounty with plain-language acceptance criteria; contributors submit a public evidence URL
(a merged PR, a live demo, an article); anyone can trigger adjudication. Every validator independently opens the
evidence page, an LLM checks it against the criteria, and the verdict only lands when validators agree.
The first accepted submission wins and its reward is credited to the contributor's on-chain reputation.

No trusted reviewer, no oracle committee — the subjective "is this work done?" question is settled by GenLayer's
Optimistic Democracy consensus.

## Live on GenLayer Studionet

| Item | Value |
|---|---|
| Contract | `0xEde691f394E128817b245bDDfC623fE4877a1826` |
| Deploy tx | `0xc3e28da7404d59d7b94cb354c6a9e4bf9475a8b822af87a253dbb5733d16cbc9` |
| `create_bounty` tx | `0x5dff5d08e99794ffdb9541623b2c35a85955bc4bf61a83da7739b1de28bd2134` |
| `submit_work` tx | `0xde2c0fbb4b41522be73bee4e5112f3651f60847447a948a4cf8dca6036ba4485` |
| `adjudicate` tx | `0xc069f88570e3cadb67c57ab067b0170ee742bd4738725f20b89f48a21ff779b7` |

End-to-end run with **real web evidence** (`scripts/e2e_studionet.py`): bounty #0 asked for a merged PR that makes
`resolve_bet` validate the winner range; the contributor submitted
[genlayerlabs/genlayer-project-boilerplate#69](https://github.com/genlayerlabs/genlayer-project-boilerplate/pull/69).
Validators reached consensus on `meets_criteria`, the bounty moved to `awarded`, and the contributor's reputation
became `150`.

## How it works

```
maintainer ── create_bounty(title, criteria, reward) ──► Bounty #n (open)
contributor ─ submit_work(n, https://evidence, note) ──► Submission (pending)
anyone ────── adjudicate(n, i) ──► each validator: web.render(evidence) → LLM verdict
                                   strict_eq on {accepted, reason_code}
                                   ├─ meets_criteria → bounty awarded, reputation += reward
                                   └─ otherwise      → submission rejected, bounty stays open
maintainer ── cancel_bounty(n)   (only while open)
```

### Consensus-friendly verdicts
Free-form LLM text never reaches consensus. The non-deterministic block reduces every verdict to a
**fixed vocabulary** — `{accepted: bool, reason_code}` with `reason_code ∈ {meets_criteria, incomplete, off_topic,
unverifiable, spam_or_injection}` — and `accepted` is *derived* from the code, never trusted from the model.
That makes `gl.eq_principle.strict_eq` safe: honest validators converge on the same tiny output even when their
models phrase things differently. Any off-vocabulary answer is normalised to `unverifiable`, so a confused model can
never award a bounty.

### Safety
- **Prompt-injection guard**: evidence and contributor notes are fenced as untrusted data; the model is told to ignore
  instructions inside them and to flag manipulation as `spam_or_injection` (covered by a test).
- **Anti-spam**: one submission per address per bounty, https-only evidence, size limits on every string,
  max 25 submissions per bounty, maintainer cannot submit to their own bounty.
- **Finality**: a submission can be judged once; an awarded or cancelled bounty accepts nothing else.
- Unreachable/empty evidence resolves deterministically to `unverifiable` instead of reverting.

## Contract API

| Method | Type | Description |
|---|---|---|
| `create_bounty(title, criteria, reward) -> int` | write | Open a bounty (reward 1–10000 reputation points) |
| `submit_work(bounty_id, evidence_url, note) -> int` | write | Submit evidence, returns submission index |
| `adjudicate(bounty_id, submission_index) -> str` | write | Validators judge the evidence, returns reason code |
| `cancel_bounty(bounty_id)` | write | Maintainer closes an open bounty |
| `get_bounty(bounty_id) -> dict` | view | Bounty with all submissions |
| `list_bounties(status) -> list` | view | Filter by `open` / `awarded` / `cancelled`, `""` for all |
| `get_bounty_count() -> int` | view | Number of bounties |
| `get_reputation(address) -> int` | view | Reputation of an address |
| `get_leaderboard() -> dict` | view | All addresses with reputation |

## Run it

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

genvm-lint check contracts/bounty_court.py   # static checks
python -m pytest tests/direct -v             # 18 direct-mode tests, web + LLM mocked

# deploy (pick studionet / testnet with `genlayer network`), then:
python scripts/e2e_studionet.py <contract_address>
```

Direct-mode tests cover creation and validation, submission rules, accepted / rejected / normalised /
injection verdicts, re-judging, closing after award, cancellation permissions and all views.

## Ideas for next steps
- Escrow real GEN rewards with a payable `create_bounty` and pay out on acceptance.
- Multi-evidence submissions (PR + deployed demo) and per-criterion verdicts.
- A GitHub Action that opens a bounty from an issue label and calls `adjudicate` when a PR is merged.

## License
MIT
