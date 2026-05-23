"""Main airdrop scanning orchestrator."""

from __future__ import annotations

import logging
from typing import Optional

from .chains import ChainConfig, get_chain, get_all_chains
from .protocols import (
    AirdropInfo, ProtocolCategory, get_protocols_for_chain, get_all_protocols,
)
from .web3_client import Web3Client
from .storage import AirdropStorage

logger = logging.getLogger(__name__)


class AirdropScanner:
    """Orchestrates wallet scanning across multiple protocols and chains."""

    def __init__(self, storage: Optional[AirdropStorage] = None):
        self.storage = storage or AirdropStorage()
        self._clients: dict[str, Web3Client] = {}

    def _get_client(self, chain_config: ChainConfig) -> Web3Client:
        """Get or create a Web3 client for a chain."""
        key = chain_config.name
        if key not in self._clients:
            self._clients[key] = Web3Client(chain_config)
        return self._clients[key]

    def _check_protocol_eligibility(self, wallet: str, protocol: dict,
                                     client: Web3Client) -> AirdropInfo:
        """Check eligibility for a specific protocol.
        
        In production, this would call specific on-chain view functions.
        This implementation uses heuristic checks based on activity.
        """
        info = AirdropInfo(
            protocol=protocol["protocol"],
            category=protocol["category"],
            token=protocol["token"],
            chain=client.chain.name.lower(),
        )

        try:
            # Generic activity-based eligibility check
            # Check ETH balance as proxy for on-chain activity
            eth_balance = client.get_eth_balance(wallet)
            tx_count = client.get_transaction_count(wallet)

            # Heuristic eligibility based on activity level
            # Real implementations would check specific contract states
            if protocol["protocol"] == "Arbitrum" and client.chain.chain_id == 42161:
                eligible = tx_count > 10
                info.eligible = eligible
                info.estimated_amount = tx_count * 1.5 if eligible else 0
                info.claim_url = "https://arbitrum.foundation"
                info.details = f"Tx count: {tx_count}"

            elif protocol["protocol"] == "Optimism" and client.chain.chain_id == 10:
                eligible = tx_count > 5
                info.eligible = eligible
                info.estimated_amount = tx_count * 2.0 if eligible else 0
                info.claim_url = "https://app.optimism.io/airdrop"
                info.details = f"Tx count: {tx_count}"

            elif protocol["protocol"] == "ENS" and client.chain.chain_id == 1:
                # Would check ENS registry for owned names
                eligible = eth_balance > 0.1 and tx_count > 20
                info.eligible = eligible
                info.estimated_amount = 100 if eligible else 0
                info.claim_url = "https://claim.ens.domains"
                info.details = f"ETH balance: {eth_balance:.4f}, Tx count: {tx_count}"

            elif protocol["protocol"] == "EigenLayer" and client.chain.chain_id == 1:
                # Would check restaking contracts
                eligible = eth_balance > 1.0
                info.eligible = eligible
                info.estimated_amount = eth_balance * 10 if eligible else 0
                info.claim_url = "https://eigenfoundation.org/claim"
                info.details = f"ETH balance: {eth_balance:.4f}"

            else:
                # Generic check: active wallet with reasonable balance
                eligible = tx_count > 15 and eth_balance > 0.05
                info.eligible = eligible
                info.estimated_amount = round(eth_balance * 5, 2) if eligible else 0
                info.details = f"Activity: {tx_count} txs, {eth_balance:.4f} ETH"

            if info.eligible:
                info.requirements = protocol.get("requirements", [])

        except Exception as e:
            logger.warning("Error checking %s for %s: %s",
                           protocol["protocol"], wallet, e)
            info.details = f"Error: {e}"

        return info

    def scan_wallet(self, wallet: str, chain_name: str) -> list[AirdropInfo]:
        """Scan a wallet for airdrop eligibility on a specific chain."""
        chain = get_chain(chain_name)
        client = self._get_client(chain)

        if not client.is_connected:
            logger.error("Cannot connect to %s RPC", chain.name)
            return []

        protocols = get_protocols_for_chain(chain_name)
        logger.info("Scanning %d protocols on %s for %s",
                     len(protocols), chain.name, wallet)

        results = []
        for protocol in protocols:
            info = self._check_protocol_eligibility(wallet, protocol, client)
            results.append(info)

        # Save results
        self.storage.save_scan_results(wallet, results)
        eligible_count = sum(1 for r in results if r.eligible)
        self.storage.log_scan(wallet, chain_name, len(results), eligible_count)

        logger.info("Scan complete: %d/%d eligible", eligible_count, len(results))
        return results

    def scan_all_chains(self, wallet: str) -> list[AirdropInfo]:
        """Scan a wallet across all supported chains."""
        all_results = []
        for chain in get_all_chains():
            try:
                results = self.scan_wallet(wallet, chain.name.lower())
                all_results.extend(results)
            except Exception as e:
                logger.error("Failed to scan %s: %s", chain.name, e)
        return all_results

    def format_results(self, wallet: str, chain: str,
                       results: list[AirdropInfo]) -> str:
        """Format scan results as a readable report."""
        eligible = [r for r in results if r.eligible]
        not_eligible = [r for r in results if not r.eligible]

        lines = [
            f"═══ Airdrop Scan Results ═══",
            f"Wallet: {wallet}",
            f"Chain: {chain}",
            f"Protocols Scanned: {len(results)}",
            f"Eligible: {len(eligible)} | Not Eligible: {len(not_eligible)}",
            "",
        ]

        if eligible:
            lines.append("── ✅ Eligible Airdrops ──")
            for r in sorted(eligible, key=lambda x: x.estimated_amount, reverse=True):
                lines.extend([
                    f"  🎁 {r.protocol} ({r.token})",
                    f"     Estimated: ~{r.estimated_amount:.2f} {r.token}",
                    f"     Claim: {r.claim_url or 'TBD'}",
                    f"     {r.details}",
                    "",
                ])
        else:
            lines.append("  No eligible airdrops found on this chain.")
            lines.append("")

        lines.append("── ℹ️  Protocols Checked (Not Eligible) ──")
        for r in not_eligible[:10]:
            lines.append(f"  ✗ {r.protocol} — {r.details or 'No activity detected'}")

        return "\n".join(lines)

    def close(self) -> None:
        """Clean up resources."""
        for client in self._clients.values():
            pass  # Web3 clients don't need explicit close
        self.storage.close()
