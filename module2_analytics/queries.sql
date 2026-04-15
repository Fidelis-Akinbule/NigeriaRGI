-- ============================================================
-- NigeriaRGI  |  Module 2  |  queries.sql
-- 12 named queries across 6 analytical sections
-- All queries run against master_table in nigeria_rgi.db
-- ============================================================



-- SECTION 2.1  REVENUE PERFORMANCE BY STATE & LGA

-- Q01: Total revenue by state, ranked highest to lowest
-- Business use: identify which states are driving the region's
-- revenue and which are underperforming relative to their size.
SELECT
    state,
    ROUND(SUM(total_revenue_ngn) / 1e6, 2)         AS total_revenue_NGN_millions,
    ROUND(SUM(data_revenue_ngn) / 1e6, 2)           AS data_revenue_NGN_millions,
    ROUND(SUM(voice_revenue_ngn) / 1e6, 2)          AS voice_revenue_NGN_millions,
    ROUND(SUM(vas_revenue_ngn) / 1e6, 2)            AS vas_revenue_NGN_millions,
    ROUND(AVG(arpu_monthly_est), 0)                 AS avg_monthly_arpu_NGN
FROM master_table
GROUP BY state
ORDER BY total_revenue_NGN_millions DESC;


-- Q02: Top 10 LGAs by total revenue
-- Business use: identify the highest-value micro-markets for
-- priority resourcing, channel investment, and retention focus.
SELECT
    state,
    lga,
    ROUND(SUM(total_revenue_ngn) / 1e6, 2)         AS total_revenue_NGN_millions,
    ROUND(AVG(arpu_monthly_est), 0)                 AS avg_monthly_arpu_NGN,
    ROUND(AVG(penetration_rate) * 100, 1)           AS avg_penetration_pct
FROM master_table
GROUP BY state, lga
ORDER BY total_revenue_NGN_millions DESC
LIMIT 10;


-- SECTION 2.2  SUBSCRIBER BASE & PENETRATION

-- Q03: Subscriber summary by state
-- Business use: assess subscriber scale, churn pressure, and
-- market share headroom across the region.
SELECT
    state,
    SUM(active_subs)                                AS total_active_subs,
    SUM(new_subs)                                   AS total_new_subs,
    SUM(churned_subs)                               AS total_churned_subs,
    ROUND(AVG(penetration_rate) * 100, 1)           AS avg_penetration_pct,
    MAX(lga_population)                             AS largest_lga_population
FROM master_table
GROUP BY state
ORDER BY total_active_subs DESC;


-- Q04: LGAs with lowest penetration rate (whitespace candidates)
-- Business use: surface demand gaps where population density is
-- high but subscriber penetration is low — prime GTM targets.
SELECT
    state,
    lga,
    lga_population,
    ROUND(AVG(penetration_rate) * 100, 1)           AS avg_penetration_pct,
    ROUND(AVG(income_index), 1)                     AS avg_income_index,
    urban_flag
FROM master_table
GROUP BY state, lga
ORDER BY avg_penetration_pct ASC
LIMIT 15;

-- SECTION 2.3  QoE & NETWORK HEALTH

-- Q05: QoE compliance rate by state
-- Business use: measure how often each state meets NCC thresholds
-- (MOS > 3.5, drop call rate < 2%). Non-compliance drives churn.
SELECT
    state,
    COUNT(*)                                        AS total_records,
    SUM(qoe_below_threshold)                        AS qoe_breach_days,
    ROUND(100.0 * SUM(qoe_below_threshold)
          / COUNT(*), 1)                            AS qoe_breach_pct,
    ROUND(AVG(avg_mos_score), 2)                    AS avg_mos_score,
    ROUND(AVG(avg_drop_call_rate) * 100, 2)         AS avg_drop_call_rate_pct,
    ROUND(AVG(avg_congestion_pct), 1)               AS avg_congestion_pct,
    ROUND(AVG(avg_download_speed), 1)               AS avg_download_speed_mbps
FROM master_table
GROUP BY state
ORDER BY qoe_breach_pct DESC;


-- Q06: 10 worst LGAs by average drop call rate
-- Business use: prioritise network investment in LGAs where call
-- quality is degrading subscriber experience and driving churn.
SELECT
    state,
    lga,
    ROUND(AVG(avg_drop_call_rate) * 100, 2)         AS avg_drop_call_rate_pct,
    ROUND(AVG(avg_mos_score), 2)                    AS avg_mos_score,
    ROUND(AVG(avg_congestion_pct), 1)               AS avg_congestion_pct,
    SUM(qoe_below_threshold)                        AS qoe_breach_days
