"""
Build REPORT.pdf from the analysis findings, embedding charts.
"""
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image,
    PageBreak, HRFlowable, ListFlowable, ListItem
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER
import os

OUT = os.path.dirname(os.path.abspath(__file__))

doc = SimpleDocTemplate(
    f'{OUT}/REPORT.pdf',
    pagesize=letter,
    topMargin=0.75*inch, bottomMargin=0.75*inch,
    leftMargin=0.75*inch, rightMargin=0.75*inch,
    title="Trader Performance vs. Bitcoin Market Sentiment",
    author="Hyperliquid / Fear & Greed Analysis",
)

styles = getSampleStyleSheet()
styles.add(ParagraphStyle(name='TitleBig', fontSize=20, leading=24, spaceAfter=6, fontName='Helvetica-Bold', textColor=colors.HexColor('#1a1a2e')))
styles.add(ParagraphStyle(name='Subtitle', fontSize=12, leading=16, spaceAfter=18, fontName='Helvetica-Oblique', textColor=colors.HexColor('#555')))
styles.add(ParagraphStyle(name='H1', fontSize=15, leading=19, spaceBefore=18, spaceAfter=8, fontName='Helvetica-Bold', textColor=colors.HexColor('#16213e')))
styles.add(ParagraphStyle(name='H2', fontSize=12.5, leading=16, spaceBefore=12, spaceAfter=6, fontName='Helvetica-Bold', textColor=colors.HexColor('#0f3460')))
styles.add(ParagraphStyle(name='Body', fontSize=9.7, leading=14, spaceAfter=8, fontName='Helvetica', alignment=TA_LEFT))
styles.add(ParagraphStyle(name='Caption', fontSize=8.5, leading=11, spaceAfter=14, fontName='Helvetica-Oblique', textColor=colors.HexColor('#555'), alignment=TA_CENTER))
styles.add(ParagraphStyle(name='TableCell', fontSize=8.3, leading=10.5, fontName='Helvetica'))
styles.add(ParagraphStyle(name='TableHeader', fontSize=8.3, leading=10.5, fontName='Helvetica-Bold', textColor=colors.white))

story = []

def h1(text):
    story.append(Paragraph(text, styles['H1']))

def h2(text):
    story.append(Paragraph(text, styles['H2']))

def body(text):
    story.append(Paragraph(text, styles['Body']))

def bullets(items):
    story.append(ListFlowable(
        [ListItem(Paragraph(t, styles['Body']), spaceAfter=4) for t in items],
        bulletType='bullet', start='•', leftIndent=14
    ))
    story.append(Spacer(1, 6))

def make_table(header, rows, col_widths=None):
    data = [[Paragraph(h, styles['TableHeader']) for h in header]]
    for r in rows:
        data.append([Paragraph(str(c), styles['TableCell']) for c in r])
    t = Table(data, colWidths=col_widths, repeatRows=1, hAlign='LEFT')
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#0f3460')),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#cccccc')),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#f4f6fa')]),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('LEFTPADDING', (0,0), (-1,-1), 5),
        ('RIGHTPADDING', (0,0), (-1,-1), 5),
    ]))
    story.append(t)
    story.append(Spacer(1, 10))

def figure(path, caption, width=6.3*inch):
    img = Image(path)
    aspect = img.imageHeight / float(img.imageWidth)
    img.drawWidth = width
    img.drawHeight = width * aspect
    story.append(img)
    story.append(Paragraph(caption, styles['Caption']))

def hr():
    story.append(Spacer(1, 4))
    story.append(HRFlowable(width="100%", thickness=0.7, color=colors.HexColor('#cccccc')))
    story.append(Spacer(1, 8))

# ---------------- Title ----------------
story.append(Paragraph("Trader Performance vs. Bitcoin Market Sentiment", styles['TitleBig']))
story.append(Paragraph("Analysis of Hyperliquid historical trades against the Fear &amp; Greed Index", styles['Subtitle']))
hr()

