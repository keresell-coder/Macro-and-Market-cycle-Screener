from __future__ import annotations

from datetime import date
import math

import pandas as pd

from .indicators import INDICATORS
from .taxonomy import SUBSECTORS


def generate_sample_observations(months: int = 72) -> pd.DataFrame:
    end = pd.Timestamp(date.today()).to_period("M").to_timestamp("M")
    dates = pd.date_range(end=end, periods=months, freq="ME")
    rows: list[dict[str, object]] = []

    for indicator in INDICATORS:
        base = _base_for(indicator.slug)
        trend = _trend_for(indicator.slug)
        phase = (sum(ord(ch) for ch in indicator.slug) % 17) / 4
        amplitude = _amplitude_for(indicator.slug)
        for idx, observed_at in enumerate(dates):
            cycle = math.sin(idx / 7.5 + phase)
            long_cycle = math.cos(idx / 18 + phase / 2)
            value = base + trend * idx + amplitude * cycle + amplitude * 0.35 * long_cycle
            value_floor = -5 if indicator.slug in {"chicago_fed_nfci", "st_louis_financial_stress", "oil_curve_pressure"} else 0.01
            rows.append(
                {
                    "indicator_slug": indicator.slug,
                    "observed_at": observed_at.date().isoformat(),
                    "value": round(max(value, value_floor), 4),
                    "source": indicator.source,
                    "unit": indicator.unit,
                }
            )

    return pd.DataFrame(rows)


def generate_sample_research_mentions() -> pd.DataFrame:
    today = pd.Timestamp(date.today()).date().isoformat()
    rows = [
        ("dnb_carnegie", "rates", "Rates are restrictive, but the next visible move is more likely easing than tightening.", 0.35),
        ("blackrock", "technology", "AI investment remains powerful, while valuation discipline is increasingly important.", -0.1),
        ("jpmorgan", "energy", "Energy risk premia remain sensitive to geopolitical disruption and supply discipline.", 0.25),
        ("goldman_sachs", "growth", "Global growth remains uneven but avoids a broad recession in the base case.", 0.15),
        ("ubs", "china", "China demand is still a swing factor for industrial commodities.", 0.05),
        ("drewry", "shipping", "Container and freight indicators remain fragmented across vessel classes.", -0.05),
    ]
    return pd.DataFrame(
        [
            {
                "source_slug": source,
                "theme": theme,
                "summary": summary,
                "sentiment": sentiment,
                "published_at": today,
                "url": "",
            }
            for source, theme, summary, sentiment in rows
        ]
    )


def generate_sample_research_profiles() -> pd.DataFrame:
    today = pd.Timestamp(date.today()).date().isoformat()
    rows: list[dict[str, object]] = []
    for subsector in SUBSECTORS:
        first_driver = subsector.drivers[0]
        second_driver = subsector.drivers[1] if len(subsector.drivers) > 1 else subsector.drivers[0]
        first_sensitivity = subsector.macro_sensitivities[0]
        profile = _PROFILE_OVERRIDES.get(subsector.slug, {})
        rows.append(
            {
                "subsector_slug": subsector.slug,
                "scope": profile.get(
                    "scope",
                    f"{subsector.name} as an Oslo-linked subsector, using public macro, commodity, rates, and market proxies.",
                ),
                "cycle_conclusion": profile.get(
                    "cycle_conclusion",
                    f"{subsector.name} is a watchlist candidate rather than a confirmed cycle turn. The relevant conclusion depends on whether {first_driver}, relative price action, and valuation proxies improve together.",
                ),
                "current_phase_hypothesis": profile.get(
                    "current_phase_hypothesis",
                    f"Watch for a cycle turn when {first_driver} stops deteriorating while {first_sensitivity} becomes less hostile.",
                ),
                "valuation_context": profile.get(
                    "valuation_context",
                    f"Use relative price performance and valuation proxy history to separate a real reset in expectations from a broad Oslo market move.",
                ),
                "market_cycle_watch": profile.get(
                    "market_cycle_watch",
                    f"The cycle chart should be read as price versus benchmark, relative price, valuation proxy, and driver pressure, with {', '.join(subsector.proxy_indicators[:3])} as the first factor set.",
                ),
                "why_now": profile.get(
                    "why_now",
                    f"The current radar setup compares recent moves in {', '.join(subsector.proxy_indicators[:3])} with the subsector's main drivers. This is a research prompt, not a score override.",
                ),
                "key_debates": profile.get(
                    "key_debates",
                    f"Bull case: {first_driver} improves before consensus catches up.\nBase case: proxies stabilize but remain noisy.\nBear case: {second_driver} offsets any macro improvement.",
                ),
                "catalysts": profile.get(
                    "catalysts",
                    f"Upcoming company updates, official data releases, policy decisions, and sector-specific price or utilization indicators tied to {first_driver}.",
                ),
                "risks": profile.get(
                    "risks",
                    f"False positives from broad market moves, stale proxy data, and unsourced claims about {second_driver}.",
                ),
                "review_status": profile.get("review_status", "reviewed"),
                "updated_at": today,
            }
        )
    return pd.DataFrame(rows)


