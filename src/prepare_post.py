from pathlib import Path
from dataclasses import dataclass
from typing import Union
from PIL import Image
import io
import frontmatter
import requests


from error import fail_with_message
from limits import MAX_POST_TEXT_LENGTH, MAX_IMAGE_SIZE_BYTES


@dataclass
class Post:
    text: str


@dataclass
class PostWithImage:
    text: str
    image_data: bytes
    image_alt: str


@dataclass
class PostWithCard:
    text: str
    image_data: bytes
    card_title: str
    card_description: str
    card_uri: str


PostVariant = Union[Post, PostWithImage, PostWithCard]


def strip_metadata(image_data: bytes) -> bytes:
    image = Image.open(io.BytesIO(image_data))

    clean_image = Image.new(image.mode, image.size)
    clean_image.putdata(list(image.getdata()))

    clean_image_bytes = io.BytesIO()
    clean_image.save(clean_image_bytes, format=image.format)

    return clean_image_bytes.getvalue()


def prepare_post(file_name: str) -> PostVariant:
    base_path = Path(file_name).parent

    post = frontmatter.load(file_name)
    text = post.content
    metadata = post.metadata

    if len(text.strip()) == 0:
        fail_with_message("Post text cannot be empty")

    if len(text) > MAX_POST_TEXT_LENGTH:
        fail_with_message(f"Post text exceeds {MAX_POST_TEXT_LENGTH} characters")

    if "image" in metadata:
        image_ref = metadata["image"]
        if image_ref.startswith("http://") or image_ref.startswith("https://"):
            # download the image from url
            response = requests.get(image_ref)
            if response.status_code != 200:
                fail_with_message(f"Failed to download image from {image_ref}")
            image_data = response.content
        else:
            # local file path
            image_path = base_path / image_ref
            if not image_path.exists():
                fail_with_message(f"Image file {image_path} does not exist")
            with open(image_path, "rb") as f:
                image_data = f.read()

        image_data = strip_metadata(image_data)

        if len(image_data) > MAX_IMAGE_SIZE_BYTES:
            fail_with_message(f"Image file size exceeds {MAX_IMAGE_SIZE_BYTES} bytes")

    if post.metadata == {}:
        return Post(text=text)

    if (
        "title" in metadata
        and "description" in metadata
        and "uri" in metadata
        and "image" in metadata
    ):
        return PostWithCard(
            text=text,
            image_data=image_data,
            card_title=metadata["title"],
            card_description=metadata["description"],
            card_uri=metadata["uri"],
        )

    if "image" in metadata and "alt" in metadata:
        return PostWithImage(
            text=text,
            image_data=image_data,
            image_alt=metadata["alt"],
        )

    if "image" in metadata and "alt" not in metadata:
        fail_with_message("Image alt text is required when an image is provided")

    fail_with_message("looks like programming error in prepare_post.py")
