"""LLM stage — Groq integration with template fallback."""

import hashlib
import json
from typing import Any

from groq import Groq

from app.config import Settings
from app.services.redis_client import get_redis_client, is_redis_available


class GroqLLMService:
    def __init__(self, settings: Settings):
        self.settings = settings
        self._client: Groq | None = None
        if settings.groq_api_key:
            self._client = Groq(api_key=settings.groq_api_key, timeout=12.0)

    @property
    def is_configured(self) -> bool:
        return self._client is not None

    def parse_intent(self, raw_intent: str) -> dict[str, Any]:
        if not self._client:
            return self._fallback_intent(raw_intent)

        try:
            response = self._client.chat.completions.create(
                model=self.settings.groq_model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "Extract product intent as JSON with keys: "
                            "normalized_name, category, attributes, confidence (0-1)."
                        ),
                    },
                    {"role": "user", "content": f"USL intent: {raw_intent}"},
                ],
                response_format={"type": "json_object"},
                temperature=0.1,
            )
            return json.loads(response.choices[0].message.content or "{}")
        except Exception:
            return self._fallback_intent(raw_intent)

    def generate_reason_text(self, reason_type: str, signals: dict[str, Any]) -> str:
        cached = self._read_explanation_cache(reason_type, signals)
        if cached:
            return cached

        if not self._client:
            text = self._template_reason(reason_type, signals)
            self._write_explanation_cache(reason_type, signals, text)
            return text

        try:
            response = self._client.chat.completions.create(
                model=self.settings.groq_model,
                messages=[
                    {
                        "role": "system",
                        "content": "Generate one sentence reason_text for a checkout recommendation.",
                    },
                    {"role": "user", "content": json.dumps({"reason_type": reason_type, **signals})},
                ],
                temperature=0.3,
                max_tokens=120,
            )
            text = (response.choices[0].message.content or "").strip()
            text = text or self._template_reason(reason_type, signals)
        except Exception:
            text = self._template_reason(reason_type, signals)

        self._write_explanation_cache(reason_type, signals, text)
        return text

    def _explanation_cache_key(self, reason_type: str, signals: dict[str, Any]) -> str:
        product = signals.get("product_name", "")
        digest = hashlib.sha256(json.dumps({"reason_type": reason_type, "product": product}, sort_keys=True).encode()).hexdigest()[:16]
        return f"llm:explain:{reason_type}:{digest}"

    def _read_explanation_cache(self, reason_type: str, signals: dict[str, Any]) -> str | None:
        if self.settings.explanation_cache_ttl_seconds <= 0 or not is_redis_available(self.settings):
            return None
        try:
            client = get_redis_client(self.settings)
            raw = client.get(self._explanation_cache_key(reason_type, signals))
            return raw.decode() if isinstance(raw, bytes) else raw
        except Exception:
            return None

    def _write_explanation_cache(self, reason_type: str, signals: dict[str, Any], text: str) -> None:
        if self.settings.explanation_cache_ttl_seconds <= 0 or not text or not is_redis_available(self.settings):
            return
        try:
            client = get_redis_client(self.settings)
            client.setex(
                self._explanation_cache_key(reason_type, signals),
                self.settings.explanation_cache_ttl_seconds,
                text,
            )
        except Exception:
            pass

    def smoke_test(self) -> dict[str, Any]:
        result = self.parse_intent("Face Wash")
        return {"ok": True, "model": self.settings.groq_model, "sample": result}

    def select_matches_from_shortlist(
        self,
        raw_intent: str,
        intent_data: dict[str, Any],
        candidates: list[dict[str, Any]],
        max_matches: int = 3,
    ) -> list[dict[str, Any]]:
        capped = candidates[: self.settings.max_catalog_shortlist]

        if not capped:
            return []

        if self._client:
            try:
                response = self._client.chat.completions.create(
                    model=self.settings.groq_model,
                    messages=[
                        {
                            "role": "system",
                            "content": (
                                "Select up to 3 best SKU matches from candidates. "
                                "Return JSON: {\"matches\":[{\"sku_id\":\"...\",\"confidence\":0.0-1.0}]}"
                            ),
                        },
                        {
                            "role": "user",
                            "content": json.dumps(
                                {
                                    "raw_intent": raw_intent,
                                    "normalized_name": intent_data.get("normalized_name"),
                                    "category": intent_data.get("category"),
                                    "candidates": capped,
                                }
                            ),
                        },
                    ],
                    response_format={"type": "json_object"},
                    temperature=0.1,
                )
                payload = json.loads(response.choices[0].message.content or "{}")
                selected: list[dict[str, Any]] = []
                by_sku = {c["sku_id"]: c for c in capped}
                for match in payload.get("matches", [])[:max_matches]:
                    sku_id = match.get("sku_id")
                    if sku_id in by_sku:
                        selected.append(
                            {
                                **by_sku[sku_id],
                                "match_confidence": float(match.get("confidence", by_sku[sku_id].get("score", 0.5))),
                            }
                        )
                if selected:
                    return selected
            except Exception:
                pass

        return self._rank_candidates(raw_intent, intent_data, capped, max_matches)

    @staticmethod
    def _rank_candidates(
        raw_intent: str,
        intent_data: dict[str, Any],
        candidates: list[dict[str, Any]],
        max_matches: int,
    ) -> list[dict[str, Any]]:
        normalized = (intent_data.get("normalized_name") or raw_intent).lower()
        category = (intent_data.get("category") or "").lower()
        raw_lower = raw_intent.lower()

        def score_row(row: dict[str, Any]) -> float:
            name = row.get("product_name", "").lower()
            cat = row.get("category", "").lower()
            base = float(row.get("score", 0.5))
            if normalized and normalized in name:
                base += 0.25
            if raw_lower and any(token in name for token in raw_lower.split() if len(token) > 2):
                base += 0.2
            if "airpod" in raw_lower and ("airdopes" in name or "earbud" in name):
                base += 0.35
            if category and category in cat:
                base += 0.1
            return min(base, 1.0)

        ranked = sorted(candidates, key=score_row, reverse=True)
        output = []
        for row in ranked[:max_matches]:
            output.append({**row, "match_confidence": score_row(row)})
        return output

    @staticmethod
    def _fallback_intent(raw_intent: str) -> dict[str, Any]:
        return {
            "normalized_name": raw_intent.strip(),
            "category": "unknown",
            "attributes": {},
            "confidence": 0.0,
        }

    @staticmethod
    def _template_reason(reason_type: str, signals: dict[str, Any]) -> str:
        name = signals.get("product_name", "this item")
        templates = {
            "memory_reminder": f"You added {name} to your Universal Shopping List. It's available on Blinkit today.",
            "cross_category_discovery": f"You came to buy groceries today, but your saved {name} is also available on Blinkit.",
            "shopping_completion": f"You can complete more of your shopping today — {name} from your list is available now.",
            "weather_context": (
                f"Rain is forecast in the next {signals.get('days_ahead', 'few')} days — "
                f"your saved {name} could help you stay dry."
            ),
            "seasonal_context": (
                f"It's {signals.get('season_label', 'the season')} — {name} from your list fits what you may need now."
            ),
            "event_based": (
                f"{signals.get('event_label', name)} is coming up in {signals.get('days_until', 'a few')} days — "
                f"grab {name} while it's available."
            ),
            "replenishment_reminder": (
                f"You bought {name} about {signals.get('days_since_purchase', '30')} days ago — "
                f"it may be time to restock."
            ),
        }
        return templates.get(reason_type, f"Recommended based on your saved shopping list: {name}.")