def generate_sample_research_facts() -> pd.DataFrame:
    today = pd.Timestamp(date.today()).date().isoformat()
    rows: list[dict[str, object]] = []
    for subsector in SUBSECTORS:
        official = _official_fact_for(subsector)
        rows.append(
            {
                "fact_id": f"{subsector.slug}-official-proxy",
                "subsector_slug": subsector.slug,
                "theme": "source_evidence",
                "claim": official["claim"],
                "source_name": official["source_name"],
                "source_url": official["source_url"],
                "source_type": "public_data",
                "source_quality": official["source_quality"],
                "source_date": today,
                "captured_at": today,
                "confidence": official["confidence"],
                "review_status": "reviewed",
                "evidence_scope": "public",
            }
        )
        rows.append(
            {
                "fact_id": f"{subsector.slug}-research-debate",
                "subsector_slug": subsector.slug,
                "theme": "key_debate",
                "claim": _debate_fact_for(subsector),
                "source_name": "Project research framework",
                "source_url": "docs/market_researcher_repo_evaluation.md",
                "source_type": "internal_methodology",
                "source_quality": "sample",
                "source_date": today,
                "captured_at": today,
                "confidence": 0.55,
                "review_status": "unreviewed",
                "evidence_scope": "manual_public",
            }
        )
        for idx, fact in enumerate(_source_backed_facts_for(subsector), start=1):
            rows.append(
                {
                    "fact_id": f"{subsector.slug}-source-{idx}",
                    "subsector_slug": subsector.slug,
                    "theme": fact["theme"],
                    "claim": fact["claim"],
                    "source_name": fact["source_name"],
                    "source_url": fact["source_url"],
                    "source_type": fact["source_type"],
                    "source_quality": fact["source_quality"],
                    "source_date": fact["source_date"],
                    "captured_at": today,
                    "confidence": fact["confidence"],
                    "review_status": "reviewed",
                    "evidence_scope": "public",
                }
            )
    return pd.DataFrame(rows)


