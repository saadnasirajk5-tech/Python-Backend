# =============================================================================
# PROJECT 2: Data Versioning with DVC (Data Version Control)
# =============================================================================
# WHAT YOU LEARN:
#   - Version large datasets like code (with Git + DVC)
#   - Never lose a dataset version — roll back any time
#   - DVC pipelines: define reproducible ML workflows as DAGs
#   - Remote storage: push data to S3 / GCS / Azure
#   - Data lineage: know exactly which data trained which model
#
# CORE CONCEPT:
#   Git tracks code. DVC tracks data + models (large binary files).
#   Together they give you FULL reproducibility: any commit = same code + same data.
#
# INSTALL:
#   pip install dvc dvc-s3 pandas scikit-learn
#
# DVC WORKFLOW (like Git but for data):
#   dvc init          ← Initialize DVC in your repo
#   dvc add data/     ← Start tracking a dataset
#   git add .         ← Commit the .dvc pointer file
#   dvc push          ← Upload data to remote storage
#   dvc pull          ← Download data on another machine
# =============================================================================

import os
import json
import hashlib
import subprocess
import pandas as pd
import numpy as np
from pathlib import Path
from sklearn.datasets import make_classification
from sklearn.model_selection import train_test_split

# =============================================================================
# PART 1: DVC SETUP HELPER
# This script shows you EXACTLY what DVC does under the hood
# so you understand it — not just run commands blindly.
# =============================================================================

