import io
import logging
from mimetypes import guess_extension
import tempfile
import uuid

from autocrop.autocrop import Cropper
import cv2
from google.cloud import storage
import magic
import numpy as np
from PIL import Image
import requests


from fastapi import FastAPI, File, UploadFile
from fastapi_versioning import VersionedFastAPI, version
from fastapi.logger import logger as fastapi_logger

from starlette import status
from starlette.responses import Response, FileResponse
from starlette.middleware.cors import CORSMiddleware
from pydantic import AnyHttpUrl

app = FastAPI()

# Google Cloud Storage
BUCKET = "autocrop-img"
storage_client = storage.Client()  # Implicitly reads environment variable
bucket = storage_client.bucket(BUCKET)

# Logging
# handler = Rotating
# logging.getLogger().setLevel(logging.NOTSET)
# fastapi_logger.addHandler(handler)

def open_file(file):
    """Given a filename, returns a numpy array"""
    try:
        # Try with PIL
        with Image.open(file) as img_orig:
            return np.asarray(img_orig)
    except Exception:
        fastapi_logger.warn(f"PIL unable to open {file}, trying cv2.")
        # Try with cv2
        # TODO: this might not be working
        return cv2.imread(file)
    return None, None


def upload_blob(img, ext: str, mime: str):
    """Given an img array and extension, uploads it to GStorage."""
    if "." in ext:
        ext = ext[1:]
    filename = str(uuid.uuid4()) + "." + ext
    fastapi_logger.info(f"Uploading to Storage: {filename}")

    blob = bucket.blob(filename)
    with tempfile.NamedTemporaryFile(suffix=ext) as temp:
        temp_filename = temp.name + "." + ext
        cv2.imwrite(temp_filename, img)
        blob.upload_from_filename(temp_filename, content_type=mime)
    blob.make_public()
    return blob.public_url


async def upload_img_file(img, ext: str, mime: str):
    """Given an img file, returns a temp file to user."""
    if "." in ext:
        ext = ext[1:]
    with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as FOUT:
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
    fastapi_logger.info(f"Reading file: {file.filename}, mime: {mime}")
    if "image" not in mime:
        return Response(status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)

    # Set up Cropper instance and crop
    c = Cropper(width=width, height=height, face_percent=face_percent)

    # Crop
    img = open_file(file.file)
    img_array = c.crop(img)
    if img_array is None:
        return {"success": False, "description": "No face detected", "url": None}

    url = upload_blob(img=img_array, ext=extension, mime=mime)
    return {
        "success": True,
        "description": "Face detected, cropped at url provided.",
        "url": url,
    }


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
    fastapi_logger.info(f"Reading file: {mime}, {extension}")

    img = open_file(file)
    img_array = c.crop(img)
    if img_array is None:
        # TODO
        return {"face detected": None}

    # Convert to bytes
    is_success, img_buffer = cv2.imencode(extension, img_array)
    if not is_success:
        # TODO
        return {"face detected": None}
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


@app.get("/healthcheck")
async def healthcheck():
    return {"status": "alive"}


app = VersionedFastAPI(app, version_format="{major}", prefix_format="/v{major}",)

origins = [
    "http://localhost",
    "http://localhost:8080",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
