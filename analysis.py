"""
Trader Performance vs. Bitcoin Market Sentiment Analysis
"""
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats as sps

sns.set_theme(style="whitegrid")
plt.rcParams['figure.dpi'] = 120

import os
ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = ROOT
DATA_DIR = os.path.join(ROOT, 'data')

# ---------------------------------------------------------------
# 1. Load data
# ---------------------------------------------------------------
trades = pd.read_csv(os.path.join(DATA_DIR, 'historical_data.csv'))
sentiment = pd.read_csv(os.path.join(DATA_DIR, 'fear_greed_index.csv'))

trades['Timestamp IST'] = pd.to_datetime(trades['Timestamp IST'], format='%d-%m-%Y %H:%M')
trades['date'] = trades['Timestamp IST'].dt.date
sentiment['date'] = pd.to_datetime(sentiment['date']).dt.date

# Order sentiment classes for plotting
SENT_ORDER = ['Extreme Fear', 'Fear', 'Neutral', 'Greed', 'Extreme Greed']
sentiment['classification'] = pd.Categorical(sentiment['classification'], categories=SENT_ORDER, ordered=True)

# ---------------------------------------------------------------
# 2. Merge trades with sentiment on date
# ---------------------------------------------------------------
df = trades.merge(sentiment[['date', 'classification', 'value']], on='date', how='inner')
df['classification'] = pd.Categorical(df['classification'], categories=SENT_ORDER, ordered=True)

print(f"Trades total: {len(trades):,}")
print(f"Trades matched to a sentiment day: {len(df):,} ({len(df)/len(trades)*100:.1f}%)")
print(f"Date range of trades: {trades['date'].min()} to {trades['date'].max()}")
print(f"Date range of sentiment: {sentiment['date'].min()} to {sentiment['date'].max()}")

df.to_csv(f'{OUT}/merged_trades_sentiment.csv', index=False)

# ---------------------------------------------------------------
# 3. Overall stats by sentiment classification
# ---------------------------------------------------------------
closed = df[df['Closed PnL'] != 0].copy()
closed['is_win'] = closed['Closed PnL'] > 0

by_sent = closed.groupby('classification', observed=True).agg(
    trades=('Closed PnL', 'count'),
    total_pnl=('Closed PnL', 'sum'),
    avg_pnl=('Closed PnL', 'mean'),
    median_pnl=('Closed PnL', 'median'),
    win_rate=('is_win', 'mean'),
    total_volume=('Size USD', 'sum'),
    avg_fee=('Fee', 'mean'),
).round(3)
by_sent['win_rate'] = (by_sent['win_rate']*100).round(2)
print("\n=== Performance by Sentiment Classification ===")
print(by_sent)
by_sent.to_csv(f'{OUT}/stats_by_sentiment.csv')

# ---------------------------------------------------------------
# 4. Daily aggregation: total PnL, volume, win rate, trade count per day + sentiment
# ---------------------------------------------------------------
daily = df.groupby(['date', 'classification'], observed=True).apply(
    lambda g: pd.Series({
        'trades': len(g),
        'total_pnl': g['Closed PnL'].sum(),
        'total_volume': g['Size USD'].sum(),
        'win_rate': (g.loc[g['Closed PnL'] != 0, 'Closed PnL'] > 0).mean() if (g['Closed PnL'] != 0).any() else np.nan,
        'unique_traders': g['Account'].nunique(),
    }), include_groups=False
).reset_index()
daily.to_csv(f'{OUT}/daily_aggregates.csv', index=False)

print("\n=== Daily-level summary by sentiment ===")
print(daily.groupby('classification', observed=True)[['total_pnl','total_volume','win_rate','trades']].mean().round(2))

# ---------------------------------------------------------------
# 5. Per-account behavior by sentiment (leverage proxy via position size, long/short bias)
# ---------------------------------------------------------------
df['is_long'] = df['Direction'].str.contains('Long|Buy', case=False, na=False)
df['is_short'] = df['Direction'].str.contains('Short|Sell', case=False, na=False)

