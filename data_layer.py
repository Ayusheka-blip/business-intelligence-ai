import math
import random
from dataclasses import dataclass, asdict
from typing import Dict, List, Any, Optional

@dataclass
class KPISnapshot:
    id: str
    name: str
    current_value: float
    baseline_value: float
    unit: str
    delta_abs: float
    delta_pct: float
    z_score: float
    p_value: float
    materiality_flag: bool
    status: str # "CRITICAL_ALERT", "WARNING", "HEALTHY", "DATA_SPARSE"
    freshness: str
    grain: str
    source_system: str

@dataclass
class DriverAttribution:
    driver_id: str
    name: str
    category: str # "Technical / Gateway", "Competitor / Pricing", "Macro / Seasonality", "Operations / Stockout"
    revenue_impact_eur: float
    percentage_contribution: float
    analytical_method: str # "Deterministic Shapley Decomposition", "Cross-Source Correlation", "Bayesian Shrinkage"
    confidence_score: float
    controllable: bool
    source_evidence: Dict[str, Any]

class DataLayer:
    def __init__(self):
        self._init_mock_datasets()

    def _init_mock_datasets(self):
        # Scenario 1: Multi-Factor EU-West Revenue Drop
        self.scenarios = {
            "multifactor_outage_ecom": {
                "name": "EU-West Revenue Drop (-8.4%) - Multi-Factor Outage & Pricing Shift",
                "description": "Gross Net Revenue dropped €128,400 across EU-West region during the last 24-hour cycle. Root cause deconstruction links 60% to a payment gateway outage, 25% to competitor discounting, and 15% to organic seasonality.",
                "kpis": {
                    "net_revenue": {
                        "id": "net_revenue",
                        "name": "Net Revenue",
                        "current": 1396600.0,
                        "baseline": 1525000.0,
                        "unit": "EUR",
                        "grain": "Hourly Stream (24h Aggregate)",
                        "source": "stream_db.checkout_events & warehouse_olap.fact_orders",
                        "freshness": "Streamed 2 mins ago (Real-time)"
                    },
                    "checkout_conversion_rate": {
                        "id": "checkout_conversion_rate",
                        "name": "Checkout Conversion Rate",
                        "current": 2.14,
                        "baseline": 3.45,
                        "unit": "%",
                        "grain": "5-Minute Stream",
                        "source": "stream_db.checkout_gateway_telemetry",
                        "freshness": "Streamed 1 min ago"
                    },
                    "stockout_rate": {
                        "id": "stockout_rate",
                        "name": "Top-100 SKU Stockout Rate",
                        "current": 3.8,
                        "baseline": 3.5,
                        "unit": "%",
                        "grain": "Daily Snapshot",
                        "source": "erp_db.warehouse_inventory_daily",
                        "freshness": "Refreshed 04:00 UTC (Batch Daily)"
                    },
                    "customer_nps": {
                        "id": "customer_nps",
                        "name": "Customer NPS Score",
                        "current": 48.0,
                        "baseline": 56.0,
                        "unit": "Score (-100 to +100)",
                        "grain": "Weekly Rollup",
                        "source": "crm_db.surveys_nps_weekly",
                        "freshness": "Refreshed Sunday 00:00 UTC"
                    },
                    "gross_margin_pct": {
                        "id": "gross_margin_pct",
                        "name": "Gross Profit Margin %",
                        "current": 41.2,
                        "baseline": 44.8,
                        "unit": "%",
                        "grain": "Daily Rollup",
                        "source": "erp_db.supplier_cogs_master",
                        "freshness": "Refreshed 06:00 UTC (Confidential)"
                    }
                },
                "variance_decomposition": [
                    {
                        "driver_id": "checkout_api_outage",
                        "name": "Checkout API Gateway HTTP 504 Outage (EU-West)",
                        "category": "Technical & Platform Infrastructure",
                        "revenue_impact_eur": -77040.0,
                        "percentage_contribution": 60.0,
                        "analytical_method": "Deterministic Shapley Counterfactual Variance",
                        "confidence_score": 0.96,
                        "controllable": True,
                        "source_evidence": {
                            "source_table": "stream_db.checkout_gateway_telemetry",
                            "error_code": "HTTP_504_GATEWAY_TIMEOUT",
                            "affected_region": "EU-West (Frankfurt / Dublin nodes)",
                            "failed_checkout_sessions": 2480,
                            "average_order_value_eur": 31.06,
                            "detection_method": "SQL Exact Error Session Counter"
                        }
                    },
                    {
                        "driver_id": "competitor_price_shift",
                        "name": "Competitor Price Undercut (-20% Flash Promo)",
                        "category": "External Market & Pricing",
                        "revenue_impact_eur": -32100.0,
                        "percentage_contribution": 25.0,
                        "analytical_method": "Econometric Cross-Elasticity Regression",
                        "confidence_score": 0.88,
                        "controllable": True,
                        "source_evidence": {
                            "source_table": "external_intel.competitor_pricing_scrapes",
                            "competitor": "MegaRetail EU",
                            "affected_categories": ["Electronics", "Smart Audio"],
                            "price_gap_pct": -22.4,
                            "lost_cart_sessions": 840,
                            "detection_method": "Scraped Daily Competitor Price Index vs Internal Cart Drops"
                        }
                    },
                    {
                        "driver_id": "organic_seasonality",
                        "name": "Post-Holiday Seasonal Demand Taper",
                        "category": "Macro & Seasonality",
                        "revenue_impact_eur": -19260.0,
                        "percentage_contribution": 15.0,
                        "analytical_method": "Holt-Winters Multiplicative Seasonality Baseline",
                        "confidence_score": 0.92,
                        "controllable": False,
                        "source_evidence": {
                            "source_table": "warehouse_olap.historical_seasonality_curves",
                            "expected_seasonal_dip": -1.26,
                            "prior_year_benchmark_dip": -1.30,
                            "detection_method": "Time-Series Residual Variance Isolation"
                        }
                    }
                ],
                "qualitative_signals": [
                    {"type": "Support Ticket Spike", "text": "Over 310 customer tickets reported timeout on EU card checkout between 10:00 and 14:30 CET.", "sentiment": "High Urgency Detractor"},
                    {"type": "Internal Slack Ops Alert", "text": "Platform team acknowledged Adyen EU secondary gateway routing failure at 10:15 CET.", "sentiment": "Technical Incident"}
                ]
            },
            "low_confidence_abstention": {
                "name": "Traffic Spike vs Conversion Discrepancy (Abstention Triggered)",
                "description": "Marketing ad spend spiked impressions by +40%, but recorded checkout conversions collapsed by -35%. Critical UTM attribution tags were stripped during a CDN deployment, rendering causal attribution mathematically inconclusive.",
                "kpis": {
                    "net_revenue": {
                        "id": "net_revenue",
                        "name": "Net Revenue",
                        "current": 840000.0,
                        "baseline": 1050000.0,
                        "unit": "EUR",
                        "grain": "Daily Stream",
                        "source": "stream_db.checkout_events",
                        "freshness": "Streamed 5 mins ago"
                    },
                    "checkout_conversion_rate": {
                        "id": "checkout_conversion_rate",
                        "name": "Checkout Conversion Rate",
                        "current": 1.40,
                        "baseline": 2.90,
                        "unit": "%",
                        "grain": "5-Minute Stream",
                        "source": "stream_db.session_logs",
                        "freshness": "Streamed 3 mins ago"
                    },
                    "stockout_rate": {
                        "id": "stockout_rate",
                        "name": "Top-100 SKU Stockout Rate",
                        "current": 3.2,
                        "baseline": 3.4,
                        "unit": "%",
                        "grain": "Daily Snapshot",
                        "source": "erp_db.warehouse_inventory_daily",
                        "freshness": "Refreshed 04:00 UTC"
                    },
                    "customer_nps": {
                        "id": "customer_nps",
                        "name": "Customer NPS Score",
                        "current": 54.0,
                        "baseline": 55.0,
                        "unit": "Score",
                        "grain": "Weekly Rollup",
                        "source": "crm_db.surveys_nps_weekly",
                        "freshness": "Refreshed Sunday"
                    },
                    "gross_margin_pct": {
                        "id": "gross_margin_pct",
                        "name": "Gross Profit Margin %",
                        "current": 43.1,
                        "baseline": 44.0,
                        "unit": "%",
                        "grain": "Daily Rollup",
                        "source": "erp_db.supplier_cogs_master",
                        "freshness": "Refreshed 06:00 UTC"
                    }
                },
                "variance_decomposition": [
                    {
                        "driver_id": "suspected_bot_or_broken_utm",
                        "name": "Unverified Bot Traffic vs CDN Tag Stripping",
                        "category": "Data Quality & Tagging Failure",
                        "revenue_impact_eur": -210000.0,
                        "percentage_contribution": 100.0,
                        "analytical_method": "Signal Conflict & Uncertainty Calibrator",
                        "confidence_score": 0.42,
                        "controllable": True,
                        "source_evidence": {
                            "conflicting_signal_1": "Google Ads API reports 145,000 valid clicks delivered (+42% YoY).",
                            "conflicting_signal_2": "Cloudflare CDN logs show 68% of incoming traffic lacked standard UTM_CAMPAIGN parameter after v3.8 edge worker rollout.",
                            "data_integrity_alert": "Missing Campaign ID attribution on 68% of landing sessions. Causal inference mathematically invalid without tag reconciliation.",
                            "detection_method": "Uncertainty Engine: Shannon Entropy & Bayesian Evidence Divergence"
                        }
                    }
                ],
                "abstention_prompt": {
                    "status": "ABSTAINED_FROM_DEFINITIVE_CLAIM",
                    "confidence_score": 0.42,
                    "reason": "Insufficient & Contradictory Telemetry: Paid ad traffic increased +42% while recorded conversion dropped -51%. 68% of sessions have missing campaign telemetry due to CDN worker misconfiguration.",
                    "clarification_request": "Human Analyst Verification Required: Please confirm whether the Cloudflare v3.8 edge deployment stripped UTM parameters before allocating ad budget reductions."
                }
            },
            "cold_start_ecopro_x": {
                "name": "Cold Start SKU 'EcoPro-X' (Sparse History Analysis)",
                "description": "Newly launched sustainable tech accessory 'EcoPro-X' has only 4 days of transactional history. The engine automatically switches to Hierarchical Bayesian Shrinkage using sibling category priors to estimate baseline variance without hallucinating false confidence.",
                "kpis": {
                    "net_revenue": {
                        "id": "net_revenue",
                        "name": "Net Revenue (EcoPro-X SKU)",
                        "current": 48200.0,
                        "baseline": 65000.0,
                        "unit": "EUR",
                        "grain": "Daily Stream (Day 4 of Launch)",
                        "source": "stream_db.checkout_events",
                        "freshness": "Streamed 10 mins ago (Day 4 Post-Launch)"
                    },
                    "checkout_conversion_rate": {
                        "id": "checkout_conversion_rate",
                        "name": "Checkout Conversion Rate",
                        "current": 1.65,
                        "baseline": 2.40,
                        "unit": "%",
                        "grain": "Hourly Stream",
                        "source": "stream_db.session_logs",
                        "freshness": "Streamed 5 mins ago"
                    },
                    "stockout_rate": {
                        "id": "stockout_rate",
                        "name": "Warehouse Fulfillment Availability",
                        "current": 0.0,
                        "baseline": 0.0,
                        "unit": "% (0% = Full Stock)",
                        "grain": "Daily Snapshot",
                        "source": "erp_db.warehouse_inventory_daily",
                        "freshness": "Refreshed 04:00 UTC"
                    },
                    "customer_nps": {
                        "id": "customer_nps",
                        "name": "Early Customer Review Sentiment",
                        "current": 72.0,
                        "baseline": 68.0,
                        "unit": "Score (N=42 reviews)",
                        "grain": "Early Sample Survey",
                        "source": "crm_db.support_tickets_sentiment",
                        "freshness": "Aggregated 1 hour ago"
                    },
                    "gross_margin_pct": {
                        "id": "gross_margin_pct",
                        "name": "Gross Profit Margin %",
                        "current": 58.4,
                        "baseline": 60.0,
                        "unit": "%",
                        "grain": "Initial Batch Estimate",
                        "source": "erp_db.supplier_cogs_master",
                        "freshness": "Batch Master"
                    }
                },
                "variance_decomposition": [
                    {
                        "driver_id": "bayesian_peer_shrinkage",
                        "name": "Funnel Dropoff vs Sibling Category Prior (EcoTech Accessories)",
                        "category": "New Product Launch Dynamics",
                        "revenue_impact_eur": -16800.0,
                        "percentage_contribution": 100.0,
                        "analytical_method": "Empirical Bayes Category Prior Shrinkage (N=4 Days)",
                        "confidence_score": 0.74,
                        "controllable": True,
                        "source_evidence": {
                            "prior_source": "Category EcoTech Accessories (12 Historical Launches)",
                            "prior_mean_conversion": "2.40% +/- 0.35%",
                            "sample_size_days": 4,
                            "shrinkage_weight_prior": "62%",
                            "shrinkage_weight_observed": "38%",
                            "detection_method": "Bayesian Conjugate Normal-Gamma Updating"
                        }
                    }
                ]
            }
        }

    def get_scenario(self, scenario_id: str = "multifactor_outage_ecom") -> Dict[str, Any]:
        return self.scenarios.get(scenario_id, self.scenarios["multifactor_outage_ecom"])

    def list_scenarios(self) -> List[Dict[str, str]]:
        return [
            {"id": k, "name": v["name"], "description": v["description"]}
            for k, v in self.scenarios.items()
        ]
