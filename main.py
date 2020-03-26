import os
import tempfile

import cv2
import numpy as np
from PIL import Image
from autocrop.autocrop import Cropper
from autocrop.constants import CV2_FILETYPES, PILLOW_FILETYPES
from fastapi import FastAPI, File, UploadFile
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
        return cv2.imread(file.file)
    if extension in PILLOW_FILETYPES:
        # Try with PIL
        with Image.open(file.file) as img_orig:
            return np.asarray(img_orig)
    return None


# def open_file(file):
#     """Given a file object, returns a numpy array"""
#     with Image.open(file.file) as img_orig:
#         return np.asarray(img_orig)


def upload_img_file(img, ext: str):
    """Given an img file, returns a temp file to user."""
    with tempfile.NamedTemporaryFile(mode="w+b", suffix=ext, delete=False) as FOUT:
        FOUT.write(img)
        return FileResponse(FOUT.name, media_type="image/png")


@app.post("/crop")
async def image_endpoint(
    width: int = 500,
    height: int = 500,
    face_percent: int = 50,
    file: UploadFile = File(...),
):
    """Returns a cropped form of the document image."""
    _, file_extension = os.path.splitext(file.filename)

    # Set up Cropper instance and crop
    c = Cropper(width=width, height=height, face_percent=face_percent)

    # Crop
    img = open_file(file, file_extension)
    img_array = c.crop(img)
    if img_array is None:
        return None

    # Convert to bytes
    is_success, img_buffer = cv2.imencode(file_extension, img_array)
    byte_im = img_buffer.tobytes()
    return upload_img_file(img=byte_im, ext=file_extension)


@app.get("/")
def home():
    return {"autocrop API":{'version': '1', 'source': 'https://github.com/leblancfg/autocrop'}}