long_short_bias = df.groupby('classification', observed=True).apply(
    lambda g: pd.Series({
        'pct_long_actions': g['is_long'].mean()*100,
        'pct_short_actions': g['is_short'].mean()*100,
        'avg_size_usd': g['Size USD'].mean(),
        'median_size_usd': g['Size USD'].median(),
    }), include_groups=False
).round(2)
print("\n=== Long/Short bias & position sizing by sentiment ===")
print(long_short_bias)
long_short_bias.to_csv(f'{OUT}/long_short_bias.csv')

# ---------------------------------------------------------------
# 6. Top coins traded per sentiment regime
# ---------------------------------------------------------------
top_coins = df.groupby(['classification', 'Coin'], observed=True)['Size USD'].sum().reset_index()
top_coins = top_coins.sort_values(['classification', 'Size USD'], ascending=[True, False])
top5_per_sent = top_coins.groupby('classification', observed=True).head(5)
print("\n=== Top 5 coins by volume per sentiment regime ===")
print(top5_per_sent.to_string(index=False))
top5_per_sent.to_csv(f'{OUT}/top_coins_by_sentiment.csv', index=False)

# ---------------------------------------------------------------
# 7. Account-level performance: does each trader do better in fear or greed?
# ---------------------------------------------------------------
acct_sent = closed.groupby(['Account', 'classification'], observed=True).agg(
    trades=('Closed PnL', 'count'),
    total_pnl=('Closed PnL', 'sum'),
    win_rate=('is_win', 'mean'),
).reset_index()
acct_sent.to_csv(f'{OUT}/account_performance_by_sentiment.csv', index=False)

# Which accounts are most sentiment-sensitive (biggest swing in avg pnl between fear vs greed)
pivot_pnl = closed.groupby(['Account', 'classification'], observed=True)['Closed PnL'].mean().unstack()
if 'Fear' in pivot_pnl.columns and 'Greed' in pivot_pnl.columns:
    pivot_pnl['fear_vs_greed_diff'] = pivot_pnl['Fear'] - pivot_pnl['Greed']
    print("\n=== Accounts with biggest Fear-vs-Greed avg PnL swing (top 10) ===")
    print(pivot_pnl['fear_vs_greed_diff'].abs().sort_values(ascending=False).head(10))
pivot_pnl.to_csv(f'{OUT}/account_fear_vs_greed_pnl.csv')

# ---------------------------------------------------------------
# 8. Correlation between sentiment value (numeric 0-100) and daily metrics
# ---------------------------------------------------------------
daily_corr = daily.merge(sentiment[['date','value']], on='date', how='left')
corr_matrix = daily_corr[['value','total_pnl','total_volume','win_rate','trades','unique_traders']].corr()
print("\n=== Correlation matrix (sentiment value vs daily metrics) ===")
print(corr_matrix['value'].round(3))
corr_matrix.to_csv(f'{OUT}/correlation_matrix.csv')

# ---------------------------------------------------------------
# 9. PLOTS
# ---------------------------------------------------------------

# Plot 1: Avg PnL per trade by sentiment
fig, axes = plt.subplots(1, 2, figsize=(14,5))
order = [c for c in SENT_ORDER if c in by_sent.index]
sns.barplot(x=by_sent.loc[order].index, y=by_sent.loc[order]['avg_pnl'], ax=axes[0], palette='RdYlGn')
axes[0].set_title('Average Closed PnL per Trade by Sentiment')
axes[0].set_ylabel('Avg Closed PnL (USD)')
axes[0].set_xlabel('')
axes[0].tick_params(axis='x', rotation=20)

sns.barplot(x=by_sent.loc[order].index, y=by_sent.loc[order]['win_rate'], ax=axes[1], palette='RdYlGn')
axes[1].set_title('Win Rate (%) by Sentiment')
axes[1].set_ylabel('Win Rate (%)')
axes[1].set_xlabel('')
axes[1].tick_params(axis='x', rotation=20)
plt.tight_layout()
plt.savefig(f'{OUT}/plot1_pnl_winrate_by_sentiment.png')
plt.close()

