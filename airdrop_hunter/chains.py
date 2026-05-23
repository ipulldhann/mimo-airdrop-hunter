"""Chain configurations and RPC endpoints."""

from __future__ import annotations

import os
from dataclasses import dataclass, field


@dataclass
class ChainConfig:
    name: str
    chain_id: int
    rpc_url: str
    native_token: str = "ETH"
    explorer_url: str = ""
    multicall_address: str = ""


# Default public RPC endpoints (users can override via env vars)
CHAINS: dict[str, ChainConfig] = {
    "ethereum": ChainConfig(
        name="Ethereum",
        chain_id=1,
        rpc_url=os.getenv("ETH_RPC_URL", "https://eth.llamarpc.com"),
        native_token="ETH",
        explorer_url="https://etherscan.io",
        multicall_address="0xcA11bde05977b3631167028862bE2a173976CA11",
    ),
    "arbitrum": ChainConfig(
        name="Arbitrum One",
        chain_id=42161,
        rpc_url=os.getenv("ARB_RPC_URL", "https://arb1.arbitrum.io/rpc"),
        native_token="ETH",
        explorer_url="https://arbiscan.io",
        multicall_address="0xcA11bde05977b3631167028862bE2a173976CA11",
    ),
    "optimism": ChainConfig(
        name="Optimism",
        chain_id=10,
        rpc_url=os.getenv("OPT_RPC_URL", "https://mainnet.optimism.io"),
        native_token="ETH",
        explorer_url="https://optimistic.etherscan.io",
        multicall_address="0xcA11bde05977b3631167028862bE2a173976CA11",
    ),
    "base": ChainConfig(
        name="Base",
        chain_id=8453,
        rpc_url=os.getenv("BASE_RPC_URL", "https://mainnet.base.org"),
        native_token="ETH",
        explorer_url="https://basescan.org",
        multicall_address="0xcA11bde05977b3631167028862bE2a173976CA11",
    ),
    "polygon": ChainConfig(
        name="Polygon",
        chain_id=137,
        rpc_url=os.getenv("POLYGON_RPC_URL", "https://polygon-rpc.com"),
        native_token="POL",
        explorer_url="https://polygonscan.com",
        multicall_address="0xcA11bde05977b3631167028862bE2a173976CA11",
    ),
}


def get_chain(name: str) -> ChainConfig:
    """Get chain config by name. Raises ValueError if not found."""
    key = name.lower()
    if key not in CHAINS:
        available = ", ".join(CHAINS.keys())
        raise ValueError(f"Unknown chain '{name}'. Available: {available}")
    return CHAINS[key]


def get_all_chains() -> list[ChainConfig]:
    """Get all supported chain configs."""
    return list(CHAINS.values())


def list_chain_names() -> list[str]:
    """Get list of supported chain names."""
    return list(CHAINS.keys())
