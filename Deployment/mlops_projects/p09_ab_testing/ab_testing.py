# =============================================================================
# PROJECT 9: A/B Testing for ML Models
# =============================================================================
# WHAT YOU LEARN:
#   - Shadow mode deployment (log predictions without serving them)
#   - Traffic splitting: route X% to Model A, Y% to Model B
#   - Statistical significance testing for model comparison
#   - Multi-armed bandit: automatically route traffic to the better model
#   - Canary deployment: gradually ramp up new model traffic
#   - Tracking business metrics (not just ML metrics) per model variant
#
# CORE CONCEPT:
#   ROC-AUC on your test set doesn't tell you if the model is better
#   IN PRODUCTION. A/B testing gives you ground truth from real users.
#   Example: Model B has higher test ROC-AUC but lower click-through rate
#   in production — the test set distribution was wrong.
#
# INSTALL:
#   pip install scipy numpy pandas fastapi
# =============================================================================

import hashlib
import json
import random
import time
import uuid
from collections import defaultdict
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from scipy import stats
import pickle
from pathlib import Path
from sklearn.datasets import load_breast_cancer
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler


# =============================================================================
# MODEL VARIANTS: Define what we're testing
# =============================================================================

@dataclass
class ModelVariant:
    """Represents one variant (A or B) in an A/B test."""
    name:           str              # e.g. "control", "treatment_v2"
    model_path:     str              # Path to the .pkl file
    traffic_weight: float = 0.5     # Fraction of traffic to send here (0.0 to 1.0)
    description:    str  = ""
    model:          object = None   # Loaded model (populated at runtime)


# =============================================================================
# EXPERIMENT TRACKER: Stores all predictions and outcomes
# =============================================================================

@dataclass
class PredictionRecord:
    """One prediction event — logged for statistical analysis."""
    record_id:       str
    variant:         str             # Which model made this prediction
    entity_id:       str             # Customer/user ID
    features_hash:   str             # Hash of input features (for matching)
    prediction:      int             # Model output
    confidence:      float           # Model probability
    timestamp:       str
    # Outcome is filled in LATER when ground truth arrives (e.g. did they churn?)
    outcome:         Optional[int]  = None
    outcome_time:    Optional[str]  = None
    # Business metrics
    conversion:      Optional[bool] = None
    revenue:         Optional[float]= None


class ExperimentStore:
    """
    In-memory store for A/B test records.
    In production: use PostgreSQL, BigQuery, or Redshift.
    """

    def __init__(self):
        self.records: Dict[str, PredictionRecord] = {}     # record_id → record
        self.variant_counts: Dict[str, int] = defaultdict(int)

    def log_prediction(self, record: PredictionRecord):
        self.records[record.record_id] = record
        self.variant_counts[record.variant] += 1

    def log_outcome(self, record_id: str, outcome: int,
                    conversion: bool = None, revenue: float = None):
        """
        Called when ground truth arrives.
        In a churn model: outcome arrives when we know if they actually churned.
        """
        if record_id in self.records:
            r = self.records[record_id]
            r.outcome      = outcome
            r.outcome_time = datetime.now().isoformat()
            r.conversion   = conversion
            r.revenue      = revenue

    def get_variant_data(self, variant: str) -> List[PredictionRecord]:
        return [r for r in self.records.values() if r.variant == variant]

    def to_dataframe(self) -> pd.DataFrame:
        rows = [asdict(r) for r in self.records.values()]
        return pd.DataFrame(rows) if rows else pd.DataFrame()


# =============================================================================
# TRAFFIC SPLITTER: Decides which model serves each request
# =============================================================================

