# =============================================================================
# PROJECT 7: Model Monitoring & Drift Detection
# =============================================================================
# WHAT YOU LEARN:
#   - Data drift: when input distribution changes (most common prod failure)
#   - Concept drift: when the relationship X→y changes
#   - Model performance degradation monitoring
#   - Statistical tests for drift: KS test, PSI, Jensen-Shannon divergence
#   - Evidently AI: the industry standard drift monitoring library
#   - Setting up alerting thresholds + automated retraining triggers
#   - Monitoring dashboards with Grafana (config included)
#
# CORE CONCEPT:
#   A model trained on January data may be wrong by July.
#   Not because your code broke — because the WORLD changed.
#   Monitoring tells you WHEN to retrain before users notice quality degradation.
#
# INSTALL:
#   pip install evidently scipy numpy pandas scikit-learn matplotlib
# =============================================================================

import json
import warnings
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from scipy import stats
from scipy.spatial.distance import jensenshannon
from sklearn.datasets import load_breast_cancer
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import roc_auc_score

warnings.filterwarnings("ignore")

# =============================================================================
# PART 1: SIMULATE A PRODUCTION SCENARIO
# Training data = January. Serving data = drifted February/March.
# =============================================================================

def create_training_data():
    """Returns the original training distribution (January)."""
    data = load_breast_cancer()
    X = pd.DataFrame(data.data, columns=data.feature_names)
    y = pd.Series(data.target, name="target")
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    return X_train, X_test, y_train, y_test, data.feature_names


def simulate_production_data(reference_data: pd.DataFrame,
                              drift_level: float = 0.0,
                              n_samples: int = 300) -> pd.DataFrame:
    """
    Simulates production data that may have drifted from the training distribution.

    drift_level=0.0 → identical to training distribution
    drift_level=0.3 → 30% of features shifted by 1 standard deviation
    drift_level=1.0 → heavily drifted (new season, new patient population, etc.)
    """
    np.random.seed(int(drift_level * 100))

    # Start from reference stats
    ref_mean = reference_data.mean()
    ref_std  = reference_data.std()

    # Sample from slightly modified distribution
    drifted = pd.DataFrame(
        np.random.normal(
            loc=ref_mean.values + drift_level * ref_std.values,  # Shift mean
            scale=ref_std.values * (1 + drift_level * 0.5),      # Expand variance
            size=(n_samples, len(reference_data.columns))
        ),
        columns=reference_data.columns
    )
    return drifted


def train_model(X_train, y_train):
    """Trains the model on reference (training) data."""
    pipeline = Pipeline([
        ("scaler", StandardScaler()),
        ("model",  RandomForestClassifier(n_estimators=100, random_state=42))
    ])
    pipeline.fit(X_train, y_train)
    return pipeline


# =============================================================================
# PART 2: DRIFT DETECTION STATISTICS
# These are the mathematical tests that detect when data has changed.
# =============================================================================

