"""End-to-end run of BountyCourt on GenLayer Studionet with real web evidence.

Usage:
    python scripts/e2e_studionet.py <contract_address>

Creates a bounty as a maintainer account, submits a real merged GitHub PR as a
contributor account, and asks validators to adjudicate it. Prints every
transaction hash and the final on-chain state.
"""

import json
import sys

from genlayer_py import create_account, create_client
from genlayer_py.chains import studionet
from genlayer_py.types import TransactionStatus

ADDRESS = sys.argv[1]

CRITERIA = (
    "A merged pull request in genlayerlabs/genlayer-project-boilerplate that "
    "makes resolve_bet in the football bets contract validate that the winner "
    "value returned for a match is within the allowed range."
)
EVIDENCE = "https://github.com/genlayerlabs/genlayer-project-boilerplate/pull/69"

maintainer = create_account()
contributor = create_account()


def send(acct, method, args):
    client = create_client(chain=studionet, account=acct)
    tx = client.write_contract(address=ADDRESS, function_name=method, args=args)
    receipt = client.wait_for_transaction_receipt(
        transaction_hash=tx, status=TransactionStatus.ACCEPTED, interval=5000, retries=60
    )
    print(f"{method}: tx={tx} status={receipt['status_name']}")
    return tx


def read(method, args):
    client = create_client(chain=studionet, account=maintainer)
    return client.read_contract(address=ADDRESS, function_name=method, args=args)


bounty_id = read("get_bounty_count", [])
send(maintainer, "create_bounty", ["Validate winner range in resolve_bet", CRITERIA, 150])
send(contributor, "submit_work", [bounty_id, EVIDENCE, "PR #69 adds the range check"])
send(contributor, "adjudicate", [bounty_id, 0])

print(json.dumps(read("get_bounty", [bounty_id]), indent=2, default=str))
print("reputation:", read("get_reputation", [contributor.address]))
