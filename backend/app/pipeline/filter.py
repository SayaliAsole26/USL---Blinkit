"""Filtering stage — deterministic rules before LLM."""

from dataclasses import dataclass


@dataclass
class FilterCandidate:
    sku_id: str
    product_name: str
    category: str
    reason_type: str
    score: float


class FilteringService:
    def __init__(self, max_shortlist: int = 80):
        self.MAX_SHORTLIST = max_shortlist

    def filter_catalog_matches(
        self,
        catalog_rows: list[dict],
        pincode: str,
        availability_checker,
        exclude_skus: set[str] | None = None,
    ) -> list[FilterCandidate]:
        exclude_skus = exclude_skus or set()
        candidates: list[FilterCandidate] = []

        for row in catalog_rows:
            sku_id = row["sku_id"]
            if sku_id in exclude_skus:
                continue
            status = availability_checker(sku_id, pincode)
            if status != "available":
                continue
            candidates.append(
                FilterCandidate(
                    sku_id=sku_id,
                    product_name=row["product_name"],
                    category=row["category"],
                    reason_type="memory_reminder",
                    score=float(row.get("score", 0.5)),
                )
            )

        candidates.sort(key=lambda c: c.score, reverse=True)
        return candidates[: self.MAX_SHORTLIST]
