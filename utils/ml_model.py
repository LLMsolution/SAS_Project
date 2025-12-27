"""
SAS Material Supply Analysis - ML Model Module
Train and use Random Forest model for material prediction
"""

import streamlit as st
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import cross_val_score
from sklearn.preprocessing import StandardScaler
import pickle
from pathlib import Path

from .feature_engineering import create_ml_features, prepare_prediction_features, get_feature_importance_names
from .data_loader import get_master_view

# Model path
MODEL_PATH = Path(__file__).parent.parent / 'models' / 'material_predictor.pkl'


class MaterialPredictor:
    """
    Material prediction model using Random Forest
    """

    def __init__(self):
        self.model = None
        self.scaler = None
        self.feature_names = []
        self.encoders = None
        self.training_stats = {}
        self.planning_accuracy_factor = 1.0

    def train(self, X, y, cv_folds=5):
        """
        Train Random Forest model on available data

        Args:
            X: Feature matrix
            y: Target variable (consumed_parts_count)
            cv_folds: Number of cross-validation folds
        """
        # Scale features
        self.scaler = StandardScaler()
        X_scaled = self.scaler.fit_transform(X)

        # Train Random Forest
        self.model = RandomForestRegressor(
            n_estimators=100,
            max_depth=10,
            min_samples_split=5,
            min_samples_leaf=2,
            random_state=42,
            n_jobs=-1
        )

        self.model.fit(X_scaled, y)

        # Cross-validation
        cv_scores = cross_val_score(
            self.model, X_scaled, y,
            cv=min(cv_folds, len(X)),
            scoring='r2'
        )

        # Store training stats
        self.training_stats = {
            'n_samples': len(X),
            'cv_mean_r2': cv_scores.mean(),
            'cv_std_r2': cv_scores.std(),
            'feature_importance': self.model.feature_importances_,
            'training_mean': y.mean(),
            'training_std': y.std(),
            'training_min': y.min(),
            'training_max': y.max(),
        }

        print(f"Model trained on {len(X)} samples")
        print(f"Cross-validation R²: {cv_scores.mean():.3f} (+/- {cv_scores.std():.3f})")

    def predict(self, X_new):
        """
        Predict material needs for new C-check

        Args:
            X_new: Feature matrix for new observation(s)

        Returns:
            dict with prediction and confidence
        """
        if self.model is None or self.scaler is None:
            return None

        # Scale features
        X_scaled = self.scaler.transform(X_new)

        # Predict
        prediction = self.model.predict(X_scaled)[0]

        # Calculate confidence (based on prediction range from trees)
        tree_predictions = np.array([tree.predict(X_scaled)[0] for tree in self.model.estimators_])
        pred_std = tree_predictions.std()

        # Confidence interval (95%)
        ci_lower = max(0, prediction - 1.96 * pred_std)
        ci_upper = prediction + 1.96 * pred_std

        # Confidence score (based on std relative to mean)
        confidence_score = max(0, min(100, 100 * (1 - pred_std / max(prediction, 1))))

        return {
            'prediction': round(prediction),
            'confidence': round(confidence_score, 1),
            'ci_lower': round(ci_lower),
            'ci_upper': round(ci_upper),
            'std': round(pred_std, 2)
        }

    def predict_with_fallback(self, input_data, planned_parts=None):
        """
        Predict with fallback to planned material

        Args:
            input_data: dict with input features
            planned_parts: Number of planned parts (if available)

        Returns:
            dict with prediction, method used, and confidence
        """
        # Try ML prediction first
        if self.model is not None and self.encoders is not None:
            X_new = prepare_prediction_features(input_data, self.encoders, self.feature_names)
            ml_result = self.predict(X_new)

            # If confidence is reasonable, use ML prediction
            if ml_result and ml_result['confidence'] > 30:
                ml_result['method'] = 'ML Model'
                ml_result['explanation'] = f"Prediction based on Random Forest model trained on {self.training_stats['n_samples']} C-checks"
                return ml_result

        # Fallback to planned material with adjustment
        if planned_parts is not None and planned_parts > 0:
            # Apply planning accuracy factor (learned from training data)
            adjusted_prediction = round(planned_parts * self.planning_accuracy_factor)

            return {
                'prediction': adjusted_prediction,
                'confidence': 60.0,
                'ci_lower': round(adjusted_prediction * 0.8),
                'ci_upper': round(adjusted_prediction * 1.2),
                'method': 'Adjusted Planned Material',
                'explanation': f"Based on planned material ({planned_parts} parts) adjusted by historical accuracy factor ({self.planning_accuracy_factor:.2f})"
            }

        # Last resort: use training mean
        if 'training_mean' in self.training_stats:
            mean_prediction = round(self.training_stats['training_mean'])

            return {
                'prediction': mean_prediction,
                'confidence': 40.0,
                'ci_lower': round(self.training_stats['training_mean'] - self.training_stats['training_std']),
                'ci_upper': round(self.training_stats['training_mean'] + self.training_stats['training_std']),
                'method': 'Historical Average',
                'explanation': f"Based on average material usage from {self.training_stats['n_samples']} historical C-checks"
            }

        return None

    def get_feature_importance(self):
        """
        Get feature importance from trained model
        """
        if self.model is None:
            return None

        importance_df = pd.DataFrame({
            'feature': get_feature_importance_names(self.feature_names, self.encoders),
            'importance': self.training_stats['feature_importance']
        }).sort_values('importance', ascending=False)

        return importance_df

    def save(self, path=None):
        """
        Save trained model to file
        """
        if path is None:
            path = MODEL_PATH

        # Create directory if it doesn't exist
        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, 'wb') as f:
            pickle.dump(self, f)

        print(f"Model saved to {path}")

    @staticmethod
    def load(path=None):
        """
        Load trained model from file
        """
        if path is None:
            path = MODEL_PATH

        if not path.exists():
            return None

        with open(path, 'rb') as f:
            model = pickle.load(f)

        print(f"Model loaded from {path}")
        return model