_PROFILE_OVERRIDES: dict[str, dict[str, str]] = {
    "crude_tankers": {
        "cycle_conclusion": "The cycle read is constructive only if oil trade disruption or inventory draws lift ton-mile demand faster than vessel supply normalizes. Relative tanker price strength without better oil-trade evidence should be treated as a sentiment move, not a confirmed cycle turn.",
        "valuation_context": "Compare tanker equities against the Oslo benchmark and freight-linked proxies. A cheaper valuation proxy is more meaningful when relative price is basing and oil-market evidence points to tighter trade flows.",
        "market_cycle_watch": "Watch Brent/WTI, oil-price pressure, G20 OECD CLI, the global annual GDP growth proxy, relative sector price, and valuation proxy together; a durable turn should show improving relative price before valuation fully normalizes.",
        "why_now": "Oil-price pressure, Brent/WTI prices, OECD CLI data, and annual GDP growth proxies can flag when oil trade activity is improving before public tanker sentiment has fully recovered.",
        "key_debates": "Bull case: trade disruption and ton-mile expansion tighten vessel supply.\nBase case: oil trade normalizes but rates stay volatile.\nBear case: weak oil demand or fleet additions absorb the recovery.",
        "catalysts": "OPEC+ decisions, sanctions or route changes, weekly oil inventory releases, fleet orderbook updates, and spot-rate inflections.",
    },
    "product_chemical_tankers": {
        "cycle_conclusion": "The setup is about refinery and product-flow dislocation, not just crude-price direction. A stronger conclusion requires distillate inventory pressure, route disruption, and relative price stabilization to line up.",
        "valuation_context": "Low valuation proxies are useful only when product tanker relative price stops underperforming while product inventory and refinery-dislocation evidence improves.",
        "market_cycle_watch": "Track heating-oil proxy data, Brent, G20 OECD CLI, the global annual GDP growth proxy, USD/NOK, relative price, and valuation proxy; product tankers can diverge from crude tankers when refinery geography changes.",
    },
    "dry_bulk": {
        "cycle_conclusion": "Dry bulk remains a high-beta China and industrial-cycle watch item. Treat rallies cautiously unless copper/aluminum, China proxy data, and relative price action confirm each other.",
        "valuation_context": "Because free freight data is limited, valuation context should lean on relative price versus Oslo and commodity-cycle proxies rather than standalone multiples.",
        "market_cycle_watch": "Copper, aluminum, G20 OECD CLI, China OECD CLI, China annual GDP growth proxy, relative price, and valuation proxy are the minimum factor set before calling a cycle recovery.",
    },
    "lng_lpg_shipping": {
        "cycle_conclusion": "The cycle conclusion depends on gas-spread and fleet-delivery timing. Strong energy-security narratives are not enough if relative price and gas-market proxies fail to confirm.",
        "valuation_context": "A discounted valuation proxy matters most when relative price firms while gas-market pressure and Asian demand indicators improve.",
        "market_cycle_watch": "Watch gas prices, Brent, G20 OECD CLI, the global annual GDP growth proxy, USD/NOK, relative price, valuation proxy, and vessel-supply commentary.",
    },
    "offshore_vessels_drilling": {
        "cycle_conclusion": "The most attractive recovery pattern is late-cycle discipline: oil companies lift offshore spending while vessel and rig supply stays tight. Relative price strength should be confirmed by backlog, utilization, and dayrate evidence.",
        "valuation_context": "Relative price can run ahead of fundamentals in offshore services; valuation should be read against backlog quality and margin conversion, not oil price alone.",
        "market_cycle_watch": "Oil curve pressure, Brent, G20 OECD CLI, the global annual GDP growth proxy, USD/NOK, relative price, valuation proxy, and order/backlog evidence should move in the same direction.",
        "why_now": "Offshore recovery setups often appear when oil prices and curve tightness improve while vessel or rig supply remains constrained.",
        "key_debates": "Bull case: E&P capex broadens and dayrates rise.\nBase case: backlog improves gradually.\nBear case: oil-company budget discipline caps utilization gains.",
        "catalysts": "E&P capex budgets, tender awards, rig/vessel utilization updates, oil-price curve shifts, and quarterly backlog commentary.",
    },
    "oil_gas_ep": {
        "cycle_conclusion": "E&P is primarily a commodity-cash-flow and reserve-replacement cycle. The cycle read improves when Brent, gas, FX translation, and relative price move together without valuation proxy becoming crowded.",
        "valuation_context": "Cheapness should be checked against commodity assumptions; low valuation can be a value trap if oil/gas curves weaken or tax/regulatory risk rises.",
        "market_cycle_watch": "Brent, WTI, gas, USD/NOK, relative price, valuation proxy, and forward-curve pressure should be read as one picture.",
    },
    "oil_services": {
        "cycle_conclusion": "Oil services is a second-derivative recovery lane: the key signal is improving orders, backlog, and margins before reported earnings fully catch up. Relative price should be checked against order-quality evidence.",
        "valuation_context": "Relative underperformance with stabilizing order data can be useful; relative outperformance without margin conversion raises exit-warning risk.",
        "market_cycle_watch": "Track Brent, G20 OECD CLI, the global annual GDP growth proxy, USD/NOK, rates pressure, relative price, valuation proxy, and backlog/order commentary.",
    },
    "seafood_aquaculture": {
        "cycle_conclusion": "Seafood is not a simple macro-beta sector. The cycle read should emphasize salmon volume/price mix, biology, regulation, FX, and feed costs before drawing conclusions from broad food inflation.",
        "valuation_context": "A lower valuation proxy is only attractive if biological risk and regulatory risk are not deteriorating and relative price has stopped discounting weaker salmon prices.",
        "market_cycle_watch": "Food-price pressure, USD/NOK, EUR/NOK, G20 OECD CLI, the global annual GDP growth proxy, relative price, valuation proxy, salmon price/volume evidence, and regulatory events are the core dashboard set.",
    },
    "metals_aluminum": {
        "cycle_conclusion": "Metals and aluminum should be treated as a commodity-plus-energy-cost cycle. The positive case needs metals price strength to outweigh China-demand and energy-cost risks.",
        "valuation_context": "Relative valuation needs to be interpreted against input-energy pressure and commodity sensitivity; cheapness alone is weak if metal prices are falling.",
        "market_cycle_watch": "Aluminum, copper, G20 OECD CLI, China OECD CLI, EUR/NOK, relative price, valuation proxy, and World Bank commodity context should be reviewed together.",
    },
    "renewables": {
        "cycle_conclusion": "Renewables remains rate-sensitive and project-economics driven. A cycle turn requires easing rate pressure and evidence that project returns or funding conditions are improving, not just policy optimism.",
        "valuation_context": "Relative price underperformance can signal improving risk/reward only when valuation proxy is low and rates pressure is rolling over.",
        "market_cycle_watch": "Rates pressure, EUR/NOK, Europe and G20 OECD CLI, copper, relative price, valuation proxy, auctions, impairments, and funding spreads are the relevant cycle picture.",
        "why_now": "Rates pressure is a central variable for project economics, so easing rate stress can improve the setup even before reported project margins recover.",
        "key_debates": "Bull case: lower rates and policy support revive project returns.\nBase case: stronger demand offsets some supply-chain friction.\nBear case: power prices, costs, or permitting keep returns below required levels.",
        "catalysts": "Central-bank decisions, power-price updates, auctions, permitting decisions, and project impairment or margin guidance.",
    },
    "norwegian_banks": {
        "cycle_conclusion": "Banks are in a late-credit-cycle watch zone: higher rates support margins but can raise credit-loss and CRE risk. The positive setup is a peak in credit fear without a sharp deterioration in loan quality.",
        "valuation_context": "Relative price strength should be weighed against credit-cost risk. A low valuation proxy is more useful if Norges Bank data and financial-stability evidence show manageable stress.",
        "market_cycle_watch": "Policy rate, CPI, rates pressure, EUR/NOK, relative price, valuation proxy, household credit, CRE exposure, and loan-loss guidance are the key factors.",
    },
    "real_estate": {
        "cycle_conclusion": "Real estate is still a refinancing and yield-spread cycle. The conclusion should stay cautious until rate pressure, transaction evidence, and relative price show that asset-value pressure is no longer worsening.",
        "valuation_context": "A cheap valuation proxy is not enough if higher yields or refinancing stress keep net asset values under pressure.",
        "market_cycle_watch": "Rates pressure, Norges Bank policy rate, CPI, EUR/NOK, relative price, valuation proxy, CRE prices, vacancy, and refinancing events should drive the read.",
        "why_now": "Real estate is highly sensitive to policy rates, inflation, and refinancing conditions; a peak in rate pressure can precede a visible earnings recovery.",
        "key_debates": "Bull case: financing costs fall before asset values reset further.\nBase case: rents cushion valuation pressure.\nBear case: refinancing stress and vacancy risk overwhelm rate relief.",
        "catalysts": "Norges Bank decisions, CPI prints, credit-spread moves, refinancing updates, and transaction evidence.",
    },
    "industrial_tech_exporters": {
        "cycle_conclusion": "Industrial and tech exporters are a mixed global capex, AI, FX, and order-intake lane. A cycle upgrade needs OECD CLI, annual growth, technology capex, and order-intake evidence to confirm relative price strength.",
        "valuation_context": "Valuation should be read against order durability and FX translation. Relative price strength driven only by global tech sentiment may not transfer evenly to Oslo exporters.",
        "market_cycle_watch": "G20 and US OECD CLI, Nasdaq proxy, USD/NOK, EUR/NOK, relative price, valuation proxy, and order-intake commentary should be reviewed together.",
    },
}


