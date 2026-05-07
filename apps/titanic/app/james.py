from fastapi import FastAPI

from .walter import Walter

app = FastAPI(title="Titanic (James)")
w=Walter()


class James:
    def __init__(self):
        pass


    def get_data(self):
        w=Walter()
        return w.get_data()
