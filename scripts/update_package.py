#!/usr/bin/env python3

import argparse
import copy
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.parse

import requests
import yaml

here = os.path.dirname(os.path.abspath(__file__))

# GITHUB_TOKEN required no matter what
token = os.environ.get("GITHUB_TOKEN")
if not token:
    sys.exit("GITHUB_TOKEN is required")

headers = {"Accept": "application/vnd.github+json", "Authorization": "token %s" % token}

# intended to be run in GitHub actions
from_repository = os.environ.get("GITHUB_REPOSITORY")
from_branch = os.environ.get("GITHUB_REF_NAME")
if not from_repository:
    print(
        "GITHUB_REPOSITORY not found in environmnt - will only print dry run to screen."
    )


def get_parser():
    parser = argparse.ArgumentParser(
        description="Spack Updater",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument(
        "package", help="name of package under packages (in local directory) to parse"
    )
    parser.add_argument(
        "--repo",
        help="repository directory",
        default=os.getcwd(),
    )
    parser.add_argument(
        "--upstream",
        help="repository upstream to update",
        default="https://github.com/vsoch/spack",
    )
    return parser


class SpackChangeRequest:
    """
    A spack change request will open an issue to a spack repository
    with a workflow that knows how to request changes.
    """

    def __init__(self, package, repo, branch):
        self.package = package
        self.from_repo = from_repository
        self.from_branch = from_branch
        self.to_repo = repo
        self.to_branch = branch
        self.request = {}

    @property
    def data(self):
        data = copy.deepcopy(self.request)
        data["repo"] = self.from_repo
        data["package"] = self.package
        if self.from_branch:
            data["branch"] = self.from_branch
        return data

    def has_issues(self, title):
        """
        Given a new issue to be opened, return True if an issue is already open.
        """
        url = "https://api.github.com/repos/%s/issues" % self.from_repo
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            sys.exit("Issue retrieving previous issues.")
        issues = response.json()
        issues = [x for x in issues if "pull_request" not in x]
        for issue in issues:
            if issue["title"].strip() == title.strip():
                return True
        return False

    def delete_issue(self, number):
        """
        Delete an old issue for a previous update request.

        This isn't currently used. The original updater logic always opened a new issue
        (and closed previous ones) but given the slowness of the PR review process,
        this will make a huge number of issues. Instead, if we find an open issue
        we simply don't open a new one.
        """
        print("Found old issue to close %s" % number)
        url = "https://api.github.com/repos/%s/issues/%s" % (self.from_repo, number)
        data = {"number": number, "state": "closed"}
        response = requests.patch(url, headers=headers, data=json.dumps(data))
        if response.status_code != 200:
            sys.exit("Issue closing issue %s" % number)

    def submit(self):
        """
        Submit an update or new package request by opening an issue on our own repo
        """
        title = "[package-update] request to update %s" % self.package
        body = "This is a request for an automated package update.\n\n" + yaml.dump(
            self.data
        )
        print(f"Title: {title}")
        print(body)
        if self.has_issues(title):
            print(f"Request {title} already has an issue opened, not re-opening.")
            return

        # This is the url we assemble that will be provided in the issue to trigger an update workflow
        encoded_title = urllib.parse.quote(title)
        encoded_body = urllib.parse.quote(body)
        update_url = f"{self.to_repo}/issues/new?labels=package-update&title={encoded_title}&body={encoded_body}"
        print(update_url)

        # Now update the body to include this link!
        body = "This is a request for an automated package update. You can click the link below to open an issue on spack and request the update.\n\n"
        body += " - [Click here to request the update](%s)\n\n" % update_url
        body += "You can close this issue once you've clicked and opened the one above!"

        # prepare the message
        if not self.from_repo:
            return

        url = "https://api.github.com/repos/%s/issues" % self.from_repo
        issue = {"title": title, "body": body}
        response = requests.post(url, headers=headers, data=json.dumps(issue))
        if response.status_code not in [200, 201]:
            sys.exit(
                "Issue making request: %s, %s" % (response.reason, response.json())
            )

        # Show url to user
        res = response.json()
        print("Opened request issue:\n%s" % res["html_url"])

    def populate_new_package(self, package_path):
        """
        Populate a new package.
        """
        self.request = {"action": "new-package", "path": package_path}

    def populate_update_package(self, package_path):
        """
        Update a package (copy all content into spack and PR)
        """
        self.request = {"action": "update-package", "path": package_path}


class PackageDiffer:
    """
    Determine if a package is different and act accordingly.
    """

    def __init__(self, repo, upstream, branch=None, pull_request=True):
        self.repo = os.path.abspath(repo)
        self.spack_root = self.clone(upstream, branch)
        self.pull_request = pull_request

    def find_package(self, package_name):
        """
        Ensure initial package directory and file exist!
        """
        package_dir = os.path.join(self.repo, "packages", package_name)
        package_file = os.path.join(package_dir, "package.py")
        if not os.path.exists(package_dir):
            print(f"{package_dir} does not exist, will obtain from upstream...")
            spack_package = self.spack_package_dir(package_name)
            shutil.copytree(spack_package, package_dir)
            self.set_changes()
        if not os.path.exists(package_file):
            sys.exit(
                f"Package file {package_file} does not exist - not found in upstream or here!"
            )
        return package_dir

    def set_changes(self):
        """
        Shared function to indicate to running action there are changes (for PR).
        """
        env_file = os.getenv("GITHUB_ENV")
        if env_file and self.pull_request:
            with open(env_file, "a") as fd:
                fd.write("spack_updater_changes=true\n")

    def spack_package_dir(self, package_name):
        """
        Get full path to current spack package directory.
        """
        return os.path.join(
            self.spack_root,
            "var",
            "spack",
            "repos",
            "builtin",
            "packages",
            package_name,
        )

    def cleanup(self):
        if self.spack_root and os.path.exists(self.spack_root):
            shutil.rmtree(self.spack_root)

    def diff(self, package_name):
        """
        Perform a diff:

        1. look for changed files and compare based on change date.
        2. look for added or removed files.
        """
        package_dir = self.find_package(package_name)
        spack_package_dir = self.spack_package_dir(package_name)

        # Prepare a spack change request
        request = SpackChangeRequest(package_name, self.upstream, self.branch)

        # Case 1: package doesn't exist in spack
        if not os.path.exists(spack_package_dir):
            request.populate_new_package(os.path.relpath(package_dir, self.repo))
            return request

        # For each file in current, compare to spack install
        # We need to decide if it's an update (to spack) or to here
        # If the file doesn't exist, it's too hard to tell if it was deleted
        # so we go by change only, assumming changes in dependency files
        # also mean changes to the main package.py
        to_spack = False
        no_change = True
        for filename in recursive_find(package_dir):
            basename = filename.replace(package_dir, "").strip(os.sep)
            spack_filename = os.path.join(spack_package_dir, basename)

            # Could be that it's a new file, OR...
            # There could be the case here of a file being deleted...
            if not os.path.exists(spack_filename):
                continue

            # The spack file was modified more recently (later time)
            modified_spack = os.stat(spack_filename).st_mtime
            modified_here = os.stat(filename).st_mtime
            if modified_spack == modified_here:
                continue
            if modified_spack > modified_here:
                to_spack = True
                no_change = False
                break

            if modified_here > modified_spack:
                no_change = False

        if to_spack:
            request.populate_update_package(os.path.relpath(package_dir, self.repo))
            return request

        # Updates here
        elif not to_spack and not no_change:
            self.stage_changes(spack_package_dir, package_dir)
            self.set_changes()

        # If we don't return a request, assume that we want to update from spack
        # to here.

    def stage_changes(self, src, dst):
        """
        Stage changes here
        """
        for filename in recursive_find(src):
            # Skip external version file, if used
            if filename.endswith("VERSION"):
                continue
            basename = filename.replace(src, "").strip(os.sep)
            to_filename = os.path.join(dst, basename)
            if os.path.exists(to_filename):
                os.remove(to_filename)
            dest_dir = os.path.dirname(to_filename)
            if not os.path.exists(dest_dir):
                os.makedirs(dest_dir)
            shutil.copyfile(filename, to_filename)

    def clone(self, upstream, branch=None):
        """
        Clone spack develop to a temporary directory.
        """
        tmpdir = tempfile.mkdtemp()
        cmd = ["git", "clone", "--depth", "1"]
        if branch:
            cmd += ["--branch", branch]
        cmd += [upstream, tmpdir]
        try:
            subprocess.run(cmd, check=True)
        except subprocess.CalledProcessError as e:
            raise ValueError("Failed to clone spack develop repository:\n{}", e)

        # Save for knowing later
        self.upstream = upstream
        self.branch = branch
        return tmpdir


def recursive_find(base, pattern=None):
    """
    Find filenames that match a particular pattern, and yield them.
    """
    # We can identify modules by finding module.lua
    for root, folders, files in os.walk(base):
        for file in files:
            fullpath = os.path.abspath(os.path.join(root, file))

            if pattern and not re.search(pattern, fullpath):
                continue

            yield fullpath


def main():

    parser = get_parser()

    # If an error occurs while parsing the arguments, the interpreter will exit with value 2
    args, extra = parser.parse_known_args()

    # Show args to the user
    print("    upstream: %s" % args.upstream)
    print("     package: %s" % args.package)
    print("        repo: %s" % args.repo)

    cli = PackageDiffer(args.repo, args.upstream, args.branch)
    request = cli.diff(args.package)
    if request and args.open_issue:
        request.submit()
    cli.cleanup()


if __name__ == "__main__":
    main()
