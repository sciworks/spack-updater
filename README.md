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