@st.cache_resource
def get_trained_model():
    """
    Get or train the material prediction model (cached)
    """
    # Try to load existing model
    model = MaterialPredictor.load()

    if model is not None:
        return model

    # Train new model
    print("Training new model...")
    master_df = get_master_view()

    if master_df is None:
        st.error("Could not load data for model training")
        return None

    # Create features
    X, y, feature_names, encoders, training_df = create_ml_features(master_df)

    if X is None or len(X) < 10:
        st.error("Insufficient data for model training (need at least 10 samples)")
        return None

    # Initialize and train model
    model = MaterialPredictor()
    model.feature_names = feature_names
    model.encoders = encoders

    # Calculate planning accuracy factor
    # (ratio of actual to planned for available data)
    valid_accuracy = training_df[
        (training_df['planned_parts_count'] > 0) &
        (training_df['consumed_parts_count'].notna())
    ]

    if len(valid_accuracy) > 0:
        accuracy_ratios = valid_accuracy['consumed_parts_count'] / valid_accuracy['planned_parts_count']
        model.planning_accuracy_factor = accuracy_ratios.median()

    # Train
    model.train(X, y)

    # Save model
    model.save()

    return model


def find_similar_checks(input_data, master_df, n_similar=5):
    """
    Find similar historical C-checks for recommendation

    Args:
        input_data: dict with input characteristics
        master_df: Master dataframe
        n_similar: Number of similar checks to return

    Returns:
        DataFrame with similar C-checks
    """
    # Filter to C-checks with consumption data
    similar_df = master_df[
        (master_df['is_c_check'] == 1) &
        (master_df['consumed_parts_count'].notna())
    ].copy()

    if len(similar_df) == 0:
        return None

    # Calculate similarity score
    similar_df['similarity_score'] = 0.0

    # Same aircraft type: +50 points
    if 'ac_typ' in input_data:
        similar_df.loc[similar_df['ac_typ'] == input_data['ac_typ'], 'similarity_score'] += 50

    # Similar station: +30 points
    if 'station' in input_data:
        similar_df.loc[similar_df['station'] == input_data['station'], 'similarity_score'] += 20

    # EOL match: +10 points
    if 'is_eol' in input_data:
        similar_df.loc[similar_df['is_eol'] == input_data['is_eol'], 'similarity_score'] += 10

    # Sort by similarity
    similar_df = similar_df.sort_values('similarity_score', ascending=False).head(n_similar)

    # Select relevant columns
    result_cols = [
        'wpno', 'ac_registr', 'ac_typ', 'check_type', 'station',
        'consumed_parts_count', 'consumed_cost', 'duration_days',
        'start_date', 'similarity_score'
    ]

    return similar_df[result_cols]
