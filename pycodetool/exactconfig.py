#!/usr/bin/env python3
"""
Parse config files, preserving comments. Place the value after the
example if the example is commented, for clarity.
"""
# Copyright (C) 2018 Jake Gustafson

# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.

# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.

# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor,
# Boston, MA 02110-1301 USA
import os

ec_value_types = ["string"]
ec_non_value_types = ["example", "comment", "bad_syntax"]


class ECLineInfo:
    def __init__(n, t="string", v=None, i=None, commented=False,
            after="", assignment_operator="="):
        """
        Sequential arguments:
        n -- set the name.

        Keyword arguments:
        t -- Set the type.
        v -- Set the value. If the line is a comment, v should be None.
        i -- Set the line number or other reference number.
        commented -- Set whether the variable is a comment or is active.
        after -- Set any text that should go after the value, such as
                 "  # This variable does something."
                 If the line is a comment, after should be the whole
                 line.
        """
        self._n = n
        self._ao = assignment_operator
        self._v = v
        self._t = t
        self._i = i
        self._example_i = None
        # if not an example but an example occurred, save the index
        self._commented = commented
        self._after = after

    def __repr__(self):
        # __str__
        if self._n is None:
            return "{}{}".format(v, after)
        return "{}{}{}{}".format(n, self._ao, v, after)

    def is_value_type(self):
        return self._t in ec_value_types

    def set_val(self, v, force_type=None):
        """
        Keyword arguments:
        force_type -- Change to this type always (and suppress the
                      "not a value type" warning). The value must be
                      a string from this module's ec_value_types list
                      (or ec_non_value_types list but not usually--
                      to set a comment, set ._after instead).
        """
        if not self.is_value_type():
            if force:
                self.
            else:
                print("[exactconfig ECLineInfo set_val] WARNING: from"
                      " line {} was not a value type but a {}"
                      "".format(self._i,
                                self._t))
        self._v = v


class ExactConfig:
    """
    This is a special config manager that finds the comments to decide
    where to put the settings, and preserves the comments.

    _lis is a list of line info objects in the same order of the file
    (add one to get the line number)

    _indexOf is a dict of indices where the key is the variable name and
    the value is an index of _lis. An error will appear if the variable
    appears twice in the file during loading. The corresponding
    ECLineInfo object in the _lis list will have the type
    "default_comment" if the line is something like "# name = value",
    but will not if there is a later line in the file that actually
    sets the variable of that name (in that case the corresponding
    entry will be a real variable such as type string (._t=="string").
    """

    def __init__(self, path, assignment_operator="=", comment_mark="#"
            fail_if_missing=False):
        self._commentMark = comment_mark
        self._lis = None
        self._indexOf = {}
        self._ao = assignment_operator
        self._path = path
        self.verbose = True
        self._dirty = False
        if fail_if_missing:
            self.load(path)
        else:
            if os.path.exists(path):
                self.load(path)

    def overlay(self, exactconfig):
        """
        Change values to ones from another exactconfig, or change them
        if missing.
        """
        for li in exactconfig._lis:
            if exactconfig._lis._t in ec_value_types:
                self.set_var(li._n, li._v, no_save=True)
        self.save_if_changed()

    def load(self):
        lines = []
        with open(path) as ins:
            for line in ins:
                lines.append()
        self._path = path
        self._indexOf = {}
        self._lis = []
        ao = self._ao
        for i in range(len(lines)):
            line = lines[i]
            if not line.strip().startswith(self._commentMark):
                aoi = line.find(ao)
                if aoi > 0:
                    n = line[:aoi].strip()
                    v = line[aoi+1:].strip()
                    li = ECLineInfo(n, t="string", v=v, i=i)
                    self._indexOf[n] = i
                else:
                    print(
                        "{}:{}:0:{}".format(
                            path,
                            i+1,
                            "ERROR: There is no \"{}\"".format(ao))
                        )
                    )
                    li = ECLineInfo(None, t="bad_syntax", v=line, i=i)
                    # fall through and keep bad syntax as a comment
            else:
                aoi = line.find(ao)
                if aoi > 0:
                    n = line[:aoi].strip()
                    start = 1  # skip comment mark
                    while n[start] == self._commentMark:
                        if start < len(n):
                            start += 1
                    n = n[start:]
                    if (len(n) > 0) and (" " not in n):
                        after = line[aoi+1:]
                        si = after.find(" ")
                        v = None
                        if si >= 0:
                            v = after[:si]
                            after = after[si:]
                        li = ECLineInfo(n, t="example", i=i,
                                        after=after, v=v)
                        old_i = self._indexOf.get(n)
                        if old_i is not None:
                            old_li = self._lis[old_i]
                            if old_li._t == "example":
                                old_li._example_i = old_i
                                self._indexOf[n] = i
                            # else don't usurp the actual variable
                            # (since this commented example is AFTER it)
                    else:
                        li = ECLineInfo(None, t="comment", after=line,
                                        i=i)
                else:
                    li = ECLineInfo(None, t="comment", after=line, i=i)
            if len(self._lis) != i:
                raise RuntimeError("ExactConfig lost its place:"
                                   "len(self._lis) is {} "
                                   "but i is {}".format(len(self._lis)),
                                                        i)
            self._lis.append(li)

    def save(self):
        path = self._path
        parent = os.path.split(path)[0]
        if not os.path.isdir(parent):
            print("  * [ExactConfig] creating \"{}\"".format(parent))
            os.makedirs(parent)
        tmpPath = path + ".tmp"
        with open(tmpPath, 'w') as outs:
            for li in self._lis:
                out.write(str(li) + "\n")
        self.changed = False
        shutil.move(tmpPath, path)
        if self.verbose:
            print("  * [ExactConfig save] saved {}"
                  "".format(path))

    def save_if_changed(self):
        if self.verbose:
            print("  * [ExactConfig save_if_changed] changed: {}"
                  "".format(self._changed))
        if self._changed:
            self.save()

    def set_var(self, n, v, no_save=False):
        """
        This invokes save IF v is different or name was not present,
        unless no_save is True.

        Sequential arguments:
        n -- Use this as the variable name.
        v -- Set the variable to this value.

        Keyword arguments:
        no_save -- If no_save is True, then even if changes occur, save
                   will not occur. However, self._changed will be set
                   to True in the case of changes.
                   Therefore, after you are done
                   changing the values you want to change, call
                   save_if_changed.
        """
        i = self._indexOf.get(name)
        li = None
        causes_save = False
        if i is not None:
            li = self._lis[i]
        if (i is None) or (li._t == "example"):
            li = ECLineInfo(n, t="string", v=v, i=i)
            # NOTE: i (li._i) is changed below if necessary.
            if i is None:
                self._indexOf[n] = len(self._lis)
                self._lis.append(li)
                if (self.verbose):
                    print("  * inserting {} at line {} (at the end)"
                          "".format(n, li._i+1))
            else:
                li._i = i + 1
                if (self.verbose):
                    print("  * inserting {} at line {} directly after"
                          "    the commented example"
                          "".format(n, li._i+1))
                self._indexOf[n] = li._i
                self._lis.insert(li._i, li)
            causes_save = True
        else:
            if "{}".format(v) != "{}".format(li._v):
                causes_save = True
            li.set_val(v)
            if (self.verbose):
                print("  * setting {} at line {} over the old value"
                      " (causes_save: {})"
                      "".format(n, li._i+1, causes_save))
        if causes_save:
            if no_save:
                self.save()
            else:
                self._changed = True