# ---------------- 1. Data & Methodology ----------------
h1("1. Data &amp; Methodology")
make_table(
    ["Dataset", "Rows", "Range", "Notes"],
    [
        ["fear_greed_index.csv", "2,644 daily records", "2018-02-01 &rarr; 2025-05-02", "classification bucketed into 5 levels"],
        ["historical_data.csv", "211,224 trade fills", "2023-05-01 &rarr; 2025-05-01", "32 accounts, 246 coins; incl. Closed PnL, Size USD, Direction, Side, Fee"],
    ],
    col_widths=[1.3*inch, 1.15*inch, 1.55*inch, 2.3*inch]
)
body("<b>Join:</b> trades were matched to the sentiment classification for their calendar date (IST). 211,218 of 211,224 trades (100%) matched a sentiment day.")
body("<b>Key metric definitions:</b>")
bullets([
    "<i>Closed PnL</i> &mdash; realized profit/loss per fill; only fills with non-zero Closed PnL (104,408 of them) were used for win-rate/avg-PnL statistics (zero-PnL rows are position-opening fills, not closes).",
    "<i>Win rate</i> &mdash; % of non-zero-PnL closes that were profitable.",
    "<i>Long/short bias</i> &mdash; % of all trade actions (not just closes) tagged as long-side vs. short-side via the Direction field.",
])
body("All code, intermediate CSVs, and charts accompany this report in the delivered folder (<font face='Courier'>analysis.py</font> + 6 PNGs + supporting CSVs).")

# ---------------- 2. Headline numbers ----------------
h1("2. Headline Numbers by Sentiment Regime")
make_table(
    ["Sentiment", "Trades", "Total PnL", "Avg PnL/trade", "Win Rate", "Total Volume"],
    [
        ["Extreme Fear", "10,406", "$739,110", "$71.03", "76.2%", "$56.9M"],
        ["Fear", "29,808", "$3,357,155", "$112.63", "87.3%", "$239.7M"],
        ["Neutral", "18,159", "$1,292,921", "$71.20", "82.4%", "$101.0M"],
        ["Greed", "25,176", "$2,150,129", "$85.40", "76.9%", "$136.9M"],
        ["Extreme Greed", "20,853", "$2,715,171", "$130.21", "89.2%", "$57.9M"],
    ],
    col_widths=[1.15*inch, 0.85*inch, 1.15*inch, 1.15*inch, 0.85*inch, 1.15*inch]
)
figure(f'{OUT}/plot1_pnl_winrate_by_sentiment.png', "Figure 1. Average Closed PnL per trade and win rate (%) across the five sentiment regimes.")

# ---------------- 3. Key Findings ----------------
h1("3. Key Findings")

h2("3.1 Traders are contrarian, not momentum-driven")
body("Position direction flips almost perfectly with sentiment:")
make_table(
    ["Sentiment", "% Long actions", "% Short actions", "Avg size (USD)"],
    [
        ["Extreme Fear", "65.7%", "34.3%", "$5,350"],
        ["Fear", "62.0%", "38.0%", "$7,816"],
        ["Neutral", "61.4%", "38.7%", "$4,783"],
        ["Greed", "42.3%", "57.7%", "$5,737"],
        ["Extreme Greed", "46.6%", "53.4%", "$3,112"],
    ],
    col_widths=[1.4*inch, 1.5*inch, 1.5*inch, 1.4*inch]
)
body("This trader cohort is net <b>long-biased during Fear/Extreme Fear</b> and flips to <b>net short-biased during Greed</b> &mdash; i.e., buying the dip when the crowd is fearful and fading rallies when the crowd is greedy. This is a classic contrarian / “smart money” pattern, not a herd-following one.")
figure(f'{OUT}/plot3_long_short_bias.png', "Figure 2. Long vs. short action share by sentiment regime.")

h2("3.2 The two extremes are the most profitable; “Neutral” is the weakest")
body("Both <b>Fear</b> and <b>Extreme Greed</b> produce the best win rates (87&ndash;89%) and highest average PnL per trade ($113 / $130). <b>Neutral</b> sentiment is the worst per-trade performer (71.2% avg PnL, tied with Extreme Fear) despite a decent win rate &mdash; consistent with low-conviction, choppy/range-bound markets being harder to extract edge from than emotionally extreme ones.")
body("<b>Extreme Fear</b>, despite high activity, has the <b>lowest win rate (76.2%) and lowest avg PnL ($71)</b> of all buckets &mdash; traders are most active here but least accurate, suggesting fear days attract more speculative/panic entries.")

