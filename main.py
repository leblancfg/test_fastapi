import io
import logging
from mimetypes import guess_extension
import tempfile

import cv2
import magic
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


def open_file(file):
    """Given a filename, returns a numpy array"""
    try:
        # Try with PIL
        with Image.open(file) as img_orig:
            return np.asarray(img_orig)
    except Exception:
        # Try with cv2
        # TODO: this might not be working
        return cv2.imread(file)
    return None, None


async def upload_img_file(img, ext: str, mime: str):
    """Given an img file, returns a temp file to user."""
    if "." in ext:
        ext = ext[1:]
    with tempfile.NamedTemporaryFile(mode="w+b", suffix=ext, delete=False) as FOUT:
        FOUT.write(img)
        return FileResponse(FOUT.name, media_type=mime)


def get_mime(file):
    """Given a file, returns mimetype and extension"""
    mime = magic.from_buffer(file.read(2048), mime=True)
    extension = guess_extension(mime, False)
    return mime, extension


@app.post("/crop")
@version(1)
async def crop(
    width: int = 500,
    height: int = 500,
    face_percent: int = 50,
    file: UploadFile = File(...),
):
    """Returns a cropped form of the document image."""
    mime, extension = get_mime(file.file)
    logging.info(f"Reading file: {mime}, {extension}")

    # Set up Cropper instance and crop
    c = Cropper(width=width, height=height, face_percent=face_percent)

    # Crop
    img = open_file(file.file)
    img_array = c.crop(img)
    if img_array is None:
        return None

    # Convert to bytes
    is_success, img_buffer = cv2.imencode(extension, img_array)
    if not is_success:
        return None

    byte_im = img_buffer.tobytes()
    return await upload_img_file(img=byte_im, ext=extension, mime=mime)


@app.post("/crop_uri")
@version(1)
async def crop_uri(
    uri: AnyHttpUrl, width: int = 500, height: int = 500, face_percent: int = 50,
):
    """Returns a cropped form of the document image."""

    # Set up Cropper instance and crop
    c = Cropper(width=width, height=height, face_percent=face_percent)

    # Crop
    r = requests.get(uri, stream=True)
    if r.status_code != 200:
        # TODO
        return None
    file = io.BytesIO(r.content)
    mime, extension = get_mime(file)
    logging.info(f"Reading file: {mime}, {extension}")

    img = open_file(file)
    img_array = c.crop(img)
    if img_array is None:
        # TODO
        return {'face detected': None}

    # Convert to bytes
    is_success, img_buffer = cv2.imencode(extension, img_array)
    if not is_success:
        # TODO
        return {'face detected': None}
    byte_im = img_buffer.tobytes()
    return await upload_img_file(img=byte_im, ext=extension, mime=mime)


@app.get("/*")
def home():
    return {
        "autocrop API": {
            "version": "1",
            "source": "https://github.com/leblancfg/autocrop",
            "docs": "$URL/v1/docs",
        }
    }


app = VersionedFastAPI(app, version_format="{major}", prefix_format="/v{major}",)
