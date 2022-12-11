#!/usr/bin/env python3

import argparse
import hashlib
import requests
import tempfile
import re
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


def set_env_and_output(name, value):
    """
    helper function to echo a key/value pair to output and env.

    Parameters:
    name (str)  : the name of the environment variable
    value (str) : the value to write to file
    """
    for env_var in ("GITHUB_ENV", "GITHUB_OUTPUT"):
        environment_file_path = os.environ.get(env_var)
        print("Writing %s=%s to %s" % (name, value, env_var))

        with open(environment_file_path, "a") as environment_file:
            environment_file.write("%s=%s\n" % (name, value))


class PackageUpdater:
    def __init__(self, package_dir, repo, dry_run=False):
        self.package_dir = package_dir
        self.repo = repo
        self.dry_run = dry_run
        self._latest_version = None
        self._current_version = self.get_current_version()
        self.download_url = None
        self.read_package()

    def read_package(self):
        """
        If a repo or VERSION isn't provided, derive from package file.
        """
        package_py = read_file(self.package_file)
        self.lines = package_py.split("\n")
        for line in self.lines:
            if "url=" in line.replace(" ", ""):
                self.download_url = (
                    line.replace(" ", "").split("url=")[-1].strip('"').strip("'")
                )
                print(f"Setting download url to {self.download_url}")
                if not self.repo and "github.com" not in self.download_url:
                    sys.exit(
                        "We currently only support release updated for GitHub, please open an issue with your setup!"
                    )

                # This is hacky, we can make it better :)
                if not self.repo:
                    repo = (
                        self.download_url.rsplit("/", 2)[0]
                        .split("//github.com")[-1]
                        .strip("/")
                    )
                    self.repo = "/".join(repo.split("/")[0:2]).strip("/")
                    print(f"Setting repo to {self.repo}")

            if not self._current_version and "version(" in line and "sha256" in line:
                current_version = line.strip().split(" ")[0]
                for char in [" ", ",", "version(", "'", '"']:
                    current_version = current_version.replace(char, "")
                print(f"Found current version {current_version}")
                self._current_version = current_version

    @property
    def package(self):
        return os.path.basename(self.package_dir).strip("/")

    @property
    def version_file(self):
        return os.path.join(self.package_dir, "VERSION")

    @property
    def package_file(self):
        return os.path.join(self.package_dir, "package.py")

    @property
    def current_version(self):
        return self._current_version

    def get_current_version(self):
        """
        Derive current version from file (or VERSION)
        """
        # Version file has latest version, eventually could be spack package
        if os.path.exists(self.version_file):
            self._current_version = read_file(self.version_file).strip("\n")

    def check(self):
        """
        Given a package directory and repository name, check for new releases.
        """
        latest = self.get_latest_release()
        version = self.current_version
        tag = latest["tag_name"]

        # Some versions are prefixed with v
        if tag == version or tag == f"v{version}":
            print("No new version found.")
            return
        print(f"New version {tag} detected!")
        self.update_package(latest)
        set_env_and_output("version", tag)

    def get_latest_release(self):
        """
        Get the lateset release of a repository (under flux-framework)
        """
        url = f"https://api.github.com/repos/{self.repo}/releases"
        response = requests.get(url, headers=headers, params={"per_page": 100})
        response.raise_for_status()

        # latest release should be first
        return response.json()[0]

    def update_package(self, latest):
        """
        Write the new package version to file
        """
        tag = latest["tag_name"]
        naked_version = tag.replace("v", "")

        tmp = tempfile.mkdtemp()
        download_path = os.path.join(tmp, "%s-%s.tar.gz" % (self.package, tag))

        # First try: we have a download url to sub version in
        if self.download_url:
            self.download_package_url(naked_version, download_path)

        # Fall back to deriving URL manually
        if not os.path.exists(download_path):
            if not self.download_release(tag, naked_version, download_path):
                self.download_archive(naked_version, download_path)

        if not os.path.exists(download_path):
            sys.exit(
                "Failed to download new release! If there isn't support for the archive type, open an issue to request it."
            )

        # Get new digest
        digest = get_sha256sum(download_path)
        shutil.rmtree(tmp)
        set_env_and_output("package", f"{self.package}@{naked_version}")
        set_env_and_output("digest", digest)
        if self.dry_run:
            return

        self.update_package_file(naked_version, digest)

    def update_package_file(self, version, digest):
        """
        Update the package file with a new version and digest.
        """
        # Create new line
        newline = '    version("%s", sha256="%s")' % (version, digest)

        # Write new package file
        lines = []
        for line in self.lines:
            # If we find the current version line, add version before it
            if self._current_version in line and "version(" in line:
                print("Updating with: %s" % newline)
                lines.append(newline)
            lines.append(line)
        write_file("\n".join(lines), self.package_file)

        # Write version file only if exists
        if os.path.exists(self.version_file):
            write_file(version, self.version_file)

    def download_package_url(self, tag, download_path):
        """
        Derive the new download url based on the existing one.
        """
        match = re.search("(\d+\.)?(\d+\.)?(\*|\d+)", self.download_url)
        if not match:
            return
        match = match.group()
        url = self.download_url.replace(match, tag)
        return self.download(url, download_path)

    def download_release(self, tag, naked_version, download_path):
        """
        Download a release tarball
        """
        tarball_url = f"https://github.com/{self.repo}/releases/download/{tag}/{self.package}-{naked_version}.tar.gz"
        return self.download(tarball_url, download_path)

    def download(self, url, dest):
        """
        Download a url to a destination file.
        """
        print(url)
        response = requests.get(url, stream=True)
        if response.status_code == 200:
            with open(dest, "wb") as f:
                f.write(response.raw.read())
            return True
        return False

    def download_archive(self, naked_version, download_path):
        """
        Download an archive tarball.
        """
        tarball_url = (
            f"https://github.com/{self.repo}/archive/refs/tags/{naked_version}.tar.gz"
        )
        return self.download(tarball_url, download_path)


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
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=False,
        help="Don't write changes to file",
    )
    return parser


def main():

    parser = get_parser()

    # If an error occurs while parsing the arguments, the interpreter will exit with value 2
    args, extra = parser.parse_known_args()

    # Show args to the user
    print("     package: %s" % args.package)
    print("        repo: %s" % args.repo)
    print("     dry-run: %s" % args.dry_run)

    # Allow the checker to derive repo from the url
    if args.repo == ".":
        args.repo = None

    updater = PackageUpdater(args.package, args.repo, args.dry_run)
    updater.check()


if __name__ == "__main__":
    main()
