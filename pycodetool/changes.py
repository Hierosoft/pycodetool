#!/usr/bin/env python
import os

try:
    import git
    from git import Repo
except ImportError as ex:
    print("This program requires gitpython. Try:")
    print("python -m pip install --user --upgrade gitpython")
    exit(1)

parent = os.path.realpath(".")

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
        # print("{}: not a git repo".format(sub))
        continue
    # o = self.repo.remotes.origin
    # o.pull()[0]
    # print(repo.untracked_files)
    try:
        changedFiles = [ item.a_path for item in repo.index.diff(None) ]
    except git.exc.GitCommandError as ex:
        print(sub + ":")
        print(str(ex))
        # raise ex
        continue
    if (len(changedFiles) > 0) or (len(repo.untracked_files) > 0):
        print(sub + ":")
        if len(changedFiles) > 0:
            # print("  changed: {}".format(changedFiles))
            print("  len(changed): {}".format(len(changedFiles)))
        if len(repo.untracked_files) > 0:
            # print("  untracked: {}".format(repo.untracked_files))
            print("  len(untracked): {}".format(len(repo.untracked_files)))
