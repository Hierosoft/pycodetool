#!/usr/bin/env python3
"""
Parse config files, preserving comments. Place the value after the
example if the example is commented, for clarity.
"""
# Copyright (C) 2020 Jake Gustafson

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
import shutil
import re
import sys
# wsRx = re.compile(r'\s+')
# \s+ means one or more whitespace
from pycodetool import (
    echo0,
    echo1,
    echo2,
)

ec_value_types = ["string"]
ec_non_value_types = ["example", "comment", "bad_syntax", "raw"]


class ECLineInfo:
    def __init__(self, n, parent, t="string", v=None, i=None,
                 commented=False, before_ao="", after_ao="", after="",
                 cm=None, path=None, orphan=False):
        """
        Sequential arguments:
        n -- set the name.
        parent -- Set the parent (an ExactConfig instance). This is
                  necessary for string conversion (.__repr__) to know
                  what assignment operator (parent._ao) and
                  comment mark (parent._cm) to use.

        Keyword arguments:
        t -- Set the type.
             - "raw": Converting to string will only give ._v
             - "comment": Converting to string will only give .after
               (n must be None or a RuntimeError will occur).
             - "example": You can provide a name and a value, but

        v -- Set the value. If the line is a comment, v should be None.
        i -- Set the line number or other reference number.
        commented -- Set whether the variable is a comment or is active.
        before_ao -- Set any text (generally whitespace) that should go
            before the assignment operator.
        after_ao -- Set any text (generally whitespace) that should go
            after the assignment operator.
        after -- Set any text that should go after the value, such as
            "  # This variable does something."
            If the line is a comment, "after" should be the whole
            line.
        cm -- A comment mark (and in the case of an example
            type of comment (._t=="example"), the comment mark
            must be followed by any whitespace that should be
            preserved).
        path -- set the path of the file from which the line originated.
        orphan -- You must set this to True if parent is None, but
            only do so if using ECLineInfo outside of ExactConfig.
        """

        if orphan is not True:
            # Assert that the parent type is correct via duck typing:
            parent_ao = parent._ao
            parent_cm = parent._cm

        self._parent = parent
        self._n = n
        self._v = v
        self._t = t
        self._i = i
        self._before_ao = before_ao
        self._after_ao = after_ao
        self._cm = cm
        self._example_i = None
        # if not an example but an example occurred, save the index
        self._commented = commented
        self._after = after
        self._path = path

    def dump(self):
        return "[{}]:{}{}{}{}{}{}".format(self._i, self._n,
                                          self._before_ao,
                                          self._parent._ao,
                                          self._after_ao,
                                          self._v,
                                          self._after)

    def __repr__(self):
        # __str__
        if self._n is None:
            if self._t == "raw":
                if self._v is None:
                    raise RuntimeError("A raw line must have a value"
                                       " even if it is \"\", but"
                                       " self._v is None.")
                return self._v
            elif self._t == "comment":
                cm = self._parent._cm
                if self._cm is not None:
                    cm = self._cm
                if not self._after.lstrip().startswith(cm):
                    raise RuntimeError("The comment (.after) did not"
                                       " start with the comment mark"
                                       " \"{}\" Dump: "
                                       "".format(cm, self.dump()))
                return "{}".format(self._after)
            else:
                raise RuntimeError("Only ECLineInfo type comment or"
                                   " blank can have _n (a name) that is"
                                   " None. Dump: {}"
                                   "".format(self.dump()))

        if not self.is_value_type():
            if self._t == "comment":
                raise RuntimeError("A comment had a value"
                                   " (should have returned sooner"
                                   " since _n should be None).")
            elif self._t == "raw":
                return self._v
            else:
                cm = self._parent._cm
                if self._cm is not None:
                    cm = self._cm
                return "{}{}{}{}{}{}{}".format(
                    cm,
                    self._n,
                    self._before_ao,
                    self._parent._ao,
                    self._after_ao,
                    self._parent.serialize(self._v),
                    self._after
                )
        return "{}{}{}{}{}{}".format(self._n, self._before_ao,
                                     self._parent._ao, self._after_ao,
                                     self._parent.serialize(self._v),
                                     self._after)

    def is_value_type(self):
        return self._t in ec_value_types

    def set_val(self, v, force_type=None):
        """
        Keyword arguments:
        force_type -- Change to this type always (and suppress the
            "not a value type" warning). The value must be a string
            from this module's ec_value_types list (or
            ec_non_value_types list but not usually-- to set a comment,
            set ._after instead). Generally don't use this unless you
            want to place the default value after it as a comment.
        """
        if not self.is_value_type():
            if force_type is not None:
                self._t = force_type
            else:
                print("    [exactconfig ECLineInfo set_val] WARNING:"
                      " line {} is not a value type but a {}: {}"
                      "".format(self._i, self._t, self))
        self._v = v


