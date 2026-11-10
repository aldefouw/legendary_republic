#!/usr/bin/env python3
"""Select or build the dependency image from a minimal, source-free context."""

import argparse
import hashlib
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile

IMAGE_DIR = Path(__file__).resolve().parent / "image"
DEPENDENCIES = ("Gemfile", "Gemfile.lock", "package.json", "yarn.lock")
RECIPES = ("Dockerfile", "entrypoint.sh")


def image_tag(app, repository):
    digest = hashlib.sha256()
    for name, root in [(n, app) for n in DEPENDENCIES] + [(n, IMAGE_DIR) for n in RECIPES]:
        data = (root / name).read_bytes()
        digest.update(name.encode() + b"\0" + str(len(data)).encode() + b"\0" + data)
    return f"{repository}:deps-{digest.hexdigest()}"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("tag", "build"))
    parser.add_argument("app", type=Path, help="Application checkout containing the lockfiles")
    parser.add_argument("--repository", default=os.environ.get("CI_IMAGE_REPOSITORY", "ghcr.io/aldefouw/piston-ci"))
    parser.add_argument("--push", action="store_true", help="Publish instead of loading into local Docker")
    args = parser.parse_args()
    try:
        image = image_tag(args.app, args.repository)
        if args.command == "tag":
            print(image)
            return
        lock = (args.app / "Gemfile.lock").read_text()
        ruby = re.search(r"^RUBY VERSION\n\s+ruby (\d+\.\d+\.\d+)", lock, re.M)
        bundler = re.search(r"^BUNDLED WITH\n\s+(\S+)", lock, re.M)
        if not ruby or not bundler:
            parser.error("Gemfile.lock must specify RUBY VERSION and BUNDLED WITH")
        # Never send source, credentials, .env, or local dependencies to Docker.
        with tempfile.TemporaryDirectory(prefix="piston-ci-image-") as directory:
            context = Path(directory)
            checksums = []
            for name in DEPENDENCIES:
                shutil.copyfile(args.app / name, context / name)
                checksums.append(f"{hashlib.sha256((context / name).read_bytes()).hexdigest()}  {name}\n")
            for name in RECIPES:
                shutil.copyfile(IMAGE_DIR / name, context / name)
            (context / "dependencies.sha256").write_text("".join(checksums))
            print(f"Building {image}", flush=True)
            subprocess.run([
                "docker", "buildx", "build", "--platform", "linux/amd64",
                "--build-arg", f"RUBY_VERSION={ruby.group(1)}",
                "--build-arg", f"BUNDLER_VERSION={bundler.group(1)}",
                "--tag", image, "--push" if args.push else "--load", str(context),
            ], check=True)
        print(image)
    except (OSError, subprocess.CalledProcessError) as error:
        parser.exit(1, f"CI image error: {error}\n")


if __name__ == "__main__":
    main()
