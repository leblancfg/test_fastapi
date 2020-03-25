import os
import tempfile

import cv2
import numpy as np
from PIL import Image
from autocrop.autocrop import Cropper
from fastapi import FastAPI, File, UploadFile
from starlette.responses import FileResponse
from starlette.middleware.cors import CORSMiddleware

app = FastAPI()
app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"]
)


def open_file(file):
    """Given a file object, returns a numpy array"""
    with Image.open(file.file) as img_orig:
        return np.asarray(img_orig)


def upload_img_file(img, ext:str):
    """Given an img file, returns a temp file to user."""
    with tempfile.NamedTemporaryFile(mode="w+b", suffix=ext, delete=False) as FOUT:
        FOUT.write(img)
        return FileResponse(FOUT.name, media_type="image/png")


@app.post("/crop")
def image_endpoint(width: int=None, height: int=None, face_percent: int=None, file: UploadFile = File(...)):
    """Returns a cropped form of the document image."""
    _, file_extension = os.path.splitext(file.filename)

    # Set up Cropper instance and crop
    args = {'width': width, 'height': height, 'face_percent': face_percent}
    kwargs = {k: v for k, v in args.items() if v is not None}
    c = Cropper(**kwargs)

    # Crop
    img = open_file(file)
    img_array = c.crop(img)

    # Convert to bytes
    is_success, img_buffer = cv2.imencode(file_extension, img_array)
    byte_im = img_buffer.tobytes()
    return upload_img_file(img=byte_im, ext=file_extension)
