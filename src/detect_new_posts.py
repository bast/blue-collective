import subprocess
import shlex
from pathlib import Path

from error import fail_with_message


def collect_new_posts(default_branch: str, posts_directory: str) -> list[str]:
    # is this a PR against the default branch?
    added_files = run_command_then_filter_md_files(
        f"git diff --name-only --diff-filter=A origin/{default_branch}...",
        posts_directory,
    )
    if added_files:
        return added_files

    # once the PR is merged, the diff against the default branch won't work
    # anymore, so we need to compare against parent commits

    if is_first_commit():
        # repository has only one commit: diff against empty tree
        added_files = added_md_files_in_first_commit(posts_directory)
        if added_files:
            return added_files

    # both for normal and merge commits, one of the two tests below should work

    added_files = run_command_then_filter_md_files(
        "git diff --name-only --diff-filter=A HEAD~1", posts_directory
    )
    if added_files:
        return added_files

    added_files = run_command_then_filter_md_files(
        "git diff --name-only --diff-filter=A HEAD~2", posts_directory
    )
    if added_files:
        return added_files

    return []


def run_command(command: str) -> list[str]:
    try:
        result = subprocess.run(
            shlex.split(command), stdout=subprocess.PIPE, text=True, check=True
        )

        return result.stdout.strip()

    except subprocess.CalledProcessError:
        fail_with_message(f"Command failed: {command}")
    except FileNotFoundError:
        fail_with_message(f"Command not found: {command}")


def filter_md_files(added_paths: list[str], posts_directory: str) -> list[Path]:
    added_paths = [Path(p) for p in added_paths]
    root = Path(posts_directory)
    return [p for p in added_paths if p.suffix == ".md" and p.is_relative_to(root)]


def run_command_then_filter_md_files(command: str, posts_directory: str) -> list[Path]:
    added_paths = run_command(command).splitlines()
    return filter_md_files(added_paths, posts_directory)


def is_first_commit() -> bool:
    parents = run_command("git rev-list --parents -n 1 HEAD")
    return len(parents.split()) == 1


def added_md_files_in_first_commit(posts_directory: str) -> list[str]:
    empty_tree = run_command("git hash-object -t tree /dev/null")
    return run_command_then_filter_md_files(
        f"git diff --name-only --diff-filter=A {empty_tree} HEAD",
        posts_directory,
    )
