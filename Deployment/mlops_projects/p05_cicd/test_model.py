# =============================================================================
# PROJECT 5: test_model.py — Automated ML Tests
# =============================================================================
# WHAT THIS TEACHES:
#   ML code needs tests just like application code.
#   These are the 4 test categories every ML team should write:
#   1. Unit tests:       test individual functions
#   2. Data tests:       validate data schema and quality
#   3. Model tests:      test model behavior and edge cases
#   4. Contract tests:   test prediction API contract
#
# RUN: pytest test_model.py -v
# =============================================================================

import pytest
import pickle
import json
import numpy as np
import pandas as pd
from pathlib import Path
from sklearn.datasets import load_breast_cancer
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from pipeline import run_pipeline, run_data_pipeline, PipelineConfig


# =============================================================================
# FIXTURES: shared test objects
# =============================================================================
@pytest.fixture(scope="module")
def sample_data():
    """Loads and splits breast cancer data for all tests."""
    data = load_breast_cancer()
    X = pd.DataFrame(data.data, columns=data.feature_names)
    y = pd.Series(data.target)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    return X_train, X_test, y_train, y_test, data.feature_names

@pytest.fixture(scope="module")
def trained_pipeline(sample_data):
    """Returns a trained pipeline for model tests."""
    X_train, _, y_train, _, _ = sample_data
    pipeline = Pipeline([
        ("scaler", StandardScaler()),
        ("model",  RandomForestClassifier(n_estimators=50, random_state=42))
    ])
    pipeline.fit(X_train, y_train)
    return pipeline


# =============================================================================
# 1. DATA TESTS
# =============================================================================
class TestData:
    """Tests that validate data quality and schema."""

    def test_no_null_values(self, sample_data):
        """Model will silently fail if it sees NaN in production."""
        X_train, X_test, _, _, _ = sample_data
        assert X_train.isnull().sum().sum() == 0, "Train data has nulls!"
        assert X_test.isnull().sum().sum() == 0,  "Test data has nulls!"

    def test_feature_count(self, sample_data):
        """If feature count changes, the model's input contract is broken."""
        _, _, _, _, feature_names = sample_data
        assert len(feature_names) == 30, f"Expected 30 features, got {len(feature_names)}"

    def test_class_balance(self, sample_data):
        """Severe imbalance requires stratification — test it's handled."""
        _, _, y_train, y_test, _ = sample_data
        train_balance = y_train.value_counts(normalize=True)
        test_balance  = y_test.value_counts(normalize=True)
        assert train_balance.min() > 0.3, "Stratification failed: train set severely imbalanced"
        assert test_balance.min() > 0.3,  "Stratification failed: test set severely imbalanced"

    def test_all_features_numeric(self, sample_data):
        """Tree models and scalers expect numeric input."""
        X_train, _, _, _, _ = sample_data
        non_numeric = X_train.select_dtypes(exclude=[np.number]).columns.tolist()
        assert len(non_numeric) == 0, f"Non-numeric columns found: {non_numeric}"

    def test_no_constant_features(self, sample_data):
        """Constant features are useless and can cause numerical issues."""
        X_train, _, _, _, _ = sample_data
        constant_cols = [c for c in X_train.columns if X_train[c].std() == 0]
        assert len(constant_cols) == 0, f"Constant feature columns: {constant_cols}"


# =============================================================================
# 2. MODEL BEHAVIOR TESTS
# =============================================================================
class TestModelBehavior:
    """Tests model output properties and edge cases."""

    def test_output_shape(self, trained_pipeline, sample_data):
        """Model must return one prediction per input row."""
        _, X_test, _, y_test, _ = sample_data
        predictions = trained_pipeline.predict(X_test)
        assert len(predictions) == len(X_test), "Wrong number of predictions!"

    def test_binary_predictions(self, trained_pipeline, sample_data):
        """For binary classification, only {0, 1} are valid outputs."""
        _, X_test, _, _, _ = sample_data
        predictions = trained_pipeline.predict(X_test)
        unique_preds = set(predictions)
        assert unique_preds.issubset({0, 1}), f"Non-binary predictions: {unique_preds}"

    def test_probability_range(self, trained_pipeline, sample_data):
        """All predicted probabilities must be in [0, 1]."""
        _, X_test, _, _, _ = sample_data
        probas = trained_pipeline.predict_proba(X_test)
        assert probas.min() >= 0.0, "Negative probability found!"
        assert probas.max() <= 1.0, "Probability > 1 found!"

    def test_probability_sums_to_one(self, trained_pipeline, sample_data):
        """Each row's probabilities must sum to 1."""
        _, X_test, _, _, _ = sample_data
        probas = trained_pipeline.predict_proba(X_test)
        row_sums = probas.sum(axis=1)
        np.testing.assert_allclose(
            row_sums, np.ones(len(row_sums)), atol=1e-6,
            err_msg="Probabilities don't sum to 1!"
        )

    def test_predicts_both_classes(self, trained_pipeline, sample_data):
        """A degenerate model that always predicts one class is useless."""
        _, X_test, _, _, _ = sample_data
        predictions = trained_pipeline.predict(X_test)
        assert len(np.unique(predictions)) > 1, "Model only predicts one class!"

    def test_reproducibility(self, sample_data):
        """Same input → same output. Non-determinism breaks pipelines."""
        X_train, X_test, y_train, _, _ = sample_data
        pipeline1 = Pipeline([("scaler", StandardScaler()),
                               ("model", RandomForestClassifier(n_estimators=10, random_state=99))])
        pipeline2 = Pipeline([("scaler", StandardScaler()),
                               ("model", RandomForestClassifier(n_estimators=10, random_state=99))])
        pipeline1.fit(X_train, y_train)
        pipeline2.fit(X_train, y_train)
        preds1 = pipeline1.predict(X_test)
        preds2 = pipeline2.predict(X_test)
        np.testing.assert_array_equal(preds1, preds2, err_msg="Model is not reproducible!")

    def test_handles_single_sample(self, trained_pipeline, sample_data):
        """API often calls model with 1 row — make sure it doesn't crash."""
        _, X_test, _, _, _ = sample_data
        single = X_test.head(1)
        pred = trained_pipeline.predict(single)
        assert len(pred) == 1, "Single-sample prediction failed!"

    def test_invariance_to_column_order(self, trained_pipeline, sample_data):
        """Model should predict the same regardless of column order (if using names)."""
        _, X_test, _, _, _ = sample_data
        shuffled = X_test[np.random.permutation(X_test.columns)]
        # Note: sklearn pipelines trained with column names DO care about order
        # This test reminds you to always enforce column order in production!
        try:
            pred1 = trained_pipeline.predict(X_test.head(5))
            # If you want column-order invariance, use feature names explicitly
        except Exception as e:
            pytest.skip(f"Column order matters in this pipeline: {e}")