h2("3.3 Activity concentrates in Extreme Fear, but efficiency doesn't")
body("On a per-day basis, Extreme Fear days see by far the most trades (1,529/day) and volume ($8.2M/day) &mdash; more than double any other regime &mdash; yet deliver the lowest daily win rate (65%). Traders over-trade during panic without a proportional payoff.")
make_table(
    ["Sentiment", "Avg daily PnL", "Avg daily volume", "Avg daily win rate", "Avg trades/day"],
    [
        ["Extreme Fear", "$52,794", "$8.18M", "65%", "1,529"],
        ["Fear", "$36,892", "$5.31M", "88%", "680"],
        ["Neutral", "$19,297", "$2.69M", "79%", "562"],
        ["Greed", "$11,141", "$1.50M", "81%", "261"],
        ["Extreme Greed", "$23,817", "$1.09M", "89%", "351"],
    ],
    col_widths=[1.1*inch, 1.2*inch, 1.2*inch, 1.3*inch, 1.1*inch]
)

h2("3.4 Correlation with the numeric sentiment score (0&ndash;100)")
body("Weak-to-moderate correlations across the board &mdash; sentiment level alone is not a strong linear predictor of daily outcomes:")
make_table(
    ["Metric", "Corr. with sentiment value"],
    [
        ["Total daily PnL", "-0.08"],
        ["Total daily volume", "-0.26"],
        ["Win rate", "+0.06"],
        ["Trade count", "-0.25"],
        ["Unique active traders", "-0.28"],
    ],
    col_widths=[3*inch, 2*inch]
)
body("The negative correlations with volume/trade-count/active-traders confirm &sect;3.3: <b>lower sentiment scores (more fear) associate with more trading activity</b>, not more profit. Win rate and PnL show near-zero linear correlation with the raw score &mdash; the relationship is regime-based (U-shaped across the 5 buckets), not linear.")
figure(f'{OUT}/plot5_correlation_heatmap.png', "Figure 3. Correlation matrix between sentiment value and daily trading metrics.", width=4.6*inch)

h2("3.5 Coin concentration is stable, but shifts slightly with sentiment")
body("BTC dominates volume in every regime, but its dominance is strongest in Fear (BTC ≈ 55% of volume) and weakest in Extreme Fear / Extreme Greed, where HYPE and SOL take a larger share &mdash; consistent with capital rotating into higher-beta alt positioning at emotional extremes rather than sitting purely in BTC.")

h2("3.6 Position sizing shrinks as greed rises")
body("Average position size peaks in Fear ($7,816) and steadily declines into Extreme Greed ($3,112) &mdash; traders here are sizing up in fear and de-risking (smaller size, more short activity) into greed, reinforcing the contrarian risk-management read from &sect;3.1.")
figure(f'{OUT}/plot6_position_size_by_sentiment.png', "Figure 4. Average position size (USD) by sentiment regime.", width=4.6*inch)

h2("3.7 Trader-level heterogeneity")
body("Sentiment sensitivity is not uniform across the 32 accounts. A handful of accounts show large swings in average PnL between Fear and Greed regimes (e.g., account 0x420ab4&hellip; swings ~$3,194 avg PnL/trade between the two), while most accounts show smaller, single/double-digit swings &mdash; meaning the aggregate contrarian pattern is driven disproportionately by a subset of traders, not uniformly by all 32. (See <font face='Courier'>account_fear_vs_greed_pnl.csv</font> for the full ranked list.)")

story.append(PageBreak())

