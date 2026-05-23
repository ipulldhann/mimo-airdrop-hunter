# MiMo Airdrop Hunter 🎯

Web3 airdrop eligibility scanner powered by MiMo AI.

## Features

- **Multi-Protocol Scanning** — Check wallet eligibility across 50+ DeFi protocols
- **MiMo AI Analysis** — AI-powered claim strategy recommendations
- **On-Chain Queries** — Direct blockchain interaction via Web3.py
- **Claim Tracking** — SQLite database to track claimed/unclaimed airdrops
- **Multi-Chain Support** — Ethereum, Base, Arbitrum, Optimism, Polygon
- **CLI Interface** — Simple command-line tool for quick scans

## Installation

```bash
pip install -e .
# or
pip install -r requirements.txt
```

## Usage

```bash
# Scan wallet on Ethereum
python -m airdrop_hunter --wallet 0x1234...abcd --chain ethereum

# Scan all supported chains
python -m airdrop_hunter --wallet 0x1234...abcd --chain all

# Get AI claim strategy
python -m airdrop_hunter --wallet 0x1234...abcd --chain ethereum --strategy

# View claim history
python -m airdrop_hunter --wallet 0x1234...abcd --history
```

## Supported Protocols

| Category | Protocols |
|----------|-----------|
| DEX | Uniswap, SushiSwap, Curve, Balancer, 1inch |
| Lending | Aave, Compound, Morpho, Spark |
| Bridges | Stargate, Hop, Across, Synapse |
| Derivatives | GMX, dYdX, Kwenta, Lyra |
| Infrastructure | ENS, Gitcoin, Optimism, Arbitrum |
| And 30+ more... | |

## Architecture

```
airdrop_hunter/
├── __main__.py      # CLI entrypoint
├── scanner.py       # Main scanning orchestrator
├── protocols.py     # Protocol definitions & eligibility checks
├── web3_client.py   # Web3.py blockchain interaction
├── strategist.py    # MiMo AI claim strategy analysis
├── storage.py       # SQLite claim tracking
└── chains.py        # Chain configuration & RPC endpoints
```

## Environment Variables

| Variable | Description |
|----------|-------------|
| `ETH_RPC_URL` | Custom Ethereum RPC endpoint |
| `ARB_RPC_URL` | Custom Arbitrum RPC endpoint |
| `OPT_RPC_URL` | Custom Optimism RPC endpoint |
| `BASE_RPC_URL` | Custom Base RPC endpoint |

## License

MIT
