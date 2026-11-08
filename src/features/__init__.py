"""Feature blocks: crowding, valuation, funding, layer, liquidity.

Judgment-coded fields must be flagged (_JUDGMENT suffix) in every output.
"""

from src.features.crowding import (
    distance_from_high,
    prior_return,
    realised_vol,
    short_interest_pct_float,
)
from src.features.funding import FUNDING_COLS, empty_funding
from src.features.layer import ai_revenue_exposure, layer_assignments
from src.features.liquidity import adv_dollar, load_volume_panel, log_mkt_cap_placeholder
from src.features.valuation import VALUATION_COLS, empty_valuation

BLOCK_COLS: dict[str, tuple[str, ...]] = {
    "crowding": (
        "prior_63d_return",
        "dist_252d_high",
        "realised_vol_21d",
        "short_interest_pct_float",
    ),
    "valuation": VALUATION_COLS,
    "funding": FUNDING_COLS,
    "layer": (
        "layer",
        "ai_revenue_exposure_0_3_JUDGMENT",
    ),
    "liquidity": (
        "log_mkt_cap",
        "adv",
    ),
}

__all__ = [
    "BLOCK_COLS",
    "FUNDING_COLS",
    "VALUATION_COLS",
    "adv_dollar",
    "ai_revenue_exposure",
    "distance_from_high",
    "empty_funding",
    "empty_valuation",
    "layer_assignments",
    "load_volume_panel",
    "log_mkt_cap_placeholder",
    "prior_return",
    "realised_vol",
    "short_interest_pct_float",
]