class TrafficSplitter:
    """
    Routes incoming requests to model variants.
    Uses consistent hashing so the SAME entity always gets the same model
    (important for fair comparison — you don't want a user to get A/B/A/B).
    """

    def __init__(self, variants: List[ModelVariant]):
        self.variants = variants
        self._validate_weights()

    def _validate_weights(self):
        total = sum(v.traffic_weight for v in self.variants)
        assert abs(total - 1.0) < 1e-6, f"Traffic weights must sum to 1.0, got {total}"

    def assign_variant(self, entity_id: str) -> ModelVariant:
        """
        Consistently assigns an entity to a variant using hashing.
        Same entity_id → always same variant (sticky assignment).
        This prevents the same user from experiencing model inconsistency.
        """
        # MD5 hash → integer 0-9999 → use as "slot" in [0, 10000)
        hash_val = int(hashlib.md5(entity_id.encode()).hexdigest(), 16) % 10000

        # Map slot to variant based on cumulative weight ranges
        cumulative = 0
        for variant in self.variants:
            cumulative += variant.traffic_weight * 10000
            if hash_val < cumulative:
                return variant

        return self.variants[-1]   # Fallback (shouldn't reach here)

    def update_weights(self, new_weights: Dict[str, float]):
        """
        Dynamically updates traffic weights (for canary deployment / bandit).
        new_weights = {"control": 0.2, "challenger": 0.8}
        """
        for variant in self.variants:
            if variant.name in new_weights:
                variant.traffic_weight = new_weights[variant.name]
        self._validate_weights()
        print(f"  Traffic updated: {new_weights}")


# =============================================================================
# SHADOW MODE: Run new model silently alongside production
# =============================================================================

class ShadowDeployment:
    """
    Shadow mode: the challenger model runs on ALL requests but its
    predictions are NOT served to users. They're only logged for comparison.

    Use this before A/B testing to catch bugs safely.
    If shadow model crashes → no user impact.
    If shadow model gives wildly different predictions → investigate before A/B.
    """

    def __init__(self, production: ModelVariant, shadow: ModelVariant):
        self.production = production
        self.shadow     = shadow
        self.shadow_log = []

    def predict(self, features: np.ndarray, entity_id: str) -> dict:
        """
        Serves production prediction to user.
        Runs shadow model in background and logs discrepancies.
        """
        prod_pred   = int(self.production.model.predict(features.reshape(1, -1))[0])
        prod_proba  = float(self.production.model.predict_proba(features.reshape(1, -1))[0, 1])

        # Shadow model runs silently
        shadow_pred  = int(self.shadow.model.predict(features.reshape(1, -1))[0])
        shadow_proba = float(self.shadow.model.predict_proba(features.reshape(1, -1))[0, 1])

        disagree = prod_pred != shadow_pred
        self.shadow_log.append({
            "entity_id":       entity_id,
            "timestamp":       datetime.now().isoformat(),
            "production_pred": prod_pred,
            "shadow_pred":     shadow_pred,
            "production_conf": round(prod_proba, 4),
            "shadow_conf":     round(shadow_proba, 4),
            "disagreement":    disagree,
        })

        return {"prediction": prod_pred, "confidence": prod_proba, "model": "production"}

    def disagreement_rate(self) -> float:
        """Fraction of predictions where models disagree."""
        if not self.shadow_log:
            return 0.0
        disagrees = sum(1 for r in self.shadow_log if r["disagreement"])
        return disagrees / len(self.shadow_log)

    def report(self):
        total    = len(self.shadow_log)
        disagree = sum(1 for r in self.shadow_log if r["disagreement"])
        print(f"\n  Shadow Deployment Report ({total} requests)")
        print(f"  Disagreement rate: {disagree/total:.1%} ({disagree}/{total})")
        if disagree / max(total, 1) > 0.2:
            print(f"  ⚠️  High disagreement — investigate before A/B testing!")
        else:
            print(f"  ✅ Low disagreement — safe to start A/B test")


# =============================================================================
# STATISTICAL ANALYSIS: Is the difference significant?
# =============================================================================

