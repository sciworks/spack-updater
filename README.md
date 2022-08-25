# Spack Updater

The spack updater is intended to target a local package.py recipe of interest,
and compare it for differences with upstream spack.

1. If the files differ and the upstream is changed more recent, a PR is done to the branch here for it.
2. If the files differ and the local change is more recent, a PR is done to spack. See below for how this is done.
3. The same is applied for changes to associates files in the package directory.

**under development**

### How do we update to spack?

We can't do a pull request to a different repository programatically without a
personal access token, which @vsoch doesn't like to provide, even scoped.

Thus, we push to a branch here, and then open an issue on the repository here with
a link to open a pull request. The pull request is open by a user, but the updates and
branch automation are handled by the action.

TLDR: This should ensure that local changes to a package.py file and associated assets
are generally synced. It's recommended to do this in unision with ensuring the package
still builds. This can be done with the [pakages spack builder](https://syspack.github.io/pakages/).

### Example

When:

 1. Here is an example of an issue that is opened with a branch to PR: [https://github.com/spack/spack/pull/32320](https://github.com/spack/spack/pull/32320)
 2. And the pull request I could open [https://github.com/spack/spack/pull/32320](https://github.com/spack/spack/pull/32320)

See [https://github.com/flux-framework/spack](https://github.com/flux-framework/spack) for an example of using the action.


### Packages Workflows

How does it all work? 

#### Organization

The main branch has a simple structure with a packages folder where you can keep your recipes.
You don't need to go digging through many levels of paths that you might forget, or get lost in
the wildnerness of thousands of packages. They are front and center. The repository also has a spack develop branch, 
and you largely don't need to interact with it. The reason it's there is because when there are changes here 
to our packages, we create a branch (that needs to be forked from spack) here, and then can give you a link to open a pull request.

### Testing Builds

Importantly, we want to always test that our packages build against the develop build of spack.
This means we want to test a matrix of builds nightly, and this is done by way of the
[.github/workflows/test-build.yaml](.github/workflows/test-build.yaml) workflow. The only thing you
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

Those names should correspond to package folders in [packages](packages). If you are interested,
[here is an example](https://github.com/flux-framework/spack/actions/runs/2916603405) of a nightly build running.

### Update Upstream

When we create a new branch with a package update to prepare to open a pull request to spack,
it's important that it's updated! It also doesn't look good to have a develop branch that is severely behind.
To support this, we have the [.github/workflows/upstream-update.yaml](.github/workflows/upstream-update.yaml)
workflow, which you can copy and use as is. If you are interested, [here is an example](https://github.com/flux-framework/spack/actions/runs/2916613894)
of it running. It will run nightly.

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