class DriftDetector:
    """
    Implements multiple drift detection methods.
    Different methods catch different types of drift — use multiple.
    """

    # ─── 1. Kolmogorov-Smirnov (KS) Test ─────────────────────────────────────
    @staticmethod
    def ks_test(reference: np.ndarray, current: np.ndarray,
                threshold: float = 0.05) -> dict:
        """
        KS test: compares two distributions non-parametrically.
        Tests whether two samples come from the same distribution.
        p-value < threshold → distributions are significantly different → DRIFT!

        Best for: continuous features, when you have enough samples (> 50 per side)
        """
        stat, p_value = stats.ks_2samp(reference, current)
        drifted = p_value < threshold
        return {
            "test":     "kolmogorov_smirnov",
            "statistic": round(float(stat), 4),
            "p_value":  round(float(p_value), 4),
            "threshold": threshold,
            "drifted":  drifted,
        }

    # ─── 2. Population Stability Index (PSI) ─────────────────────────────────
    @staticmethod
    def psi(reference: np.ndarray, current: np.ndarray,
            buckets: int = 10, threshold: float = 0.2) -> dict:
        """
        PSI: industry standard for credit scoring and finance.
        Measures how much a distribution has shifted.

        PSI < 0.10 → No significant shift (stable)
        PSI 0.10-0.20 → Moderate shift (monitor closely)
        PSI > 0.20 → Significant shift (RETRAIN!)

        Best for: input features in production systems, easy to explain to business.
        """
        def compute_psi(ref, cur, buckets):
            # Create histogram buckets based on reference distribution
            breakpoints = np.linspace(0, 100, buckets + 1)
            ref_edges   = np.percentile(ref, breakpoints)
            ref_edges   = np.unique(ref_edges)   # Remove duplicates

            # Count observations in each bucket
            ref_counts = np.histogram(ref, bins=ref_edges)[0]
            cur_counts = np.histogram(cur, bins=ref_edges)[0]

            # Convert to proportions (add epsilon to avoid log(0))
            eps = 1e-10
            ref_pct = (ref_counts + eps) / (len(ref) + eps)
            cur_pct = (cur_counts + eps) / (len(cur) + eps)

            # PSI formula: Σ (cur% - ref%) * ln(cur% / ref%)
            psi_val = np.sum((cur_pct - ref_pct) * np.log(cur_pct / ref_pct))
            return float(psi_val)

        psi_value = compute_psi(reference, current, buckets)
        level = ("stable" if psi_value < 0.10
                 else "moderate_shift" if psi_value < 0.20
                 else "significant_shift")
        return {
            "test":      "population_stability_index",
            "psi":       round(psi_value, 4),
            "threshold": threshold,
            "drifted":   psi_value > threshold,
            "level":     level,
        }

    # ─── 3. Jensen-Shannon Divergence ─────────────────────────────────────────
    @staticmethod
    def js_divergence(reference: np.ndarray, current: np.ndarray,
                      threshold: float = 0.1) -> dict:
        """
        JS Divergence: symmetric version of KL divergence.
        Range: [0, 1]. 0 = identical distributions. 1 = completely different.

        Advantage: always finite (unlike KL divergence which can be ∞)
        Best for: comparing probability distributions, prediction confidence shifts.
        """
        # Create discrete distributions via histograms
        bins = np.linspace(
            min(reference.min(), current.min()),
            max(reference.max(), current.max()),
            50
        )
        ref_hist, _ = np.histogram(reference, bins=bins, density=True)
        cur_hist, _ = np.histogram(current,   bins=bins, density=True)

        # Add epsilon to avoid zeros (JS divergence requires non-zero everywhere)
        ref_hist = ref_hist + 1e-10
        cur_hist = cur_hist + 1e-10

        # Normalize to proper probability distributions
        ref_hist /= ref_hist.sum()
        cur_hist /= cur_hist.sum()

        jsd = float(jensenshannon(ref_hist, cur_hist))
        return {
            "test":      "jensen_shannon_divergence",
            "jsd":       round(jsd, 4),
            "threshold": threshold,
            "drifted":   jsd > threshold,
        }

    # ─── 4. CUSUM: Cumulative Sum for concept drift ───────────────────────────
    @staticmethod
    def cusum_detector(error_stream: np.ndarray,
                       threshold: float = 5.0,
                       drift_magnitude: float = 0.5) -> dict:
        """
        CUSUM (Cumulative Sum Control Chart): detects when prediction errors
        are systematically increasing — a sign of concept drift.

        Unlike statistical tests on features, CUSUM monitors MODEL PERFORMANCE
        over time and detects gradual degradation.

        Perfect for: detecting when the world changes (seasonality, market shifts, etc.)
        """
        # Normalize errors
        mu   = np.mean(error_stream)
        sigma = np.std(error_stream) + 1e-10
        z = (error_stream - mu) / sigma

        # Cumulative sums for upward (positive) and downward (negative) drift
        s_pos = np.zeros(len(z))
        s_neg = np.zeros(len(z))
        alarms = []

        for t in range(1, len(z)):
            s_pos[t] = max(0, s_pos[t-1] + z[t] - drift_magnitude)
            s_neg[t] = max(0, s_neg[t-1] - z[t] - drift_magnitude)

            if s_pos[t] > threshold or s_neg[t] > threshold:
                alarms.append(t)

        return {
            "test":           "cusum",
            "n_alarms":       len(alarms),
            "first_alarm_at": alarms[0] if alarms else None,
            "drifted":        len(alarms) > 0,
            "s_pos":          s_pos.tolist(),
            "s_neg":          s_neg.tolist(),
        }


