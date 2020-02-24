import os
from io import BytesIO
import tempfile

from autocrop.autocrop import crop
from autocrop.constants import CV2_FILETYPES, PILLOW_FILETYPES
import cv2
from fastapi import FastAPI, File, UploadFile
import numpy as np
from starlette.responses import FileResponse
from starlette.middleware.cors import CORSMiddleware

app = FastAPI()
app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"]
)


def open_file(file, extension):
    """Given a filename, returns a numpy array"""

    if extension in CV2_FILETYPES:
        # Try with cv2
        return cv2.imread(file)
    if extension in PILLOW_FILETYPES:
        # Try with PIL
        with Image.open(file) as img_orig:
            return np.asarray(img_orig)
    return None


def upload_img_file(img, ext:str):
    """Given an img file, returns a temp file to user."""
    with tempfile.NamedTemporaryFile(mode="w+b", suffix=ext, delete=False) as FOUT:
        FOUT.write(img)
        return FileResponse(FOUT.name, media_type="image/png")


# From URL
# @app.get("/crop/{url}")
# async def crop_from_URL(url):
#     img = requests.get
#     return upload_img_file(img, ext)


# From upload as form data
@app.post("/crop")
async def image_endpoint(file: UploadFile = File(...)):
    # Returns a cropped form of the document image
    _, file_extension = os.path.splitext(file.filename)
    img = await file.read()
    image = crop(open_file(file.file, file_extension))
    return upload_img_file(img=image, ext=file_extension)

