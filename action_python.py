from dataclasses import dataclass
from typing import Dict, List, Any, Optional

@dataclass
class ActionItem:
    action_id: str
    driver_id: str
    driver_name: str
    controllable_lever: str
    action_title: str
    detailed_description: str
    expected_financial_impact_eur: float
    expected_kpi_lift: str
    owner_role: str
    decision_right_code: str
    confidence_score: float
    implementation_time: str
    monitoring_plan: str
    rollback_protocol: str
    status: str = "PENDING_APPROVAL"

class ActionEngine:
    def __init__(self):
        self.action_catalogs = {
            "multifactor_outage_ecom": [
                ActionItem(
                    action_id="ACT-001",
                    driver_id="checkout_api_outage",
                    driver_name="Checkout API Gateway HTTP 504 Outage (EU-West)",
                    controllable_lever="Payment Infrastructure Routing & Gateway Redundancy",
                    action_title="Initiate Immediate Gateway Failover to Stripe EU Backup",
                    detailed_description="Reroute 100% of EU-West card checkout requests away from degraded Frankfurt node to Stripe European backup gateway. Trigger automatic retry for 2,480 dropped sessions.",
                    expected_financial_impact_eur=77040.0,
                    expected_kpi_lift="+1.31% Checkout Conversion Rate recovery within 15 minutes",
                    owner_role="operations_lead",
                    decision_right_code="gateway_failover_trigger",
                    confidence_score=0.96,
                    implementation_time="< 5 Minutes (Automated Trigger)",
                    monitoring_plan="Track HTTP error response code rates on stream_db.checkout_gateway_telemetry at 1-minute intervals.",
                    rollback_protocol="Revert DNS traffic routing back to primary Adyen endpoint if Stripe error rates exceed 0.5%."
                ),
                ActionItem(
                    action_id="ACT-002",
                    driver_id="competitor_price_shift",
                    driver_name="Competitor Price Undercut (-20% Flash Promo)",
                    controllable_lever="Dynamic Promotional Pricing & Personalized Vouchers",
                    action_title="Deploy Automated 10% Price-Match Voucher for High-Intent Cart Abandoners",
                    detailed_description="Issue targeted €10/10% discount codes to EU customers who abandoned electronics carts within the last 6 hours to neutralize MegaRetail EU campaign.",
                    expected_financial_impact_eur=24500.0,
                    expected_kpi_lift="+0.45% Conversion Lift; Recover €24.5k of contested revenue",
                    owner_role="growth_marketer",
                    decision_right_code="promotional_voucher_grant",
                    confidence_score=0.85,
                    implementation_time="30 Minutes",
                    monitoring_plan="Monitor voucher redemption rate and gross margin floor guardrails (minimum 35% margin) in real-time.",
                    rollback_protocol="Auto-cap budget at €15,000 maximum discount spend; pause campaign if ROAS falls below 3.5x."
                ),
                ActionItem(
                    action_id="ACT-003",
                    driver_id="organic_seasonality",
                    driver_name="Post-Holiday Seasonal Demand Taper",
                    controllable_lever="Inventory & Ad Spend Capital Reallocation",
                    action_title="Reallocate €50k Marketing Capital to High-Growth APAC Region",
                    detailed_description="Reduce low-margin EU-West broad display spend by €50k and shift budget toward high-margin APAC Spring campaign.",
                    expected_financial_impact_eur=18000.0,
                    expected_kpi_lift="Maintain corporate EBITDA target despite regional volume dip",
                    owner_role="executive_vp",
                    decision_right_code="capital_reallocation",
                    confidence_score=0.88,
                    implementation_time="24 Hours",
                    monitoring_plan="Evaluate weekly blended ROAS and inventory turnover velocity.",
                    rollback_protocol="Re-enable EU seasonal campaigns if regional organic search volume surges > 15%."
                )
            ],
            "low_confidence_abstention": [
                ActionItem(
                    action_id="ACT-004",
                    driver_id="suspected_bot_or_broken_utm",
                    driver_name="Unverified Bot Traffic vs CDN Tag Stripping",
                    controllable_lever="Data Pipeline & Tagging Infrastructure",
                    action_title="Audit CDN Edge Worker & Validate Campaign Tracking Tags",
                    detailed_description="Deploy hotfix to Cloudflare edge worker v3.8 to restore UTM query string passthrough before executing any marketing budget changes.",
                    expected_financial_impact_eur=0.0,
                    expected_kpi_lift="Restore 100% data telemetry integrity and eliminate analytical ambiguity",
                    owner_role="data_analyst",
                    decision_right_code="deploy_dag_fix",
                    confidence_score=0.92,
                    implementation_time="15 Minutes",
                    monitoring_plan="Verify UTM presence in 100 consecutive stream_db session records.",
                    rollback_protocol="Roll back edge worker to v3.7 if tag propagation fails."
                )
            ],
            "cold_start_ecopro_x": [
                ActionItem(
                    action_id="ACT-005",
                    driver_id="bayesian_peer_shrinkage",
                    driver_name="Funnel Dropoff vs Sibling Category Prior",
                    controllable_lever="Product Launch Onboarding & Early Influencer Seeding",
                    action_title="Launch Category Benchmark Influencer Seeding Campaign",
                    detailed_description="Accelerate review collection (target N=150 reviews) to narrow Bayesian confidence intervals and boost conversion from 1.65% to 2.40%.",
                    expected_financial_impact_eur=16800.0,
                    expected_kpi_lift="Expected conversion lift to match 2.40% category standard",
                    owner_role="growth_marketer",
                    decision_right_code="retargeting_creative_shift",
                    confidence_score=0.82,
                    implementation_time="2 Days",
                    monitoring_plan="Daily Bayesian posterior variance monitoring until N >= 100 reviews.",
                    rollback_protocol="Pause promotional seeding if product return rate exceeds 5%."
                )
            ]
        }

    def get_recommended_actions(self, scenario_id: str, role_id: str) -> List[Dict[str, Any]]:
        actions = self.action_catalogs.get(scenario_id, self.action_catalogs["multifactor_outage_ecom"])
        results = []
        for a in actions:
            d = dict(a.__dict__)
            # Check role alignment
            d["is_role_primary_owner"] = (a.owner_role == role_id)
            results.append(d)
        return results

    def execute_action(self, action_id: str, user_role: str) -> Dict[str, Any]:
        return {
            "action_id": action_id,
            "executed_by": user_role,
            "status": "EXECUTED_SUCCESSFULLY",
            "message": f"Action {action_id} triggered. Automated webhook dispatched to operational endpoint. Real-time telemetry monitoring activated."
        }