class DVCWorkflowDemo:
    """
    Demonstrates the full DVC workflow programmatically.
    In real usage you'd run DVC CLI commands, but this shows what happens internally.
    """

    def __init__(self, project_root: str = "."):
        self.root      = Path(project_root)
        self.data_dir  = self.root / "data"
        self.dvc_dir   = self.root / ".dvc"
        self.data_dir.mkdir(exist_ok=True)

    # ─── Step 1: Generate versioned datasets ─────────────────────────────────
    def generate_dataset_v1(self):
        """
        Version 1 of our dataset: 1000 samples, 20 features, 2 classes.
        In real life this would be your initial data extract from a database.
        """
        X, y = make_classification(
            n_samples=1000, n_features=20, n_informative=10,
            n_redundant=5, random_state=42
        )
        df = pd.DataFrame(X, columns=[f"feature_{i}" for i in range(20)])
        df["target"] = y

        path = self.data_dir / "dataset_v1.csv"
        df.to_csv(path, index=False)
        print(f"✅ Generated dataset v1: {len(df)} rows → {path}")
        return path

    def generate_dataset_v2(self):
        """
        Version 2: More data + a new engineered feature added.
        Simulates what happens when your data team adds new signals.
        """
        X, y = make_classification(
            n_samples=2000, n_features=20, n_informative=12,  # More samples + informative
            n_redundant=4, random_state=42
        )
        df = pd.DataFrame(X, columns=[f"feature_{i}" for i in range(20)])

        # Add an engineered feature: interaction between two features
        df["feature_interaction"] = df["feature_0"] * df["feature_1"]
        df["target"] = y

        path = self.data_dir / "dataset_v2.csv"
        df.to_csv(path, index=False)
        print(f"✅ Generated dataset v2: {len(df)} rows, new features → {path}")
        return path

    # ─── Step 2: Compute data hash (what DVC does internally) ────────────────
    def compute_data_hash(self, file_path: str) -> str:
        """
        DVC identifies each version of a file by its MD5 hash.
        This hash is stored in the .dvc file that gets committed to Git.
        The actual data lives in .dvc/cache/ or a remote.
        """
        hasher = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                hasher.update(chunk)
        return hasher.hexdigest()

    # ─── Step 3: Create .dvc pointer file (what `dvc add` creates) ───────────
    def create_dvc_pointer(self, file_path: str) -> dict:
        """
        DVC pointer file (.dvc) is a tiny YAML/JSON that stores:
          - md5 hash of the data file
          - file size
          - path
        This tiny file is what goes into Git — NOT the large data file!
        The actual data goes to the DVC cache or remote storage.
        """
        file_path = Path(file_path)
        data_hash = self.compute_data_hash(file_path)
        file_size = file_path.stat().st_size

        pointer = {
            "outs": [{
                "md5":  data_hash,
                "size": file_size,
                "path": str(file_path.name),
            }]
        }

        pointer_path = str(file_path) + ".dvc"
        with open(pointer_path, "w") as f:
            json.dump(pointer, f, indent=2)

        print(f"📌 DVC pointer created: {pointer_path}")
        print(f"   MD5: {data_hash} | Size: {file_size:,} bytes")
        return pointer

    # ─── Step 4: Data validation ─────────────────────────────────────────────
    def validate_dataset(self, file_path: str) -> dict:
        """
        CRITICAL in real MLOps: validate data BEFORE training.
        Catch schema changes, null values, distribution drift early.
        This is called a 'data quality gate'.
        """
        df = pd.read_csv(file_path)

        validation_results = {
            "file": file_path,
            "rows": len(df),
            "columns": list(df.columns),
            "null_counts": df.isnull().sum().to_dict(),
            "dtypes": {c: str(t) for c, t in df.dtypes.items()},
            "has_target": "target" in df.columns,
            "class_balance": df["target"].value_counts(normalize=True).to_dict() if "target" in df.columns else {},
            "feature_stats": df.describe().to_dict(),
            "passed": True,
            "errors": []
        }

        # ── Validation rules ─────────────────────────────────────────────────
        # Rule 1: No missing values allowed
        total_nulls = sum(validation_results["null_counts"].values())
        if total_nulls > 0:
            validation_results["errors"].append(f"Found {total_nulls} null values")
            validation_results["passed"] = False

        # Rule 2: Target column must exist
        if not validation_results["has_target"]:
            validation_results["errors"].append("Missing 'target' column")
            validation_results["passed"] = False

        # Rule 3: Class imbalance check (warn if < 20% minority class)
        if validation_results["class_balance"]:
            min_class_frac = min(validation_results["class_balance"].values())
            if min_class_frac < 0.2:
                validation_results["errors"].append(
                    f"Severe class imbalance: minority class = {min_class_frac:.1%}"
                )

        # Rule 4: Minimum row count
        if len(df) < 100:
            validation_results["errors"].append(f"Too few rows: {len(df)} < 100 minimum")
            validation_results["passed"] = False

        status = "✅ PASSED" if validation_results["passed"] else "❌ FAILED"
        print(f"Data validation {status}: {file_path}")
        if validation_results["errors"]:
            for err in validation_results["errors"]:
                print(f"  ⚠️  {err}")

        return validation_results

    # ─── Step 5: Split and save train/val/test (tracked by DVC) ──────────────
    def create_data_splits(self, raw_path: str, version: str = "v1"):
        """
        Creates train/val/test splits and saves them.
        Each split file is tracked separately by DVC.
        This ensures the exact same splits are used for training vs evaluation.
        """
        df = pd.read_csv(raw_path)

        # 70% train, 15% val, 15% test — standard split ratios
        X = df.drop("target", axis=1)
        y = df["target"]
        X_temp, X_test, y_temp, y_test = train_test_split(
            X, y, test_size=0.15, random_state=42, stratify=y
        )
        X_train, X_val, y_train, y_val = train_test_split(
            X_temp, y_temp, test_size=0.176, random_state=42, stratify=y_temp
            # 0.176 of 85% ≈ 15% of total
        )

        splits = {
            "train": (X_train, y_train),
            "val":   (X_val,   y_val),
            "test":  (X_test,  y_test),
        }
        split_dir = self.data_dir / f"splits_{version}"
        split_dir.mkdir(exist_ok=True)

        for split_name, (X_split, y_split) in splits.items():
            split_df = X_split.copy()
            split_df["target"] = y_split.values
            path = split_dir / f"{split_name}.csv"
            split_df.to_csv(path, index=False)
            self.create_dvc_pointer(path)
            print(f"  Saved {split_name}: {len(split_df)} rows → {path}")

        return split_dir


# =============================================================================
# PART 2: DVC PIPELINE (dvc.yaml)
# A DVC pipeline is a DAG where each stage has:
#   - deps:   input files (if they change, stage reruns)
#   - cmd:    command to execute
#   - outs:   output files (cached by DVC)
# =============================================================================

