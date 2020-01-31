from enum import Enum

from fastapi import FastAPI


class ModelName(str, Enum):
    alexnet = "alexnet"
    resnet = "resnet"
    lenet = "lenet"


app = FastAPI()


# From URL
@app.get("/crop/{url}")
async def crop_from_URL(url):
    return {"model_name": url, "message": "Have some residuals"}
