from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SourceDefinition:
    slug: str
    name: str
    url: str
    source_type: str
    access: str
    notes: str


SOURCE_DEFINITIONS: tuple[SourceDefinition, ...] = (
    SourceDefinition("fred_public", "FRED public CSV downloads", "https://fred.stlouisfed.org/graph/fredgraph.csv", "download", "public", "Keyless public CSV downloads for macro, rates, commodities, FX, and market proxies."),
    SourceDefinition("fred", "FRED API", "https://fred.stlouisfed.org/docs/api/fred/", "api", "free_key", "Optional API path for richer FRED metadata; not required for the default refresh."),
    SourceDefinition("world_bank", "World Bank Indicators", "https://api.worldbank.org/v2/", "api", "public", "Global macro indicators."),
    SourceDefinition("world_bank_commodities", "World Bank Pink Sheet", "https://www.worldbank.org/en/research/commodity-markets", "download", "public", "Monthly commodity prices for energy, metals, agriculture, and food/input proxies."),
    SourceDefinition("eia", "EIA Open Data", "https://www.eia.gov/opendata/", "api", "free_key", "Energy prices, inventories, production, forecasts."),
    SourceDefinition("ecb", "ECB Data Portal", "https://data-api.ecb.europa.eu/service/", "api", "public", "European rates and macro series."),
    SourceDefinition("ssb", "Statistics Norway", "https://data.ssb.no/api/v0/en/table/", "api", "public", "Norwegian macro statistics."),
    SourceDefinition("norges_bank", "Norges Bank", "https://data.norges-bank.no/api/", "api", "public", "Rates and exchange rates."),
    SourceDefinition("yahoo_chart", "Yahoo chart data", "https://query1.finance.yahoo.com/v8/finance/chart/", "market_data", "public", "Public chart endpoint used only for broad traded proxies when official keyless data is not wired."),
    SourceDefinition("dnb_carnegie", "DNB Carnegie", "https://www.dnb.no/markets/analyser/economic-outlook", "research", "public", "Public macro and market outlook pages."),
    SourceDefinition("blackrock", "BlackRock Investment Institute", "https://www.blackrock.com/institutions/en-us/insights/blackrock-investment-institute/global-investment-outlook", "research", "public", "Public global investment outlook."),
    SourceDefinition("jpmorgan", "J.P. Morgan", "https://www.jpmorgan.com/insights/markets-and-economy/outlook/2026-market-outlook", "research", "public", "Public market outlook pages."),
    SourceDefinition("goldman_sachs", "Goldman Sachs", "https://www.goldmansachs.com/insights/outlooks/2026-outlooks", "research", "public", "Public outlook pages."),
    SourceDefinition("ubs", "UBS wealth management insights", "https://www.ubs.com/lu/en/wealthmanagement/insights.html", "research", "public", "Public investment outlook and wealth-management insights page; access failures should be reported, not bypassed."),
    SourceDefinition("euronext", "Euronext Market Data", "https://www.euronext.com/en/data/market-data/how-access-market-data", "market_data", "licensed", "Use only licensed or terms-compliant data."),
    SourceDefinition("baltic_exchange", "Baltic Exchange", "https://www.balticexchange.com/en/data-services.html", "shipping_data", "licensed", "Shipping indices are generally licensed."),
    SourceDefinition("drewry", "Drewry Trackers", "https://www.drewry.co.uk/trackers-and-indices", "shipping_data", "public_limited", "Some public tracker pages are available."),
)


RESEARCH_KEYWORDS: dict[str, tuple[str, ...]] = {
    "shipping": ("shipping", "freight", "tanker", "dry bulk", "container", "fleet"),
    "energy": ("oil", "gas", "energy", "opec", "brent", "lng"),
    "rates": ("rates", "inflation", "central bank", "yield", "higher for longer"),
    "growth": ("growth", "recession", "pmi", "cycle", "soft landing"),
    "china": ("china", "property", "stimulus", "industrial"),
    "technology": ("technology", "ai", "semiconductor", "capex"),
}
