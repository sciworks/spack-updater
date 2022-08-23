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
package = os.environ.get("package")
from_repository = os.environ.get("GITHUB_REPOSITORY")
from_branch = os.environ.get("BRANCH_FROM")
if not from_repository or not from_branch:
    print("GITHUB_REPOSITORY or FROM_BRANCH not found in environment.")

print(f"Repo: {from_repository}")
print(f"From Branch: {from_branch}")
print(f"Package: {package}")


def has_issues(title):
    """
    Given a new issue to be opened, return True if an issue is already open.
    """
    url = "https://api.github.com/repos/%s/issues" % from_repository
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        sys.exit("Issue retrieving previous issues.")
    issues = response.json()
    issues = [x for x in issues if "pull_request" not in x]
    for issue in issues:
        if issue["title"].strip() == title.strip():
            return True
    return False


def open_issue():
    """
    Open an issue with link to open a pull request.
    """
    title = f"[package-update] for {package}: {from_branch}"
    body = "This is a request to open a pull request for a package update.\n\n"

    # Ensure we don't open the same one twice
    if has_issues(title):
        print("An issue is already open for this branch update.")
        return

    # This is the url we assemble that will be provided in the issue to trigger an update workflow
    url = f"https://api.github.com/repos/{from_repository}/issues"
    print(url)
    issue = {"title": title, "body": body}
    print(issue)
    response = requests.post(url, headers=headers, data=json.dumps(issue))
    if response.status_code not in [200, 201]:
        sys.exit("Issue making request: %s, %s" % (response.reason, response.json()))
    # Show url to user
    res = response.json()
    print("Opened request issue:\n%s" % res["html_url"])

    # Patch with the URL
    number = res["number"]
    reference = urllib.parse.quote(
        f"This will close https://github.com/{from_repository}/issues/{number}"
    )
    issue_url = f"https://github.com/{from_repository}/pull/new/{from_branch}?expand=1&body={reference}"
    body += f"[Click here to open the pull request]({issue_url})"
    issue = {"body": body}
    response = requests.patch(
        url + "/" + str(number), headers=headers, data=json.dumps(issue)
    )
    res = response.json()
    print("Patched issue with update link:\n%s" % res["html_url"])


if __name__ == "__main__":
    open_issue()
