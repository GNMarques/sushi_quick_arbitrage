from brownie import interface
from web3 import Web3
import brownie


def test_flashloan(acct, flashloan_v2, set_tokens):

    amount_to_loan = Web3.toWei(1, 'ether')

    with brownie.reverts("Did not make profit"):
        flashloan_v2.flashloan(amount_to_loan, {"from": acct})