class ExactConfig:
    """
    This is a special config manager that finds the comments to decide
    where to put the settings, and preserves the comments.

    Properties:
    _lis -- a list of line info objects (ECLineInfo objects) in the same
        order of the file (add one to the index to get the line number)
    _indexOf -- a dict of indices where the key is the variable name and
        the value is an index of _lis. An error will appear if the
        variable appears twice in the file during loading. The
        corresponding ECLineInfo object in the _lis list will have the
        type "default_comment" if the line is something like "# name =
        value", but will not if there is a later line in the file that
        actually sets the variable of that name (in that case the
        corresponding entry will be a real variable such as type string
        (._t=="string").
    """

    def __init__(self, path, assignment_operator="=", comment_mark="#",
                 fail_if_missing=False, serializeNoneAs=""):
        self._null = serializeNoneAs
        self._cm = comment_mark
        self._lis = None
        self._indexOf = {}
        self._ao = assignment_operator
        self._path = path
        self.verbose = True
        self._changed = False
        if fail_if_missing:
            self.load(path)
        else:
            if os.path.exists(path):
                self.load(path)

    def serialize(self, value):
        if value is None:
            return self._null
        else:
            return str(value)

    def overlay(self, exactconfig):
        """
        Change values to ones from another exactconfig, or change them
        if missing.
        """
        echo0("* overlaying \"{}\" onto \"{}\""
              "".format(exactconfig._path, self._path))
        for li in exactconfig._lis:
            if li._t in ec_value_types:
                self.set_var(li._n, li._v, no_save=True)
        self.save_if_changed()

    def load(self, path):
        lines = []
        if self.verbose:
            print("* [ExactConfig load] loading \"{}\""
                  "".format(path))
        with open(path) as ins:
            for line in ins:
                lines.append(line.rstrip())
        self._path = path
        self._indexOf = {}
        self._lis = []
        ao = self._ao
        for i in range(len(lines)):
            line = lines[i]
            if len(line.strip()) == 0:
                li = ECLineInfo(None, self, t="raw", v="", i=i)
            elif not line.strip().startswith(self._cm):
                aoi = line.find(ao)
                if aoi > 0:
                    n = line[:aoi].strip()
                    v = line[aoi+1:].strip()
                    li = ECLineInfo(n, self, t="string", v=v, i=i)
                    self._indexOf[n] = i
                else:
                    print(
                        "{}:{}:0:{}".format(
                            path,
                            i+1,
                            "ERROR: There is no \"{}\"".format(ao)
                        )
                    )
                    li = ECLineInfo(None, self, t="bad_syntax", v=line,
                                    i=i)
                    # fall through and keep bad syntax as a comment
            else:
                aoi = line.find(ao)
                if aoi > 0:
                    n = line[:aoi]  # don't strip: preserve spaces below
                    start = 1  # skip comment mark
                    while n[start] == self._cm:
                        if start < len(n):
                            start += 1
                    while n[start].isspace():
                        start += 1
                    cm = n[:start]
                    if cm == self._cm:
                        cm = None
                    n = n[start:]
                    before_ao = ""
                    end = len(n)
                    while (end > 0) and (n[end-1].isspace()):
                        end -= 1
                    if end != len(n):
                        # print("  *** using \"{}\" to {}"
                        #       "".format(n, end))
                        before_ao = n[end:]
                        n = n[:end]
                    else:
                        pass
                        # print("  *** the entire name is good.")
                    # print("  *** line {} name: \"{}\"".format(i+1, n))
                    match = re.search(r'\s+', n)
                    # \s+ means one or more whitespace
                    # if it matched, the span (start,end tuple) would
                    # be am.span(0)
                    if (len(n) > 0) and (match is None):
                        after = line[aoi+1:]
                        si = after.find(" ")
                        v = None
                        if si >= 0:
                            v = after[:si]
                            after = after[si:]
                        li = ECLineInfo(n, self, t="example", i=i,
                                        after=after,
                                        before_ao=before_ao, v=v,
                                        cm=cm)
                        old_i = self._indexOf.get(n)
                        self._indexOf[n] = i
                        if old_i is not None:
                            if old_i >= len(self._lis):
                                raise RuntimeError(
                                    ("old_i {} is >= "
                                     " len(self._lis) {}"
                                     "".format(old_i, len(self._lis)))
                                )
                            old_li = self._lis[old_i]
                            if old_li._t == "example":
                                old_li._example_i = old_i
                                self._indexOf[n] = i
                            # else don't usurp the actual variable
                            # (since this commented example is AFTER it)
                    else:
                        li = ECLineInfo(None, self, t="comment",
                                        before_ao=before_ao,
                                        after=line, i=i,
                                        cm="")
                    print("  *** line {} is a(n) {}: {}"
                          "".format(li._i+1, li._t, li))
                else:
                    li = ECLineInfo(None, self, t="comment", after=line,
                                    i=i)
            self._lis.append(li)
            last_i = self._lis[-1]._i
            if last_i != i:
                raise RuntimeError("ExactConfig lost its place:"
                                   "self._lis[-1]._i is {} "
                                   "but i is {}".format(last_i, i))

    def save(self):
        path = self._path
        parent = os.path.split(path)[0]
        if not os.path.isdir(parent):
            print("  * [ExactConfig] creating \"{}\"".format(parent))
            os.makedirs(parent)
        tmpPath = path + ".tmp"
        with open(tmpPath, 'w') as outs:
            for li in self._lis:
                outs.write(str(li) + "\n")
        self._changed = False
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
        i = self._indexOf.get(n)
        li = None
        causes_save = False
        if i is not None:
            li = self._lis[i]
        if (i is None) or (li._t == "example"):
            li = ECLineInfo(n, self, t="string", v=v, i=i)
            # NOTE: i (li._i) is changed below if None or moves.
            if i is None:
                li._i = len(self._lis)
                self._indexOf[n] = li._i
                self._lis.append(li)
                if self._lis[-1]._i != li._i:
                    raise RuntimeError("The last line was {} not {}"
                                       "".format(self._lis[-1]._i,
                                                 li._i))
                if (self.verbose):
                    print("  * inserting {} at line {} (at the end)"
                          "".format(n, li._i+1))
            else:
                li._i = i + 1
                if (self.verbose):
                    print("  * inserting {} at line {}"
                          " directly after the commented example"
                          "".format(n, li._i+1))
                self._indexOf[n] = li._i
                self._lis.insert(li._i, li)
                for change_i in range(li._i + 1, len(self._lis)):
                    self._lis[change_i]._i = change_i
                for k, v in self._indexOf.items():
                    if v >= li._i + 1:
                        self._indexOf[k] += 1
            causes_save = True
        elif li._t == "comment":
            raise RuntimeError("The index is wrong. _i {} is a comment"
                               "not a {} at {}: {}"
                               "".format(li._i, type(v), i, li))
        else:
            if (self.verbose):
                print("  * setting {} at line {} over the old {}"
                      " (causes_save: {})"
                      "".format(n, li._i+1, li._t, causes_save))
            if li._i != i:
                raise RuntimeError("The index is wrong. _i is {} not {}"
                                   "".format(li._i, i))
            if "{}".format(v) != "{}".format(li._v):
                causes_save = True
            li.set_val(v)
        if causes_save:
            if no_save:
                self._changed = True
            else:
                self.save()
