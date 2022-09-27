#!/usr/bin/env python
import os
import sys

try:
    import git
    from git import Repo
except ImportError as ex:
    print("changes requires gitpython. Try:")
    print("python -m pip install --user --upgrade gitpython")
    sys.exit(1)


def echo0(*args, **kwargs):  # formerly prerr
    print(*args, file=sys.stderr, **kwargs)


def get_repo_infos(parent):
    repos = []
    folders = []
    for sub in sorted(os.listdir(parent), key=str.casefold):
        if sub.startswith("."):
            continue
        subPath = os.path.join(parent, sub)
        if not os.path.isdir(subPath):
            continue
        repo = None
        try:
            repo = Repo(subPath)
        except git.exc.InvalidGitRepositoryError as ex:
            folders.append(sub)
            continue
        # o = self.repo.remotes.origin
        # o.pull()[0]
        # print(repo.untracked_files)
        try:
            changedFiles = [item.a_path for item in repo.index.diff(None)]
        except git.exc.GitCommandError as ex:
            print(sub + ":")
            print("  "+str(ex))
            # raise
            continue
        if (len(changedFiles) > 0) or (len(repo.untracked_files) > 0):
            print(sub + ":")
            if len(changedFiles) > 0:
                # print("  changed: {}".format(changedFiles))
                print("  len(changed): {}".format(len(changedFiles)))
            if len(repo.untracked_files) > 0:
                # print("  untracked: {}".format(repo.untracked_files))
                print("  len(untracked): {}".format(len(repo.untracked_files)))
        repos.append(repo)
    if len(repos) < 1:
        echo0("There are no git repositories in {}".format(parent))
        return [], folders
    echo0("The following are not git repos: {}".format(folders))
    return repos, folders


def main():
    parent = os.path.realpath(".")
    # realpath: follow symlinks
    # abspath: only remove instances of ".."

    repos, folders = get_repo_infos(parent)
    if len(repos) < 1:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