FROM master_table
GROUP BY state, lga
ORDER BY avg_drop_call_rate_pct DESC
LIMIT 10;

-- SECTION 2.4  SITE PROFITABILITY


-- Q07: Site profitability ranking by LGA
-- Business use: identify which LGAs generate strong returns per
-- site and which are profit drains requiring opex review.
SELECT
    state,
    lga,
    site_count,
    ROUND(AVG(daily_revenue_per_site), 0)           AS avg_daily_rev_per_site_NGN,
    ROUND(AVG(daily_opex_per_site), 0)              AS avg_daily_opex_per_site_NGN,
    ROUND(AVG(site_profit_proxy), 0)                AS avg_daily_profit_per_site_NGN,
    ROUND(AVG(total_monthly_opex) / 1e6, 2)         AS avg_monthly_opex_NGN_millions
FROM master_table
GROUP BY state, lga
ORDER BY avg_daily_profit_per_site_NGN DESC;


-- Q08: LGAs where opex exceeds revenue per site (loss-making)
-- Business use: escalation list for RGM — sites running at a
-- loss require immediate opex renegotiation or decommissioning.
SELECT
    state,
    lga,
    site_count,
    ROUND(AVG(daily_revenue_per_site), 0)           AS avg_daily_rev_per_site_NGN,
    ROUND(AVG(daily_opex_per_site), 0)              AS avg_daily_opex_per_site_NGN,
    ROUND(AVG(site_profit_proxy), 0)                AS avg_daily_profit_per_site_NGN
FROM master_table
GROUP BY state, lga
HAVING avg_daily_profit_per_site_NGN < 0
ORDER BY avg_daily_profit_per_site_NGN ASC;


-- SECTION 2.5  EARLY WARNING SIGNALS

-- Q09: LGAs currently under active churn risk flag
-- Business use: proactive retention triggers — these LGAs show
-- simultaneous subscriber decline and ARPU erosion over 7 days.
SELECT
    state,
    lga,
    SUM(churn_risk_flag)                            AS churn_flag_days,
    ROUND(AVG(subs_7d_change) * 100, 2)             AS avg_subs_7d_change_pct,
    ROUND(AVG(arpu_7d_change) * 100, 2)             AS avg_arpu_7d_change_pct,
    ROUND(AVG(active_subs), 0)                      AS avg_active_subs,
    ROUND(AVG(avg_mos_score), 2)                    AS avg_mos_score
FROM master_table
GROUP BY state, lga
HAVING churn_flag_days > 0
ORDER BY churn_flag_days DESC;


-- Q10: ARPU deterioration watch — LGAs with negative 7-day trend
-- Business use: early revenue warning before churn flags trigger.
-- These LGAs need pricing or product intervention now.
SELECT
    state,
    lga,
    ROUND(AVG(arpu_monthly_est), 0)                 AS avg_monthly_arpu_NGN,
    ROUND(AVG(arpu_7d_change) * 100, 2)             AS avg_arpu_7d_change_pct,
    ROUND(AVG(subs_7d_change) * 100, 2)             AS avg_subs_7d_change_pct,
    ROUND(AVG(penetration_rate) * 100, 1)           AS avg_penetration_pct
FROM master_table
GROUP BY state, lga
HAVING avg_arpu_7d_change_pct < 0
ORDER BY avg_arpu_7d_change_pct ASC
LIMIT 15;


-- SECTION 2.6  WHITESPACE & DEMAND GAPS

-- Q11: Whitespace LGAs — high population, low penetration
-- Business use: identifies markets where demand exists but supply
-- (network coverage or sales presence) is absent or insufficient.
SELECT
    state,
    lga,
    lga_population,
    ROUND(AVG(penetration_rate) * 100, 1)           AS avg_penetration_pct,
    ROUND(AVG(income_index), 1)                     AS avg_income_index,
    poi_total,
    whitespace_flag,
    urban_flag
FROM master_table
WHERE whitespace_flag = 1
GROUP BY state, lga
ORDER BY lga_population DESC;


-- Q12: Composite opportunity candidates — whitespace + income + POI
-- Business use: final GTM targeting shortlist. LGAs with large
-- underserved populations, commercial activity, and revenue potential.
SELECT
    state,
    lga,
    lga_population,
    ROUND(AVG(penetration_rate) * 100, 1)           AS avg_penetration_pct,
    ROUND(AVG(income_index), 1)                     AS avg_income_index,
    poi_total,
    poi_markets,
    ROUND(AVG(site_profit_proxy), 0)                AS avg_site_profit_proxy,
    whitespace_flag
FROM master_table
GROUP BY state, lga
ORDER BY
    whitespace_flag DESC,
    avg_income_index DESC,
    poi_total DESC
LIMIT 15;