class ABTestAnalyzer:
    """
    Runs statistical tests to determine if one model variant is
    significantly better than another.
    """

    def __init__(self, store: ExperimentStore):
        self.store = store

    def analyze(self, variant_a: str, variant_b: str,
                 metric: str = "accuracy",     # "accuracy", "conversion", "revenue"
                 alpha: float = 0.05,          # Significance level (5% false positive rate)
                 min_samples: int = 100) -> dict:
        """
        Compares two variants using appropriate statistical tests.

        For binary outcomes (accuracy, conversion): chi-squared test
        For continuous outcomes (revenue, confidence): t-test
        """
        data_a = pd.DataFrame([asdict(r) for r in self.store.get_variant_data(variant_a)])
        data_b = pd.DataFrame([asdict(r) for r in self.store.get_variant_data(variant_b)])

        print(f"\n{'─'*55}")
        print(f"A/B Test: {variant_a} vs {variant_b} on metric={metric}")
        print(f"{'─'*55}")
        print(f"  {variant_a}: n={len(data_a)}, {variant_b}: n={len(data_b)}")

        if len(data_a) < min_samples or len(data_b) < min_samples:
            return {"error": f"Insufficient data. Need {min_samples}, have {len(data_a)}/{len(data_b)}",
                    "significant": False}

        if metric == "accuracy":
            # Need outcome column (ground truth labels)
            labeled_a = data_a.dropna(subset=["outcome"])
            labeled_b = data_b.dropna(subset=["outcome"])

            if len(labeled_a) < 30 or len(labeled_b) < 30:
                return {"error": "Not enough labeled outcomes yet", "significant": False}

            acc_a = (labeled_a["prediction"] == labeled_a["outcome"]).mean()
            acc_b = (labeled_b["prediction"] == labeled_b["outcome"]).mean()

            # Chi-squared test for binary proportions
            correct_a   = int(acc_a * len(labeled_a))
            correct_b   = int(acc_b * len(labeled_b))
            contingency = [[correct_a, len(labeled_a) - correct_a],
                           [correct_b, len(labeled_b) - correct_b]]
            chi2, p_val = stats.chi2_contingency(contingency)[:2]

            metric_a, metric_b = acc_a, acc_b
            test_used = "chi_squared"

        elif metric == "confidence":
            # Use t-test for continuous confidence scores
            metric_a = data_a["confidence"].mean()
            metric_b = data_b["confidence"].mean()
            _, p_val = stats.ttest_ind(data_a["confidence"], data_b["confidence"])
            test_used = "welchs_t_test"

        elif metric == "revenue":
            labeled_a = data_a.dropna(subset=["revenue"])
            labeled_b = data_b.dropna(subset=["revenue"])
            metric_a  = labeled_a["revenue"].mean()
            metric_b  = labeled_b["revenue"].mean()
            _, p_val  = stats.mannwhitneyu(labeled_a["revenue"], labeled_b["revenue"],
                                           alternative="two-sided")
            test_used = "mann_whitney_u"
        else:
            return {"error": f"Unknown metric: {metric}"}

        significant    = p_val < alpha
        improvement    = (metric_b - metric_a) / max(metric_a, 1e-10)
        winner         = variant_b if metric_b > metric_a else variant_a

        result = {
            "variant_a":    variant_a,
            "variant_b":    variant_b,
            "metric":       metric,
            "metric_a":     round(float(metric_a), 4),
            "metric_b":     round(float(metric_b), 4),
            "improvement":  round(float(improvement), 4),
            "p_value":      round(float(p_val), 4),
            "alpha":        alpha,
            "significant":  significant,
            "winner":       winner if significant else "inconclusive",
            "test_used":    test_used,
            "n_a":          len(data_a),
            "n_b":          len(data_b),
        }

        status = "✅ SIGNIFICANT" if significant else "❌ NOT SIGNIFICANT"
        print(f"  {variant_a}: {metric}={metric_a:.4f}")
        print(f"  {variant_b}: {metric}={metric_b:.4f}")
        print(f"  Improvement: {improvement:+.1%} | p-value={p_val:.4f} | {status}")
        print(f"  Winner: {result['winner']}")
        return result

    def power_analysis(self, effect_size: float = 0.05,
                        alpha: float = 0.05, power: float = 0.80) -> int:
        """
        Calculates required sample size BEFORE running the experiment.
        This prevents the common mistake of stopping early when you see
        a significant result (p-hacking!).

        effect_size: minimum meaningful improvement (0.05 = 5%)
        power:       probability of detecting the effect if it exists (0.8 = 80%)
        """
        from statsmodels.stats.power import TTestIndPower
        analysis = TTestIndPower()
        n = analysis.solve_power(effect_size=effect_size, alpha=alpha, power=power)
        n = int(np.ceil(n))
        print(f"\n  Power Analysis: need {n} samples per variant")
        print(f"  (Effect={effect_size:.2%}, α={alpha}, Power={power:.0%})")
        return n


