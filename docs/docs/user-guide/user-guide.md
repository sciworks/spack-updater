# User's Guide

## Table of Contents

- [Organization](#organization)
- [Actions](#actions)
  - [Testing Builds](#testing-builds)
  - [Update Upstream](#update-upstream)
  - [Look for New Releases](#look-for-new-releases)
  - [Spack Updater](#spack-updater)

This is the user guide for the actions! To see how to setup your own spack updater repository,
see the Developer Guide.

## Organization

The main branch has a simple structure with a packages folder where you can keep your recipes.
It might look like this:

```
├── packages
│   ├── flux-core
│   │   ├── 0001-build-fix-build-errors-with-side-installed-0MQ.patch
│   │   ├── package.py
│   │   └── VERSION
│   ├── flux-pmix
│   │   ├── package.py
│   │   └── VERSION
│   └── flux-sched
│       ├── jobid-sign-compare-fix.patch
│       ├── no-valgrind.patch
│       ├── package.py
│       └── VERSION
├── README.md
└── repo.yaml
```
The only addition to the core packages is the addition of a VERSION file in
the package directory with the latest spack version. While we *could* parse
this from the package.py, due to subtle differences in package.py format
it's easier to do it this way (for now)! If you'd like to submit a pull
request to the action to deem this file unnecessary, please do!

### Why this organization?

?> The answer is simplicity.

You don't need to go digging through many levels of paths that you might forget, or get lost in
the wildnerness of thousands of packages. They are front and center. The repository also has a spack develop branch, 
and you largely don't need to interact with it. The reason it's there is because when there are changes here 
to our packages, we create a branch (that needs to be forked from spack) here, and then can give you a link to open a pull request.

## Actions

For each action, examples are provided that are being used actively for flux-framework.

### Testing Builds

Importantly, we want to always test that our packages build against the develop build of spack.
This means we want to test a matrix of builds nightly, or on any pull request that changes a package file. This is done by way of a
[.github/workflows/test-build.yaml](https://github.com/flux-framework/spack/blob/main/.github/workflows/test-build.yaml) workflow. The only thing you
need to update here is the list of your packages under the matrix:

```yaml
jobs:
  package-builds:
    name: Test Package Builds
    runs-on: ubuntu-latest
    strategy:
      max-parallel: 4
      matrix:
        # Here are the names you'll want to edit
        package: [flux-core, flux-sched, flux-pmix]
```

Those names should correspond to package folders in [packages](https://github.com/flux-framework/spack/blob/main/packages). If you are interested,
[here is an example](https://github.com/flux-framework/spack/actions/runs/2916603405) of a nightly build running, and you
can mimic the logic in [.github/workflows/test-build.yaml](https://github.com/flux-framework/spack/blob/main/.github/workflows/test-build.yaml) 
to make a matrix and use caches before the action.

#### Why do we cache?

You'll notice that we cache both clingo and the package build, and it's based on the micro-architecture of the runner.
The reason is that different runners can produce different hashes, so if we only generate one cache it will be missed
about 3/4 of the time (the spack directory generated will have a different name). But the cache is great - by caching
clingo, it saves us about 22 minutes, and then for a long package build, it can reduce 45-55 minutes down to maybe 5
(depending on the changes in your packages that might warrant an update).

#### How are the builds done?

The builds are done by way of the [pakages](https://syspack.github.io/pakages/) action, which is what
makes it possible to run a command like:

```bash
$ pakages --builder spack build zlib
```

And then use the repository in the present working directory. Pakages also is optimized to push
to GitHub packages (as a build cache) so [check out the library and actions](https://syspack.github.io/pakages/getting_started/user-guide.html)
if you are interested! 

### Update Upstream

When we create a new branch with a package update to prepare to open a pull request to spack,
it's important that it's updated! It also doesn't look good to have a develop branch that is severely behind.
To support this, we have the [.github/workflows/upstream-update.yaml](https://github.com/flux-framework/spack/blob/main/.github/workflows/upstream-update.yaml)
workflow, which you can copy and use as is. If you are interested, [here is an example](https://github.com/flux-framework/spack/actions/runs/2916613894)
of it running. It will run nightly, or at the frequency you desire! Here is an example to update your develop with spack develop (and see the [action.yaml](https://github.com/sciworks/spack-updater/tree/main/upstream/action.yaml)
for additional variables.

```yaml
name: Spack Upstream Updater
on:
  workflow_dispatch:
  schedule:
    - cron:  '5 4 * * *'

jobs:
  update-spack:
    name: Pull updates from upstream spack
    runs-on: ubuntu-latest
    steps:
      - name: Update with Upstream
        uses: sciworks/spack-updater/upstream@main
        with:
          token: ${{ secrets.GITHUB_TOKEN }}
```

### Look for New Releases

If you maintain packages on GitHub, we use the releases API to (also nightly) check to see if there is a new release.
When we find one we:

- update the package.py file
- test the new build
- open a pull request on success

You can see an example workflow under [flux-sched](https://github.com/flux-framework/spack/runs/7988450863?check_suite_focus=true),
and the [pull request it opened](https://github.com/flux-framework/spack/pull/31). Once these changes are in, the next run of
the spack updater action, discussed next, will prepare to open a pull request to spack.

**Important** checking for new releases is currently only supported for GitHub releases. If you have another
package release type with an API that could be supported, please open an issue and it can be added.

### Spack Updater

This action is the core of the set, as it is going to coordinate changes from your repository
here to spack! It runs nightly to essentially do a diff between your packages on the main branch
and spack develop, and:

 - Given changes here, a branch is prepared to pull request to spack, and an issue opned you can click to open the PR (e.g, [see this example](https://github.com/spack/spack/pull/32320))
 - If there are changes to spack, it will instead open a pull request here (the less likely case if you do most development here, but not impossible!)

And that's it! Please don't hesitate to ask a question or suggest a change for any of these workflows.
They are fairly new and we are excited to make them better!