def generate_sample_market_cycle(months: int = 72) -> pd.DataFrame:
    end = pd.Timestamp(date.today()).to_period("M").to_timestamp("M")
    dates = pd.date_range(end=end, periods=months, freq="ME")
    rows: list[dict[str, object]] = []

    for subsector in SUBSECTORS:
        phase = (sum(ord(ch) for ch in subsector.slug) % 31) / 5
        beta = _market_beta_for(subsector.slug)
        valuation_base = _valuation_base_for(subsector.slug)
        for idx, observed_at in enumerate(dates):
            benchmark = 100 + idx * 0.42 + math.sin(idx / 11) * 4.5
            subsector_cycle = math.sin(idx / 6.5 + phase) * 9 + math.cos(idx / 19 + phase) * 5
            driver_pressure = math.sin(idx / 8 + phase / 2) * 0.55 + math.cos(idx / 16 + phase) * 0.25
            price_index = benchmark * (0.82 + beta * 0.18) + subsector_cycle + idx * (beta - 1) * 0.16
            relative_price = price_index / benchmark * 100
            valuation_proxy = valuation_base - (relative_price - 100) * 0.38 - driver_pressure * 7
            rows.append(
                {
                    "subsector_slug": subsector.slug,
                    "observed_at": observed_at.date().isoformat(),
                    "price_index": round(max(price_index, 1), 3),
                    "benchmark_index": round(max(benchmark, 1), 3),
                    "relative_price_index": round(max(relative_price, 1), 3),
                    "valuation_proxy": round(max(valuation_proxy, 10), 3),
                    "driver_pressure": round(max(min(driver_pressure, 1), -1), 3),
                    "source": "sample_market_proxy",
                    "notes": "Deterministic sector price and valuation proxy for dashboard development; replace with licensed/public market data when configured.",
                }
            )

    return pd.DataFrame(rows)


