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
    direct_evidence_required: tuple[str, ...] = ()
    parent_slug: str = ""


SUBSECTORS: tuple[Subsector, ...] = (
    Subsector("crude_tankers", "Crude tankers", "Shipping", ("route freight", "ton-miles", "fleet supply", "oil flows"), ("brent", "wti", "us_crude_stocks", "g20_cli", "global_equity_proxy", "geopolitical_risk"), ("oil flows", "geopolitics", "global growth"), "proxy_only", "Treat macro and oil signals as a research trigger, not tanker utilisation.", ("route spot/time-charter rates", "ton-miles", "fleet/orderbook and scrapping", "utilisation")),
    Subsector("product_tankers", "Product tankers", "Shipping", ("product trade", "refinery dislocation", "ton-miles", "fleet supply"), ("brent", "us_distillate_stocks", "g20_cli", "global_equity_proxy", "geopolitical_risk"), ("refining", "oil products", "trade disruption"), "proxy_only", "Product-tanker economics must be separated from chemical parcel shipping.", ("route product-tanker rates", "refinery runs and cracks", "product trade/stock flows", "fleet/orderbook"), "product_chemical_tankers"),
    Subsector("chemical_tankers", "Chemical tankers", "Shipping", ("chemical trade", "specialised fleet", "contracts", "parcel utilisation"), ("g20_cli", "europe_cli", "china_cli", "brent", "global_equity_proxy"), ("industrial production", "chemical demand", "global trade"), "proxy_only", "Chemical-tanker supply and contract structures differ from clean-product tankers.", ("chemical trade volumes", "parcel freight/contract rates", "specialised fleet supply", "utilisation"), "product_chemical_tankers"),
    Subsector("dry_bulk", "Dry bulk", "Shipping", ("iron ore", "coal", "grain", "China demand", "fleet supply"), ("copper", "aluminum", "g20_cli", "china_cli", "china_growth_proxy", "em_equity_proxy"), ("China activity", "industrial commodities", "global trade"), "proxy_only", "Commodity and China signals are background until freight and fleet data confirm.", ("segment freight/day rates", "commodity ton-miles", "China steel/property activity", "fleet/orderbook and scrapping")),
    Subsector("lng_shipping", "LNG shipping", "Shipping", ("regional gas spreads", "liquefaction capacity", "Asian demand", "fleet deliveries"), ("us_natural_gas", "brent", "g20_cli", "japan_equity_proxy", "geopolitical_risk"), ("gas security", "Asian demand", "rates"), "proxy_only", "LNG must be assessed through gas spreads, export capacity and LNG fleet balance.", ("LNG charter rates", "TTF/JKM/Henry Hub spreads", "liquefaction/export starts", "fleet/orderbook and utilisation"), "lng_lpg_shipping"),
    Subsector("lpg_shipping", "LPG shipping", "Shipping", ("propane exports", "petrochemical demand", "arbitrage", "VLGC supply"), ("us_natural_gas", "brent", "china_cli", "em_equity_proxy", "geopolitical_risk"), ("US exports", "Asian petrochemicals", "trade routes"), "proxy_only", "LPG shipping is a separate cargo and fleet cycle from LNG.", ("VLGC spot/time-charter rates", "US/Middle East LPG exports", "propane/naphtha spreads", "fleet/orderbook"), "lng_lpg_shipping"),
    Subsector("offshore_vessels", "Offshore service vessels", "Energy services", ("offshore capex", "vessel utilisation", "day rates", "fleet reactivation"), ("brent", "g20_cli", "global_equity_proxy", "rates_pressure", "geopolitical_risk"), ("E&P capex", "oil price", "financing"), "proxy_only", "OSV economics require vessel-specific utilisation and day-rate evidence.", ("OSV day rates", "fleet utilisation", "tenders/contracts", "reactivation/scrapping"), "offshore_vessels_drilling"),
    Subsector("offshore_drilling", "Offshore drilling", "Energy services", ("rig demand", "utilisation", "day rates", "contract backlog"), ("brent", "g20_cli", "global_equity_proxy", "rates_pressure", "geopolitical_risk"), ("E&P capex", "oil price", "financing"), "proxy_only", "Rig markets have different contract duration and supply from offshore vessels.", ("rig day rates", "marketed utilisation", "contract backlog", "newbuild/reactivation/scrap supply"), "offshore_vessels_drilling"),
    Subsector("oil_gas_ep", "Oil and gas E&P", "Energy", ("forward prices", "realised prices", "costs", "reserves", "balance sheet"), ("brent", "wti", "us_natural_gas", "usd_nok", "geopolitical_risk"), ("oil and gas", "FX", "geopolitics"), "proxy_only", "Commodity context is necessary but not sufficient for E&P equity-cycle claims.", ("forward curve and hedging", "realised price and lifting cost", "capex/reserve replacement", "free cash flow and leverage")),
    Subsector("oil_services", "Oil services", "Energy services", ("client capex", "orders", "backlog", "pricing", "margins"), ("brent", "g20_cli", "global_equity_proxy", "rates_pressure", "usd_nok"), ("E&P capex", "global growth", "financing"), "proxy_only", "Client spending and order conversion must confirm macro signals.", ("order intake/backlog", "book-to-bill", "utilisation/pricing", "margins and cash conversion")),
    Subsector("seafood_aquaculture", "Seafood and aquaculture", "Seafood", ("salmon prices", "biomass", "mortality", "feed", "regulation", "FX"), ("food_price_pressure", "usd_nok", "eur_nok", "g20_cli", "europe_cli"), ("consumer demand", "FX", "feed cost"), "proxy_only", "Fish meal and FX are inputs, not a seafood operating-cycle measure.", ("salmon spot/realised price", "biomass and harvest", "mortality/disease", "feed conversion/cost and regulatory capacity")),
    Subsector("metals_aluminum", "Metals and aluminium", "Materials", ("metal price", "power cost", "China output", "capacity utilisation", "margins"), ("aluminum", "copper", "china_cli", "g20_cli", "europe_cli"), ("China activity", "power costs", "industrial demand"), "proxy_only", "Price momentum requires cost, inventory and utilisation confirmation.", ("LME price/premium and inventories", "power/alumina costs", "China/global output and utilisation", "producer margins")),
    Subsector("renewables", "Renewables", "Energy transition", ("power/PPA price", "WACC", "project returns", "grid", "balance sheet"), ("rates_pressure", "us_real_10y_yield", "europe_cli", "copper", "global_equity_proxy"), ("real rates", "policy", "power markets"), "proxy_only", "Lower rates alone do not prove improving project economics.", ("auction/PPA/power prices", "project IRR/WACC", "backlog/cancellations", "impairments, cash conversion and leverage")),
    Subsector("industrial_exporters", "Industrial exporters", "Industrials", ("orders", "backlog", "global capex", "FX", "margins"), ("g20_cli", "europe_cli", "copper", "usd_nok", "eur_nok", "global_equity_proxy"), ("global capex", "Europe", "FX"), "proxy_only", "Industrial orders and backlog must confirm global leading indicators.", ("orders and book-to-bill", "backlog and cancellations", "export mix/FX sensitivity", "margins and cash conversion"), "industrial_tech_exporters"),
    Subsector("technology_exporters", "Technology exporters", "Technology", ("semiconductor/AI cycle", "orders", "book-to-bill", "valuation", "FX"), ("nasdaq_proxy", "global_equity_proxy", "us_cli", "g20_cli", "usd_nok"), ("AI capex", "global technology", "rates"), "proxy_only", "Technology duration and semiconductor cycles should not be merged with general industrials.", ("orders/book-to-bill", "semiconductor/AI end demand", "earnings revisions", "valuation and concentration"), "industrial_tech_exporters"),
    Subsector("norwegian_banks", "Norwegian banks", "Financials", ("net interest income", "funding", "loan growth", "credit losses", "capital"), ("norges_bank_policy_rate", "norway_cpi", "chicago_fed_nfci", "us_high_yield_spread", "eur_nok"), ("Norwegian rates", "credit", "housing/CRE"), "proxy_only", "Banks require bank-specific earnings, asset-quality, funding and capital evidence.", ("NIM and deposit beta", "loan growth and Stage 2/3", "losses and CRE exposure", "funding/liquidity and CET1")),
    Subsector("income_real_estate", "Income-producing real estate", "Real estate", ("rents", "vacancy", "cap rates", "LTV", "refinancing"), ("norges_bank_policy_rate", "rates_pressure", "us_real_10y_yield", "us_high_yield_spread", "norway_cpi"), ("rates", "credit", "inflation"), "proxy_only", "Stabilised income property differs from development risk.", ("rents and vacancy", "cap rates/transaction values", "LTV and interest coverage", "debt maturities/refinancing spreads"), "real_estate"),
    Subsector("property_developers", "Property developers", "Real estate", ("new-home demand", "construction cost", "project finance", "pre-sales", "liquidity"), ("norges_bank_policy_rate", "rates_pressure", "us_high_yield_spread", "norway_cpi", "eur_nok"), ("rates", "credit", "construction"), "proxy_only", "Developers carry project, sales and refinancing risks not shared by stabilised landlords.", ("pre-sales and starts", "construction costs", "project margins", "liquidity, covenants and refinancing"), "real_estate"),
)


LEGACY_SUBSECTOR_MAP: dict[str, tuple[str, ...]] = {
    "product_chemical_tankers": ("product_tankers", "chemical_tankers"),
    "lng_lpg_shipping": ("lng_shipping", "lpg_shipping"),
    "offshore_vessels_drilling": ("offshore_vessels", "offshore_drilling"),
    "industrial_tech_exporters": ("industrial_exporters", "technology_exporters"),
    "real_estate": ("income_real_estate", "property_developers"),
}


def subsector_by_slug() -> dict[str, Subsector]:
    return {subsector.slug: subsector for subsector in SUBSECTORS}