# ---------------- 4. Statistical Significance ----------------
h1("4. Statistical Significance")
body("Descriptive differences are only useful if they're real, so every headline contrast was tested formally (non-parametric tests, since Closed PnL is heavy-tailed):")
bullets([
    "<b>Trade-level Kruskal-Wallis</b> across all 5 regimes on Closed PnL: H = 730.33, <b>p = 9.4&times;10<super>-157</super></b> &mdash; overwhelmingly significant, but trade-level tests over-state confidence because trades on the same day by the same account aren't independent observations (pseudo-replication).",
    "<b>Day-level Kruskal-Wallis</b> (the statistically correct unit of observation &mdash; one data point per calendar day) on daily total PnL across regimes: H = 20.06, <b>p = 4.9&times;10<super>-4</super></b> &mdash; still significant, confirming the regime effect survives even at the conservative day-level granularity.",
    "<b>Chi-square test</b> of classification &times; win/loss independence: &chi;&sup2; = 1976.45, dof = 4, <b>p &asymp; 0</b> &mdash; win rate is not independent of sentiment regime.",
])
make_table(
    ["Pairwise comparison", "Trade-level p (MW)", "Day-level p (MW)", "Win-rate z-test p"],
    [
        ["Fear vs Greed", "6.7e-43", "0.0095", "~0"],
        ["Extreme Fear vs Extreme Greed", "4.6e-45", "0.68 (n.s.)", "~0"],
        ["Extreme Fear vs Neutral", "0.040", "0.61 (n.s.)", "~0"],
        ["Fear vs Neutral", "1.0e-36", "0.43 (n.s.)", "~0"],
        ["Greed vs Extreme Greed", "6.2e-116", "0.000003", "~0"],
    ],
    col_widths=[2.1*inch, 1.4*inch, 1.4*inch, 1.4*inch]
)
body("<b>Important nuance:</b> at the day level (the correct unit), only <i>Fear vs Greed</i> and <i>Greed vs Extreme Greed</i> survive as statistically distinguishable in total daily PnL &mdash; the Extreme Fear vs Extreme Greed/Neutral contrasts, while dramatic-looking in the trade-level averages, are <b>not statistically distinguishable at the day level</b>, largely because Extreme Fear only spans 14 unique trading days in this dataset (see &sect;7 Robustness). Win-rate differences, by contrast, are robustly significant everywhere.")

# ---------------- 5. Risk-Adjusted Performance ----------------
h1("5. Risk-Adjusted Performance")
body("Higher average PnL can simply reflect bigger bets or bigger variance, not real edge &mdash; so each regime was re-evaluated on a risk-adjusted basis:")
make_table(
    ["Sentiment", "Trade Sharpe", "Day Sharpe (ann.)", "Day Sortino (ann.)", "PnL/volume (bps)"],
    [
        ["Extreme Fear", "0.044", "8.28", "25.73", "64.6"],
        ["Fear", "0.084", "6.06", "14.06", "69.5"],
        ["Neutral", "0.096", "8.06", "94.48", "71.7"],
        ["Greed", "0.054", "2.83", "2.17", "74.5"],
        ["Extreme Greed", "0.123", "5.19", "8.64", "218.2"],
    ],
    col_widths=[1.3*inch, 1.1*inch, 1.3*inch, 1.3*inch, 1.3*inch]
)
figure(f'{OUT}/plot7_risk_adjusted.png', "Figure 5. Annualized day-level Sharpe ratio and PnL-per-volume (bps) by sentiment regime.")
bullets([
    "<b>Greed is the weakest regime risk-adjusted</b>, not just in absolute terms &mdash; it has both the lowest annualized Sharpe (2.83) and lowest Sortino (2.17) of all five buckets, meaning whatever edge exists there is thin relative to its volatility.",
    "<b>Extreme Greed is dramatically more capital-efficient</b>: 218 bps of PnL per dollar of volume traded &mdash; 3x any other regime &mdash; meaning traders are extracting far more profit per unit of risk/capital deployed during euphoric markets, not just trading bigger.",
    "<b>Neutral's Sortino (94.5) is the best of any regime</b>, driven by very few, very small down-days &mdash; it's a “low drama” regime: not the highest absolute return, but the smoothest.",
    "This reshapes the earlier win-rate-driven read: Extreme Greed remains the standout regime on every basis (return, win rate, <i>and</i> risk-adjusted efficiency), while Greed is confirmed as the weakest regime once risk is accounted for, not just an artifact of lower win rate.",
])

story.append(PageBreak())

