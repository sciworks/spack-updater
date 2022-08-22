#!/bin/bash
# A package pull request opens a branch from main
# where the packages/ are, and opens to update
printf "GitHub Actor: ${GITHUB_ACTOR}\n"
export BRANCH_FROM="update-package/${package}-$(date '+%Y-%m-%d')"
git remote set-url origin "https://x-access-token:${GITHUB_TOKEN}@github.com/${GITHUB_REPOSITORY}.git"
git remote add upstream "https://x-access-token:${GITHUB_TOKEN}@github.com/spack/spack.git"
git config --global user.name "github-actions"
git config --global user.email "github-actions@users.noreply.github.com"

git fetch
git branch

# Move packages somewhere else
repo_path=${PWD}/packages/${package}
echo ${repo_path}
ls ${repo_path}
mkdir -p /tmp/packages/${package}
cp -R ${repo_path} /tmp/packages/
ls /tmp/packages

# Trivial commit
git commit -a -s -m 'save trivial changes'

# Important - needs to be checked out from upstream develop!
git checkout -b "${BRANCH_FROM}" upstream/develop
git branch

# Update with develop
git pull upstream develop

# Copy changed files to put in new branch
cp /tmp/packages/${package}/* var/spack/repos/builtin/packages/${package}/
rm -rf var/spack/repos/builtin/packages/${package}/VERSION
git add var/spack/repos/builtin/packages/${package}/*

git status
ls var/spack/repos/builtin/packages/${package}/*

git commit -m "Automated deployment to update package ${package} $(date '+%Y-%m-%d')" && git push origin ${BRANCH_FROM} && echo "open_pr=1" >> $GITHUB_ENV  || echo "No changes"
echo "PULL_REQUEST_FROM_BRANCH=${BRANCH_FROM}" >> $GITHUB_ENV
echo "BRANCH_FROM=${BRANCH_FROM}" >> $GITHUB_ENV
