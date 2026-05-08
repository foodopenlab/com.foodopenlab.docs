from fastapi import FastAPI

from pathlib import Path

from .walter import Walter

app = FastAPI(title="Titanic (James)")


class James:
    def __init__(self):
        pass

    def get_data(self):
        w=Walter()
        return w.get_data()

    def get_count(self):
        w=Walter()
        return w.get_count()

    def get_count_survived(self):
        w=Walter()
        return w.get_count_survived()

    def get_count_dead(self):
        w=Walter()
        return w.get_count_dead()

    def has_decision_tree_model(self) -> bool:
        model_path = Path(__file__).resolve().parent / "rose_decision_tree.joblib"
        return model_path.exists()    