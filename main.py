import io
import logging
import os
import tempfile

import cv2
import numpy as np
from PIL import Image
from autocrop.autocrop import Cropper

from fastapi import FastAPI, File, UploadFile
from fastapi_versioning import VersionedFastAPI, version
from pydantic import AnyHttpUrl
import requests
from starlette.responses import FileResponse
from starlette.middleware.cors import CORSMiddleware

app = FastAPI()
app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"]
)


def open_file(file, extension):
    """Given a filename, returns a numpy array"""
    try:
        # Try with PIL
        with Image.open(file) as img_orig:
            return np.asarray(img_orig)
    except Exception:
        # Try with cv2
        # TODO: this might not be working
        return cv2.imread(file)
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
@version(1)
async def crop(
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
    img = open_file(file.file, file_extension)
    img_array = c.crop(img)
    if img_array is None:
        return None

    # Convert to bytes
    is_success, img_buffer = cv2.imencode(file_extension, img_array)
    byte_im = img_buffer.tobytes()
    return upload_img_file(img=byte_im, ext=file_extension)


@app.post("/crop_uri")
@version(1)
async def crop_uri(
    uri: AnyHttpUrl, width: int = 500, height: int = 500, face_percent: int = 50,
):
    """Returns a cropped form of the document image."""
    _, file_extension = os.path.splitext(uri)

    # Set up Cropper instance and crop
    c = Cropper(width=width, height=height, face_percent=face_percent)

    # Crop
    r = requests.get(uri, stream=True)
    if r.status_code != 200:
        # TODO
        return None
    file = io.BytesIO(r.content)

    img = open_file(file, file_extension)
    img_array = c.crop(img)
    if img_array is None:
        # TODO
        return None

    # Convert to bytes
    is_success, img_buffer = cv2.imencode(file_extension, img_array)
    byte_im = img_buffer.tobytes()
    return upload_img_file(img=byte_im, ext=file_extension)


@app.get("/")
@version(1)
def home():
    return {
        "autocrop API": {
            "version": "1",
            "source": "https://github.com/leblancfg/autocrop",
        }
    }


app = VersionedFastAPI(app, version_format="{major}", prefix_format="/v{major}",)