DVC_YAML_CONTENT = """
# dvc.yaml — defines your reproducible ML pipeline as a DAG
# Run with: dvc repro
# DVC will only re-run stages whose deps have changed (smart caching!)

stages:

  # Stage 1: Download / prepare raw data
  prepare_data:
    cmd: python prepare_data.py
    deps:
      - prepare_data.py          # Reruns if the script changes
    outs:
      - data/raw/dataset.csv     # Output tracked by DVC (not Git)
    params:
      - params.yaml:             # Read params from this file
        - data.random_seed
        - data.n_samples

  # Stage 2: Validate + split data
  split_data:
    cmd: python split_data.py
    deps:
      - split_data.py
      - data/raw/dataset.csv     # Depends on Stage 1 output
    outs:
      - data/train.csv
      - data/val.csv
      - data/test.csv
    params:
      - params.yaml:
        - data.test_size
        - data.val_size

  # Stage 3: Train the model
  train:
    cmd: python train_model.py
    deps:
      - train_model.py
      - data/train.csv
      - data/val.csv
    outs:
      - models/model.pkl         # Model artifact tracked by DVC
    params:
      - params.yaml:             # All training params tracked
        - model.n_estimators
        - model.max_depth
        - model.learning_rate
    metrics:
      - metrics/train_metrics.json:   # DVC tracks these as metrics
          cache: false

  # Stage 4: Evaluate on held-out test set
  evaluate:
    cmd: python evaluate.py
    deps:
      - evaluate.py
      - models/model.pkl
      - data/test.csv
    metrics:
      - metrics/test_metrics.json:
          cache: false
    plots:
      - plots/confusion_matrix.csv:   # DVC can plot these automatically
          cache: false
          x: actual
          y: predicted
"""

DVC_PARAMS_YAML = """
# params.yaml — all experiment parameters in one place
# DVC tracks which params changed between runs
# MLflow also reads these for logging

data:
  random_seed: 42
  n_samples: 10000
  test_size: 0.15
  val_size: 0.15

model:
  type: random_forest
  n_estimators: 100
  max_depth: 10
  learning_rate: 0.1    # Used if model.type = gradient_boosting
  min_samples_leaf: 2

training:
  early_stopping_rounds: 10
  eval_metric: roc_auc
"""

def write_dvc_config_files():
    """Writes the DVC config files to disk so you can use them."""
    with open("dvc.yaml", "w") as f:
        f.write(DVC_YAML_CONTENT)
    with open("params.yaml", "w") as f:
        f.write(DVC_PARAMS_YAML)
    print("✅ Written: dvc.yaml and params.yaml")
    print("   Run: dvc repro  to execute the full pipeline")
    print("   Run: dvc dag    to visualize the pipeline DAG")


# =============================================================================
# PART 3: REMOTE STORAGE CONFIGURATION
# (What you'd set up for a real team)
# =============================================================================

def show_remote_storage_setup():
    """
    Prints the commands to set up DVC with cloud storage.
    This lets your whole team share the same datasets.
    """
    print("""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
DVC REMOTE STORAGE SETUP (run these once per project)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# Option A: AWS S3 (most common in production)
dvc remote add -d myremote s3://your-bucket/dvc-data
dvc remote modify myremote region us-east-1
# Uses your AWS credentials automatically (IAM role or ~/.aws/credentials)

# Option B: Google Cloud Storage
dvc remote add -d myremote gs://your-bucket/dvc-data

# Option C: Azure Blob Storage
dvc remote add -d myremote azure://your-container/dvc-data

# Option D: SSH server (great for on-premise)
dvc remote add -d myremote ssh://user@server:/path/to/dvc-data

# After setup, push/pull data with:
dvc push    ← Upload all tracked files to remote
dvc pull    ← Download latest versions from remote

# Share data with teammates:
git push    ← Push code + .dvc pointer files
dvc push    ← Push actual data to cloud

# Teammate workflow:
git pull    ← Get latest code + pointers
dvc pull    ← Download the exact data versions those pointers point to
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
""")


# =============================================================================
# MAIN: Run the full demo
# =============================================================================
if __name__ == "__main__":
    print("PROJECT 2: Data Versioning with DVC\n")

    demo = DVCWorkflowDemo()

    # Generate two dataset versions
    path_v1 = demo.generate_dataset_v1()
    path_v2 = demo.generate_dataset_v2()

    # Show how DVC tracks them
    print("\n--- DVC Pointer Files (what goes into Git) ---")
    demo.create_dvc_pointer(path_v1)
    demo.create_dvc_pointer(path_v2)

    # Validate both datasets
    print("\n--- Data Validation ---")
    demo.validate_dataset(path_v1)
    demo.validate_dataset(path_v2)

    # Create train/val/test splits (DVC tracks each split file)
    print("\n--- Creating Data Splits ---")
    splits_v1 = demo.create_data_splits(path_v1, version="v1")
    splits_v2 = demo.create_data_splits(path_v2, version="v2")

    # Write DVC pipeline config files
    print("\n--- Writing DVC Config Files ---")
    write_dvc_config_files()

    # Show remote storage setup instructions
    show_remote_storage_setup()

    print("\n✅ Project 2 complete!")
    print("\nNEXT STEPS:")
    print("  pip install dvc dvc-s3")
    print("  git init && dvc init")
    print("  dvc add data/")
    print("  dvc repro       ← runs the full pipeline")
    print("  dvc metrics show ← compare metrics across commits")
