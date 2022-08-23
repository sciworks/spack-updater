#!/bin/basj
printf "GitHub Actor: ${GITHUB_ACTOR}\n"
export BRANCH_FROM="update-package/${package}-$(date '+%Y-%m-%d')"
git remote set-url origin "https://x-access-token:${GITHUB_TOKEN}@github.com/${GITHUB_REPOSITORY}.git"
git branch
git checkout -b "${BRANCH_FROM}" || git checkout "${BRANCH_FROM}"
git branch
git config --global user.name "github-actions"
git config --global user.email "github-actions@users.noreply.github.com"
repo_path=$(realpath "${repo}")
tree ${repo_path}
repo_path=${repo_path}/packages/${package}
git add $repo_path/*
if git diff-index --quiet HEAD --; then
    printf "No changes\n"
else
    printf "Changes\n"
    git commit -m "Automated deployment to update package ${package} $(date '+%Y-%m-%d')"
    git push origin "${BRANCH_FROM}"
    echo "open_pr_to_here=1" >> $GITHUB_ENV
    fi
echo "PULL_REQUEST_FROM_BRANCH=${BRANCH_FROM}" >> $GITHUB_ENV