# Plot 2: Total trading volume by sentiment
fig, ax = plt.subplots(figsize=(8,5))
sns.barplot(x=by_sent.loc[order].index, y=by_sent.loc[order]['total_volume'], ax=ax, palette='coolwarm')
ax.set_title('Total Trading Volume (USD) by Sentiment')
ax.set_ylabel('Total Volume (USD)')
ax.set_xlabel('')
plt.xticks(rotation=20)
plt.tight_layout()
plt.savefig(f'{OUT}/plot2_volume_by_sentiment.png')
plt.close()

# Plot 3: Long vs Short bias
fig, ax = plt.subplots(figsize=(9,5))
lsb = long_short_bias.loc[order]
x = np.arange(len(lsb))
width = 0.35
ax.bar(x - width/2, lsb['pct_long_actions'], width, label='Long %')
ax.bar(x + width/2, lsb['pct_short_actions'], width, label='Short %')
ax.set_xticks(x)
ax.set_xticklabels(lsb.index, rotation=20)
ax.set_ylabel('% of Actions')
ax.set_title('Long vs Short Bias by Sentiment')
ax.legend()
plt.tight_layout()
plt.savefig(f'{OUT}/plot3_long_short_bias.png')
plt.close()

# Plot 4: Daily PnL time series with sentiment overlay
fig, ax1 = plt.subplots(figsize=(14,6))
daily_sorted = daily_corr.sort_values('date')
ax1.plot(daily_sorted['date'], daily_sorted['total_pnl'].rolling(3, min_periods=1).mean(), color='black', label='3-day avg Total PnL')
ax1.set_ylabel('Total Daily PnL (USD, 3d avg)')
ax1.set_xlabel('Date')
ax2 = ax1.twinx()
ax2.plot(daily_sorted['date'], daily_sorted['value'], color='orange', alpha=0.5, label='Sentiment Value')
ax2.set_ylabel('Fear/Greed Value (0-100)')
fig.suptitle('Daily Total PnL vs Market Sentiment Over Time')
fig.legend(loc='upper right')
plt.tight_layout()
plt.savefig(f'{OUT}/plot4_pnl_timeseries.png')
plt.close()

# Plot 5: Correlation heatmap
fig, ax = plt.subplots(figsize=(7,6))
sns.heatmap(corr_matrix, annot=True, cmap='coolwarm', center=0, ax=ax, fmt='.2f')
ax.set_title('Correlation: Sentiment vs Daily Trading Metrics')
plt.tight_layout()
plt.savefig(f'{OUT}/plot5_correlation_heatmap.png')
plt.close()

# Plot 6: Position sizing by sentiment
fig, ax = plt.subplots(figsize=(8,5))
sns.barplot(x=lsb.index, y=lsb['avg_size_usd'], ax=ax, palette='viridis')
ax.set_title('Average Position Size (USD) by Sentiment')
ax.set_ylabel('Avg Size USD')
plt.xticks(rotation=20)
plt.tight_layout()
plt.savefig(f'{OUT}/plot6_position_size_by_sentiment.png')
plt.close()

# =================================================================
# 10. STATISTICAL SIGNIFICANCE TESTING
# =================================================================
print("\n" + "="*60)
print("10. STATISTICAL SIGNIFICANCE TESTING")
print("="*60)

# 10a. Trade-level: are Closed PnL distributions different across regimes?
groups_trade = [closed.loc[closed['classification']==c, 'Closed PnL'].values for c in order]
kw_trade = sps.kruskal(*groups_trade)
print(f"\nKruskal-Wallis (trade-level Closed PnL across 5 regimes): H={kw_trade.statistic:.2f}, p={kw_trade.pvalue:.2e}")

# 10b. Day-level: are daily total_pnl distributions different across regimes? (correct unit of observation)
groups_day = [daily.loc[daily['classification']==c, 'total_pnl'].values for c in order]
kw_day = sps.kruskal(*groups_day)
print(f"Kruskal-Wallis (day-level total PnL across 5 regimes):   H={kw_day.statistic:.2f}, p={kw_day.pvalue:.2e}")

