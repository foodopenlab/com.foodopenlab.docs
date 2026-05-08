import json
from pathlib import Path

import pandas as pd

_DATA_DIR = Path(__file__).resolve().parent
_CSV_PATH = _DATA_DIR / "doro-dataset.csv"


class DoroReader:
    def __init__(self):
        pass

    def get_data(self):
        df = pd.read_csv(_CSV_PATH, encoding="cp949")
        # 인덱스 1번 행만 반환 (DataFrame 형태 유지)
        return df.iloc[[1]].astype(object).where(df.iloc[[1]].notna(), None)

    def head_records(self, n: int = 10) -> list[dict]:
        df = pd.read_csv(_CSV_PATH, encoding="cp949")
        return json.loads(df.head(n).to_json(orient="records"))
                  