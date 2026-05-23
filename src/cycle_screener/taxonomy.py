from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Subsector:
    slug: str
    name: str
    group: str
    drivers: tuple[str, ...]
    proxy_indicators: tuple[str, ...]
    macro_sensitivities: tuple[str, ...]
    data_confidence: str
    thesis_prompt: str


SUBSECTORS: tuple[Subsector, ...] = (
    Subsector(
        "crude_tankers",
        "Crude tankers",
        "Shipping",
        ("fleet supply", "ton-mile demand", "oil trade disruption", "scrapping"),
        ("brent", "wti", "us_crude_stocks", "global_pmi", "usd_nok"),
        ("oil price", "geopolitics", "global growth", "rates"),
        "medium",
        "Recovery setups usually combine weak recent freight/proxy momentum with improving oil trade volumes or disruption-led ton-miles.",
    ),
    Subsector(
        "product_chemical_tankers",
        "Product and chemical tankers",
        "Shipping",
        ("refinery dislocation", "product inventories", "ton-mile demand", "fleet supply"),
        ("brent", "us_distillate_stocks", "global_pmi", "usd_nok"),
        ("oil products", "global growth", "geopolitics"),
        "medium",
        "Look for inventory normalization, refinery outages, and trade-route changes before equity enthusiasm returns.",
    ),
    Subsector(
        "dry_bulk",
        "Dry bulk",
        "Shipping",
        ("iron ore", "coal", "grain", "China property and stimulus", "fleet supply"),
        ("copper", "aluminum", "global_pmi", "china_growth_proxy"),
        ("China growth", "industrial metals", "rates"),
        "low",
        "Free freight data is limited, so V1 relies on industrial commodity and growth proxies.",
    ),
    Subsector(
        "lng_lpg_shipping",
        "LNG/LPG shipping",
        "Shipping",
        ("gas spreads", "export capacity", "Asian demand", "fleet deliveries"),
        ("us_natural_gas", "brent", "global_pmi", "usd_nok"),
        ("energy security", "gas prices", "rates"),
        "low",
        "Cycle turns often show up through gas spreads, export capacity, and vessel supply timing.",
    ),
    Subsector(
        "offshore_vessels_drilling",
        "Offshore vessels and drilling",
        "Energy services",
        ("offshore capex", "rig utilization", "dayrates", "oil company cash flow"),
        ("brent", "oil_curve_pressure", "global_pmi", "usd_nok"),
        ("oil price", "E&P capex", "rates"),
        "medium",
        "A durable recovery needs oil company capex discipline to loosen while asset supply remains tight.",
    ),
    Subsector(
        "oil_gas_ep",
        "Oil and gas E&P",
        "Energy",
        ("oil price", "gas price", "reserve replacement", "tax regime", "FX"),
        ("brent", "wti", "us_natural_gas", "usd_nok"),
        ("oil price", "gas price", "geopolitics", "NOK"),
        "high",
        "E&P tends to rerate before reported earnings when commodity prices and forward curves move together.",
    ),
    Subsector(
        "oil_services",
        "Oil services",
        "Energy services",
        ("order intake", "offshore capex", "margins", "backlog quality"),
        ("brent", "global_pmi", "usd_nok", "rates_pressure"),
        ("oil capex", "rates", "global growth"),
        "medium",
        "The strongest setups appear when order momentum improves before margins are fully visible.",
    ),
    Subsector(
        "seafood_aquaculture",
        "Seafood and aquaculture",
        "Seafood",
        ("salmon prices", "biomass", "disease", "feed costs", "regulation", "FX"),
        ("food_price_pressure", "usd_nok", "eur_nok", "global_pmi"),
        ("consumer demand", "NOK", "regulation", "feed costs"),
        "low",
        "V1 uses FX and food-price proxies until direct salmon-price feeds are added.",
    ),
    Subsector(
        "metals_aluminum",
        "Metals and aluminum",
        "Materials",
        ("aluminum price", "energy costs", "China demand", "industrial cycle"),
        ("aluminum", "copper", "global_pmi", "eur_nok"),
        ("China growth", "energy prices", "industrial production"),
        "medium",
        "Recovery is more credible when metals prices, PMIs, and energy-cost pressure improve together.",
    ),
    Subsector(
        "renewables",
        "Renewables",
        "Energy transition",
        ("rates", "power prices", "policy", "project returns", "supply chains"),
        ("rates_pressure", "eur_nok", "global_pmi", "copper"),
        ("rates", "policy", "power prices"),
        "medium",
        "Lower rate pressure and improving project economics matter more than broad green-equity sentiment.",
    ),
    Subsector(
        "norwegian_banks",
        "Norwegian banks",
        "Financials",
        ("credit losses", "net interest margin", "housing", "NOK rates", "funding spreads"),
        ("norges_bank_policy_rate", "norway_cpi", "rates_pressure", "eur_nok"),
        ("rates", "credit cycle", "housing", "NOK"),
        "medium",
        "A recovery setup usually needs credit fear to peak before earnings estimates trough.",
    ),
    Subsector(
        "real_estate",
        "Real estate",
        "Real estate",
        ("rates", "credit spreads", "rents", "asset values", "refinancing"),
        ("rates_pressure", "norges_bank_policy_rate", "norway_cpi", "eur_nok"),
        ("rates", "inflation", "credit"),
        "medium",
        "The sector improves when rate pressure rolls over before refinancing stress becomes permanent.",
    ),
    Subsector(
        "industrial_tech_exporters",
        "Industrial and tech exporters",
        "Industrials/technology",
        ("global capex", "AI/tech cycle", "NOK", "order intake", "semis"),
        ("global_pmi", "nasdaq_proxy", "usd_nok", "eur_nok"),
        ("global growth", "technology capex", "FX"),
        "low",
        "Use as a broad early-warning lane for export demand and technology-cycle spillovers.",
    ),
)


def subsector_by_slug() -> dict[str, Subsector]:
    return {subsector.slug: subsector for subsector in SUBSECTORS}