# 10c. Pairwise contrasts of interest (trade-level Mann-Whitney + day-level Mann-Whitney + win-rate proportion z-test)
pairs = [('Fear','Greed'), ('Extreme Fear','Extreme Greed'), ('Extreme Fear','Neutral'),
         ('Fear','Neutral'), ('Greed','Extreme Greed')]

sig_rows = []
for a, b in pairs:
    # trade-level Mann-Whitney on Closed PnL
    ga = closed.loc[closed['classification']==a, 'Closed PnL']
    gb = closed.loc[closed['classification']==b, 'Closed PnL']
    mw_trade = sps.mannwhitneyu(ga, gb, alternative='two-sided')

    # day-level Mann-Whitney on daily total_pnl
    da = daily.loc[daily['classification']==a, 'total_pnl']
    db = daily.loc[daily['classification']==b, 'total_pnl']
    mw_day = sps.mannwhitneyu(da, db, alternative='two-sided') if len(da) > 0 and len(db) > 0 else None

    # win-rate two-proportion z-test
    wins_a, n_a = ga.gt(0).sum(), len(ga)
    wins_b, n_b = gb.gt(0).sum(), len(gb)
    p_pool = (wins_a + wins_b) / (n_a + n_b)
    se = np.sqrt(p_pool*(1-p_pool)*(1/n_a + 1/n_b))
    z = (wins_a/n_a - wins_b/n_b) / se
    p_prop = 2*(1 - sps.norm.cdf(abs(z)))

    sig_rows.append({
        'comparison': f'{a} vs {b}',
        'trade_level_mw_p': mw_trade.pvalue,
        'day_level_mw_p': mw_day.pvalue if mw_day else np.nan,
        'winrate_a_pct': round(wins_a/n_a*100, 2),
        'winrate_b_pct': round(wins_b/n_b*100, 2),
        'winrate_ztest_p': p_prop,
    })

sig_df = pd.DataFrame(sig_rows)
print("\n=== Pairwise significance tests ===")
print(sig_df.to_string(index=False))
sig_df.to_csv(f'{OUT}/significance_tests.csv', index=False)

# 10d. Chi-square: classification vs win/loss (overall independence test)
contingency = pd.crosstab(closed['classification'], closed['is_win'])
chi2, chi2_p, dof, _ = sps.chi2_contingency(contingency)
print(f"\nChi-square (classification x win/loss independence): chi2={chi2:.2f}, dof={dof}, p={chi2_p:.2e}")

with open(f'{OUT}/significance_summary.txt', 'w') as f:
    f.write(f"Kruskal-Wallis trade-level Closed PnL across regimes: H={kw_trade.statistic:.2f}, p={kw_trade.pvalue:.2e}\n")
    f.write(f"Kruskal-Wallis day-level total PnL across regimes:   H={kw_day.statistic:.2f}, p={kw_day.pvalue:.2e}\n")
    f.write(f"Chi-square classification x win/loss: chi2={chi2:.2f}, dof={dof}, p={chi2_p:.2e}\n")

# =================================================================
# 11. RISK-ADJUSTED METRICS (Sharpe / Sortino style)
# =================================================================
print("\n" + "="*60)
print("11. RISK-ADJUSTED METRICS")
print("="*60)

