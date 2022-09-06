#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#
# Copyright (c) 2022 Huawei Device Co., Ltd.
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

import os
import sys


VERSION = "0.4.6"
# execv execution fragment
EXECV_FRAGMENT = """
import sys
import importlib

sys.path.append(sys.argv.pop())
entry = importlib.import_module("__entry__")
sys.exit(entry.main())
"""


def find_top():
    cur_dir = os.getcwd()
    while cur_dir != "/":
        hb_internal = os.path.join(cur_dir, 'build/lite/hb_internal')
        if os.path.exists(hb_internal):
            return cur_dir
        cur_dir = os.path.dirname(cur_dir)
    raise Exception("Please call hb utilities inside source root directory")


def search(findir, target):
    for root, dirs, files in os.walk(findir):
        if target in files:
            return root


def main():
    try:
        topdir = find_top()
    except Exception as ex:
        return print("hb_error: Please call hb utilities inside source root directory")
    python_base_dir = os.path.join(topdir, 'prebuilts/python')
    if os.path.exists(python_base_dir):
        python_dir = search(python_base_dir, 'python3')
        python_executable = os.path.join(python_dir, 'python3')
        lite_dir = os.path.join(topdir, 'build/lite')
        hb_dir = search(lite_dir, '__entry__.py')
        param_list = ["python3", "-c", EXECV_FRAGMENT]
        for arg in sys.argv[1:]:
            param_list.append(arg)
        param_list.append(hb_dir)
        os.environ['PATH'] = python_dir + ":" + os.getenv('PATH')
        os.execv(python_executable, param_list)
    else:
        print("please execute build/prebuilts_download.sh")


if __name__ == "__main__":
    sys.exit(main())