# =============================================================================
# MULTI-ARMED BANDIT: Automatically route more traffic to the better model
# =============================================================================

class EpsilonGreedyBandit:
    """
    Multi-armed bandit alternative to fixed 50/50 A/B split.
    Epsilon-greedy: with probability epsilon, explore (random variant),
    with probability 1-epsilon, exploit (best known variant).

    Advantage over A/B: learns which model is better DURING the experiment
    and routes more traffic to the winner → less opportunity cost.
    """

    def __init__(self, variant_names: List[str], epsilon: float = 0.1):
        self.epsilon        = epsilon   # Exploration rate
        self.variant_names  = variant_names
        self.counts         = {v: 0   for v in variant_names}   # Times chosen
        self.rewards        = {v: 0.0 for v in variant_names}   # Cumulative reward

    def select_variant(self) -> str:
        """
        Selects a variant using epsilon-greedy strategy.
        With probability epsilon: random choice (exploration)
        With probability 1-epsilon: best known variant (exploitation)
        """
        if random.random() < self.epsilon or all(c == 0 for c in self.counts.values()):
            return random.choice(self.variant_names)   # Explore
        # Exploit: choose variant with highest average reward
        avg_rewards = {v: self.rewards[v] / max(self.counts[v], 1) for v in self.variant_names}
        return max(avg_rewards, key=avg_rewards.get)

    def update(self, variant: str, reward: float):
        """Called after getting feedback. Reward = 1 for correct prediction, 0 otherwise."""
        self.counts[variant]  += 1
        self.rewards[variant] += reward

    def report(self):
        print("\n  Multi-Armed Bandit Status")
        for v in self.variant_names:
            avg = self.rewards[v] / max(self.counts[v], 1)
            print(f"  {v}: chosen={self.counts[v]}, avg_reward={avg:.3f}")


# =============================================================================
# CANARY DEPLOYMENT: Gradual traffic ramp-up
# =============================================================================

class CanaryDeployer:
    """
    Canary deployment: start with 5% traffic to new model,
    gradually increase if metrics look good.
    Roll back immediately if metrics degrade.
    """

    def __init__(self, splitter: TrafficSplitter, store: ExperimentStore):
        self.splitter  = splitter
        self.store     = store
        self.ramp_schedule = [0.05, 0.10, 0.25, 0.50, 0.75, 1.00]
        self.current_step  = 0

    def should_advance(self, challenger_name: str, control_name: str,
                       error_rate_threshold: float = 0.05) -> bool:
        """
        Returns True if the canary is healthy and ready for more traffic.
        In production: checks error rate, latency P99, and business metrics.
        """
        chall_data = self.store.get_variant_data(challenger_name)
        if len(chall_data) < 20:
            return False   # Not enough data yet

        # Check: are there anomalous low-confidence predictions?
        confidences = [r.confidence for r in chall_data]
        low_conf    = sum(1 for c in confidences if c < 0.5) / len(confidences)
        return low_conf < error_rate_threshold

    def advance(self, challenger_name: str, control_name: str):
        """Increases challenger traffic to the next ramp level."""
        if self.current_step >= len(self.ramp_schedule):
            print("  🎉 Canary at 100% — full rollout complete!")
            return

        challenger_weight = self.ramp_schedule[self.current_step]
        self.splitter.update_weights({
            control_name:    1.0 - challenger_weight,
            challenger_name: challenger_weight,
        })
        self.current_step += 1
        print(f"  🐤 Canary advanced to {challenger_weight:.0%} traffic")

    def rollback(self, challenger_name: str, control_name: str, reason: str):
        """Emergency rollback — route all traffic back to control."""
        self.splitter.update_weights({control_name: 1.0, challenger_name: 0.0})
        self.current_step = 0
        print(f"  ⚠️  Canary ROLLBACK: {reason}")


