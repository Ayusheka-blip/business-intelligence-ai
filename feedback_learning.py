import sqlite3
import json
import os
import datetime
from typing import Dict, List, Any

class FeedbackLearningEngine:
    def __init__(self, db_path: str = "data/feedback.db"):
        self.db_path = db_path
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS feedback_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    scenario_id TEXT NOT NULL,
                    persona TEXT NOT NULL,
                    driver_id TEXT NOT NULL,
                    feedback_type TEXT NOT NULL, -- 'CONFIRMED', 'REJECTED', 'WEIGHT_ADJUSTED'
                    rating INTEGER,
                    comment TEXT,
                    original_weight REAL,
                    adjusted_weight REAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS calibration_priors (
                    driver_id TEXT PRIMARY KEY,
                    calibrated_weight_multiplier REAL DEFAULT 1.0,
                    total_confirmations INTEGER DEFAULT 0,
                    total_rejections INTEGER DEFAULT 0,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()

    def submit_feedback(
        self,
        scenario_id: str,
        persona: str,
        driver_id: str,
        feedback_type: str,
        rating: int = 5,
        comment: str = "",
        original_weight: float = 0.0,
        adjusted_weight: float = 0.0
    ) -> Dict[str, Any]:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO feedback_log (
                    scenario_id, persona, driver_id, feedback_type, rating, comment, original_weight, adjusted_weight
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (scenario_id, persona, driver_id, feedback_type, rating, comment, original_weight, adjusted_weight))
            
            # Recalibrate Bayesian priors
            cursor.execute("SELECT calibrated_weight_multiplier, total_confirmations, total_rejections FROM calibration_priors WHERE driver_id = ?", (driver_id,))
            row = cursor.fetchone()
            if row:
                mult, confs, rejs = row
            else:
                mult, confs, rejs = (1.0, 0, 0)
                
            if feedback_type == "CONFIRMED":
                confs += 1
                mult = round(mult * 1.05, 3)
            elif feedback_type == "REJECTED":
                rejs += 1
                mult = round(mult * 0.90, 3)
            elif feedback_type == "WEIGHT_ADJUSTED" and original_weight > 0:
                ratio = adjusted_weight / original_weight
                mult = round((mult * 0.7) + (ratio * 0.3), 3)
                
            cursor.execute("""
                INSERT OR REPLACE INTO calibration_priors (
                    driver_id, calibrated_weight_multiplier, total_confirmations, total_rejections, last_updated
                ) VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
            """, (driver_id, mult, confs, rejs))
            
            conn.commit()

        return {
            "status": "FEEDBACK_LOGGED_AND_RECALIBRATED",
            "driver_id": driver_id,
            "feedback_type": feedback_type,
            "new_calibrated_multiplier": mult,
            "total_confirmations": confs,
            "total_rejections": rejs
        }

    def get_feedback_history(self, limit: int = 15) -> List[Dict[str, Any]]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM feedback_log ORDER BY id DESC LIMIT ?", (limit,))
            rows = cursor.fetchall()
            return [dict(r) for r in rows]

    def get_calibration_priors(self) -> Dict[str, Any]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM calibration_priors")
            rows = cursor.fetchall()
            return {r["driver_id"]: dict(r) for r in rows}
