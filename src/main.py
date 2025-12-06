import click

from detect_new_posts import collect_new_posts
from prepare_post import PostVariant, prepare_post
from publish import publish_posts


@click.command()
@click.option("--default-branch", required=True, help="Name of the default Git branch.")
@click.option("--dry-run", type=bool, default=False, help="Run in dry-run mode.")
@click.option(
    "--posts-directory",
    required=True,
    type=click.Path(exists=True),
    help="Look in this subdirectory for new posts.",
)
def main(default_branch: str, dry_run: bool, posts_directory: str) -> None:
    files: list[str] = collect_new_posts(default_branch, posts_directory)

    posts: list[PostVariant] = list(map(prepare_post, files))

    if not dry_run:
        publish_posts(posts)


if __name__ == "__main__":
    main()
