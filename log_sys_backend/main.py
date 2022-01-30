import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from logic.estimates import *
from logic.inference2 import *


def get_tree(formula):
    parser = make_estimates_parser()
    fl = parse_formula(parser, formula)
    print(str(fl))
    tree = build_full_tree_v3([fl])
    return tree.to_dict()


app = FastAPI()

origins = [
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {"suck": 'cock'}


from pydantic import BaseModel


class FormRequest(BaseModel):
    formula: str


@app.post('/make_tree')
def make_tree(fr: FormRequest):
    return get_tree(fr.formula)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)
