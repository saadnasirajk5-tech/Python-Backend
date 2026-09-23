# =============================================================================
# PROJECT 4: Feature Store (from scratch + Feast overview)
# =============================================================================
# WHAT YOU LEARN:
#   - What a feature store is and WHY it's critical for production ML
#   - Build a minimal feature store from scratch to understand internals
#   - Offline store (for training) vs Online store (for serving, low latency)
#   - Feature engineering pipelines that feed the store
#   - Point-in-time correct feature retrieval (the hardest part!)
#   - How Feast, Hopsworks, and Tecton work conceptually
#
# CORE CONCEPT:
#   Without a feature store, every team recomputes the same features differently.
#   The "training-serving skew" problem: features computed differently at train
#   time vs serve time → model degrades silently in production.
#   Feature store solves this by computing once, serving everywhere.
#
# INSTALL:
#   pip install pandas numpy scikit-learn feast redis (optional: feast[redis])
# =============================================================================

import os
import json
import sqlite3
import hashlib
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import List, Dict, Optional, Any
from sklearn.preprocessing import StandardScaler, LabelEncoder

# =============================================================================
# PART 1: FEATURE DEFINITIONS
# Define features once → use everywhere (training + serving)
# This is the core idea of a feature store
# =============================================================================

@dataclass
class FeatureDefinition:
    """
    A feature definition describes a single feature:
    - What it is (name, description)
    - How to compute it (dtype, transformation)
    - Where it lives (entity it belongs to)
    - Freshness requirements (how stale is OK)
    """
    name:        str
    entity:      str        # e.g. "customer_id" — what this feature describes
    dtype:       str        # "float", "int", "string", "bool"
    description: str
    ttl_hours:   int = 24   # Max age before feature is considered stale


@dataclass
class FeatureView:
    """
    A FeatureView groups related features for the same entity.
    Think of it as a table in your feature store.
    e.g. "customer_transaction_features" has: total_spend, avg_basket, txn_count
    """
    name:     str
    entity:   str                        # Which entity's features this describes
    features: List[FeatureDefinition]    # Features in this view
    ttl_hours: int = 24                  # Default TTL for all features in this view

    def feature_names(self) -> List[str]:
        return [f.name for f in self.features]


# Define our feature catalog — this is the "schema" of our feature store
CUSTOMER_FEATURES = FeatureView(
    name="customer_transaction_features",
    entity="customer_id",
    features=[
        FeatureDefinition("total_spend_30d",    "customer_id", "float", "Total spend in last 30 days"),
        FeatureDefinition("transaction_count_30d","customer_id","int",   "Number of transactions in 30 days"),
        FeatureDefinition("avg_basket_size",     "customer_id", "float", "Average transaction value"),
        FeatureDefinition("days_since_last_txn", "customer_id", "int",   "Days since most recent transaction"),
        FeatureDefinition("preferred_category",  "customer_id", "string","Most purchased product category"),
        FeatureDefinition("churn_risk_score",    "customer_id", "float", "Computed churn risk 0-1"),
    ]
)

USER_PROFILE_FEATURES = FeatureView(
    name="user_profile_features",
    entity="customer_id",
    features=[
        FeatureDefinition("age_bucket",       "customer_id", "string", "Age group: 18-25, 26-35, etc."),
        FeatureDefinition("tenure_months",    "customer_id", "int",    "Months as customer"),
        FeatureDefinition("loyalty_tier",     "customer_id", "string", "Bronze/Silver/Gold/Platinum"),
        FeatureDefinition("has_mobile_app",   "customer_id", "bool",   "Whether customer uses mobile app"),
        FeatureDefinition("email_open_rate",  "customer_id", "float",  "30-day email campaign open rate"),
    ]
)


# =============================================================================
# PART 2: THE FEATURE STORE (simplified implementation)
# =============================================================================

