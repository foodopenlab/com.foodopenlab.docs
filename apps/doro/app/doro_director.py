'''from doro_reader import DoroReader


class DoroDirector:
    def __init__(self):
        pass   

if __name__ == "__main__":

    print("디텍터가 메인이다.")
    R = DoroReader()
    R.get_data()
'''
from fastapi import FastAPI

from .doro_reader import DoroReader

app = FastAPI(title="Doro (DoroDirector)")
do=DoroReader()


class DoroDirector:
    def __init__(self):
        pass


    def get_data(self):
        do=DoroReader()
        return do.get_data()