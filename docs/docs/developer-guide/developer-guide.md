# Developer's Guide

## Table of Contents

- [Setting Up](#setting-up)
  - [Repository](#repository)
  - [Content](#content)

## Setting Up

This guide will walk you through how to create your own spack updater fork to maintain
your spack packages. To see instructions for using the actions, see the User Guide.

### Repository

To setup, you can do the following:

1. Create a fork of spack to your organization, only grabbing the develop branch.
2. Clone and create an orphan branch `git switch --orphan main` and then add the content here (the README, and .github workflows)
3. Add your custom packages and repo.yaml under packages.

The above might look like the following:

```bash
# You can use the flux-framework repository as a template
$ git clone https://flux-framework/spack /tmp/spack-template

# This is your fork
$ git clone git@github.com:<your-org>/spack spack
$ cd spack

# Create an orphan branch
$ git switch --orphan main

# Copy over the content you need (or you can emulate / update)
cp /tmp/spack-template/README.md ./README.md
cp -R /tmp/spack-template/.github ./.github
cp -R /tmp/spack-template/repo.yaml ./repo.yaml
```

### Content

You'll then want to:

1. Update the repo.yaml with some name for your packages repository (it will be added to spack and needs a different name than builtin).
2. Delete the subdirectories of packages that you don't need (and add your own from spack). 
3. Ensure issues are enabled on your fork.
4. Add a label for "spack-updater"
5. Ensure your develop branch is protected (so you cannot delete it)!
6. Update the workflows with matrices to list the packages you want to update/build.
7. After that, you can push the main branch and make it default so it's the first seen upon visiting your repository (akin to this one!)

You might next want to look at the User Guide to see action-specific instructions, or 
see [https://github.com/flux-framework/spack](https://github.com/flux-framework/spack) for an example of this setup.
