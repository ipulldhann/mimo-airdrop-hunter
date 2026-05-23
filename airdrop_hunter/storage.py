"""SQLite storage for tracking airdrop claims and scan history."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

from .protocols import AirdropInfo, ProtocolCategory


class AirdropStorage:
    """SQLite-backed storage for airdrop scan results and claim tracking."""

    def __init__(self, db_path: str = "airdrop_hunter.db"):
        self.db_path = db_path
        self._conn: Optional[sqlite3.Connection] = None

    def _get_conn(self) -> sqlite3.Connection:
        if self._conn is None:
            self._conn = sqlite3.connect(self.db_path)
            self._conn.row_factory = sqlite3.Row
            self._conn.execute("PRAGMA journal_mode=WAL")
            self._init_tables()
        return self._conn

    def _init_tables(self) -> None:
        conn = self._get_conn()
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS scan_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                wallet TEXT NOT NULL,
                chain TEXT NOT NULL,
                protocol TEXT NOT NULL,
                category TEXT NOT NULL,
                token TEXT NOT NULL,
                eligible INTEGER NOT NULL DEFAULT 0,
                estimated_amount REAL DEFAULT 0,
                claim_url TEXT,
                claim_deadline TEXT,
                details TEXT,
                scanned_at TEXT NOT NULL DEFAULT (datetime('now')),
                UNIQUE(wallet, chain, protocol)
            );

            CREATE TABLE IF NOT EXISTS claims (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                wallet TEXT NOT NULL,
                chain TEXT NOT NULL,
                protocol TEXT NOT NULL,
                token TEXT NOT NULL,
                amount REAL DEFAULT 0,
                tx_hash TEXT,
                claimed_at TEXT NOT NULL DEFAULT (datetime('now')),
                status TEXT DEFAULT 'pending'
            );

            CREATE TABLE IF NOT EXISTS scan_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                wallet TEXT NOT NULL,
                chain TEXT NOT NULL,
                protocols_scanned INTEGER DEFAULT 0,
                eligible_found INTEGER DEFAULT 0,
                scanned_at TEXT NOT NULL DEFAULT (datetime('now'))
            );

            CREATE INDEX IF NOT EXISTS idx_scan_wallet
                ON scan_results(wallet);
            CREATE INDEX IF NOT EXISTS idx_claims_wallet
                ON claims(wallet);
        """)
        conn.commit()

    def save_scan_result(self, wallet: str, result: AirdropInfo) -> None:
        """Save a single scan result."""
        conn = self._get_conn()
        conn.execute(
            """INSERT OR REPLACE INTO scan_results
               (wallet, chain, protocol, category, token, eligible,
                estimated_amount, claim_url, claim_deadline, details)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (wallet, result.chain, result.protocol, result.category.value,
             result.token, int(result.eligible), result.estimated_amount,
             result.claim_url, result.claim_deadline, result.details),
        )
        conn.commit()

    def save_scan_results(self, wallet: str, results: list[AirdropInfo]) -> None:
        """Save multiple scan results."""
        for r in results:
            self.save_scan_result(wallet, r)

    def log_scan(self, wallet: str, chain: str, protocols_scanned: int,
                 eligible_found: int) -> None:
        """Log a scan attempt."""
        conn = self._get_conn()
        conn.execute(
            """INSERT INTO scan_history (wallet, chain, protocols_scanned, eligible_found)
               VALUES (?, ?, ?, ?)""",
            (wallet, chain, protocols_scanned, eligible_found),
        )
        conn.commit()

    def record_claim(self, wallet: str, chain: str, protocol: str,
                     token: str, amount: float, tx_hash: str = "") -> None:
        """Record a claim transaction."""
        conn = self._get_conn()
        conn.execute(
            """INSERT INTO claims (wallet, chain, protocol, token, amount, tx_hash)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (wallet, chain, protocol, token, amount, tx_hash),
        )
        conn.commit()

    def get_eligible(self, wallet: str, chain: str | None = None) -> list[dict]:
        """Get all eligible airdrops for a wallet."""
        conn = self._get_conn()
        if chain:
            rows = conn.execute(
                """SELECT * FROM scan_results
                   WHERE wallet = ? AND chain = ? AND eligible = 1
                   ORDER BY estimated_amount DESC""",
                (wallet, chain),
            ).fetchall()
        else:
            rows = conn.execute(
                """SELECT * FROM scan_results
                   WHERE wallet = ? AND eligible = 1
                   ORDER BY estimated_amount DESC""",
                (wallet,),
            ).fetchall()
        return [dict(r) for r in rows]

    def get_claims(self, wallet: str) -> list[dict]:
        """Get claim history for a wallet."""
        conn = self._get_conn()
        rows = conn.execute(
            "SELECT * FROM claims WHERE wallet = ? ORDER BY claimed_at DESC",
            (wallet,),
        ).fetchall()
        return [dict(r) for r in rows]

    def get_scan_history(self, wallet: str, limit: int = 10) -> list[dict]:
        """Get scan history for a wallet."""
        conn = self._get_conn()
        rows = conn.execute(
            """SELECT * FROM scan_history WHERE wallet = ?
               ORDER BY scanned_at DESC LIMIT ?""",
            (wallet, limit),
        ).fetchall()
        return [dict(r) for r in rows]

    def close(self) -> None:
        if self._conn:
            self._conn.close()
            self._conn = None