def _official_fact_for(subsector) -> dict[str, object]:
    if any(indicator in subsector.proxy_indicators for indicator in ("brent", "wti", "us_crude_stocks", "us_distillate_stocks")):
        return {
            "claim": "Energy-linked cycle work should anchor commodity and inventory context in public price and stock series before drawing subsector conclusions.",
            "source_name": "EIA Open Data",
            "source_url": "https://www.eia.gov/opendata/",
            "source_quality": "official",
            "confidence": 0.8,
        }
    if any(indicator in subsector.proxy_indicators for indicator in ("norges_bank_policy_rate", "norway_cpi", "rates_pressure")):
        return {
            "claim": "Rates-sensitive subsectors should be checked against policy-rate, inflation, and funding-pressure proxies before treating a recovery signal as durable.",
            "source_name": "Norges Bank data",
            "source_url": "https://data.norges-bank.no/api/",
            "source_quality": "official",
            "confidence": 0.78,
        }
    if any(indicator in subsector.proxy_indicators for indicator in ("copper", "aluminum", "china_growth_proxy")):
        return {
            "claim": "Industrial and materials cycle claims need public macro or commodity proxies because free direct subsector demand data can be incomplete.",
            "source_name": "World Bank Indicators",
            "source_url": "https://api.worldbank.org/v2/",
            "source_quality": "official",
            "confidence": 0.72,
        }
    return {
        "claim": "Subsector research evidence should cite public sources and mark unsupported narrative claims as unreviewed until an analyst validates them.",
        "source_name": "Project source policy",
        "source_url": "README.md",
        "source_quality": "sample",
        "confidence": 0.65,
    }