risk_rows = []
for c in order:
    trade_pnl = closed.loc[closed['classification']==c, 'Closed PnL']
    day_pnl = daily.loc[daily['classification']==c, 'total_pnl']
    day_vol = daily.loc[daily['classification']==c, 'total_volume']

    # trade-level risk-adjusted return (dimensionless)
    trade_sharpe = trade_pnl.mean() / trade_pnl.std()

    # day-level Sharpe, annualized as if strategy only traded on days of this regime
    day_sharpe = (day_pnl.mean() / day_pnl.std()) * np.sqrt(252) if day_pnl.std() > 0 else np.nan

    # Sortino: use downside deviation (std of negative returns only) at day level
    downside = day_pnl[day_pnl < 0]
    downside_std = downside.std() if len(downside) > 1 else np.nan
    day_sortino = (day_pnl.mean() / downside_std) * np.sqrt(252) if downside_std and downside_std > 0 else np.nan

    # return on volume traded (edge normalized for bet size)
    pnl_per_volume_bp = (day_pnl.sum() / day_vol.sum()) * 10000  # basis points

    risk_rows.append({
        'classification': c,
        'trade_level_sharpe': round(trade_sharpe, 3),
        'day_level_sharpe_annualized': round(day_sharpe, 2) if pd.notna(day_sharpe) else np.nan,
        'day_level_sortino_annualized': round(day_sortino, 2) if pd.notna(day_sortino) else np.nan,
        'pnl_per_volume_bps': round(pnl_per_volume_bp, 2),
    })

risk_df = pd.DataFrame(risk_rows).set_index('classification')
print(risk_df.to_string())
risk_df.to_csv(f'{OUT}/risk_adjusted_metrics.csv')

fig, axes = plt.subplots(1, 2, figsize=(14,5))
sns.barplot(x=risk_df.index, y=risk_df['day_level_sharpe_annualized'], ax=axes[0], palette='RdYlGn')
axes[0].set_title('Annualized Sharpe Ratio (day-level) by Sentiment')
axes[0].set_ylabel('Sharpe Ratio')
axes[0].tick_params(axis='x', rotation=20)
axes[0].axhline(0, color='black', linewidth=0.8)

sns.barplot(x=risk_df.index, y=risk_df['pnl_per_volume_bps'], ax=axes[1], palette='RdYlGn')
axes[1].set_title('PnL per Volume Traded (bps) by Sentiment')
axes[1].set_ylabel('Basis Points of Volume')
axes[1].tick_params(axis='x', rotation=20)
axes[1].axhline(0, color='black', linewidth=0.8)
plt.tight_layout()
plt.savefig(f'{OUT}/plot7_risk_adjusted.png')
plt.close()

# =================================================================
# 12. LAGGED / PREDICTIVE ANALYSIS (does YESTERDAY's sentiment predict TODAY's performance?)
# =================================================================
print("\n" + "="*60)
print("12. LAGGED / PREDICTIVE ANALYSIS")
print("="*60)

# Build a continuous daily sentiment series and shift by 1 day
sent_full = sentiment[['date','classification','value']].sort_values('date').reset_index(drop=True)
sent_full['prev_classification'] = sent_full['classification'].shift(1)
sent_full['prev_value'] = sent_full['value'].shift(1)

# Recompute daily trading aggregates independent of same-day sentiment merge (pure trades side)
daily_trades_only = trades.groupby('date').apply(
    lambda g: pd.Series({
        'trades': len(g),
        'total_pnl': g['Closed PnL'].sum(),
        'total_volume': g['Size USD'].sum(),
        'win_rate': (g.loc[g['Closed PnL'] != 0, 'Closed PnL'] > 0).mean() if (g['Closed PnL'] != 0).any() else np.nan,
    }), include_groups=False
).reset_index()

lagged = daily_trades_only.merge(sent_full[['date','prev_classification','prev_value']], on='date', how='inner')
lagged['prev_classification'] = pd.Categorical(lagged['prev_classification'], categories=SENT_ORDER, ordered=True)
lagged = lagged.dropna(subset=['prev_classification'])

lagged_by_regime = lagged.groupby('prev_classification', observed=True).agg(
    days=('total_pnl','count'),
    avg_next_day_pnl=('total_pnl','mean'),
    avg_next_day_winrate=('win_rate','mean'),
    avg_next_day_volume=('total_volume','mean'),
).round(3)
lagged_by_regime['avg_next_day_winrate'] = (lagged_by_regime['avg_next_day_winrate']*100).round(2)
print("\n=== Next-day performance conditioned on PRIOR day's sentiment ===")
print(lagged_by_regime.to_string())
lagged_by_regime.to_csv(f'{OUT}/lagged_sentiment_analysis.csv')

