from fastapi import FastAPI

try:
    from titanic.app.james import James
except ModuleNotFoundError:
    from apps.titanic.app.james import James

try:
    from doro.app.doro_director import DoroDirector
except ModuleNotFoundError:
    from apps.doro.app.doro_director import DoroDirector

app = FastAPI(title="Foodopenlab Main Page ")

@app.get("/")
def read_root():
    return {"message": "FAST API 메인 페이지","docs": "/docs"}


@app.get("/titanic/data")
def read_titanic_data():
    james = James()
    df = james.get_data()

    return df.to_dict(orient="records")

@app.get("/titanic/count")
def read_titanic_count():
    james = James()
    df = james.get_count()

    return df.to_dict(orient="records")

@app.get("/titanic/tree")
def read_titanic_tree():
    james = James()
    has_model = james.has_decision_tree_model()

    return {"has_decision_tree_model": has_model}

@app.get("/titanic/count/survived")
def read_titanic_count_survived():
    james = James()
    df = james.get_count_survived()

    return df.to_dict(orient="records")  

@app.get("/titanic/count/dead")
def read_titanic_count_dead():
    james = James()
    df = james.get_count_dead()

    return df.to_dict(orient="records")        

@app.get("/doro/data")
def read_doro_data():
    doro_director = DoroDirector()
    df = doro_director.get_data()

    return df.to_dict(orient="records")    

if __name__ == "__main__":
    import uvicorn
    
    # Run using the already-imported ASGI app object.
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)