def _debate_fact_for(subsector) -> str:
    return (
        f"The main unresolved debate for {subsector.name.lower()} is whether {subsector.drivers[0]} "
        f"is changing fast enough to matter before {subsector.drivers[-1]} becomes the dominant constraint."
    )


def _source_backed_facts_for(subsector) -> list[dict[str, object]]:
    group = subsector.group
    slug = subsector.slug
    if group == "Shipping":
        return [
            {
                "theme": "market_structure",
                "claim": "UNCTAD treats seaborne trade, fleet ownership, shipbuilding, demolitions, freight rates, and port traffic as core shipping-cycle evidence, so tanker and dry-bulk conclusions should not rely on price momentum alone.",
                "source_name": "UNCTAD Review of Maritime Transport",
                "source_url": "https://unctad.org/topic/transport-and-trade-logistics/review-of-maritime-transport",
                "source_type": "public_report",
                "source_quality": "public_institution",
                "source_date": "2025-09-24",
                "confidence": 0.82,
            },
            {
                "theme": "macro_driver",
                "claim": "The IEA Oil Market Report covers oil supply, demand, inventories, prices, refining activity, and oil trade, making it a relevant public source for tanker, product-tanker, and LNG/LPG shipping cycle checks.",
                "source_name": "IEA Oil Market Report",
                "source_url": "https://www.iea.org/reports/oil-market-report-may-2026",
                "source_type": "public_report",
                "source_quality": "public_institution",
                "source_date": "2026-05-13",
                "confidence": 0.8,
            },
        ]
    if slug in {"offshore_vessels_drilling", "oil_gas_ep", "oil_services"}:
        return [
            {
                "theme": "macro_driver",
                "claim": "IEA oil-market coverage of supply, demand, inventories, prices, refining activity, and oil trade is directly relevant to offshore capex, E&P cash flow, and oil-service order-cycle research.",
                "source_name": "IEA Oil Market Report",
                "source_url": "https://www.iea.org/reports/oil-market-report-may-2026",
                "source_type": "public_report",
                "source_quality": "public_institution",
                "source_date": "2026-05-13",
                "confidence": 0.82,
            },
            {
                "theme": "public_data",
                "claim": "EIA Open Data is an appropriate public anchor for energy prices, inventories, production, and forecast series before turning subsector evidence into a cycle view.",
                "source_name": "EIA Open Data",
                "source_url": "https://www.eia.gov/opendata/",
                "source_type": "public_data",
                "source_quality": "official",
                "source_date": "2026-05-23",
                "confidence": 0.78,
            },
        ]
    if slug == "seafood_aquaculture":
        return [
            {
                "theme": "sector_demand",
                "claim": "Norwegian seafood exports reached a record NOK 181.5 billion in 2025, while salmon export value rose 2% and salmon volume rose 13%, so price/volume mix matters more than headline export value alone.",
                "source_name": "Norwegian Seafood Council",
                "source_url": "https://www.mynewsdesk.com/seafood/pressreleases/price-growth-for-wild-fish-and-increased-salmon-volume-resulted-in-record-value-for-norwegian-seafood-exports-in-2025-3423570",
                "source_type": "public_report",
                "source_quality": "industry_body",
                "source_date": "2026-01-07",
                "confidence": 0.84,
            },
            {
                "theme": "risk",
                "claim": "The same Seafood Council release highlights weak salmon price development and US tariff noise as risks, so a seafood recovery signal should check both demand and price realization.",
                "source_name": "Norwegian Seafood Council",
                "source_url": "https://www.mynewsdesk.com/seafood/pressreleases/price-growth-for-wild-fish-and-increased-salmon-volume-resulted-in-record-value-for-norwegian-seafood-exports-in-2025-3423570",
                "source_type": "public_report",
                "source_quality": "industry_body",
                "source_date": "2026-01-07",
                "confidence": 0.78,
            },
        ]
    if slug == "renewables":
        return [
            {
                "theme": "sector_driver",
                "claim": "IEA Renewables 2025 frames policy changes, manufacturing trends, and financial health as important sector variables, matching the dashboard focus on rates, project returns, and supply chains.",
                "source_name": "IEA Renewables 2025",
                "source_url": "https://www.iea.org/reports/renewables-2025",
                "source_type": "public_report",
                "source_quality": "public_institution",
                "source_date": "2025-10-07",
                "confidence": 0.82,
            },
            {
                "theme": "rates",
                "claim": "Norges Bank's 2026 policy-rate path is relevant for renewables because project economics and discount rates are central to sector valuation.",
                "source_name": "Norges Bank Monetary Policy Report 1/2026",
                "source_url": "https://www.norges-bank.no/en/news-events/publications/Monetary-Policy-Report/2026/mpr-12026/web-report-mpr-12026/",
                "source_type": "official_report",
                "source_quality": "official",
                "source_date": "2026-03-26",
                "confidence": 0.8,
            },
        ]
    if slug in {"norwegian_banks", "real_estate"}:
        return [
            {
                "theme": "rates",
                "claim": "Norges Bank's March 2026 monetary-policy report projected a higher policy-rate path and policy rate between 4.25% and 4.5% at end-2026, directly affecting banks, real estate, and refinancing-sensitive sectors.",
                "source_name": "Norges Bank Monetary Policy Report 1/2026",
                "source_url": "https://www.norges-bank.no/en/news-events/publications/Monetary-Policy-Report/2026/mpr-12026/web-report-mpr-12026/",
                "source_type": "official_report",
                "source_quality": "official",
                "source_date": "2026-03-26",
                "confidence": 0.86,
            },
            {
                "theme": "credit_risk",
                "claim": "Norges Bank Financial Stability Report 2026 H1 describes Norwegian banks' substantial commercial-real-estate exposure and notes that commercial property selling prices have been broadly flat after rising at the beginning of 2025.",
                "source_name": "Norges Bank Financial Stability Report 2026 H1",
                "source_url": "https://www.norges-bank.no/contentassets/6f0e9520ff8344e993289d406e21d1b5/financial-stability-report_1_26.pdf?v=12052026110956",
                "source_type": "official_report",
                "source_quality": "official",
                "source_date": "2026-05-12",
                "confidence": 0.86,
            },
        ]
    if slug in {"metals_aluminum", "dry_bulk"}:
        return [
            {
                "theme": "commodity_cycle",
                "claim": "World Bank Commodity Markets Outlook April 2026 frames energy, metals, fertilizer, and broader commodity prices as a major macro input, so metals and dry-bulk reads should include commodity-price and China-demand context.",
                "source_name": "World Bank Commodity Markets Outlook",
                "source_url": "https://www.worldbank.org/en/research/commodity-markets",
                "source_type": "public_report",
                "source_quality": "public_institution",
                "source_date": "2026-04-28",
                "confidence": 0.82,
            },
            {
                "theme": "macro_risk",
                "claim": "IMF WEO April 2026 provides the global growth and geopolitical-risk backdrop needed before treating industrial commodity moves as a subsector-specific recovery.",
                "source_name": "IMF World Economic Outlook",
                "source_url": "https://www.imf.org/en/publications/weo/issues/2026/04/14/world-economic-outlook-april-2026",
                "source_type": "public_report",
                "source_quality": "public_institution",
                "source_date": "2026-04-14",
                "confidence": 0.78,
            },
        ]
    return [
        {
            "theme": "macro_risk",
            "claim": "IMF WEO April 2026 is a relevant global-growth and geopolitical-risk anchor for exporter-cycle analysis, especially where local subsector data is incomplete.",
            "source_name": "IMF World Economic Outlook",
            "source_url": "https://www.imf.org/en/publications/weo/issues/2026/04/14/world-economic-outlook-april-2026",
            "source_type": "public_report",
            "source_quality": "public_institution",
            "source_date": "2026-04-14",
            "confidence": 0.76,
        },
        {
            "theme": "valuation_context",
            "claim": "Relative price and valuation proxies should be interpreted as screening context only until reliable subsector constituent data or licensed market data is connected.",
            "source_name": "Project publication policy",
            "source_url": "docs/publication_policy.md",
            "source_type": "methodology",
            "source_quality": "sample",
            "source_date": "2026-05-23",
            "confidence": 0.68,
        },
    ]


