#!/bin/bash
# A package pull request opens a branch from main
# where the packages/ are, and opens to update
printf "GitHub Actor: ${GITHUB_ACTOR}\n"
export BRANCH_FROM="update-package/${package}-$(date '+%Y-%m-%d')"
git remote set-url origin "https://x-access-token:${GITHUB_TOKEN}@github.com/${GITHUB_REPOSITORY}.git"
git fetch
git branch

# Move packages somewhere else
repo_path=$(realpath "${repo}")
repo_path=${repo_path}/packages/${package}
mkdir -p /tmp/packages/${package}
cp -R ${repo_path} /tmp/packages/${package}

# Important - needs to be checked out from develop!
git checkout -b "${BRANCH_FROM}" origin/develop
git branch
git config --global user.name "github-actions"
git config --global user.email "github-actions@users.noreply.github.com"
cp /tmp/packages/${repo_path}/* var/spack/repos/builtin/packages/${package}/
rm -rf var/spack/repos/builtin/packages/${package}/VERSION
git add var/spack/repos/builtin/packages/${package}/*
if git diff-index --quiet HEAD --; then
    printf "No changes\n"
else
    printf "Changes\n"
    git commit -m "Automated deployment to update package ${package} $(date '+%Y-%m-%d')"
    git push origin "${BRANCH_FROM}"
    echo "open_pr=1" >> $GITHUB_ENV
fi
echo "PULL_REQUEST_FROM_BRANCH=${BRANCH_FROM}" >> $GITHUB_ENV
echo "BRANCH_FROM=${BRANCH_FROM}" >> $GITHUB_ENV

