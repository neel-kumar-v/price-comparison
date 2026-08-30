"""Browser-driven retailer price comparison via agent-browser + Helium CDP."""

from .browser import AgentBrowser, ensure_cdp
from .match import ProductReference, VerificationResult, load_fixture, verify_same_product
from .profile import (
    AMAZON_PRIME_DISCOUNT,
    AMAZON_SUBSCRIBE_AND_SAVE_DISCOUNT,
    BEST_BUY_TOTALTECH_DISCOUNT,
    COSTCO_EXECUTIVE_REWARDS,
    REI_MEMBER_DIVIDEND,
    TARGET_CIRCLE_DEBIT_CARD_DISCOUNT,
    WALMART_PLUS_DISCOUNT,
    WALMART_SUBSCRIPTION_DISCOUNT,
    WEGMANS_INSTACART_MARKUP,
    final_price_for_retailer,
    price_with_profile,
)
from .workflow import ComparisonRow, GeneralMerchWorkflow, PriceCompareWorkflow, get_workflow

__all__ = [
    "AgentBrowser",
    "ensure_cdp",
    "ProductReference",
    "VerificationResult",
    "verify_same_product",
    "load_fixture",
    "ComparisonRow",
    "GeneralMerchWorkflow",
    "PriceCompareWorkflow",
    "get_workflow",
    "TARGET_CIRCLE_DEBIT_CARD_DISCOUNT",
    "WALMART_PLUS_DISCOUNT",
    "WALMART_SUBSCRIPTION_DISCOUNT",
    "AMAZON_PRIME_DISCOUNT",
    "AMAZON_SUBSCRIBE_AND_SAVE_DISCOUNT",
    "REI_MEMBER_DIVIDEND",
    "BEST_BUY_TOTALTECH_DISCOUNT",
    "COSTCO_EXECUTIVE_REWARDS",
    "WEGMANS_INSTACART_MARKUP",
    "final_price_for_retailer",
    "price_with_profile",
]
