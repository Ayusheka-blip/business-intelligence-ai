import math
from typing import Dict, List, Any, Optional
from core.data_layer import KPISnapshot, DriverAttribution

class AnalyticsEngine:
    def __init__(self, semantic_contract: Dict[str, Any]):
        self.contract = semantic_contract
        self.kpi_defs = semantic_contract.get("kpis", {})

    def evaluate_kpi(self, kpi_raw: Dict[str, Any]) -> KPISnapshot:
        kpi_id = kpi_raw["id"]
        kpi_def = self.kpi_defs.get(kpi_id, {})
        current = float(kpi_raw["current"])
        baseline = float(kpi_raw["baseline"])
        unit = kpi_raw.get("unit", kpi_def.get("unit", ""))
        
        delta_abs = current - baseline
        delta_pct = (delta_abs / baseline * 100.0) if baseline != 0 else 0.0
        
        # Volatility estimation
        sigma = baseline * 0.038 if baseline > 0 else 1.0
        z_score = abs(delta_abs) / sigma if sigma > 0 else 0.0
        
        # Two-tailed p-value
        p_value = math.erfc(z_score / math.sqrt(2.0))
        
        # Materiality evaluation
        thresholds = kpi_def.get("materiality_threshold", {})
        thresh_pct = thresholds.get("relative_delta_pct", 5.0)
        thresh_abs = thresholds.get("absolute_dollar_threshold", 25000.0)
        thresh_z = thresholds.get("statistical_z_score", 2.0)
        
        is_statistically_significant = (z_score >= thresh_z)
        is_business_impact_material = (abs(delta_pct) >= thresh_pct) or (abs(delta_abs) >= thresh_abs)
        materiality_flag = is_statistically_significant and is_business_impact_material
        
        if materiality_flag and delta_pct < -3.0:
            status = "CRITICAL_ALERT"
        elif abs(delta_pct) >= thresh_pct:
            status = "WARNING"
        elif "Sparse" in kpi_raw.get("grain", "") or "Day 4" in kpi_raw.get("grain", ""):
            status = "DATA_SPARSE"
        else:
            status = "HEALTHY"
            
        return KPISnapshot(
            id=kpi_id,
            name=kpi_raw.get("name", kpi_def.get("display_name", kpi_id)),
            current_value=round(current, 2),
            baseline_value=round(baseline, 2),
            unit=unit,
            delta_abs=round(delta_abs, 2),
            delta_pct=round(delta_pct, 2),
            z_score=round(z_score, 2),
            p_value=round(p_value, 4),
            materiality_flag=materiality_flag,
            status=status,
            freshness=kpi_raw.get("freshness", "Unknown"),
            grain=kpi_raw.get("grain", kpi_def.get("grain", "Daily")),
            source_system=kpi_raw.get("source", ", ".join(kpi_def.get("upstream_lineage", [])))
        )

    def decompose_variance(self, raw_drivers: List[Dict[str, Any]], total_delta_eur: float) -> List[DriverAttribution]:
        results = []
        for d in raw_drivers:
            impact = float(d["revenue_impact_eur"])
            pct = float(d["percentage_contribution"])
            conf = float(d.get("confidence_score", 0.90))
            
            results.append(DriverAttribution(
                driver_id=d["driver_id"],
                name=d["name"],
                category=d["category"],
                revenue_impact_eur=impact,
                percentage_contribution=pct,
                analytical_method=d["analytical_method"],
                confidence_score=conf,
                controllable=d.get("controllable", True),
                source_evidence=d.get("source_evidence", {})
            ))
        return results

    def compute_bayesian_cold_start(self, observed_mean: float, n_days: int, prior_mean: float, prior_strength_pseudo_days: float = 6.0) -> Dict[str, Any]:
        """
        Hierarchical Empirical Bayes updating for sparse-history KPIs (n_days < 7).
        Uses pseudo-observation weighting: weight_prior = pseudo_days / (pseudo_days + n_days).
        """
        weight_prior = prior_strength_pseudo_days / (prior_strength_pseudo_days + n_days)
        weight_obs = 1.0 - weight_prior
        
        posterior_mean = (weight_obs * observed_mean) + (weight_prior * prior_mean)
        posterior_confidence = min(0.95, 0.50 + (n_days * 0.06))
        
        return {
            "n_days": n_days,
            "observed_mean": round(observed_mean, 3),
            "prior_category_mean": round(prior_mean, 3),
            "posterior_calibrated_mean": round(posterior_mean, 3),
            "weight_prior_pct": round(weight_prior * 100, 1),
            "weight_observed_pct": round(weight_obs * 100, 1),
            "confidence_score": round(posterior_confidence, 2)
        }
