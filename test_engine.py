import unittest
import json
import os
import sys

# Ensure repository root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.data_layer import DataLayer
from core.analytics_engine import AnalyticsEngine
from core.rbac_engine import RBACEngine
from core.narrative_engine import NarrativeEngine
from core.action_engine import ActionEngine
from core.feedback_learning import FeedbackLearningEngine
from core.telemetry import TelemetryEngine

class TestKPIEngine(unittest.TestCase):
    def setUp(self):
        with open("core/semantic_contract.json") as f:
            self.contract = json.load(f)
        self.data_layer = DataLayer()
        self.analytics = AnalyticsEngine(self.contract)
        self.rbac = RBACEngine(self.contract)
        self.narrative = NarrativeEngine(self.contract)
        self.action = ActionEngine()
        self.feedback = FeedbackLearningEngine("data/test_feedback.db")
        self.telemetry = TelemetryEngine()

    def test_1_anomaly_detection_and_materiality(self):
        scenario = self.data_layer.get_scenario("multifactor_outage_ecom")
        rev_raw = scenario["kpis"]["net_revenue"]
        kpi_eval = self.analytics.evaluate_kpi(rev_raw)
        
        self.assertEqual(kpi_eval.id, "net_revenue")
        self.assertEqual(kpi_eval.status, "CRITICAL_ALERT")
        self.assertTrue(kpi_eval.materiality_flag)
        self.assertLess(kpi_eval.delta_pct, -5.0)
        self.assertGreater(kpi_eval.z_score, 2.0)
        print("  ✓ Test 1: Anomaly Detection & Materiality Filter Passed")

    def test_2_variance_decomposition_exact_closure(self):
        scenario = self.data_layer.get_scenario("multifactor_outage_ecom")
        drivers = self.analytics.decompose_variance(scenario["variance_decomposition"], -128400.0)
        
        total_impact = sum(d.revenue_impact_eur for d in drivers)
        total_pct = sum(d.percentage_contribution for d in drivers)
        
        self.assertAlmostEqual(total_impact, -128400.0, places=2)
        self.assertAlmostEqual(total_pct, 100.0, places=2)
        self.assertEqual(len(drivers), 3)
        self.assertEqual(drivers[0].driver_id, "checkout_api_outage")
        self.assertEqual(drivers[0].percentage_contribution, 60.0)
        print("  ✓ Test 2: Multi-Factor Variance Exact Closure Passed")

    def test_3_low_confidence_abstention_trigger(self):
        scenario = self.data_layer.get_scenario("low_confidence_abstention")
        drivers = self.analytics.decompose_variance(scenario["variance_decomposition"], -210000.0)
        abstention = scenario.get("abstention_prompt")
        
        self.assertIsNotNone(abstention)
        self.assertEqual(abstention["status"], "ABSTAINED_FROM_DEFINITIVE_CLAIM")
        self.assertLess(abstention["confidence_score"], 0.65)
        
        narrative = self.narrative.generate_narrative("data_analyst", "low_confidence_abstention", {}, drivers, abstention)
        self.assertIn("⚠️ Engine Abstention", narrative["headline"])
        print("  ✓ Test 3: Low-Confidence & Abstention Mechanism Passed")

    def test_4_sparse_history_bayesian_cold_start(self):
        cold_start = self.analytics.compute_bayesian_cold_start(
            observed_mean=1.65,
            n_days=4,
            prior_mean=2.40,
            prior_strength_pseudo_days=6.0
        )
        self.assertEqual(cold_start["n_days"], 4)
        self.assertGreater(cold_start["weight_prior_pct"], 50.0)
        self.assertGreater(cold_start["posterior_calibrated_mean"], 1.65)
        self.assertLess(cold_start["posterior_calibrated_mean"], 2.40)
        print("  ✓ Test 4: Sparse-History Bayesian Cold-Start Passed")

    def test_5_rbac_and_column_masking(self):
        scenario = self.data_layer.get_scenario("multifactor_outage_ecom")
        kpi_dict = {k: self.analytics.evaluate_kpi(v).__dict__ for k, v in scenario["kpis"].items()}
        
        # Test Executive persona (unmasked)
        exec_kpis = self.rbac.filter_and_mask_kpis("executive_vp", kpi_dict)
        self.assertFalse(exec_kpis["gross_margin_pct"]["is_masked"])
        self.assertEqual(exec_kpis["gross_margin_pct"]["current_value"], 41.2)
        
        # Test Operations persona (masked)
        ops_kpis = self.rbac.filter_and_mask_kpis("operations_lead", kpi_dict)
        self.assertTrue(ops_kpis["gross_margin_pct"]["is_masked"])
        self.assertEqual(ops_kpis["gross_margin_pct"]["current_value"], "CONFIDENTIAL [FINANCE RESTRICTED]")
        
        # Test Decision rights verification
        auth_exec = self.rbac.verify_action_entitlement("executive_vp", "capital_reallocation")
        self.assertTrue(auth_exec["authorized"])
        auth_ops = self.rbac.verify_action_entitlement("operations_lead", "capital_reallocation")
        self.assertFalse(auth_ops["authorized"])
        print("  ✓ Test 5: RBAC Column Masking & Entitlements Passed")

    def test_6_action_matrix_and_decision_rights(self):
        actions = self.action.get_recommended_actions("multifactor_outage_ecom", "operations_lead")
        self.assertEqual(len(actions), 3)
        self.assertTrue(any(a["driver_id"] == "checkout_api_outage" for a in actions))
        
        exec_res = self.action.execute_action("ACT-001", "operations_lead")
        self.assertEqual(exec_res["status"], "EXECUTED_SUCCESSFULLY")
        print("  ✓ Test 6: Action Matrix & Execution Workflow Passed")

    def test_7_feedback_learning_loop(self):
        res = self.feedback.submit_feedback(
            scenario_id="multifactor_outage_ecom",
            persona="data_analyst",
            driver_id="checkout_api_outage",
            feedback_type="CONFIRMED",
            rating=5,
            comment="Root cause validated via network packet telemetry."
        )
        self.assertEqual(res["status"], "FEEDBACK_LOGGED_AND_RECALIBRATED")
        history = self.feedback.get_feedback_history(limit=5)
        self.assertGreater(len(history), 0)
        print("  ✓ Test 7: Feedback Learning & Recalibration Passed")

    def test_8_telemetry_and_economics(self):
        tel = self.telemetry.compute_telemetry_profile("executive_vp", "multifactor_outage_ecom")
        self.assertLess(tel["total_latency_ms"], 100.0)
        self.assertGreater(tel["token_economics"]["cost_savings_vs_full_llm_pct"], 90.0)
        print("  ✓ Test 8: Runtime Telemetry & Sub-100ms Latency Passed")

if __name__ == "__main__":
    unittest.main()
