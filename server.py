import http.server
import socketserver
import json
import urllib.parse
import os
import sys
from typing import Dict, Any

from core.data_layer import DataLayer
from core.analytics_engine import AnalyticsEngine
from core.rbac_engine import RBACEngine
from core.narrative_engine import NarrativeEngine
from core.action_engine import ActionEngine
from core.feedback_learning import FeedbackLearningEngine
from core.telemetry import TelemetryEngine

# Global singletons
with open("core/semantic_contract.json") as f:
    CONTRACT = json.load(f)

DATA_LAYER = DataLayer()
ANALYTICS = AnalyticsEngine(CONTRACT)
RBAC = RBACEngine(CONTRACT)
NARRATIVE = NarrativeEngine(CONTRACT)
ACTION = ActionEngine()
FEEDBACK = FeedbackLearningEngine()
TELEMETRY = TelemetryEngine()

class APIHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory="static", **kwargs)

    def _send_json(self, data: Any, status_code: int = 200):
        response_bytes = json.dumps(data, indent=2).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(response_bytes)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
        self.wfile.write(response_bytes)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if path == "/api/contract":
            self._send_json(CONTRACT)
        elif path == "/api/scenarios":
            self._send_json(DATA_LAYER.list_scenarios())
        elif path == "/api/feedback/history":
            self._send_json({
                "history": FEEDBACK.get_feedback_history(),
                "priors": FEEDBACK.get_calibration_priors()
            })
        elif path.startswith("/api/"):
            self._send_json({"error": f"Endpoint {path} not found"}, 404)
        else:
            # Fallback to static file server
            super().do_GET()

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        content_len = int(self.headers.get("Content-Length", 0))
        post_body = self.rfile.read(content_len) if content_len > 0 else b"{}"

        try:
            body = json.loads(post_body.decode("utf-8")) if post_body else {}
        except Exception as e:
            self._send_json({"error": f"Invalid JSON body: {str(e)}"}, 400)
            return

        if path == "/api/analyze":
            scenario_id = body.get("scenario_id", "multifactor_outage_ecom")
            role_id = body.get("role_id", "executive_vp")

            # 1. Fetch raw data for scenario
            scenario_data = DATA_LAYER.get_scenario(scenario_id)

            # 2. Evaluate all KPIs
            kpi_snapshots = {}
            for k, raw in scenario_data["kpis"].items():
                eval_snap = ANALYTICS.evaluate_kpi(raw)
                kpi_snapshots[k] = eval_snap.__dict__

            # 3. RBAC Filtering & Masking
            kpi_snapshots_masked = RBAC.filter_and_mask_kpis(role_id, kpi_snapshots)

            # 4. Variance Decomposition
            rev_delta = scenario_data["kpis"]["net_revenue"]["current"] - scenario_data["kpis"]["net_revenue"]["baseline"]
            raw_drivers = scenario_data.get("variance_decomposition", [])
            drivers = ANALYTICS.decompose_variance(raw_drivers, rev_delta)
            drivers_dict = [d.__dict__ for d in drivers]

            # 5. Abstention evaluation
            abstention_info = scenario_data.get("abstention_prompt")

            # 6. Cold-start evaluation
            cold_start_meta = None
            if scenario_id == "cold_start_ecopro_x":
                cold_start_meta = ANALYTICS.compute_bayesian_cold_start(
                    observed_mean=1.65,
                    n_days=4,
                    prior_mean=2.40
                )

            # 7. Persona Narrative
            narrative = NARRATIVE.generate_narrative(
                role_id=role_id,
                scenario_id=scenario_id,
                kpi_snapshots=kpi_snapshots,
                drivers=drivers,
                abstention_info=abstention_info
            )

            # 8. Action Matrix
            actions = ACTION.get_recommended_actions(scenario_id, role_id)
            # Add entitlement checks per action
            for act in actions:
                entitle = RBAC.verify_action_entitlement(role_id, act["decision_right_code"])
                act["is_user_authorized"] = entitle["authorized"]
                act["authorization_rejection"] = entitle["rejection_reason"]

            # 9. Runtime Telemetry
            telemetry = TELEMETRY.compute_telemetry_profile(role_id, scenario_id)

            response = {
                "scenario": {
                    "id": scenario_id,
                    "name": scenario_data["name"],
                    "description": scenario_data["description"]
                },
                "role_profile": RBAC.get_role_profile(role_id),
                "kpis": kpi_snapshots_masked,
                "drivers": drivers_dict,
                "abstention": abstention_info,
                "cold_start_meta": cold_start_meta,
                "narrative": narrative,
                "recommended_actions": actions,
                "qualitative_signals": scenario_data.get("qualitative_signals", []),
                "telemetry": telemetry
            }
            self._send_json(response)

        elif path == "/api/action/execute":
            action_id = body.get("action_id")
            role_id = body.get("role_id", "executive_vp")
            decision_right = body.get("decision_right_code", "general")
            
            entitle = RBAC.verify_action_entitlement(role_id, decision_right)
            if not entitle["authorized"]:
                self._send_json({
                    "status": "UNAUTHORIZED_ACTION",
                    "error": entitle["rejection_reason"]
                }, 403)
                return

            result = ACTION.execute_action(action_id, role_id)
            self._send_json(result)

        elif path == "/api/feedback":
            scenario_id = body.get("scenario_id", "multifactor_outage_ecom")
            persona = body.get("persona", "data_analyst")
            driver_id = body.get("driver_id", "checkout_api_outage")
            feedback_type = body.get("feedback_type", "CONFIRMED")
            rating = int(body.get("rating", 5))
            comment = body.get("comment", "")
            original_weight = float(body.get("original_weight", 0.0))
            adjusted_weight = float(body.get("adjusted_weight", 0.0))

            res = FEEDBACK.submit_feedback(
                scenario_id=scenario_id,
                persona=persona,
                driver_id=driver_id,
                feedback_type=feedback_type,
                rating=rating,
                comment=comment,
                original_weight=original_weight,
                adjusted_weight=adjusted_weight
            )
            self._send_json(res)

        else:
            self._send_json({"error": f"Endpoint {path} not found"}, 404)

def run_server(port: int = 8080):
    handler = APIHandler
    # Allow port reuse
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("", port), handler) as httpd:
        print(f"🚀 BusinessIntelligence.ai Prototype Server running at: http://localhost:{port}")
        httpd.serve_forever()

if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8080
    run_server(port)
