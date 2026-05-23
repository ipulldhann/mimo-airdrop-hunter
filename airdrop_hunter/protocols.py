"""Protocol definitions and eligibility checking logic."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

logger = logging.getLogger(__name__)


class ProtocolCategory(str, Enum):
    DEX = "dex"
    LENDING = "lending"
    BRIDGE = "bridge"
    DERIVATIVES = "derivatives"
    INFRASTRUCTURE = "infrastructure"
    NFT = "nft"
    YIELD = "yield"
    GOVERNANCE = "governance"


@dataclass
class AirdropInfo:
    protocol: str
    category: ProtocolCategory
    token: str
    chain: str
    contract_address: str = ""
    eligible: bool = False
    estimated_amount: float = 0.0
    claim_deadline: Optional[str] = None
    claim_url: str = ""
    requirements: list[str] = field(default_factory=list)
    details: str = ""


# Protocol registry — each entry defines a protocol's airdrop check
PROTOCOL_REGISTRY: list[dict] = [
    # DEX Protocols
    {
        "protocol": "Uniswap",
        "category": ProtocolCategory.DEX,
        "token": "UNI",
        "chains": ["ethereum", "arbitrum", "optimism", "base", "polygon"],
        "checker": "check_uniswap",
        "requirements": ["Swapped on Uniswap before Sep 2020", "Provided liquidity"],
    },
    {
        "protocol": "SushiSwap",
        "category": ProtocolCategory.DEX,
        "token": "SUSHI",
        "chains": ["ethereum", "arbitrum", "polygon"],
        "checker": "check_sushiswap",
        "requirements": ["Swapped or staked on SushiSwap"],
    },
    {
        "protocol": "1inch",
        "category": ProtocolCategory.DEX,
        "token": "1INCH",
        "chains": ["ethereum"],
        "checker": "check_1inch",
        "requirements": ["Used 1inch aggregator before Dec 2020"],
    },
    {
        "protocol": "Curve",
        "category": ProtocolCategory.DEX,
        "token": "CRV",
        "chains": ["ethereum", "arbitrum", "optimism", "polygon"],
        "checker": "check_curve",
        "requirements": ["Provided liquidity on Curve"],
    },
    {
        "protocol": "Balancer",
        "category": ProtocolCategory.DEX,
        "token": "BAL",
        "chains": ["ethereum", "arbitrum", "polygon"],
        "checker": "check_balancer",
        "requirements": ["Provided liquidity on Balancer"],
    },
    # Lending Protocols
    {
        "protocol": "Aave",
        "category": ProtocolCategory.LENDING,
        "token": "AAVE",
        "chains": ["ethereum", "arbitrum", "optimism", "polygon", "base"],
        "checker": "check_aave",
        "requirements": ["Supplied or borrowed on Aave"],
    },
    {
        "protocol": "Compound",
        "category": ProtocolCategory.LENDING,
        "token": "COMP",
        "chains": ["ethereum", "arbitrum", "base"],
        "checker": "check_compound",
        "requirements": ["Supplied or borrowed on Compound"],
    },
    {
        "protocol": "Morpho",
        "category": ProtocolCategory.LENDING,
        "token": "MORPHO",
        "chains": ["ethereum", "base"],
        "checker": "check_morpho",
        "requirements": ["Used Morpho for lending/borrowing"],
    },
    # Bridge Protocols
    {
        "protocol": "Stargate",
        "category": ProtocolCategory.BRIDGE,
        "token": "STG",
        "chains": ["ethereum", "arbitrum", "optimism", "polygon"],
        "checker": "check_stargate",
        "requirements": ["Bridged assets via Stargate"],
    },
    {
        "protocol": "Hop Protocol",
        "category": ProtocolCategory.BRIDGE,
        "token": "HOP",
        "chains": ["ethereum", "arbitrum", "optimism", "polygon"],
        "checker": "check_hop",
        "requirements": ["Bridged via Hop Protocol"],
    },
    {
        "protocol": "Across",
        "category": ProtocolCategory.BRIDGE,
        "token": "ACX",
        "chains": ["ethereum", "arbitrum", "optimism", "base"],
        "checker": "check_across",
        "requirements": ["Bridged via Across"],
    },
    # Derivatives
    {
        "protocol": "GMX",
        "category": ProtocolCategory.DERIVATIVES,
        "token": "GMX",
        "chains": ["arbitrum"],
        "checker": "check_gmx",
        "requirements": ["Traded or staked on GMX"],
    },
    {
        "protocol": "dYdX",
        "category": ProtocolCategory.DERIVATIVES,
        "token": "DYDX",
        "chains": ["ethereum"],
        "checker": "check_dydx",
        "requirements": ["Traded on dYdX before launch"],
    },
    # Infrastructure
    {
        "protocol": "ENS",
        "category": ProtocolCategory.INFRASTRUCTURE,
        "token": "ENS",
        "chains": ["ethereum"],
        "checker": "check_ens",
        "requirements": ["Registered an ENS name"],
    },
    {
        "protocol": "Optimism",
        "category": ProtocolCategory.INFRASTRUCTURE,
        "token": "OP",
        "chains": ["optimism"],
        "checker": "check_optimism",
        "requirements": ["Used Optimism network", "Voted in governance"],
    },
    {
        "protocol": "Arbitrum",
        "category": ProtocolCategory.INFRASTRUCTURE,
        "token": "ARB",
        "chains": ["arbitrum"],
        "checker": "check_arbitrum",
        "requirements": ["Bridged to Arbitrum", "Used dApps on Arbitrum"],
    },
    {
        "protocol": "EigenLayer",
        "category": ProtocolCategory.INFRASTRUCTURE,
        "token": "EIGEN",
        "chains": ["ethereum"],
        "checker": "check_eigenlayer",
        "requirements": ["Restaked ETH on EigenLayer"],
    },
    # Yield
    {
        "protocol": "Yearn Finance",
        "category": ProtocolCategory.YIELD,
        "token": "YFI",
        "chains": ["ethereum", "arbitrum"],
        "checker": "check_yearn",
        "requirements": ["Deposited in Yearn vaults"],
    },
    {
        "protocol": "Convex Finance",
        "category": ProtocolCategory.YIELD,
        "token": "CVX",
        "chains": ["ethereum"],
        "checker": "check_convex",
        "requirements": ["Staked CRV on Convex"],
    },
    # Governance
    {
        "protocol": "Gitcoin",
        "category": ProtocolCategory.GOVERNANCE,
        "token": "GTC",
        "chains": ["ethereum"],
        "checker": "check_gitcoin",
        "requirements": ["Donated on Gitcoin Grants"],
    },
]


def get_protocols_for_chain(chain: str) -> list[dict]:
    """Get all protocols that have a presence on the given chain."""
    return [p for p in PROTOCOL_REGISTRY if chain in p["chains"]]


def get_all_protocols() -> list[dict]:
    """Get the full protocol registry."""
    return PROTOCOL_REGISTRY


def get_protocol_count() -> int:
    """Get total number of tracked protocols."""
    return len(PROTOCOL_REGISTRY)
