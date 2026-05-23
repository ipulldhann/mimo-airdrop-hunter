"""CLI entrypoint for Airdrop Hunter."""

from __future__ import annotations

import sys

import click
from rich.console import Console
from rich.table import Table

from .chains import list_chain_names
from .scanner import AirdropScanner
from .storage import AirdropStorage
from .strategist import ClaimStrategist

console = Console()


@click.command()
@click.option("--wallet", "-w", required=True, help="Wallet address to scan (0x...).")
@click.option("--chain", "-c", default="ethereum",
              help="Chain to scan (ethereum/arbitrum/optimism/base/polygon/all).")
@click.option("--strategy", "-s", is_flag=True, help="Generate AI claim strategy.")
@click.option("--history", is_flag=True, help="Show claim history.")
@click.option("--db", default="airdrop_hunter.db", help="SQLite database path.")
@click.option("--verbose", "-v", is_flag=True, help="Enable debug logging.")
def cli(wallet: str, chain: str, strategy: bool, history: bool, db: str, verbose: bool):
    """MiMo Airdrop Hunter — Web3 airdrop eligibility scanner."""
    import logging
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Validate wallet address
    if not wallet.startswith("0x") or len(wallet) != 42:
        console.print("[red]Error: Invalid wallet address. Must be 0x + 40 hex chars.[/red]")
        sys.exit(1)

    storage = AirdropStorage(db)

    # Show history mode
    if history:
        _show_history(storage, wallet)
        return

    scanner = AirdropScanner(storage)

    console.print(f"[bold blue]🔍 Scanning wallet {wallet[:10]}...{wallet[-6:]}[/bold blue]")

    try:
        if chain.lower() == "all":
            console.print("[dim]Scanning all supported chains...[/dim]")
            results = scanner.scan_all_chains(wallet)
        else:
            results = scanner.scan_wallet(wallet, chain.lower())

        # Display results
        console.print()
        console.print(scanner.format_results(wallet, chain, results))

        # AI Strategy analysis
        if strategy:
            eligible = [r for r in results if r.eligible]
            if eligible:
                console.print("\n[bold yellow]🤖 Generating AI claim strategy...[/bold yellow]")
                strategist = ClaimStrategist()
                strat = strategist.analyze_eligibility(wallet, chain, results)
                report = strategist.format_strategy_report(wallet, chain, strat)
                console.print(report)
                strategist.close()
            else:
                console.print("\n[dim]No eligible airdrops — skipping strategy.[/dim]")

    finally:
        scanner.close()


def _show_history(storage: AirdropStorage, wallet: str):
    """Display claim and scan history."""
    # Show scan history
    scans = storage.get_scan_history(wallet)
    if scans:
        table = Table(title="Scan History")
        table.add_column("Date", style="dim")
        table.add_column("Chain")
        table.add_column("Scanned", justify="right")
        table.add_column("Eligible", justify="right", style="green")

        for scan in scans:
            table.add_row(
                scan["scanned_at"],
                scan["chain"],
                str(scan["protocols_scanned"]),
                str(scan["eligible_found"]),
            )
        console.print(table)
    else:
        console.print("[dim]No scan history found.[/dim]")

    # Show eligible airdrops
    eligible = storage.get_eligible(wallet)
    if eligible:
        console.print()
        table = Table(title="Eligible Airdrops")
        table.add_column("Protocol")
        table.add_column("Token")
        table.add_column("Chain")
        table.add_column("Amount", justify="right")
        table.add_column("Claim URL")

        for e in eligible:
            table.add_row(
                e["protocol"], e["token"], e["chain"],
                f"{e['estimated_amount']:.2f}", e.get("claim_url", "N/A"),
            )
        console.print(table)

    # Show claims
    claims = storage.get_claims(wallet)
    if claims:
        console.print()
        table = Table(title="Claim History")
        table.add_column("Date", style="dim")
        table.add_column("Protocol")
        table.add_column("Token")
        table.add_column("Amount", justify="right")
        table.add_column("Status")

        for c in claims:
            status_color = "green" if c["status"] == "confirmed" else "yellow"
            table.add_row(
                c["claimed_at"], c["protocol"], c["token"],
                f"{c['amount']:.2f}", f"[{status_color}]{c['status']}[/{status_color}]",
            )
        console.print(table)


if __name__ == "__main__":
    cli()
