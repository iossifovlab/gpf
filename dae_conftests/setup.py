#!/usr/bin/env python

import codecs
import os

from setuptools import setup


def read(fname):
    file_path = os.path.join(os.path.dirname(__file__), fname)
    return codecs.open(file_path, encoding="utf-8").read()


setup(
    name="dae_conftests",
    version="0.1.0",
    py_modules=["dae_conftests"],
    # scripts=[
    #     "dae_conftests/tools/tests_setup.py",
    # ],
    entry_points={
        "pytest11": [
            "dae_conftests = dae_conftests",
        ],
    },
    classifiers=[
        "Framework :: Pytest",
    ],
)
