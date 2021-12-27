pragma solidity ^0.6.6;

import "./aave/FlashLoanReceiverBaseV2.sol";
import "../../interfaces/v2/ILendingPoolAddressesProviderV2.sol";
import "../../interfaces/v2/ILendingPoolV2.sol";
import "../../interfaces/IUniswapRouterV2.sol";
import "../utils/Withdrawable.sol";

contract FlashloanV2 is FlashLoanReceiverBaseV2, Withdrawable {
    address public constant ROUTERquickswap =
        0xa5E0829CaCEd8fFDD4De3c43696c57F7D7A678ff;
    address public constant ROUTERsushiswap =
        0x1b02dA8Cb0d097eB8D57A175b88c7D8b47997506;
    address public constant LENDING_POOL_ADDRESS =
        0x8dFf5E27EA6b7AC08EbFdf9eB090F32ee9a30fcf;
    address public fromToken;
    uint256 public fromTokenInd;
    address public toToken;
    uint256 public toTokenInd;
    uint256 public owed;
    uint256 public bal;
    bool public tokensSet = false;

    constructor(address _addressProvider)
        public
        FlashLoanReceiverBaseV2(_addressProvider)
    {}

    function executeOperation(
        address[] calldata assets,
        uint256[] calldata amounts,
        uint256[] calldata premiums,
        address initiator,
        bytes calldata params
    ) external override returns (bool) {
        require(tokensSet, "Tokens not set");
        owed = amounts[0].add(premiums[0]);

        swap_sushiswap(IERC20(fromToken).balanceOf(address(this)));
        swap_quickswap(IERC20(toToken).balanceOf(address(this)));

        bal = IERC20(assets[0]).balanceOf(address(this));
        require(bal > owed, "Did not make profit");

        // Approve the LendingPool contract allowance to *pull* the owed amount
        for (uint256 i = 0; i < assets.length; i++) {
            uint256 amountOwing = amounts[i].add(premiums[i]);
            IERC20(assets[i]).approve(address(LENDING_POOL), amountOwing);
        }

        return true;
    }

    function swap_quickswap(uint256 amount) public {
        address[] memory path;
        path = new address[](2);
        path[0] = toToken;
        // path[1] = WMATIC;
        path[1] = fromToken;
        IUniswapRouterV2(ROUTERquickswap).swapExactTokensForTokens(
            amount,
            1,
            path,
            address(this),
            block.timestamp + 99999999
        );
    }

    function swap_sushiswap(uint256 amount) public {
        address[] memory path;
        path = new address[](2);
        path[0] = toToken;
        // path[1] = WMATIC;
        path[1] = fromToken;
        IUniswapRouterV2(ROUTERsushiswap).swapExactTokensForTokens(
            amount,
            1,
            path,
            address(this),
            block.timestamp + 99999999
        );
    }

    function _flashloan(address[] memory assets, uint256[] memory amounts)
        internal
    {
        address receiverAddress = address(this);

        address onBehalfOf = address(this);
        bytes memory params = "";
        uint16 referralCode = 0;

        uint256[] memory modes = new uint256[](assets.length);

        // 0 = no debt (flash), 1 = stable, 2 = variable
        for (uint256 i = 0; i < assets.length; i++) {
            modes[i] = 0;
        }

        LENDING_POOL.flashLoan(
            receiverAddress,
            assets,
            amounts,
            modes,
            onBehalfOf,
            params,
            referralCode
        );
    }

    function flashloan(uint256 _amount) public onlyOwner {
        bytes memory data = "";
        uint256 amount = _amount;

        address[] memory assets = new address[](1);
        assets[0] = fromToken;

        uint256[] memory amounts = new uint256[](1);
        amounts[0] = amount;

        _flashloan(assets, amounts);
    }

    function setTokens(
        address from,
        uint256 fromInd,
        address to,
        uint256 toInd
    ) public onlyOwner {
        fromToken = from;
        fromTokenInd = fromInd;
        toToken = to;
        toTokenInd = toInd;
        tokensSet = true;
        IERC20(toToken).approve(ROUTERquickswap, type(uint256).max);
        IERC20(toToken).approve(ROUTERsushiswap, type(uint256).max);
        IERC20(fromToken).approve(ROUTERquickswap, type(uint256).max);
        IERC20(fromToken).approve(ROUTERquickswap, type(uint256).max);
    }

    function getProfit(address _asset) public onlyOwner {
        IERC20(fromToken).transfer(
            msg.sender,
            IERC20(fromToken).balanceOf(address(this))
        );
        withdraw(_asset);
    }
}
