from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from whoosh.fields import Schema, TEXT, ID
from whoosh.index import create_in, open_dir
from whoosh.qparser import QueryParser

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

schema = Schema(title=TEXT(stored=True), content=TEXT(stored=True), url=ID(stored=True))
index_dir = 'index_dir'

try:
    index = open_dir(index_dir)
except:
    index = create_in(index_dir, schema)


@app.get("/")
def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/search")
def search(request: Request, query: str):
    with index.searcher() as searcher:
        query_parser = QueryParser("content", index.schema)
        parsed_query = query_parser.parse(query)
        results = searcher.search(parsed_query)
        print(results)


        return templates.TemplateResponse("index.html", {"request": request, "results": results})

