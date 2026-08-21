# Model Governance and Evidence Basis

Updated 2026-08-21. This document is the audit trail for why an input exists, what it can support, and what it cannot support.

## Construct map

| Construct | Evidence basis | Implementation | Boundary |
|---|---|---|---|
| Growth-cycle turning points | The OECD designs CLIs to anticipate turning points in activity relative to trend and describes them as qualitative, not quantitative forecasts. | CLI level is converted to distance from 100; changes supply momentum. Countries collapse into one CLI family. | Revisions are material near the end of the sample. A CLI is not PMI, GDP growth, or a recession probability. |
| Inflation and policy | CPI is converted to twelve-month inflation. BIS centrally selected policy-rate histories provide a comparable cross-country layer. | Six inflation regions and ten relevant policy-rate histories. | Headline CPI is not core or wage inflation. Policy-rate levels alone do not encode neutral rates or forward guidance. |
| Yield curve and real rates | Estrella and Mishkin document forecasting information in the US yield curve; real yields capture discount-rate pressure. | US 10y, real 10y and 10y-2y are kept as separate families. | The curve is context, not an automatic recession signal; rapid re-steepening and inversion can mean different things. |
| Financial conditions and credit | Chicago Fed NFCI is a broad standardized conditions index. Gilchrist and Zakrajsek document information in credit spreads for future activity. | NFCI, STLFSI, high-yield and investment-grade spreads, and broad dollar. | Public OAS series are not the excess bond premium and are US-centric. Correlation is not causation. |
| Market momentum and participation | Cross-sectional and time-series momentum have extensive empirical literature; breadth/participation can qualify index strength. | Twelve-month returns, bounded standardized momentum, VIX and adjusted-close equal-weight relative performance. | The screener does not claim a calibrated momentum premium. RSP/SPY is leadership, not true breadth. |
| Valuation | Long-horizon valuation can frame risk and prospective returns. | Aggregate US market-cap-to-GDP is context only. | It is not a short-term timing tool and cannot proxy sector valuation. |
| Commodities and inventories | Prices and inventories reflect different parts of supply-demand balance. | World Bank commodity prices and direct EIA crude/distillate inventories are separate families. | Brent-WTI is a cross-benchmark differential, not futures-curve backwardation or contango. |
| Geopolitical risk | Caldara and Iacoviello's peer-reviewed news-based GPR measure is associated with lower investment/employment and downside risk. | Native monthly GPR level, lower-is-better polarity. | It is media-based, globally aggregated, revised/method-dependent, and not a complete geopolitical scenario model. |
| Institutional outlooks | Multilateral and BIS reports are primary policy/macro sources; bank and manager reports are attributed house views. IMF evaluations find forecast performance broadly comparable with private consensus and document difficulty around recessions. | Reviewed official URLs, publication dates, horizons, source tiers, categorical views and dispersion. Non-scoring. | Consensus is not independent validation. Shared information, assumptions, incentives and herding reduce effective sample independence. |
| Sector cycles | Industry cycles require direct price/relative return, earnings, revision, valuation and operating evidence. | Macro-driver research ranking only; phase is blocked by an evidence gate in live mode. | No direct sector evidence means no asserted investable sector-cycle phase. |

## Composite-score governance

The research-priority output is a transparent heuristic. It is not trained on returns and therefore must not be read as expected return, probability of outperformance or empirical confidence.

- Inputs are transformed by explicit contracts before percentile and momentum calculations.
- Minimum transformed histories are 36 monthly, 16 quarterly or eight annual observations.
- Daily and weekly series are reduced to month-end before scoring.
- Each economic family gets one averaged contribution, limiting double counting from correlated countries or aliases.
- Mixed-polarity inputs cannot create a positive tailwind automatically.
- Stale inputs are displayed but excluded from the dimension score.
- Sector data support is capped at 45% while direct sector evidence is absent.
- Reviewed prose and institutional outlooks never enter numeric scoring.

The next empirical step is a point-in-time vintage database, pre-specified phase rules, transaction-cost-aware sector benchmarks and true out-of-sample tests. Until then, archive replay tests software consistency only.

## Primary and scientific references

- [OECD Composite Leading Indicators](https://www.oecd.org/en/data/datasets/oecd-composite-leading-indicators-clis.html)
- [OECD guide to interpreting CLIs](https://www.oecd.org/content/dam/oecd/en/data/methods/Interpreting_OECD_Composite_Leading_Indicators.pdf)
- [BIS central-bank policy-rate dataset documentation](https://www.bis.org/statistics/cbpol/cbpol_doc.pdf)
- [Chicago Fed NFCI methodology](https://www.chicagofed.org/research/data/nfci/about)
- [Estrella and Mishkin, The Yield Curve as a Predictor of U.S. Recessions](https://www.newyorkfed.org/research/current_issues/ci2-7.html)
- [Gilchrist and Zakrajsek, Credit Spreads and Business Cycle Fluctuations](https://www.aeaweb.org/articles?id=10.1257/aer.102.4.1692)
- [Jegadeesh and Titman, Profitability of Momentum Strategies](https://www.nber.org/papers/w7159)
- [Caldara and Iacoviello, Measuring Geopolitical Risk](https://www.aeaweb.org/articles?id=10.1257/aer.20191823)
- [IMF Independent Evaluation Office, quality of IMF forecasts](https://www.elibrary.imf.org/display/book/9781475599510/ch004.xml)
- [OECD/EU/JRC Handbook on Constructing Composite Indicators](https://doi.org/10.1787/9789264043466-en)

## Outlook-source register

The governed CSV includes current reviewed publications from the IMF, World Bank, OECD, BIS, BlackRock, J.P. Morgan, Goldman Sachs, Morgan Stanley and Vanguard. The report presents each institution separately, preserves publication dates and horizons, and reports dispersion rather than converting views into a synthetic forecast.