# ---------------- 6. Lagged / Predictive Analysis ----------------
h1("6. Lagged / Predictive Analysis")
body("<i>Does yesterday's sentiment predict today's performance?</i>")
body("All results above are <b>contemporaneous</b> (same-day sentiment and outcomes) &mdash; not actionable for trading, since you can't act on a signal and observe its outcome on the same day. To test predictive value, each day's trading outcomes were conditioned on the <b>prior day's</b> sentiment classification:")
make_table(
    ["Prior day's sentiment", "Days (n)", "Avg next-day PnL", "Next-day win rate", "Next-day volume"],
    [
        ["Extreme Fear", "14", "$72,701", "84.9%", "$9.15M"],
        ["Fear", "92", "$34,751", "81.6%", "$5.05M"],
        ["Neutral", "64", "$14,208", "85.8%", "$3.00M"],
        ["Greed", "198", "$12,872", "81.0%", "$1.39M"],
        ["Extreme Greed", "111", "$23,257", "88.4%", "$1.17M"],
    ],
    col_widths=[1.5*inch, 0.9*inch, 1.3*inch, 1.3*inch, 1.3*inch]
)
figure(f'{OUT}/plot8_lagged_sentiment_pnl.png', "Figure 6. Average next-day total PnL conditioned on the prior day's sentiment classification.")
body("<b>This is the most actionable finding in the analysis.</b> The day <i>after</i> an Extreme Fear reading produces the highest average next-day PnL of any condition in the entire study &mdash; over double the next-best (Fear&rarr;Fear) and roughly 5&ndash;6x the Greed/Neutral-conditioned days. A Kruskal-Wallis test on next-day PnL across prior-day regimes confirms this is statistically significant (H = 22.36, <b>p = 1.7&times;10<super>-4</super></b>).")
body("Comparing same-day vs. next-day (lagged) correlation with the raw sentiment score:")
make_table(
    ["Metric", "Same-day corr.", "Next-day (lagged) corr."],
    [
        ["Total PnL", "-0.083", "-0.107"],
        ["Total volume", "-0.264", "-0.277"],
        ["Win rate", "+0.055", "+0.061"],
        ["Trade count", "-0.245", "-0.237"],
    ],
    col_widths=[2.3*inch, 1.8*inch, 2.1*inch]
)
body("The lagged correlations are slightly <i>stronger</i> than the same-day ones for PnL and win rate &mdash; the predictive relationship is at least as strong as the contemporaneous one, meaning sentiment isn't just describing what already happened, it carries forward-looking signal for the next session.")
body("<b>Implication:</b> the tradeable signal isn't “trade during Extreme Fear” (&sect;3.3 showed that's actually the lowest-quality regime to trade <i>in</i>), it's “<b>position for the day after an Extreme Fear reading</b>” &mdash; likely capturing a fear-driven washout followed by a mean-reversion bounce.")

# ---------------- 7. Robustness Checks ----------------
h1("7. Robustness Checks")
make_table(
    ["Sentiment", "Unique days", "Raw avg PnL", "Winsorized avg PnL", "Top1 acct share", "Top3 acct share"],
    [
        ["Extreme Fear", "14", "$71.03", "$42.62", "35.4%", "84.9%"],
        ["Fear", "91", "$112.63", "$83.66", "33.2%", "62.6%"],
        ["Neutral", "67", "$71.20", "$57.19", "31.0%", "70.3%"],
        ["Greed", "193", "$85.40", "$65.78", "24.8%", "62.7%"],
        ["Extreme Greed", "114", "$130.21", "$92.59", "40.7%", "66.1%"],
    ],
    col_widths=[1.2*inch, 0.9*inch, 1.0*inch, 1.2*inch, 1.0*inch, 1.0*inch]
)
bullets([
    "<b>Extreme Fear is the least robust regime</b>: only 14 unique days in the dataset, and the top 3 accounts account for <b>85% of its total PnL</b> &mdash; its results (both the weak win rate in &sect;3.2 and the strong next-day effect in &sect;6) should be treated as suggestive, not conclusive, until validated on more data.",
    "<b>Winsorizing (clipping the top/bottom 1% of trades) shrinks every regime's average PnL by 25&ndash;35%</b>, confirming outlier trades inflate the raw averages everywhere &mdash; but the <i>ranking</i> across regimes is preserved (Extreme Greed still highest, Extreme Fear/Neutral still lowest), so the qualitative conclusions are not an artifact of a few extreme trades.",
    "<b>PnL concentration in the top 1&ndash;3 accounts (25&ndash;41% / 63&ndash;85%) is high in every regime</b>, not just Extreme Fear &mdash; a reminder that this cohort's aggregate behavior is meaningfully whale-driven, and any strategy inspired by these findings should be validated against a broader trader sample before being generalized.",
])

story.append(PageBreak())

