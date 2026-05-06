import pandas as pd

class DoroReader:
    def __init__(self):
        pass

    def get_data(self):
        df = pd.read_csv("doro-dataset.csv", encoding="cp949")
        print(df.head())            