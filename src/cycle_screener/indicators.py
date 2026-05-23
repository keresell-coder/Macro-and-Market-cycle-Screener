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
    IndicatorDefinition("us_crude_stocks", "World oil price average", "world_bank_commodity", "CRUDE_PETRO", "USD/bbl", "lower_tailwind", "Oil-market pressure proxy used until keyless inventory data is available."),
    IndicatorDefinition("us_distillate_stocks", "Heating oil futures proxy", "yahoo_chart", "HO=F", "USD/gal", "lower_tailwind", "Product-market distillate/fuel proxy."),
    IndicatorDefinition("global_pmi", "Global growth proxy", "world_bank_indicator", "WLD/NY.GDP.MKTP.KD.ZG", "%", "higher_tailwind", "Global growth proxy from World Bank Indicators."),
    IndicatorDefinition("china_growth_proxy", "China growth proxy", "world_bank_indicator", "CHN/NY.GDP.MKTP.KD.ZG", "%", "higher_tailwind", "China demand proxy from World Bank Indicators."),
    IndicatorDefinition("copper", "Copper price proxy", "world_bank_commodity", "COPPER", "USD/metric ton", "higher_tailwind", "Industrial metals proxy."),
    IndicatorDefinition("aluminum", "Aluminum price proxy", "world_bank_commodity", "ALUMINUM", "USD/metric ton", "higher_tailwind", "Aluminum cycle proxy."),
    IndicatorDefinition("usd_nok", "USD/NOK", "norges_bank_csv", "EXR/B.USD.NOK.SP", "FX", "mixed", "Export and commodity translation proxy."),
    IndicatorDefinition("eur_nok", "EUR/NOK", "norges_bank_csv", "EXR/B.EUR.NOK.SP", "FX", "mixed", "European export and domestic pressure proxy."),
    IndicatorDefinition("rates_pressure", "US 10-year Treasury yield proxy", "yahoo_chart", "^TNX", "%", "lower_tailwind", "Global rates headwind proxy."),
    IndicatorDefinition("norges_bank_policy_rate", "Norges Bank policy rate", "norges_bank_csv", "IR/B.KPRA.RR", "%", "lower_tailwind", "Norwegian rate pressure."),
    IndicatorDefinition("norway_cpi", "Norway CPI", "ssb_cpi", "03013/TOTAL/KpiIndMnd", "index", "lower_tailwind", "Inflation pressure proxy."),
    IndicatorDefinition("food_price_pressure", "Fish meal price proxy", "world_bank_commodity", "FISH_MEAL", "USD/metric ton", "mixed", "Seafood demand and input-cost proxy."),
    IndicatorDefinition("nasdaq_proxy", "NASDAQ Composite", "yahoo_chart", "^IXIC", "index", "mixed", "Global technology and AI sentiment proxy."),
    IndicatorDefinition("oil_curve_pressure", "Brent-WTI spread proxy", "derived_public", "brent-wti", "USD/bbl", "higher_tailwind", "Oil-market pressure proxy derived from public Brent and WTI series."),
)


def indicator_by_slug() -> dict[str, IndicatorDefinition]:
    return {indicator.slug: indicator for indicator in INDICATORS}
