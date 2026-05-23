"""Tests for Airdrop Hunter storage and protocols."""

import os
import tempfile
import pytest

from airdrop_hunter.storage import AirdropStorage
from airdrop_hunter.protocols import (
    AirdropInfo, ProtocolCategory, get_protocols_for_chain,
    get_all_protocols, get_protocol_count,
)


@pytest.fixture
def db():
    """Create a temporary database."""
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    storage = AirdropStorage(path)
    yield storage
    storage.close()
    os.unlink(path)


@pytest.fixture
def sample_result():
    """Create a sample airdrop result."""
    return AirdropInfo(
        protocol="Uniswap",
        category=ProtocolCategory.DEX,
        token="UNI",
        chain="ethereum",
        eligible=True,
        estimated_amount=400.0,
        claim_url="https://app.uniswap.org",
        details="Test result",
    )


class TestStorage:
    def test_save_and_retrieve(self, db, sample_result):
        db.save_scan_result("0x1234", sample_result)
        eligible = db.get_eligible("0x1234")
        assert len(eligible) == 1
        assert eligible[0]["protocol"] == "Uniswap"
        assert eligible[0]["eligible"] == 1

    def test_save_not_eligible(self, db):
        result = AirdropInfo(
            protocol="Test",
            category=ProtocolCategory.DEX,
            token="TST",
            chain="ethereum",
            eligible=False,
            estimated_amount=0,
        )
        db.save_scan_result("0x1234", result)
        eligible = db.get_eligible("0x1234")
        assert len(eligible) == 0

    def test_record_claim(self, db):
        db.record_claim("0x1234", "ethereum", "Uniswap", "UNI", 400.0, "0xabc")
        claims = db.get_claims("0x1234")
        assert len(claims) == 1
        assert claims[0]["protocol"] == "Uniswap"

    def test_scan_history(self, db):
        db.log_scan("0x1234", "ethereum", 20, 5)
        db.log_scan("0x1234", "arbitrum", 15, 3)
        history = db.get_scan_history("0x1234")
        assert len(history) == 2

    def test_filter_by_chain(self, db, sample_result):
        db.save_scan_result("0x1234", sample_result)
        other = AirdropInfo(
            protocol="GMX",
            category=ProtocolCategory.DERIVATIVES,
            token="GMX",
            chain="arbitrum",
            eligible=True,
            estimated_amount=50.0,
        )
        db.save_scan_result("0x1234", other)

        eth_only = db.get_eligible("0x1234", chain="ethereum")
        assert len(eth_only) == 1
        assert eth_only[0]["protocol"] == "Uniswap"

        all_chains = db.get_eligible("0x1234")
        assert len(all_chains) == 2


class TestProtocols:
    def test_protocol_count(self):
        assert get_protocol_count() > 15

    def test_ethereum_protocols(self):
        protocols = get_protocols_for_chain("ethereum")
        names = [p["protocol"] for p in protocols]
        assert "Uniswap" in names
        assert "ENS" in names

    def test_arbitrum_protocols(self):
        protocols = get_protocols_for_chain("arbitrum")
        names = [p["protocol"] for p in protocols]
        assert "GMX" in names

    def test_all_protocols(self):
        all_protocols = get_all_protocols()
        assert len(all_protocols) > 0
        for p in all_protocols:
            assert "protocol" in p
            assert "token" in p
            assert "chains" in p
