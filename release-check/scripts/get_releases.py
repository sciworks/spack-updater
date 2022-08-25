#!/usr/bin/env python3

import argparse
import hashlib
import requests
import tempfile
import shutil
import sys
import os

# Look for version updates for a package
# python script/get_releases.py packages/flux-core

master_branch = 'version("master", branch="master"'
main_branch = 'version("main", branch="main"'

token = os.environ.get("GITHUB_TOKEN")
headers = {}
if token:
    headers["Authorization"] = "token %s" % token


def get_sha256sum(filename):
    hasher = hashlib.sha256()
    with open(filename, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def get_latest_release(repo):
    """
    Get the lateset release of a repository (under flux-framework)
    """
    url = f"https://api.github.com/repos/{repo}/releases"
    response = requests.get(url, headers=headers, params={"per_page": 100})
    response.raise_for_status()

    # latest release should be first
    return response.json()[0]


def download_release(repo, tag, package, naked_version, download_path):
    tarball_url = f"https://github.com/{repo}/releases/download/{tag}/{package}-{naked_version}.tar.gz"
    print(tarball_url)
    response = requests.get(tarball_url, stream=True)
    if response.status_code == 200:
        with open(download_path, "wb") as f:
            f.write(response.raw.read())
        return True
    return False


def download_archive(repo, naked_version, download_path):
    tarball_url = f"https://github.com/{repo}/archive/refs/tags/{naked-version}.tar.gz"
    print(tarball_url)
    response = requests.get(tarball_url, stream=True)
    if response.status_code == 200:
        with open(download_path, "wb") as f:
            f.write(response.raw.read())
        return True
    return False


def update_package(package_dir, latest, repo):
    """
    Write the new package version to file
    """
    package = os.path.basename(package_dir)
    package_file = os.path.join(package_dir, "package.py")
    version_file = os.path.join(package_dir, "VERSION")

    tag = latest["tag_name"]
    naked_version = tag.replace("v", "")

    tmp = tempfile.mkdtemp()
    download_path = os.path.join(tmp, "%s-%s.tar.gz" % (package, tag))
    version_file = os.path.join(package_dir, "VERSION")

    if not self.download_release(repo, tag, package, naked_version, download_path):
        self.download_archive(repo, naked_version, download_path)

    if not os.path.exists(download_path):
        sys.exit(
            "Failed to download new release! If there isn't support for the archive type, open an issue to request it."
        )

    # Get new digest
    digest = get_sha256sum(download_path)

    # Create new line
    newline = '    version("%s", sha256="%s")' % (naked_version, digest)

    # Write new package file
    package_py = read_file(package_file)
    last_line = None
    lines = []
    for line in package_py.split("\n"):
        if last_line and (master_branch in last_line or main_branch in last_line):
            print("Updating with: %s" % newline)
            lines.append(newline)
        lines.append(line)
        last_line = line
    write_file("\n".join(lines), package_file)
    write_file(naked_version, version_file)
    shutil.rmtree(tmp)
    print(f"::set-output name=package::{package}@{naked_version}")


def write_file(data, filename):
    """
    Write content to file
    """
    with open(filename, "w") as fd:
        fd.writelines(data)


def read_file(filename):
    """
    Read content from file
    """
    with open(filename, "r") as fd:
        content = fd.read()
    return content


def check_for_releases(package_dir, repo):
    """
    Given a package directory and repository name, check for new releases.
    """
    package = os.path.basename(package_dir).strip("/")
    version_file = os.path.join(package_dir, "VERSION")

    # Version file has latest version, eventually could be spack package
    if not os.path.exists(version_file):
        sys.exit("Version file %s does not exist." % version_file)

    version = read_file(version_file).strip("\n")
    print(f"Current version is {version}")
    latest = get_latest_release(repo)
    tag = latest["tag_name"]

    # Some versions are prefixed with v
    if tag == version or tag == f"v{version}":
        print("No new version found.")
        return
    print(f"New version {tag} detected!")
    update_package(package_dir, latest, repo)
    print(f"::set-output name=version::{tag}")


def get_parser():
    parser = argparse.ArgumentParser(
        description="Spack Updater for Releases",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument(
        "package", help="name of package under packages (in local directory) to parse"
    )
    parser.add_argument(
        "--repo",
        help="GitHub repository name",
    )
    return parser


def main():

    parser = get_parser()

    # If an error occurs while parsing the arguments, the interpreter will exit with value 2
    args, extra = parser.parse_known_args()

    # Show args to the user
    print("     package: %s" % args.package)
    print("        repo: %s" % args.repo)

    check_for_releases(args.package, args.repo)


if __name__ == "__main__":
    main()