class FeatureStore:
    """
    A minimal feature store with two stores:
    - Offline Store: historical features for training (slow, cheap, large)
    - Online Store:  latest features for serving  (fast, expensive, small)

    Real feature stores (Feast, Hopsworks) do exactly this, at scale.
    """

    def __init__(self, store_dir: str = "./feature_store"):
        self.store_dir   = Path(store_dir)
        self.offline_dir = self.store_dir / "offline"
        self.online_db   = self.store_dir / "online.db"   # SQLite as online store
        self.store_dir.mkdir(exist_ok=True)
        self.offline_dir.mkdir(exist_ok=True)

        # Initialize online store (SQLite simulates Redis/DynamoDB)
        self._init_online_store()
        print(f"✅ FeatureStore initialized at {self.store_dir}")

    def _init_online_store(self):
        """Creates the online store schema. In production this is Redis or DynamoDB."""
        conn = sqlite3.connect(self.online_db)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS online_features (
                entity_id    TEXT NOT NULL,
                feature_name TEXT NOT NULL,
                value        TEXT NOT NULL,      -- JSON-serialized value
                event_time   TEXT NOT NULL,      -- When this feature was valid
                created_at   TEXT NOT NULL,      -- When it was written to store
                PRIMARY KEY  (entity_id, feature_name)
            )
        """)
        conn.commit(); conn.close()

    # ─── OFFLINE STORE: Write and read historical features ───────────────────

    def materialize_offline(self, feature_view: FeatureView,
                            feature_df: pd.DataFrame, event_time_col: str = "event_time"):
        """
        Writes features to the offline store (Parquet files).
        `feature_df` must have: entity_id, event_time, and all feature columns.

        The offline store is append-only — we keep all historical versions.
        This allows POINT-IN-TIME correct feature retrieval for training.
        """
        required_cols = {"customer_id", event_time_col} | set(feature_view.feature_names())
        missing = required_cols - set(feature_df.columns)
        if missing:
            raise ValueError(f"Missing columns: {missing}")

        # Partition by date for efficient time-range queries
        feature_df[event_time_col] = pd.to_datetime(feature_df[event_time_col])
        feature_df["date_partition"] = feature_df[event_time_col].dt.date

        output_path = self.offline_dir / f"{feature_view.name}.parquet"
        # In production: partitioned Parquet on S3 (Hive partitioning)
        feature_df.to_parquet(output_path, index=False)
        print(f"  📥 Offline store: wrote {len(feature_df)} rows to {output_path}")

    def get_historical_features(self, entity_df: pd.DataFrame,
                                 feature_views: List[FeatureView],
                                 label_col: str = None) -> pd.DataFrame:
        """
        POINT-IN-TIME CORRECT feature retrieval — the hardest part of feature stores!

        The problem: If you trained on 2023-01-01 data but used features computed
        on 2023-06-01, you used FUTURE data → data leakage → optimistic metrics!

        Point-in-time correct = for each training row's timestamp, get feature
        values that were available AT THAT TIME (not later values).

        entity_df must have: customer_id, event_time (the label timestamp)
        """
        entity_df = entity_df.copy()
        entity_df["event_time"] = pd.to_datetime(entity_df["event_time"])

        result = entity_df.copy()

        for fv in feature_views:
            offline_path = self.offline_dir / f"{fv.name}.parquet"
            if not offline_path.exists():
                print(f"  ⚠️  No offline data for {fv.name} — skipping")
                continue

            hist_df = pd.read_parquet(offline_path)
            hist_df["event_time"] = pd.to_datetime(hist_df["event_time"])

            # Point-in-time join: for each entity+timestamp in entity_df,
            # find the LATEST feature row that occurred BEFORE that timestamp
            # This is the "as-of join" — Feast does exactly this
            merged = pd.merge_asof(
                result.sort_values("event_time"),            # Left: label timestamps
                hist_df.sort_values("event_time"),           # Right: feature timestamps
                on="event_time",
                by="customer_id",
                direction="backward",                        # Most recent feature BEFORE label time
                suffixes=("", f"_{fv.name}")
            )
            result = merged

        print(f"  ✅ Retrieved {len(result)} rows with point-in-time correct features")
        return result

    # ─── ONLINE STORE: Write and read latest features (for serving) ──────────

    def materialize_online(self, feature_view: FeatureView, feature_df: pd.DataFrame):
        """
        Writes the LATEST feature values to the online store.
        The online store only keeps the most recent value per entity — optimized for speed.
        Called during "materialization" — typically run every hour/day.
        """
        conn = sqlite3.connect(self.online_db)
        now = datetime.now().isoformat()

        written = 0
        for _, row in feature_df.iterrows():
            entity_id  = str(row["customer_id"])
            event_time = str(row.get("event_time", now))

            for feat in feature_view.features:
                if feat.name in row:
                    # Use INSERT OR REPLACE to upsert (overwrite old value)
                    conn.execute("""
                        INSERT OR REPLACE INTO online_features
                        (entity_id, feature_name, value, event_time, created_at)
                        VALUES (?, ?, ?, ?, ?)
                    """, (entity_id, feat.name, json.dumps(row[feat.name]), event_time, now))
                    written += 1

        conn.commit(); conn.close()
        print(f"  ⚡ Online store: upserted {written} feature values")

    def get_online_features(self, customer_ids: List[str],
                             feature_view: FeatureView) -> pd.DataFrame:
        """
        Fetches latest features for a list of customers — used at prediction time.
        This must be FAST (< 10ms in production) — it's on the critical path!
        In production: Redis MGET for sub-millisecond latency.
        """
        conn = sqlite3.connect(self.online_db)
        placeholders = ",".join(["?"] * len(customer_ids))

        rows = conn.execute(f"""
            SELECT entity_id, feature_name, value, event_time
            FROM online_features
            WHERE entity_id IN ({placeholders})
              AND feature_name IN ({placeholders})
        """, customer_ids + feature_view.feature_names()).fetchall()
        conn.close()

        if not rows:
            return pd.DataFrame()

        # Pivot from long format to wide format (one row per customer)
        long_df = pd.DataFrame(rows, columns=["customer_id","feature","value","event_time"])
        long_df["value"] = long_df["value"].apply(json.loads)
        wide_df = long_df.pivot(index="customer_id", columns="feature", values="value").reset_index()
        print(f"  ⚡ Online fetch: {len(wide_df)} customers, {len(wide_df.columns)-1} features")
        return wide_df


# =============================================================================
# PART 3: FEATURE ENGINEERING PIPELINE
# Transforms raw data into features, then materializes to both stores
# =============================================================================

def generate_raw_transactions(n_customers: int = 500, n_days: int = 90) -> pd.DataFrame:
    """Generates synthetic transaction data — replace with your database query."""
    np.random.seed(42)
    records = []
    categories = ["Electronics", "Clothing", "Food", "Sports", "Books"]

    for cid in range(1, n_customers + 1):
        n_txns = np.random.poisson(lam=15)   # Average 15 transactions per customer
        for _ in range(n_txns):
            days_ago = np.random.randint(0, n_days)
            records.append({
                "customer_id": f"cust_{cid:04d}",
                "transaction_date": datetime.now() - timedelta(days=days_ago),
                "amount":    round(np.random.lognormal(4, 0.8), 2),  # Log-normal spend
                "category":  np.random.choice(categories),
            })
    return pd.DataFrame(records)


def engineer_features(raw_df: pd.DataFrame, reference_date: datetime = None) -> pd.DataFrame:
    """
    Computes all features from raw transactions.
    This same function must be used for BOTH training AND serving to avoid skew!
    (In a real feature store, this runs in a Spark job or dbt model)
    """
    if reference_date is None:
        reference_date = datetime.now()

    raw_df["transaction_date"] = pd.to_datetime(raw_df["transaction_date"])

    # Only consider transactions in the last 30 days
    cutoff = reference_date - timedelta(days=30)
    recent = raw_df[raw_df["transaction_date"] >= cutoff]

    features = []
    for cid, group in recent.groupby("customer_id"):
        all_txns  = raw_df[raw_df["customer_id"] == cid]
        last_date = all_txns["transaction_date"].max()

        feature_row = {
            "customer_id":           cid,
            "event_time":            reference_date.isoformat(),  # When features were computed
            "total_spend_30d":       round(group["amount"].sum(), 2),
            "transaction_count_30d": len(group),
            "avg_basket_size":       round(group["amount"].mean(), 2),
            "days_since_last_txn":   (reference_date - last_date).days,
            "preferred_category":    group["category"].value_counts().index[0],
            "churn_risk_score":      round(min((reference_date - last_date).days / 90, 1.0), 4),
        }
        features.append(feature_row)

    return pd.DataFrame(features)


# =============================================================================
# MAIN
# =============================================================================
if __name__ == "__main__":
    print("PROJECT 4: Feature Store\n")

    # ── Generate raw data ─────────────────────────────────────────────────────
    print("1. Generating raw transaction data...")
    raw_df = generate_raw_transactions(n_customers=200, n_days=90)
    print(f"   {len(raw_df)} transactions for {raw_df['customer_id'].nunique()} customers")

    # ── Engineer features ─────────────────────────────────────────────────────
    print("\n2. Engineering features...")
    feature_df = engineer_features(raw_df)
    print(f"   {len(feature_df)} feature rows computed")
    print(f"   Features: {list(feature_df.columns)}")

    # ── Initialize feature store ──────────────────────────────────────────────
    print("\n3. Initializing feature store...")
    fs = FeatureStore("./feature_store_demo")

    # ── Materialize to offline store ─────────────────────────────────────────
    print("\n4. Materializing to offline store (for training)...")
    fs.materialize_offline(CUSTOMER_FEATURES, feature_df)

    # ── Materialize to online store ───────────────────────────────────────────
    print("\n5. Materializing to online store (for serving)...")
    fs.materialize_online(CUSTOMER_FEATURES, feature_df)

    # ── Demo: Training time — point-in-time correct features ─────────────────
    print("\n6. Retrieving training features (point-in-time correct)...")
    label_df = pd.DataFrame({
        "customer_id": feature_df["customer_id"].sample(50, random_state=42),
        "event_time":  [datetime.now() - timedelta(days=np.random.randint(1, 30))
                        for _ in range(50)],
        "churned":     np.random.randint(0, 2, 50)
    })
    training_data = fs.get_historical_features(label_df, [CUSTOMER_FEATURES])
    print(f"   Training dataset shape: {training_data.shape}")

    # ── Demo: Serving time — low-latency online features ──────────────────────
    print("\n7. Serving-time feature retrieval (online store)...")
    serving_customers = feature_df["customer_id"].head(5).tolist()
    online_features = fs.get_online_features(serving_customers, CUSTOMER_FEATURES)
    print(f"   Online features retrieved: {online_features.shape}")
    print(online_features.head(3).to_string())

    print("\n✅ Project 4 complete!")
    print("\nKEY LESSON: The engineer_features() function must be IDENTICAL")
    print("at training time and serving time. Feature stores enforce this.")
