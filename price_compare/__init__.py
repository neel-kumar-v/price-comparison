"""Browser-driven retailer price comparison via agent-browser + Helium CDP."""

from .browser import AgentBrowser, ensure_cdp
from .match import ProductReference, VerificationResult, verify_same_product
from .profile import (
    AMAZON_PRIME_DISCOUNT,
    AMAZON_SUBSCRIBE_AND_SAVE_DISCOUNT,
    TARGET_CIRCLE_DEBIT_CARD_DISCOUNT,
    WALMART_PLUS_DISCOUNT,
    WALMART_SUBSCRIPTION_DISCOUNT,
    final_price_for_retailer,
    price_with_profile,
)
from .workflow import ComparisonRow, PriceCompareWorkflow

__all__ = [
    "AgentBrowser",
    "ensure_cdp",
    "ProductReference",
    "VerificationResult",
    "verify_same_product",
    "ComparisonRow",
    "PriceCompareWorkflow",
    "TARGET_CIRCLE_DEBIT_CARD_DISCOUNT",
    "WALMART_PLUS_DISCOUNT",
    "WALMART_SUBSCRIPTION_DISCOUNT",
    "AMAZON_PRIME_DISCOUNT",
    "AMAZON_SUBSCRIBE_AND_SAVE_DISCOUNT",
    "final_price_for_retailer",
    "price_with_profile",
]
