import os

from atproto import Client, models
from atproto_client.exceptions import BadRequestError


from prepare_post import Post, PostWithImage, PostWithCard, PostVariant
from error import fail_with_message


def publish_posts(posts: list[PostVariant]) -> None:
    if len(posts) == 0:
        print("No posts to publish.")
        return

    BLUESKY_USERNAME = os.getenv("BLUESKY_USERNAME")
    BLUESKY_APP_PASSWORD = os.getenv("BLUESKY_APP_PASSWORD")

    if BLUESKY_USERNAME is None or BLUESKY_APP_PASSWORD is None:
        fail_with_message(
            "BLUESKY_USERNAME and/or BLUESKY_APP_PASSWORD environment variables are not set."
        )

    client = Client()
    _profile = client.login(BLUESKY_USERNAME, BLUESKY_APP_PASSWORD)

    for post in posts:
        if isinstance(post, PostWithCard):
            try:
                thumb = client.upload_blob(post.image_data)
                embed = models.AppBskyEmbedExternal.Main(
                    external=models.AppBskyEmbedExternal.External(
                        title=post.card_title,
                        description=post.card_description,
                        uri=post.card_uri,
                        thumb=thumb.blob,
                    )
                )
                client.send_post(text=post.text, embed=embed)
            except BadRequestError as _e:
                fail_with_message(
                    "got 'BadRequestError' when publishing post with card"
                )
        elif isinstance(post, PostWithImage):
            try:
                client.send_image(
                    text=post.text,
                    image=post.image_data,
                    image_alt=post.image_alt,
                )
            except BadRequestError as _e:
                fail_with_message(
                    "got 'BadRequestError' when publishing post with image"
                )
        elif isinstance(post, Post):
            try:
                client.send_post(text=post.text)
            except BadRequestError as _e:
                fail_with_message(
                    "got 'BadRequestError' when publishing text-only post"
                )
