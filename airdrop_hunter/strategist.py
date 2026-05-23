"""MiMo AI-powered claim strategy analysis."""

from __future__ import annotations

import json
import logging
from typing import Optional

from openai import OpenAI

from .protocols import AirdropInfo

logger = logging.getLogger(__name__)

STRATEGY_PROMPT = """You are a DeFi airdrop strategist. Given the following airdrop eligibility results 
for wallet {wallet} on {chain}, analyze and provide:

1. **Priority Ranking** — Which airdrops to claim first (considering gas costs, deadlines, and value)
2. **Gas Optimization** — Batch claiming strategies to save on gas
3. **Risk Assessment** — Any known risks with claiming specific tokens
4. **Action Plan** — Step-by-step instructions

Eligibility Results:
{eligibility_data}

Respond in JSON format:
{{
  "priority_claims": [
    {{"protocol": "...", "token": "...", "estimated_value_usd": 0, "urgency": "high/medium/low", "reason": "..."}}
  ],
  "gas_optimization": "...",
  "risk_notes": ["..."],
  "action_steps": ["Step 1: ...", "Step 2: ..."],
  "total_estimated_value_usd": 0,
  "confidence": "high/medium/low"
}}"""


class ClaimStrategist:
    """AI-powered airdrop claim strategy advisor using MiMo LLM."""

    def __init__(self, api_url: str = "https://opengateway.gitlawb.com/v1/xiaomi-mimo",
                 model: str = "xiaomi-mimo"):
        self.client = OpenAI(
            base_url=api_url,
            api_key="not-needed",
        )
        self.model = model

    def analyze_eligibility(self, wallet: str, chain: str,
                            results: list[AirdropInfo]) -> dict:
        """Analyze airdrop eligibility results and generate a claim strategy."""
        eligible = [r for r in results if r.eligible]
        if not eligible:
            return {
                "priority_claims": [],
                "gas_optimization": "No eligible airdrops found.",
                "risk_notes": [],
                "action_steps": ["Continue using DeFi protocols to qualify for future airdrops."],
                "total_estimated_value_usd": 0,
                "confidence": "high",
            }

        # Format eligibility data for the prompt
        eligibility_data = []
        for r in eligible:
            eligibility_data.append(
                f"- {r.protocol} ({r.token}) on {r.chain}: "
                f"~{r.estimated_amount:.2f} tokens | "
                f"Deadline: {r.claim_deadline or 'Unknown'} | "
                f"Claim: {r.claim_url or 'N/A'}"
            )

        prompt = STRATEGY_PROMPT.format(
            wallet=wallet,
            chain=chain,
            eligibility_data="\n".join(eligibility_data),
        )

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert DeFi strategist. Respond only in valid JSON."},
                    {"role": "user", "content": prompt},
                ],
                max_tokens=1024,
                temperature=0.2,
            )
            content = response.choices[0].message.content.strip()
            # Try to extract JSON from response
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()

            return json.loads(content)

        except json.JSONDecodeError:
            logger.warning("Failed to parse MiMo strategy response as JSON")
            return self._fallback_strategy(eligible)
        except Exception as e:
            logger.warning("Strategy generation failed: %s", e)
            return self._fallback_strategy(eligible)

    def _fallback_strategy(self, eligible: list[AirdropInfo]) -> dict:
        """Generate a basic strategy without AI."""
        priority_claims = []
        for r in sorted(eligible, key=lambda x: x.estimated_amount, reverse=True):
            priority_claims.append({
                "protocol": r.protocol,
                "token": r.token,
                "estimated_value_usd": 0,
                "urgency": "medium",
                "reason": f"Eligible for {r.estimated_amount:.2f} {r.token}",
            })

        return {
            "priority_claims": priority_claims,
            "gas_optimization": "Claim higher-value airdrops first. Consider batching claims to save gas.",
            "risk_notes": [
                "Always verify claim URLs are official",
                "Be wary of phishing sites mimicking claim pages",
            ],
            "action_steps": [
                "Visit each protocol's official claim page",
                "Claim highest-value tokens first",
                "Monitor gas prices for optimal claiming time",
            ],
            "total_estimated_value_usd": 0,
            "confidence": "low",
        }

    def format_strategy_report(self, wallet: str, chain: str, strategy: dict) -> str:
        """Format strategy as a human-readable report."""
        lines = [
            f"═══ Airdrop Claim Strategy ═══",
            f"Wallet: {wallet}",
            f"Chain: {chain}",
            f"Confidence: {strategy.get('confidence', 'unknown')}",
            f"Estimated Total Value: ${strategy.get('total_estimated_value_usd', 0):,.2f}",
            "",
            "── Priority Claims ──",
        ]

        for i, claim in enumerate(strategy.get("priority_claims", []), 1):
            urgency_icon = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(
                claim.get("urgency", "medium"), "⚪"
            )
            lines.append(
                f"  {i}. {urgency_icon} {claim['protocol']} ({claim['token']}) — "
                f"${claim.get('estimated_value_usd', 0):,.2f}"
            )
            lines.append(f"     {claim.get('reason', '')}")

        lines.extend([
            "",
            "── Gas Optimization ──",
            f"  {strategy.get('gas_optimization', 'N/A')}",
            "",
            "── Risk Notes ──",
        ])
        for note in strategy.get("risk_notes", []):
            lines.append(f"  ⚠️  {note}")

        lines.extend(["", "── Action Plan ──"])
        for step in strategy.get("action_steps", []):
            lines.append(f"  → {step}")

        return "\n".join(lines)

    def close(self) -> None:
        self.client.close()
