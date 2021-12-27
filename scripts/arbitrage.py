from brownie import FlashloanV2, interface, accounts, network, config, Contract
import random

LENDING_POOL = "0x8dFf5E27EA6b7AC08EbFdf9eB090F32ee9a30fcf"
SUSHI_ROUTER = "0x1b02dA8Cb0d097eB8D57A175b88c7D8b47997506"
UNI_ROUTER = "0xa5E0829CaCEd8fFDD4De3c43696c57F7D7A678ff"
SUSHI_SWAP = interface.IUniswapRouterV2(SUSHI_ROUTER)
UNI_SWAP = interface.IUniswapRouterV2(UNI_ROUTER)
ACCOUNT = accounts[8]
AMOUNT_BORROW = 1000


def main():
    if 'fork' not in network.show_active():
        account = connect_fork()
        flashloan = FlashloanV2.deploy(
            LENDING_POOL,
            {"from": account}
        )

    flashloan_addr = input("Contract address: ")

    approve_all()
    token_swap = ['dai']
    token_names = ['weth', 'link', 'uniswap']

    all_token_pairs = [(a, b) for idx, a in enumerate(token_swap)
                       for b in token_names[idx + 1:]]

    for pair in all_token_pairs:
        profitable, from_token, to_token, amount = test_arb(*pair)

        if profitable:
            account = connect_mainnet()
            flashloan = Contract(flashloan_addr)
            flashloan.setTokens(
                from_token,
                sushi_tokens[from_token],
                to_token,
                sushi_tokens[to_token],
                {'from': account}
            )
            flashloan.flashloan(amount, {"from": account})
            flashloan.getProfit(from_token, {'from': account})
            account = connect_fork()


def test_arb(from_token, to_token):
    from_address = tokens[from_token]
    to_address = tokens[to_token]
    from_index = sushi_tokens[from_token]
    to_index = sushi_tokens[to_token]

    decimals = int(ERC20(from_address).decimals())

    if from_token in ['dai']:
        amount = AMOUNT_BORROW * 10**decimals
    else:
        return None

    swap_eth_for_erc20(from_address, amount * 1.1, ACCOUNT)

    # ARBITRAGE
    starting_from = balanceOf(from_address, ACCOUNT.address)
    print(f"Starting balance of {from_token}: {starting_from}")
    SUSHI_SWAP.swapExactTokensForTokens(balanceOf(from_address, ACCOUNT.address), 1, [
                                        from_address, to_address], ACCOUNT.address, 9999999999999999, {'from': ACCOUNT})
    UNI_SWAP.swapExactTokensForTokens(balanceOf(to_address, ACCOUNT.address), 1, [
        to_address, from_address], ACCOUNT.address, 9999999999999999, {'from': ACCOUNT})
    ending_from = balanceOf(from_address, ACCOUNT.address)
    profit = ending_from - starting_from
    print(f"PAIR: ({from_token}, {to_token})\nARBITRAGE PROFIT: {profit} wei")
    if profit > 0:
        return (True, from_address, to_address, amount)
    return (False, from_address, to_address, amount)


def connect_mainnet():
    network.diconect()
    print("Connecting...")
    network.connect('polygon-main')
    return accounts.add(config["wallets"]["from_key"])


def connect_fork():
    network.disconnect()
    network.connect('polygon-main-fork')
    return accounts[0]


def swap_eth_for_erc20(erc20_address, amount_out, account):
    router = interface.IUniswapRouterV2(
        "0xa5E0829CaCEd8fFDD4De3c43696c57F7D7A678ff")
    router.swapETHForExactTokens(amount_out, [tokens['wmatic'], erc20_address], account.address, 9999999999999999, {
        "from": account, "value": 10000 * 10**18})


def approve_all():
    for token in [tokens[token] for token in tokens.keys() if token != 'wmatic']:
        ERC20(token).approve(SUSHI_ROUTER,
                             1_000_000_000_000 * 10**18, {"from": ACCOUNT})
        ERC20(token).approve(UNI_ROUTER,
                             1_000_000_000_000 * 10**18, {"from": ACCOUNT})


def balanceOf(erc20_address, account_address):
    return ERC20(erc20_address).balanceOf(account_address)


def ERC20(token_address):
    return interface.IERC20(token_address)


tokens = {
    'wmatic': "0x0d500B1d8E8eF31E21C99d1Db9A6444d3ADf1270",
    'dai': "0x8f3Cf7ad23Cd3CaDbD9735AFf958023239c6A063",
    'usdc': "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174",
    'usdt': "0xc2132D05D31c914a87C6611C10748AEb04B58e8F",
    'weth': "0x7ceB23fD6bC0adD59E62ac25578270cFf1b9f619",
    'wbtc': "0x1BFD67037B42Cf73acF2047067bd4F2C47D9BfD6",
    'link': "0x53e0bca35ec356bd5dddfebbd1fc0fd03fabad39",
    'uniswap': "0xb33eaad8d922b1083446dc23f610c2567fb5180f",
    'mana': "0xa1c57f48f0deb89f569dfbe6e2b7f46d33606fd4",
    'theta': "0xb46e0ae620efd98516f49bb00263317096c114b2",
    'ftm': "0xc9c1c1c20b3658f8787cc2fd702267791f224ce1",
    'grt': "0x5fe2b58c013d7601147dcdd68c143a77499f5531",

}

sushi_tokens = {
    'dai': 0,
    'weth': 1,
    'link': 2,
    'uniswap': 3,
    'mana': 4
}
