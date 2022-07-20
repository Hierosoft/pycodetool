#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jul 19 18:29:39 2022

@author: Jake "Poikilos" Gustafson
"""

import unittest
import sys
import os

from pycodetool import (
    echo0,
    echo1,
    echo2,
    set_verbosity,
)

from pycodetool.parsing import (
    quoted_slices,
    explode_unquoted,
)

class TestParsing(unittest.TestCase):
    def test_quoted_slices(self):
        set_verbosity(1)
        subject = '"example\'s param1", \'"param 2"\', param3'
        #                     0                 18
        #                                        19             31
        #                                                        32
        # ^ Note that the backslash is skipped in these indices.
        good_indices = [
            0,
            subject.find('\'"param 2'),
        ]
        good_ends = [
            subject.find(', \'"param 2'),
            subject.find(', param3'),
        ]
        # ^ param3 is NOT part of quoted_slices, and
        #   quoted_slices is NOT the same as explode_strings
        #   (quoted_slices does not look for delimiters).
        good_pairs = []
        for i in range(len(good_indices)):
            good_pairs.append((good_indices[i], good_ends[i]))

        results = quoted_slices(subject)

        self.assertEqual(
            len(results),
            2
        )

        self.assertEqual(
            results,
            good_pairs
        )

        parts = []
        for pair in results:
            parts.append(subject[pair[0]:pair[1]])

        self.assertEqual(
            parts,
            ['"example\'s param1"', '\'"param 2"\'']
        )

    def test_quoted_slices_comment_exclusion(self):
        subject = 'x = "a" + (i + a) + "a" # "a"'
        #          0   4 6             20
        #                                22  26
        #                                      28
        # ^ Note the quotes 26 and 28 should be ignored since commented.
        slices = quoted_slices(subject)
        self.assertEqual(
            len(slices),
            2
        )
        parts = []
        for params in slices:
            parts.append(subject[params[0]:params[1]])
        self.assertEqual(parts, ['"a"', '"a"'])

    def test_explode_strings(self):
        set_verbosity(1)
        subject = '"example\'s param1", \'"param 2"\', param3'
        good_indices = [
            0,
            subject.find(' "param 2'),
            subject.find(' param3'),
        ]
        good_ends = [
            good_indices[1]-1,
            good_indices[2]-1,
            len(subject),
        ]

        echo0("good_indices={}".format(good_indices))

        good_params = ['"example\'s param1"', '\'"param 2"\'', "param3"]

        results = explode_unquoted(subject, ",")

        self.assertEqual(
            results,
            good_params
        )


    def test_explode_strings_and_indices(self):
        set_verbosity(1)
        subject = '"example\'s param1",, \'"param 3"\', param4'
        good_params = ['"example\'s param1"', "", '\'"param 3"\'', "param4"]
        good_indices = [
            0,
            subject.find(",,")+1, # +1 for START of element 1
            subject.find(' \'"param 3'),
            subject.find(' param4'),
        ]
        good_ends = [
            good_indices[1]-1,
            good_indices[2]-1,
            good_indices[3]-1,
            len(subject),
        ]

        echo0("good_indices={}".format(good_indices))

        good_pairs = []
        for i in range(len(good_params)):
            good_pairs.append((good_params[i], good_indices[i], good_ends[i]))

        results = explode_unquoted(subject, ",", get_str_i_pair=True)

        self.assertEqual(
            results,
            good_pairs
        )
