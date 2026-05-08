import json
from pathlib import Path

import pandas as pd

_DATA_DIR = Path(__file__).resolve().parent
_CSV_PATH = _DATA_DIR / "Titanic-Dataset.csv"


class Walter:
    def __init__(self):
        pass

    def get_data(self):
        df = pd.read_csv(_CSV_PATH)
        # 인덱스 1번 행만 반환 (DataFrame 형태 유지)
        return df.iloc[[0]].astype(object).where(df.iloc[[0]].notna(), None)
    
    def get_count(self):
        df = pd.read_csv(_CSV_PATH)
        count = int(df.shape[0])
        return pd.DataFrame([{"count": count}])

    def get_count_survived(self):
        df = pd.read_csv(_CSV_PATH)
        count_survived = int(df[df["Survived"] == 1].shape[0])
        return pd.DataFrame([{"count_survived": count_survived}])

    def get_count_dead(self):
        df = pd.read_csv(_CSV_PATH)
        count_dead = int(df[df["Survived"] == 0].shape[0])
        return pd.DataFrame([{"count_dead": count_dead}])