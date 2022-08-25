# Frequently Asked Questions

## Why do we open an issue to request a pull request?

In order to open a pull request programatically, it either requires that you have
a GitHub token scoped to the repository in question (e.g., within GitHub actions
running on repository "myorg/pancakes" I can create a new branch and pull request
to "myorg/pancakes" all with the workflow token) OR it requires a personal
access token. @vsoch is not a fan of putting personal access tokens in places,
so as a workaround, the action does the work to create the pull request
branch, and then opens an issue with a link that you just need to click! This
also makes sense because the pull request is opened by *you* as the spack
package maintainer.

## I have an idea! How do I share it?

Great! These actions exist to help maintainers, and contributors, and if you
have an idea for how to make the library better we want to hear from you! Please [get in contact with us](support).
