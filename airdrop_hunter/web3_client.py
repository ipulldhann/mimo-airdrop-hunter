"""Web3 client for on-chain queries."""

from __future__ import annotations

import logging
from typing import Optional

from web3 import Web3
from web3.exceptions import ContractLogicError

from .chains import ChainConfig

logger = logging.getLogger(__name__)

# Minimal ERC20 ABI for balance checks
ERC20_ABI = [
    {
        "constant": True,
        "inputs": [{"name": "_owner", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "balance", "type": "uint256"}],
        "type": "function",
    },
    {
        "constant": True,
        "inputs": [],
        "name": "decimals",
        "outputs": [{"name": "", "type": "uint8"}],
        "type": "function",
    },
    {
        "constant": True,
        "inputs": [],
        "name": "symbol",
        "outputs": [{"name": "", "type": "string"}],
        "type": "function",
    },
]

# Minimal ERC20 balance/transfer event for activity detection
TRANSFER_TOPIC = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"


class Web3Client:
    """Web3 client for querying blockchain state."""

    def __init__(self, chain_config: ChainConfig):
        self.chain = chain_config
        self.w3 = Web3(Web3.HTTPProvider(
            chain_config.rpc_url,
            request_kwargs={"timeout": 30},
        ))
        self._connected: Optional[bool] = None

    @property
    def is_connected(self) -> bool:
        """Check if connected to the RPC endpoint."""
        if self._connected is None:
            try:
                self._connected = self.w3.is_connected()
            except Exception:
                self._connected = False
        return self._connected

    def get_eth_balance(self, address: str) -> float:
        """Get native token balance for an address."""
        try:
            checksum = Web3.to_checksum_address(address)
            balance_wei = self.w3.eth.get_balance(checksum)
            return float(self.w3.from_wei(balance_wei, "ether"))
        except Exception as e:
            logger.warning("Failed to get ETH balance for %s: %s", address, e)
            return 0.0

    def get_token_balance(self, token_address: str, wallet_address: str) -> float:
        """Get ERC20 token balance."""
        try:
            contract = self.w3.eth.contract(
                address=Web3.to_checksum_address(token_address),
                abi=ERC20_ABI,
            )
            balance = contract.functions.balanceOf(
                Web3.to_checksum_address(wallet_address)
            ).call()
            decimals = contract.functions.decimals().call()
            return balance / (10 ** decimals)
        except Exception as e:
            logger.debug("Token balance check failed for %s: %s", token_address, e)
            return 0.0

    def has_transfer_activity(self, address: str, contract_address: str,
                              from_block: int = 0, to_block: int = -1) -> int:
        """Check if address has transfer events involving a contract."""
        try:
            checksum = Web3.to_checksum_address(address)
            if to_block == -1:
                to_block = self.w3.eth.block_number

            # Check as sender
            from_filter = {
                "fromBlock": from_block,
                "toBlock": to_block,
                "address": Web3.to_checksum_address(contract_address),
                "topics": [TRANSFER_TOPIC, Web3.to_bytes(hexstr=checksum).hex()],
            }
            from_logs = self.w3.eth.get_logs(from_filter)

            # Check as receiver
            to_filter = {
                "fromBlock": from_block,
                "toBlock": to_block,
                "address": Web3.to_checksum_address(contract_address),
                "topics": [TRANSFER_TOPIC, None, Web3.to_bytes(hexstr=checksum).hex()],
            }
            to_logs = self.w3.eth.get_logs(to_filter)

            return len(from_logs) + len(to_logs)

        except Exception as e:
            logger.debug("Activity check failed for %s on %s: %s",
                         address, contract_address, e)
            return 0

    def get_transaction_count(self, address: str) -> int:
        """Get total transaction count for an address."""
        try:
            checksum = Web3.to_checksum_address(address)
            return self.w3.eth.get_transaction_count(checksum)
        except Exception as e:
            logger.warning("Failed to get tx count for %s: %s", address, e)
            return 0

    def get_block_number(self) -> int:
        """Get current block number."""
        return self.w3.eth.block_number

    def resolve_ens(self, name: str) -> Optional[str]:
        """Resolve an ENS name to an address (Ethereum mainnet only)."""
        if self.chain.chain_id != 1:
            return None
        try:
            address = self.w3.ens.address(name)
            return address
        except Exception:
            return None

    def validate_address(self, address: str) -> bool:
        """Check if an address is valid."""
        try:
            Web3.to_checksum_address(address)
            return True
        except Exception:
            return False
