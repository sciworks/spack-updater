# Spack Updater

This is a set of actions to supplement a fork of spack that will deploy an automated set of workflows to do updates,
and ensure that changes to your packages OR changes to spack do not break your builds.
This means that:

1. We have a main branch that is an orphan from spack develop
2. Spack develop is updated from upstream nightly
3. The packages in your main branch can be worked on, are automatically updated, and builds are always tested.

Or in short terms, you can maintain your spack packages in one simple place,
and the automation will support you to update the package versions, test builds
with updates (and nightly) and assist with opening pull requests to spack.

Interested to create your own, or see how it works? Check out:

 - ⭐️ [Spack Updater Documentation](https://sciworks.github.io/spack-updater/) ⭐️.
 - 🌀️ [Flux Framework Example](https://github.com/flux-framework/spack/) 🌀️


## License

This project is in support of [Flux Framework](https://github.com/flux-framework/flux-core), with release:
 - SPDX-License-Identifier: LGPL-3.0
 - LLNL-CODE-764420

And [Spack](https://github.com/spack/spack):
 - SPDX-License-Identifier: (Apache-2.0 OR MIT)
 - LLNL-CODE-811652
 
See the respective repositories for details.
