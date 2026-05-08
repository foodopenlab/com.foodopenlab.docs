from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

try:
    import joblib
    from sklearn.compose import ColumnTransformer
    from sklearn.impute import SimpleImputer
    from sklearn.model_selection import train_test_split
    from sklearn.pipeline import Pipeline
    from sklearn.preprocessing import OneHotEncoder
    from sklearn.tree import DecisionTreeClassifier
except ModuleNotFoundError as e:  # pragma: no cover
    raise ModuleNotFoundError(
        "Missing ML dependencies. Install `scikit-learn` and `joblib`."
    ) from e


_DATA_DIR = Path(__file__).resolve().parent
_CSV_PATH = _DATA_DIR / "Titanic-Dataset.csv"
_DEFAULT_MODEL_PATH = _DATA_DIR / "rose_decision_tree.joblib"


class Rose:
    def __init__(self):
        pass

    def train_and_save(
        self,
        model_path: str | Path = _DEFAULT_MODEL_PATH,
        *,
        random_state: int = 42,
        max_depth: int | None = 5,
    ) -> dict[str, Any]:
        df = pd.read_csv(_CSV_PATH)

        target_col = "Survived"
        feature_cols = ["Pclass", "Sex", "Age", "SibSp", "Parch", "Fare", "Embarked"]
        X = df[feature_cols]
        y = df[target_col].astype(int)

        numeric_features = ["Pclass", "Age", "SibSp", "Parch", "Fare"]
        categorical_features = ["Sex", "Embarked"]

        numeric_transformer = Pipeline(
            steps=[("imputer", SimpleImputer(strategy="median"))]
        )
        categorical_transformer = Pipeline(
            steps=[
                ("imputer", SimpleImputer(strategy="most_frequent")),
                ("onehot", OneHotEncoder(handle_unknown="ignore")),
            ]
        )

        preprocessor = ColumnTransformer(
            transformers=[
                ("num", numeric_transformer, numeric_features),
                ("cat", categorical_transformer, categorical_features),
            ]
        )

        model = DecisionTreeClassifier(
            random_state=random_state,
            max_depth=max_depth,
        )

        clf = Pipeline(steps=[("preprocess", preprocessor), ("model", model)])

        X_train, X_test, y_train, y_test = train_test_split(
            X,
            y,
            test_size=0.2,
            random_state=random_state,
            stratify=y,
        )
        clf.fit(X_train, y_train)

        model_path = Path(model_path)
        model_path.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(clf, model_path)

        return {
            "model_path": str(model_path),
            "train_accuracy": float(clf.score(X_train, y_train)),
            "test_accuracy": float(clf.score(X_test, y_test)),
            "n_rows": int(df.shape[0]),
        }

    def load_model(self, model_path: str | Path = _DEFAULT_MODEL_PATH):
        return joblib.load(Path(model_path))