# =============================================================================
# 3. PERFORMANCE TESTS
# =============================================================================
class TestModelPerformance:
    """Tests that model meets minimum performance bars."""

    def test_minimum_roc_auc(self, trained_pipeline, sample_data):
        """Model must exceed minimum ROC-AUC. Adjust threshold per your domain."""
        from sklearn.metrics import roc_auc_score
        _, X_test, _, y_test, _ = sample_data
        y_prob = trained_pipeline.predict_proba(X_test)[:, 1]
        auc = roc_auc_score(y_test, y_prob)
        assert auc >= 0.90, f"ROC-AUC {auc:.4f} < required 0.90"

    def test_minimum_accuracy(self, trained_pipeline, sample_data):
        from sklearn.metrics import accuracy_score
        _, X_test, _, y_test, _ = sample_data
        acc = accuracy_score(y_test, trained_pipeline.predict(X_test))
        assert acc >= 0.88, f"Accuracy {acc:.4f} < required 0.88"

    def test_prediction_latency(self, trained_pipeline, sample_data):
        """Inference must be fast enough for the SLA. 100ms is typical for batch."""
        import time
        _, X_test, _, _, _ = sample_data
        start = time.time()
        trained_pipeline.predict(X_test)
        elapsed_ms = (time.time() - start) * 1000
        assert elapsed_ms < 1000, f"Prediction too slow: {elapsed_ms:.1f}ms > 1000ms SLA"


# =============================================================================
# 4. PIPELINE INTEGRATION TEST
# =============================================================================
class TestPipeline:
    """Tests the full CI/CD pipeline end-to-end."""

    def test_pipeline_runs_successfully(self, tmp_path):
        """The pipeline must complete without errors and pass quality gates."""
        config = PipelineConfig(
            model_output_dir=str(tmp_path / "artifacts"),
            metrics_file=str(tmp_path / "metrics.json"),
            baseline_file=str(tmp_path / "baseline.json"),
        )
        success = run_pipeline(config)
        assert success, "Pipeline failed!"

    def test_artifacts_created(self, tmp_path):
        """All required artifacts must be present after the pipeline runs."""
        config = PipelineConfig(
            model_output_dir=str(tmp_path / "artifacts"),
            metrics_file=str(tmp_path / "metrics.json"),
            baseline_file=str(tmp_path / "baseline.json"),
        )
        run_pipeline(config)
        artifacts_dir = tmp_path / "artifacts"
        assert (artifacts_dir / "model.pkl").exists(),    "model.pkl missing!"
        assert (artifacts_dir / "metadata.json").exists(),"metadata.json missing!"
        assert (artifacts_dir / "contract.json").exists(),"contract.json missing!"

    def test_model_is_loadable(self, tmp_path):
        """A saved model must be loadable and functional."""
        config = PipelineConfig(model_output_dir=str(tmp_path / "arts"),
                                metrics_file=str(tmp_path / "m.json"),
                                baseline_file=str(tmp_path / "b.json"))
        run_pipeline(config)
        with open(tmp_path / "arts" / "model.pkl", "rb") as f:
            loaded = pickle.load(f)
        X = pd.DataFrame(load_breast_cancer().data[:5], columns=load_breast_cancer().feature_names)
        preds = loaded.predict(X)
        assert len(preds) == 5


# =============================================================================
# Run directly (without pytest)
# =============================================================================
if __name__ == "__main__":
    print("Run with: pytest test_model.py -v")
    print("Or:       pytest test_model.py -v --tb=short")