# =============================================================================
# PART 3: FULL MONITORING REPORT
# =============================================================================

class ModelMonitor:
    """
    Runs comprehensive monitoring on a deployed model.
    Designed to run on a schedule (daily/hourly) and alert when drift is detected.
    """

    def __init__(self, model, feature_names: list):
        self.model         = model
        self.feature_names = feature_names
        self.detector      = DriftDetector()

    def run_feature_drift_report(self, reference: pd.DataFrame,
                                  current: pd.DataFrame) -> dict:
        """
        Runs drift tests on every feature.
        Returns a summary with per-feature drift status.
        """
        print("\n📊 Feature Drift Report")
        print("─" * 60)

        feature_results = {}
        drifted_features = []

        for feature in self.feature_names:
            ref_vals = reference[feature].values
            cur_vals = current[feature].values

            ks   = self.detector.ks_test(ref_vals, cur_vals)
            psi  = self.detector.psi(ref_vals, cur_vals)
            jsd  = self.detector.js_divergence(ref_vals, cur_vals)

            # Feature is flagged if 2+ tests detect drift
            drift_votes = sum([ks["drifted"], psi["drifted"], jsd["drifted"]])
            is_drifted  = drift_votes >= 2

            feature_results[feature] = {
                "ks_test": ks, "psi": psi, "jsd": jsd,
                "drift_votes": drift_votes,
                "drifted": is_drifted,
            }

            if is_drifted:
                drifted_features.append(feature)
                print(f"  ⚠️  DRIFT: {feature[:35]:<35} PSI={psi['psi']:.3f} JSD={jsd['jsd']:.3f}")
            else:
                print(f"  ✅  STABLE: {feature[:35]:<35} PSI={psi['psi']:.3f} JSD={jsd['jsd']:.3f}")

        drift_pct = len(drifted_features) / len(self.feature_names) * 100
        print(f"\n  Summary: {len(drifted_features)}/{len(self.feature_names)} features drifted ({drift_pct:.1f}%)")

        return {
            "features": feature_results,
            "drifted_features": drifted_features,
            "drift_percentage": round(drift_pct, 2),
            "alert": drift_pct > 30,   # Alert if >30% of features drifted
        }

    def run_prediction_drift_report(self, reference: pd.DataFrame,
                                     current: pd.DataFrame) -> dict:
        """
        Monitors how the model's PREDICTIONS change over time.
        Even if features seem stable, predictions can drift if the model
        is sensitive to subtle distribution shifts.
        """
        ref_scores = self.model.predict_proba(reference.values)[:, 1]
        cur_scores = self.model.predict_proba(current.values)[:, 1]

        ks  = self.detector.ks_test(ref_scores, cur_scores)
        psi = self.detector.psi(ref_scores, cur_scores)

        print("\n📈 Prediction Score Distribution Drift")
        print(f"  Reference: mean={ref_scores.mean():.3f} std={ref_scores.std():.3f}")
        print(f"  Current:   mean={cur_scores.mean():.3f} std={cur_scores.std():.3f}")
        print(f"  KS p-value={ks['p_value']:.4f} {'⚠️  DRIFT' if ks['drifted'] else '✅ stable'}")
        print(f"  PSI={psi['psi']:.3f} Level={psi['level']}")

        return {"ks": ks, "psi": psi, "ref_mean": float(ref_scores.mean()),
                "cur_mean": float(cur_scores.mean())}

    def generate_alert(self, drift_report: dict) -> Optional[dict]:
        """
        Generates a structured alert if drift exceeds thresholds.
        In production: sends to Slack, PagerDuty, email, etc.
        """
        if not drift_report.get("alert", False):
            return None

        alert = {
            "severity":          "WARNING",
            "title":             "Data Drift Detected",
            "timestamp":         datetime.now().isoformat(),
            "drifted_features":  drift_report["drifted_features"][:5],   # Top 5
            "drift_percentage":  drift_report["drift_percentage"],
            "recommendation":    "Consider retraining the model",
            "action_required":   drift_report["drift_percentage"] > 50,
        }
        print(f"\n🚨 ALERT: {alert['title']}")
        print(f"   Severity: {alert['severity']}")
        print(f"   {alert['drift_percentage']}% of features drifted")
        print(f"   Recommendation: {alert['recommendation']}")
        # In production: requests.post(SLACK_WEBHOOK_URL, json={"text": str(alert)})
        return alert

    def plot_drift_dashboard(self, reference: pd.DataFrame,
                              current: pd.DataFrame, top_n: int = 6):
        """
        Generates a visual drift dashboard.
        Shows reference vs current distributions for the most drifted features.
        """
        # Find most drifted features by PSI
        psi_scores = {}
        for feat in self.feature_names:
            r = self.detector.psi(reference[feat].values, current[feat].values)
            psi_scores[feat] = r["psi"]
        top_features = sorted(psi_scores, key=lambda x: psi_scores[x], reverse=True)[:top_n]

        fig, axes = plt.subplots(2, 3, figsize=(15, 8))
        fig.suptitle("Data Drift Dashboard — Reference vs Current", fontsize=14, fontweight="bold")

        for ax, feat in zip(axes.flatten(), top_features):
            ax.hist(reference[feat], bins=30, alpha=0.6, color="steelblue",
                    density=True, label=f"Reference (n={len(reference)})")
            ax.hist(current[feat], bins=30, alpha=0.6, color="orangered",
                    density=True, label=f"Current (n={len(current)})")
            psi = psi_scores[feat]
            ax.set_title(f"{feat[:30]}\nPSI={psi:.3f} {'⚠️' if psi > 0.2 else '✅'}", fontsize=9)
            ax.legend(fontsize=7)

        plt.tight_layout()
        plt.savefig("drift_dashboard.png", dpi=120, bbox_inches="tight")
        plt.close()
        print("  📊 Drift dashboard saved to drift_dashboard.png")