# Correlation of lagged sentiment value vs next-day metrics, vs same-day correlation (already in corr_matrix)
lag_corr = lagged[['prev_value','total_pnl','total_volume','win_rate','trades']].corr()['prev_value']
same_day_corr = corr_matrix['value']
compare_corr = pd.DataFrame({
    'same_day_corr': same_day_corr.reindex(['total_pnl','total_volume','win_rate','trades']),
    'next_day_lagged_corr': lag_corr.reindex(['total_pnl','total_volume','win_rate','trades']),
})
print("\n=== Same-day vs. next-day (lagged) correlation with sentiment ===")
print(compare_corr.round(3).to_string())
compare_corr.to_csv(f'{OUT}/same_day_vs_lagged_correlation.csv')

# Kruskal-Wallis: does next-day PnL differ significantly by prior-day regime?
lag_groups = [lagged.loc[lagged['prev_classification']==c, 'total_pnl'].values for c in order if c in lagged['prev_classification'].values]
if len(lag_groups) > 1:
    kw_lag = sps.kruskal(*lag_groups)
    print(f"\nKruskal-Wallis (next-day PnL across prior-day regimes): H={kw_lag.statistic:.2f}, p={kw_lag.pvalue:.2e}")
    with open(f'{OUT}/significance_summary.txt', 'a') as f:
        f.write(f"Kruskal-Wallis next-day PnL across prior-day sentiment regimes: H={kw_lag.statistic:.2f}, p={kw_lag.pvalue:.2e}\n")

fig, ax = plt.subplots(figsize=(9,5))
lag_order = [c for c in order if c in lagged_by_regime.index]
sns.barplot(x=lag_order, y=lagged_by_regime.loc[lag_order]['avg_next_day_pnl'], ax=ax, palette='RdYlGn')
ax.set_title("Next-Day Total PnL Conditioned on Prior Day's Sentiment")
ax.set_ylabel('Avg Next-Day Total PnL (USD)')
ax.set_xlabel("Prior day's sentiment classification")
plt.xticks(rotation=20)
plt.tight_layout()
plt.savefig(f'{OUT}/plot8_lagged_sentiment_pnl.png')
plt.close()

# =================================================================
# 13. ROBUSTNESS CHECKS
# =================================================================
print("\n" + "="*60)
print("13. ROBUSTNESS CHECKS")
print("="*60)

robust_rows = []
for c in order:
    sub = closed[closed['classification']==c]
    n_days = daily.loc[daily['classification']==c, 'date'].nunique()

    # top-account concentration of total PnL magnitude
    acct_abs_pnl = sub.groupby('Account')['Closed PnL'].sum().abs().sort_values(ascending=False)
    total_abs = sub['Closed PnL'].sum()
    top1_share = (acct_abs_pnl.iloc[0] / abs(total_abs) * 100) if len(acct_abs_pnl) > 0 and total_abs != 0 else np.nan
    top3_share = (acct_abs_pnl.iloc[:3].sum() / abs(total_abs) * 100) if len(acct_abs_pnl) >= 3 and total_abs != 0 else np.nan

    # winsorized (1%/99%) avg PnL vs raw avg PnL -- sensitivity to outlier trades
    lo, hi = sub['Closed PnL'].quantile([0.01, 0.99])
    winsorized = sub['Closed PnL'].clip(lo, hi)

    robust_rows.append({
        'classification': c,
        'unique_days': n_days,
        'raw_avg_pnl': round(sub['Closed PnL'].mean(), 2),
        'winsorized_avg_pnl_1_99pct': round(winsorized.mean(), 2),
        'top1_account_pnl_share_pct': round(top1_share, 1) if pd.notna(top1_share) else np.nan,
        'top3_account_pnl_share_pct': round(top3_share, 1) if pd.notna(top3_share) else np.nan,
    })

robust_df = pd.DataFrame(robust_rows).set_index('classification')
print(robust_df.to_string())
robust_df.to_csv(f'{OUT}/robustness_checks.csv')

print("\nAll outputs saved to", OUT)
