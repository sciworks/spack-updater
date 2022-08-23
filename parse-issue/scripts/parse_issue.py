#!/usr/bin/env python3

import argparse
import os
import sys

# If we are in an issue, get title from environment
title = os.environ.get("title")


def get_parser():
    parser = argparse.ArgumentParser(
        description="Spack Updater Issue Parser",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument("issue_text", help="path to issue text file.")
    return parser


env_file = os.getenv("GITHUB_ENV")


def main():

    parser = get_parser()

    # If an error occurs while parsing the arguments, the interpreter will exit with value 2
    args, extra = parser.parse_known_args()

    # Show args to the user
    print("issue-txt: %s" % args.issue_text)
    if not os.path.exists(args.issue_text):
        sys.exit("File %s does not exist." % args.issue_text)
    with open(args.issue_text, "r") as fd:
        text = fd.read()

    # Get a dict of values
    values = {
        xx.split(":", 1)[0].strip(): xx.split(":", 1)[-1].strip()
        for xx in [x for x in text.split("\n") if ":" in x]
    }

    # Exit early if we have a title and doesn't matach
    if title and "[package-update]" not in title:
        return
    for k, v in values.items():
        if k == "repo" and not v.startswith("http"):
            v = "https://github.com/%s" % v
        if env_file:
            with open(env_file, "a") as fd:
                fd.write("spack_updater_%s=%s\n" % (k.lower(), v))
        print('"spack_updater_%s=%s" >> $GITHUB_ENV' % (k.lower(), v))


if __name__ == "__main__":
    main()
