"""Black-Scholes options pricing and Greeks."""

from __future__ import annotations

import math
from dataclasses import dataclass


def norm_cdf(x: float) -> float:
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def norm_pdf(x: float) -> float:
    return math.exp(-0.5 * x * x) / math.sqrt(2.0 * math.pi)


def _d1d2(s: float, k: float, t: float, r: float, sigma: float) -> tuple[float, float]:
    if t <= 0 or sigma <= 0 or s <= 0:
        return 0.0, 0.0
    d1 = (math.log(s / k) + (r + 0.5 * sigma * sigma) * t) / (sigma * math.sqrt(t))
    d2 = d1 - sigma * math.sqrt(t)
    return d1, d2


@dataclass
class OptionGreeks:
    price: float
    delta: float
    gamma: float
    theta: float  # per calendar day
    vega: float   # per 1% IV move
    rho: float    # per 1% rate move


def black_scholes(
    spot: float,
    strike: float,
    time_years: float,
    rate: float,
    volatility: float,
    option_type: str = "call",
) -> OptionGreeks:
    if time_years <= 0:
        intrinsic = max(spot - strike, 0) if option_type == "call" else max(strike - spot, 0)
        delta = 1.0 if (option_type == "call" and spot > strike) else (-1.0 if option_type == "put" and spot < strike else 0.0)
        return OptionGreeks(intrinsic, delta, 0.0, 0.0, 0.0, 0.0)

    d1, d2 = _d1d2(spot, strike, time_years, rate, volatility)
    nd1 = norm_cdf(d1)
    nd2 = norm_cdf(d2)
    npd1 = norm_pdf(d1)

    if option_type == "call":
        price = spot * nd1 - strike * math.exp(-rate * time_years) * nd2
        delta = nd1
        rho = strike * time_years * math.exp(-rate * time_years) * nd2 / 100
    else:
        price = strike * math.exp(-rate * time_years) * norm_cdf(-d2) - spot * norm_cdf(-d1)
        delta = nd1 - 1
        rho = -strike * time_years * math.exp(-rate * time_years) * norm_cdf(-d2) / 100

    gamma = npd1 / (spot * volatility * math.sqrt(time_years)) if spot > 0 else 0.0
    vega = spot * npd1 * math.sqrt(time_years) / 100

    term1 = -(spot * npd1 * volatility) / (2 * math.sqrt(time_years))
    if option_type == "call":
        term2 = -rate * strike * math.exp(-rate * time_years) * nd2
        theta = (term1 + term2) / 365
    else:
        term2 = rate * strike * math.exp(-rate * time_years) * norm_cdf(-d2)
        theta = (term1 + term2) / 365

    return OptionGreeks(price, delta, gamma, theta, vega, rho)