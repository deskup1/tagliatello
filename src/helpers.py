import PIL.Image
import dearpygui.dearpygui as dpg
import cv2
import numpy as np
from PIL import Image
import base64
from io import BytesIO
import numpy
import re

default_thumbnail_size = (150, 150)

def convert_base64_to_pil(base64_image: str) -> PIL.Image.Image:
    base64_image = re.sub('^data:image/.+;base64,', '', base64_image)
    base64_image = base64_image.encode()
    base64_image = base64.b64decode(base64_image)
    return Image.open(BytesIO(base64_image))


def convert_to_thumbnail(pillow_image: PIL.Image.Image, size=default_thumbnail_size) -> PIL.Image.Image:
    # scale to 150x150
    pillow_image.thumbnail(size)
    # set alpha channel to 255
    pillow_image.putalpha(255)
    # convert to png
    pillow_image = pillow_image.convert("RGBA")
  
    return pillow_image

def image_grid(images: list[PIL.Image.Image], grid_size: tuple[int, int]) -> PIL.Image.Image:
    width, height = images[0].size
    max_images = grid_size[0] * grid_size[1]
    grid = PIL.Image.new('RGB', (width * grid_size[0], height * grid_size[1]))
    for i, image in enumerate(images):
        grid.paste(image, (width * (i % grid_size[0]), height * (i // grid_size[0])))
        if i >= max_images - 1:
            break
    return grid

def images_thumbnail(images: list[PIL.Image.Image], size=default_thumbnail_size) -> PIL.Image.Image:
    thumbnails = [convert_to_thumbnail(image, size) for image in images]
    image = None
    if len(thumbnails) == 0:
        image = PIL.Image.new('RGBA', size)
    elif len(thumbnails) == 1:
        image = thumbnails[0]
    elif len(thumbnails) == 2:
        image = image_grid(thumbnails, (2, 1))
    elif len(thumbnails) == 3:
        image = image_grid(thumbnails, (3, 1))
    elif len(thumbnails) == 4:
        image = image_grid(thumbnails, (2, 2))
    elif len(thumbnails) <= 6:
        image = image_grid(thumbnails, (3, 2))
    elif len(thumbnails) <= 9:
        image = image_grid(thumbnails, (3, 3))
    else:
        image = image_grid(thumbnails, (4, 4))

    return convert_to_thumbnail(image, size)

def convert_cv_to_dpg(image, size=default_thumbnail_size):
    resize_image = cv2.resize(image, size)

    data = np.flip(resize_image, 2)
    data = data.ravel()
    data = np.asfarray(data, dtype='f')

    texture_data = np.true_divide(data, 255.0)

    return texture_data

def convert_pil_to_cv(pil_image):
    open_cv_image = numpy.array(pil_image) 
    # Convert RGB to BGR 
    return open_cv_image[:, :, ::-1].copy()