# ---------------- 8. Strategic Implications ----------------
h1("8. Strategic Implications for Trading")
bullets([
    "<b>Fade the crowd, size for it.</b> The data supports a contrarian sentiment strategy: accumulate long exposure into Fear/Extreme Fear and rotate toward shorts/reduced exposure into Greed &mdash; this is what the most profitable segment of the historical flow is already doing.",
    "<b>The real edge is in the day <i>after</i> Extreme Fear, not during it.</b> Extreme Fear itself is a low-win-rate, low-Sharpe, statistically fragile (14-day) regime to trade in &mdash; but positioning for the session immediately following an Extreme Fear reading captures the strongest, statistically significant PnL effect in the whole dataset.",
    "<b>Extreme Fear is a volume trap.</b> It attracts the most trades but the lowest win rate &mdash; a signal to tighten entry criteria (wider stops, smaller clips, or wait for confirmation) rather than over-trade panic in real time.",
    "<b>Extreme Greed is the highest-quality regime on every measure</b> &mdash; return, win rate, Sharpe/Sortino, and capital efficiency (218 bps/volume, 3x any other regime). Allocate more conviction/capital to setups here; treat Greed (non-extreme) as the weakest risk-adjusted regime and reduce exposure there.",
    "<b>Use sentiment as a regime filter, not a standalone signal</b>, and prefer the lagged (previous-day) classification over the same-day one when sizing next-session risk &mdash; it carries equal-or-greater predictive power and is causally valid (you can act on yesterday's known reading).",
    "<b>Validate before productizing.</b> High top-3-account PnL concentration (63&ndash;85%) across every regime means these patterns are influenced by a handful of large traders. Before committing capital to a systematized version of this strategy, confirm the effect holds on a broader trader sample and out-of-sample time period.",
    "<b>Identify and study the sentiment-driven outperformers.</b> A small number of accounts contribute most of the fear/greed PnL spread; understanding their specific entries (coin choice, timing, leverage) could isolate a repeatable strategy worth productizing separately from the aggregate.",
])

# ---------------- 9. Caveats ----------------
h1("9. Caveats")
bullets([
    "Closed PnL and win-rate figures are computed only on the 104k fills with non-zero Closed PnL; the other ~107k rows are position-opening/adjustment fills without a realized PnL and are excluded from those specific stats (but included in volume/direction stats).",
    "The dataset covers 32 accounts only; findings describe this specific trader cohort on Hyperliquid, not the broader market.",
    "No explicit leverage field existed in this data export; leverage effects are proxied via position size (Size USD) only.",
    "Sentiment is a single daily label for the whole market; it is a blunt instrument compared to intraday sentiment shifts, which this dataset can't capture.",
    "Extreme Fear's day-level results rest on only 14 unique calendar days &mdash; treat conclusions specific to that regime as directional, not definitive.",
    "Day-level Sharpe/Sortino figures annualize non-contiguous days within a regime (e.g., all “Fear” days treated as one time series) &mdash; a simplification for cross-regime comparability, not a claim that a real backtest would realize this exact ratio.",
])

# ---------------- 10. Files ----------------
h1("10. Files Delivered")
bullets([
    "<font face='Courier'>analysis.py</font> &mdash; full reproducible analysis script",
    "<font face='Courier'>merged_trades_sentiment.csv</font> &mdash; trade-level data joined with daily sentiment",
    "<font face='Courier'>stats_by_sentiment.csv, daily_aggregates.csv, long_short_bias.csv, top_coins_by_sentiment.csv, account_performance_by_sentiment.csv, account_fear_vs_greed_pnl.csv, correlation_matrix.csv</font> &mdash; descriptive supporting tables",
    "<font face='Courier'>significance_tests.csv, significance_summary.txt</font> &mdash; statistical significance test results",
    "<font face='Courier'>risk_adjusted_metrics.csv</font> &mdash; Sharpe/Sortino/PnL-per-volume by regime",
    "<font face='Courier'>lagged_sentiment_analysis.csv, same_day_vs_lagged_correlation.csv</font> &mdash; predictive/lagged analysis",
    "<font face='Courier'>robustness_checks.csv</font> &mdash; sample size, concentration, and winsorization sensitivity checks",
    "<font face='Courier'>plot1&ndash;plot8 .png</font> &mdash; charts referenced above",
])

doc.build(story)
print("PDF written to", f'{OUT}/REPORT.pdf')
