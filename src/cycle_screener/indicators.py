from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class IndicatorDefinition:
    slug: str
    name: str
    source: str
    source_key: str
    unit: str
    higher_is: str
    description: str
    transform: str = "level"
    family: str = "other"
    expected_release_days: int = 75
    scoring_role: str = "scoring"
    critical: bool = False


# Source and transformation contracts are intentionally explicit. A label is not
# allowed to imply a construct that the source does not measure.
INDICATORS: tuple[IndicatorDefinition, ...] = (
    IndicatorDefinition("brent", "Brent crude oil", "world_bank_commodity", "CRUDE_BRENT", "USD/bbl", "mixed", "Global oil-price context; not an inventory or forward-curve measure.", "yoy_return", "energy_prices", 50),
    IndicatorDefinition("wti", "WTI crude oil", "world_bank_commodity", "CRUDE_WTI", "USD/bbl", "mixed", "US oil-price context; not an inventory or forward-curve measure.", "yoy_return", "energy_prices", 50),
    IndicatorDefinition("us_natural_gas", "US natural gas", "world_bank_commodity", "NGAS_US", "USD/MMBtu", "mixed", "Henry Hub-linked gas-price context; not a complete LNG-market balance.", "yoy_return", "energy_prices", 50),
    IndicatorDefinition("us_crude_stocks", "US commercial crude-oil inventories", "eia_petroleum", "WCESTUS1", "thousand barrels", "lower_tailwind", "Weekly EIA commercial crude-oil inventories excluding the Strategic Petroleum Reserve.", "yoy_change", "energy_inventories", 14),
    IndicatorDefinition("us_distillate_stocks", "US distillate fuel-oil inventories", "eia_petroleum", "WDISTUS1", "thousand barrels", "lower_tailwind", "Weekly EIA distillate fuel-oil inventories.", "yoy_change", "energy_inventories", 14),
    IndicatorDefinition("global_pmi", "Global annual GDP growth background", "world_bank_indicator", "WLD/NY.GDP.MKTP.KD.ZG", "%", "higher_tailwind", "Slow-moving World Bank annual real-GDP growth background; explicitly not PMI.", "level", "growth_background", 550, "context"),
    IndicatorDefinition("china_growth_proxy", "China annual GDP growth background", "world_bank_indicator", "CHN/NY.GDP.MKTP.KD.ZG", "%", "higher_tailwind", "Slow-moving World Bank annual real-GDP growth background for China.", "level", "growth_background", 550, "context"),
    IndicatorDefinition("g20_cli", "G20 OECD CLI", "dbnomics_oecd_cli", "G20.M.LI...AA...H", "index", "higher_tailwind", "OECD composite leading indicator for G20 turning-point monitoring.", "gap_from_100", "oecd_cli", 75, "scoring", True),
    IndicatorDefinition("g7_cli", "G7 OECD CLI", "dbnomics_oecd_cli", "G7.M.LI...AA...H", "index", "higher_tailwind", "OECD composite leading indicator for G7 turning-point monitoring.", "gap_from_100", "oecd_cli", 75),
    IndicatorDefinition("us_cli", "US OECD CLI", "dbnomics_oecd_cli", "USA.M.LI...AA...H", "index", "higher_tailwind", "OECD composite leading indicator for US turning-point monitoring.", "gap_from_100", "oecd_cli", 75),
    IndicatorDefinition("china_cli", "China OECD CLI", "dbnomics_oecd_cli", "CHN.M.LI...AA...H", "index", "higher_tailwind", "OECD composite leading indicator for China turning-point monitoring.", "gap_from_100", "oecd_cli", 75),
    IndicatorDefinition("europe_cli", "Major Europe OECD CLI", "dbnomics_oecd_cli", "G4E.M.LI...AA...H", "index", "higher_tailwind", "OECD composite leading indicator for the four major European economies.", "gap_from_100", "oecd_cli", 75),
    IndicatorDefinition("copper", "Copper", "world_bank_commodity", "COPPER", "USD/metric ton", "higher_tailwind", "Industrial-metals price momentum and scarcity proxy.", "yoy_return", "industrial_metals", 50),
    IndicatorDefinition("aluminum", "Aluminium", "world_bank_commodity", "ALUMINUM", "USD/metric ton", "higher_tailwind", "Aluminium price momentum and scarcity proxy.", "yoy_return", "industrial_metals", 50),
    IndicatorDefinition("usd_nok", "USD/NOK", "norges_bank_csv", "EXR/B.USD.NOK.SP", "FX", "mixed", "NOK translation and risk context; polarity is sector-dependent.", "yoy_return", "fx", 14, "context"),
    IndicatorDefinition("eur_nok", "EUR/NOK", "norges_bank_csv", "EXR/B.EUR.NOK.SP", "FX", "mixed", "European/Norwegian FX context; polarity is sector-dependent.", "yoy_return", "fx", 14, "context"),
    IndicatorDefinition("rates_pressure", "US 10-year Treasury yield", "fred_public", "DGS10", "%", "lower_tailwind", "Official Federal Reserve 10-year constant-maturity Treasury yield.", "level", "sovereign_yields", 14, "scoring", True),
    IndicatorDefinition("us_real_10y_yield", "US 10-year real Treasury yield", "fred_public", "DFII10", "%", "lower_tailwind", "Inflation-indexed 10-year Treasury yield and global duration pressure proxy.", "level", "sovereign_yields", 14),
    IndicatorDefinition("us_yield_curve", "US 10y–2y Treasury curve", "fred_public", "T10Y2Y", "percentage points", "mixed", "US term-spread context; inversions and rapid re-steepening require different interpretation.", "level", "yield_curve", 14, "context"),
    IndicatorDefinition("norges_bank_policy_rate", "Norges Bank key policy rate", "norges_bank_csv", "IR/B.KPRA.SD", "%", "lower_tailwind", "Official Norwegian key policy rate (SD), not the reserve rate.", "level", "policy_rates", 14, "scoring", True),
    IndicatorDefinition("fed_policy_rate", "Federal Reserve policy rate", "dbnomics_bis_policy", "M.US", "%", "lower_tailwind", "BIS monthly central-bank policy-rate series for the United States.", "level", "policy_rates", 45),
    IndicatorDefinition("ecb_policy_rate", "ECB policy rate", "dbnomics_bis_policy", "M.XM", "%", "lower_tailwind", "BIS monthly central-bank policy-rate series for the euro area.", "level", "policy_rates", 45),
    IndicatorDefinition("boe_policy_rate", "Bank of England policy rate", "dbnomics_bis_policy", "M.GB", "%", "lower_tailwind", "BIS monthly central-bank policy-rate series for the United Kingdom.", "level", "policy_rates", 45),
    IndicatorDefinition("boj_policy_rate", "Bank of Japan policy rate", "dbnomics_bis_policy", "M.JP", "%", "lower_tailwind", "BIS monthly central-bank policy-rate series for Japan.", "level", "policy_rates", 45),
    IndicatorDefinition("pboc_policy_rate", "People's Bank of China policy rate", "dbnomics_bis_policy", "M.CN", "%", "lower_tailwind", "BIS monthly central-bank policy-rate series for China.", "level", "policy_rates", 45),
    IndicatorDefinition("boc_policy_rate", "Bank of Canada policy rate", "dbnomics_bis_policy", "M.CA", "%", "lower_tailwind", "BIS monthly central-bank policy-rate series for Canada.", "level", "policy_rates", 45),
    IndicatorDefinition("rba_policy_rate", "Reserve Bank of Australia policy rate", "dbnomics_bis_policy", "M.AU", "%", "lower_tailwind", "BIS monthly central-bank policy-rate series for Australia.", "level", "policy_rates", 45),
    IndicatorDefinition("snb_policy_rate", "Swiss National Bank policy rate", "dbnomics_bis_policy", "M.CH", "%", "lower_tailwind", "BIS monthly central-bank policy-rate series for Switzerland.", "level", "policy_rates", 45),
    IndicatorDefinition("riksbank_policy_rate", "Riksbank policy rate", "dbnomics_bis_policy", "M.SE", "%", "lower_tailwind", "BIS monthly central-bank policy-rate series for Sweden.", "level", "policy_rates", 45),
    IndicatorDefinition("norway_cpi", "Norway CPI inflation (12-month)", "ssb_cpi", "14700/TOTAL/Tolvmanedersendring", "% y/y", "lower_tailwind", "Statistics Norway CPI twelve-month change from the current CPI table.", "level", "inflation", 50, "scoring", True),
    IndicatorDefinition("us_cpi", "US CPI inflation", "fred_public", "CPIAUCSL", "% y/y", "lower_tailwind", "US CPI index transformed by the screener to twelve-month inflation.", "yoy_pct", "inflation", 50),
    IndicatorDefinition("euro_cpi", "Euro-area HICP inflation", "fred_public", "CP0000EZ19M086NEST", "% y/y", "lower_tailwind", "Euro-area HICP index transformed to twelve-month inflation.", "yoy_pct", "inflation", 60),
    IndicatorDefinition("uk_cpi", "UK CPI inflation", "fred_public", "GBRCPIALLMINMEI", "% y/y", "lower_tailwind", "UK CPI index transformed to twelve-month inflation.", "yoy_pct", "inflation", 60),
    IndicatorDefinition("japan_cpi", "Japan CPI inflation", "fred_public", "JPNCPIALLMINMEI", "% y/y", "lower_tailwind", "Japan CPI index transformed to twelve-month inflation.", "yoy_pct", "inflation", 60),
    IndicatorDefinition("china_cpi", "China CPI inflation", "fred_public", "CHNCPIALLMINMEI", "% y/y", "lower_tailwind", "China CPI index transformed to twelve-month inflation.", "yoy_pct", "inflation", 60),
    IndicatorDefinition("chicago_fed_nfci", "Chicago Fed NFCI", "fred_public", "NFCI", "standard deviations", "lower_tailwind", "Broad weekly US financial conditions; positive values are tighter than average.", "standardized_index", "financial_conditions", 21, "scoring", True),
    IndicatorDefinition("st_louis_financial_stress", "St. Louis Fed Financial Stress Index", "fred_public", "STLFSI4", "standard deviations", "lower_tailwind", "Broad weekly US financial-stress measure; positive values indicate above-average stress.", "standardized_index", "financial_conditions", 21),
    IndicatorDefinition("us_high_yield_spread", "US high-yield option-adjusted spread", "fred_public", "BAMLH0A0HYM2", "percentage points", "lower_tailwind", "ICE BofA US high-yield option-adjusted spread via FRED.", "level", "credit_spreads", 21),
    IndicatorDefinition("us_investment_grade_spread", "US investment-grade option-adjusted spread", "fred_public", "BAMLC0A0CM", "percentage points", "lower_tailwind", "ICE BofA US corporate option-adjusted spread via FRED.", "level", "credit_spreads", 21),
    IndicatorDefinition("broad_us_dollar", "Broad trade-weighted US dollar", "fred_public", "DTWEXBGS", "index", "lower_tailwind", "Broad dollar strength as a global financial-conditions proxy.", "yoy_return", "dollar_liquidity", 21),
    IndicatorDefinition("vix_proxy", "CBOE VIX", "yahoo_chart", "^VIX", "index", "lower_tailwind", "US equity implied-volatility proxy.", "level", "volatility", 14),
    IndicatorDefinition("sp500_equal_weight_proxy", "S&P 500 equal-weight ETF", "yahoo_chart", "RSP", "USD", "mixed", "Adjusted-close market proxy used only to derive equal-weight relative performance.", "yoy_return", "market_breadth", 14, "context"),
    IndicatorDefinition("sp500_cap_weight_proxy", "S&P 500 cap-weight ETF", "yahoo_chart", "SPY", "USD", "mixed", "Adjusted-close benchmark used only to derive equal-weight relative performance.", "yoy_return", "market_breadth", 14, "context"),
    IndicatorDefinition("food_price_pressure", "Fish meal price", "world_bank_commodity", "FISH_MEAL", "USD/metric ton", "mixed", "One seafood feed-cost input; not a seafood operating-cycle measure.", "yoy_return", "food_inputs", 50, "context"),
    IndicatorDefinition("nasdaq_proxy", "NASDAQ Composite", "yahoo_chart", "^IXIC", "index", "higher_tailwind", "US technology-heavy equity market momentum proxy.", "yoy_return", "global_equities", 14),
    IndicatorDefinition("global_equity_proxy", "Global equities (ACWI ETF)", "yahoo_chart", "ACWI", "USD", "higher_tailwind", "Public adjusted-close proxy for developed and emerging global equities.", "yoy_return", "global_equities", 14, "scoring", True),
    IndicatorDefinition("europe_equity_proxy", "European equities (VGK ETF)", "yahoo_chart", "VGK", "USD", "higher_tailwind", "Public adjusted-close proxy for broad European equities.", "yoy_return", "global_equities", 14),
    IndicatorDefinition("japan_equity_proxy", "Japanese equities (EWJ ETF)", "yahoo_chart", "EWJ", "USD", "higher_tailwind", "Public adjusted-close proxy for Japanese equities.", "yoy_return", "global_equities", 14),
    IndicatorDefinition("em_equity_proxy", "Emerging-market equities (EEM ETF)", "yahoo_chart", "EEM", "USD", "higher_tailwind", "Public adjusted-close proxy for broad emerging-market equities.", "yoy_return", "global_equities", 14),
    IndicatorDefinition("geopolitical_risk", "Geopolitical Risk Index", "academic_gpr", "GPR", "index", "lower_tailwind", "Caldara–Iacoviello monthly news-based geopolitical risk index.", "standardized_index", "geopolitical_risk", 75, "scoring"),
    IndicatorDefinition("oil_curve_pressure", "Brent–WTI cross-benchmark spread", "derived_public", "brent-wti", "USD/bbl", "mixed", "Cross-benchmark oil differential; explicitly not a futures term-structure measure.", "level", "energy_spreads", 50, "context"),
    IndicatorDefinition("us_equity_market_cap_gdp_proxy", "US equity market-cap-to-GDP", "derived_public", "BOGZ1LM883164105Q/GDP", "%", "lower_tailwind", "Long-horizon aggregate US valuation context; not a timing signal.", "level", "valuation", 280, "context"),
    IndicatorDefinition("sp500_equal_weight_leadership_proxy", "S&P 500 equal-weight relative performance", "derived_public", "RSP/SPY", "ratio", "higher_tailwind", "Adjusted-close equal-weight versus cap-weight relative-performance proxy; not pure market breadth.", "yoy_return", "market_breadth", 21),
)


PUBLIC_INDICATOR_SLUGS = {
    "global_pmi": "global_gdp_growth_background",
    "oil_curve_pressure": "brent_wti_cross_benchmark_spread",
}


def indicator_by_slug() -> dict[str, IndicatorDefinition]:
    return {indicator.slug: indicator for indicator in INDICATORS}


def public_indicator_slug(slug: str) -> str:
    return PUBLIC_INDICATOR_SLUGS.get(slug, slug)
