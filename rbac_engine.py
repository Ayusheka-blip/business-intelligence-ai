from typing import Dict, List, Any
import datetime

class RBACEngine:
    def __init__(self, semantic_contract: Dict[str, Any]):
        self.roles = semantic_contract.get("roles_and_entitlements", {})
        self.access_log: List[Dict[str, Any]] = []

    def get_role_profile(self, role_id: str) -> Dict[str, Any]:
        return self.roles.get(role_id, self.roles.get("executive_vp", {}))

    def filter_and_mask_kpis(self, role_id: str, kpis: Dict[str, Any]) -> Dict[str, Any]:
        profile = self.get_role_profile(role_id)
        allowed_kpi_keys = profile.get("allowed_kpis", list(kpis.keys()))
        masked_fields = profile.get("masked_fields", [])
        
        filtered = {}
        for k, v in kpis.items():
            if k not in allowed_kpi_keys:
                continue
            
            kpi_copy = dict(v)
            if k in masked_fields or "gross_margin_pct" in masked_fields and k == "gross_margin_pct":
                kpi_copy["current_value"] = "CONFIDENTIAL [FINANCE RESTRICTED]"
                kpi_copy["baseline_value"] = "CONFIDENTIAL [FINANCE RESTRICTED]"
                kpi_copy["delta_abs"] = "MASKED"
                kpi_copy["delta_pct"] = "MASKED"
                kpi_copy["is_masked"] = True
            else:
                kpi_copy["is_masked"] = False
                
            filtered[k] = kpi_copy
            
        self.access_log.append({
            "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
            "role_id": role_id,
            "accessed_kpis": list(filtered.keys()),
            "masked_applied": [k for k in filtered.keys() if filtered[k].get("is_masked")]
        })
        
        return filtered

    def verify_action_entitlement(self, role_id: str, action_code: str) -> Dict[str, Any]:
        profile = self.get_role_profile(role_id)
        rights = profile.get("action_decision_rights", [])
        allowed = action_code in rights
        return {
            "role_id": role_id,
            "action_code": action_code,
            "authorized": allowed,
            "decision_rights": rights,
            "rejection_reason": None if allowed else f"Role '{role_id}' lacks decision rights for '{action_code}'. Required executive sign-off."
        }
