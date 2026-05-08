from fastapi import FastAPI

from .doro_reader import DoroReader

app = FastAPI(title="Doro (DoroDirector)")


class DoroDirector:
    def __init__(self):
        pass


    def get_data(self):
        do=DoroReader()
        return do.get_data()