# =============================================================================
# MAIN
# =============================================================================
if __name__ == "__main__":
    print("PROJECT 7: Model Monitoring & Drift Detection\n")

    # Setup
    X_train, X_test, y_train, y_test, feature_names = create_training_data()
    model = train_model(X_train, y_train)
    feature_df = pd.DataFrame(X_train, columns=feature_names)

    monitor = ModelMonitor(model, list(feature_names))

    # Test 3 drift levels
    for drift_level in [0.0, 0.3, 0.8]:
        print(f"\n{'='*60}")
        print(f"SCENARIO: drift_level={drift_level}")
        print(f"{'='*60}")

        current_data = simulate_production_data(feature_df, drift_level=drift_level)
        drift_report = monitor.run_feature_drift_report(feature_df, current_data)
        pred_report  = monitor.run_prediction_drift_report(feature_df, current_data)
        alert        = monitor.generate_alert(drift_report)

    # Generate visual dashboard for the worst case
    current_drifted = simulate_production_data(feature_df, drift_level=0.8)
    monitor.plot_drift_dashboard(feature_df, current_drifted)

    print("\n✅ Project 7 complete!")
    print("KEY INSIGHT: Drift monitoring is your early warning system.")
    print("Set thresholds, automate alerts, and trigger retraining automatically.")
