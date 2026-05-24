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


INDICATORS: tuple[IndicatorDefinition, ...] = (
    IndicatorDefinition("brent", "Brent crude oil", "world_bank_commodity", "CRUDE_BRENT", "USD/bbl", "mixed", "Oil price proxy for energy and shipping demand."),
    IndicatorDefinition("wti", "WTI crude oil", "world_bank_commodity", "CRUDE_WTI", "USD/bbl", "mixed", "US oil price proxy."),
    IndicatorDefinition("us_natural_gas", "US natural gas", "world_bank_commodity", "NGAS_US", "USD/MMBtu", "mixed", "Gas-market pressure proxy."),
    IndicatorDefinition("us_crude_stocks", "World oil price average proxy", "world_bank_commodity", "CRUDE_PETRO", "USD/bbl", "lower_tailwind", "Backward-compatible slug; this is a World Bank oil price proxy, not crude inventory data."),
    IndicatorDefinition("us_distillate_stocks", "Heating oil futures proxy", "yahoo_chart", "HO=F", "USD/gal", "lower_tailwind", "Product-market fuel proxy; not a distillate inventory feed."),
    IndicatorDefinition("global_pmi", "Global annual GDP growth proxy", "world_bank_indicator", "WLD/NY.GDP.MKTP.KD.ZG", "%", "higher_tailwind", "World Bank annual real GDP growth for the world aggregate; not PMI or CLI data."),
    IndicatorDefinition("china_growth_proxy", "China annual GDP growth proxy", "world_bank_indicator", "CHN/NY.GDP.MKTP.KD.ZG", "%", "higher_tailwind", "World Bank annual real GDP growth for China; not PMI or CLI data."),
    IndicatorDefinition("g20_cli", "G20 OECD CLI", "dbnomics_oecd_cli", "G20.M.LI...AA...H", "index", "higher_tailwind", "Monthly OECD Composite Leading Indicator for the G20, accessed through the DB.nomics mirror of OECD data."),
    IndicatorDefinition("g7_cli", "G7 OECD CLI", "dbnomics_oecd_cli", "G7.M.LI...AA...H", "index", "higher_tailwind", "Monthly OECD Composite Leading Indicator for the G7, accessed through the DB.nomics mirror of OECD data."),
    IndicatorDefinition("us_cli", "US OECD CLI", "dbnomics_oecd_cli", "USA.M.LI...AA...H", "index", "higher_tailwind", "Monthly OECD Composite Leading Indicator for the United States, accessed through the DB.nomics mirror of OECD data."),
    IndicatorDefinition("china_cli", "China OECD CLI", "dbnomics_oecd_cli", "CHN.M.LI...AA...H", "index", "higher_tailwind", "Monthly OECD Composite Leading Indicator for China, accessed through the DB.nomics mirror of OECD data."),
    IndicatorDefinition("europe_cli", "Major Europe OECD CLI", "dbnomics_oecd_cli", "G4E.M.LI...AA...H", "index", "higher_tailwind", "Monthly OECD Composite Leading Indicator for the major four European countries, accessed through the DB.nomics mirror of OECD data."),
    IndicatorDefinition("copper", "Copper price proxy", "world_bank_commodity", "COPPER", "USD/metric ton", "higher_tailwind", "Industrial metals proxy."),
    IndicatorDefinition("aluminum", "Aluminum price proxy", "world_bank_commodity", "ALUMINUM", "USD/metric ton", "higher_tailwind", "Aluminum cycle proxy."),
    IndicatorDefinition("usd_nok", "USD/NOK", "norges_bank_csv", "EXR/B.USD.NOK.SP", "FX", "mixed", "Export and commodity translation proxy."),
    IndicatorDefinition("eur_nok", "EUR/NOK", "norges_bank_csv", "EXR/B.EUR.NOK.SP", "FX", "mixed", "European export and domestic pressure proxy."),
    IndicatorDefinition("rates_pressure", "US 10-year Treasury yield proxy", "yahoo_chart", "^TNX", "%", "lower_tailwind", "Global rates headwind proxy."),
    IndicatorDefinition("norges_bank_policy_rate", "Norges Bank policy rate", "norges_bank_csv", "IR/B.KPRA.RR", "%", "lower_tailwind", "Norwegian rate pressure."),
    IndicatorDefinition("norway_cpi", "Norway CPI", "ssb_cpi", "03013/TOTAL/KpiIndMnd", "index", "lower_tailwind", "Inflation pressure proxy."),
    IndicatorDefinition("food_price_pressure", "Fish meal price proxy", "world_bank_commodity", "FISH_MEAL", "USD/metric ton", "mixed", "Seafood demand and input-cost proxy."),
    IndicatorDefinition("nasdaq_proxy", "NASDAQ Composite chart proxy", "yahoo_chart", "^IXIC", "index", "mixed", "Global technology and AI sentiment proxy from a public market chart endpoint."),
    IndicatorDefinition("oil_curve_pressure", "Brent-WTI spread proxy", "derived_public", "brent-wti", "USD/bbl", "higher_tailwind", "Oil-market pressure proxy derived from public Brent and WTI series."),
)

PUBLIC_INDICATOR_SLUGS = {
    "global_pmi": "global_growth_proxy",
    "us_crude_stocks": "world_oil_price_proxy",
    "us_distillate_stocks": "heating_oil_futures_proxy",
}


def indicator_by_slug() -> dict[str, IndicatorDefinition]:
    return {indicator.slug: indicator for indicator in INDICATORS}


def public_indicator_slug(slug: str) -> str:
    return PUBLIC_INDICATOR_SLUGS.get(slug, slug)