def _market_beta_for(slug: str) -> float:
    return {
        "crude_tankers": 1.15,
        "product_chemical_tankers": 1.08,
        "dry_bulk": 1.22,
        "lng_lpg_shipping": 1.12,
        "offshore_vessels_drilling": 1.35,
        "oil_gas_ep": 1.18,
        "oil_services": 1.32,
        "seafood_aquaculture": 0.78,
        "metals_aluminum": 1.18,
        "renewables": 1.45,
        "norwegian_banks": 0.82,
        "real_estate": 1.28,
        "industrial_tech_exporters": 1.12,
    }.get(slug, 1.0)


def _valuation_base_for(slug: str) -> float:
    return {
        "renewables": 118,
        "real_estate": 112,
        "offshore_vessels_drilling": 96,
        "oil_services": 102,
        "norwegian_banks": 86,
        "seafood_aquaculture": 94,
    }.get(slug, 100)


def _base_for(slug: str) -> float:
    return {
        "brent": 76,
        "wti": 72,
        "us_natural_gas": 3.2,
        "us_crude_stocks": 430_000,
        "us_distillate_stocks": 116_000,
        "global_pmi": 50,
        "china_growth_proxy": 50,
        "g20_cli": 100,
        "g7_cli": 100,
        "us_cli": 100,
        "china_cli": 100,
        "europe_cli": 100,
        "copper": 100,
        "aluminum": 100,
        "usd_nok": 10.4,
        "eur_nok": 11.5,
        "rates_pressure": 100,
        "norges_bank_policy_rate": 4.2,
        "norway_cpi": 3.4,
        "chicago_fed_nfci": -0.35,
        "st_louis_financial_stress": -0.55,
        "food_price_pressure": 100,
        "nasdaq_proxy": 100,
        "oil_curve_pressure": 50,
    }.get(slug, 100)


def _trend_for(slug: str) -> float:
    return {
        "brent": 0.05,
        "wti": 0.04,
        "global_pmi": 0.01,
        "g20_cli": 0.015,
        "g7_cli": 0.012,
        "us_cli": 0.014,
        "china_cli": 0.006,
        "europe_cli": 0.008,
        "rates_pressure": -0.06,
        "norges_bank_policy_rate": -0.01,
        "norway_cpi": -0.015,
        "chicago_fed_nfci": -0.004,
        "st_louis_financial_stress": -0.006,
        "nasdaq_proxy": 0.18,
        "oil_curve_pressure": 0.04,
    }.get(slug, 0.02)


def _amplitude_for(slug: str) -> float:
    if slug in {"us_crude_stocks", "us_distillate_stocks"}:
        return 18_000
    if slug in {"usd_nok", "eur_nok", "us_natural_gas", "norges_bank_policy_rate", "norway_cpi", "chicago_fed_nfci", "st_louis_financial_stress"}:
        return 0.65
    if slug in {"global_pmi", "china_growth_proxy", "oil_curve_pressure", "g20_cli", "g7_cli", "us_cli", "china_cli", "europe_cli"}:
        return 3.5
    return 12.0