# =============================================================================
# MAIN: Full A/B test simulation
# =============================================================================

def build_demo_models():
    """Build two slightly different models to compare."""
    data = load_breast_cancer()
    X = pd.DataFrame(data.data, columns=data.feature_names)
    y = pd.Series(data.target)
    X_train, _, y_train, _ = train_test_split(X, y, test_size=0.2, random_state=42)

    model_a = Pipeline([("scaler", StandardScaler()),
                        ("model",  RandomForestClassifier(n_estimators=50, random_state=42))])
    model_b = Pipeline([("scaler", StandardScaler()),
                        ("model",  GradientBoostingClassifier(n_estimators=100, random_state=42))])
    model_a.fit(X_train, y_train)
    model_b.fit(X_train, y_train)
    return model_a, model_b


if __name__ == "__main__":
    print("PROJECT 9: A/B Testing for ML Models\n")

    model_a, model_b = build_demo_models()

    # Define variants
    control    = ModelVariant("control",    "", traffic_weight=0.5, model=model_a)
    challenger = ModelVariant("challenger", "", traffic_weight=0.5, model=model_b)

    # Traffic splitter and experiment store
    splitter = TrafficSplitter([control, challenger])
    store    = ExperimentStore()

    # ── Shadow mode first ──────────────────────────────────────────────────────
    print("PHASE 1: Shadow Deployment (challenger silent)")
    shadow = ShadowDeployment(control, challenger)
    data   = load_breast_cancer()

    for i in range(200):
        features = data.data[i % len(data.data)]
        entity   = f"user_{i:04d}"
        shadow.predict(features, entity)
    shadow.report()

    # ── A/B Test ───────────────────────────────────────────────────────────────
    print("\nPHASE 2: A/B Test")
    for i in range(500):
        entity_id = f"user_{i:04d}"
        variant   = splitter.assign_variant(entity_id)
        features  = data.data[i % len(data.data)].reshape(1, -1)
        pred      = int(variant.model.predict(features)[0])
        conf      = float(variant.model.predict_proba(features)[0, pred])

        record = PredictionRecord(
            record_id=str(uuid.uuid4())[:8],
            variant=variant.name,
            entity_id=entity_id,
            features_hash=hashlib.md5(features.tobytes()).hexdigest()[:8],
            prediction=pred,
            confidence=conf,
            timestamp=datetime.now().isoformat(),
            outcome=int(data.target[i % len(data.target)]),   # Simulate same-day label
            conversion=random.random() < (0.3 + pred * 0.1),  # Simulated business metric
            revenue=round(random.uniform(10, 200) * (1 + pred * 0.2), 2),
        )
        store.log_prediction(record)

    # Statistical analysis
    analyzer = ABTestAnalyzer(store)
    result   = analyzer.analyze("control", "challenger", metric="confidence")

    # Multi-armed bandit demo
    print("\nPHASE 3: Multi-Armed Bandit")
    bandit = EpsilonGreedyBandit(["control", "challenger"], epsilon=0.1)
    for i in range(300):
        chosen  = bandit.select_variant()
        variant = control if chosen == "control" else challenger
        features = data.data[i % len(data.data)].reshape(1, -1)
        pred     = int(variant.model.predict(features)[0])
        reward   = float(pred == data.target[i % len(data.target)])
        bandit.update(chosen, reward)
    bandit.report()

    # Canary deployment demo
    print("\nPHASE 4: Canary Deployment")
    canary = CanaryDeployer(splitter, store)
    for step in range(3):
        if canary.should_advance("challenger", "control"):
            canary.advance("challenger", "control")
        else:
            print(f"  Step {step+1}: Not ready to advance yet")

    print("\n✅ Project 9 complete!")
