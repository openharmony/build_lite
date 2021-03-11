#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2020 Huawei Device Co., Ltd.
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
import subprocess
import argparse
import shlex
from tempfile import NamedTemporaryFile
from shutil import copyfile


def cmd_exec(command, temp_file, error_log_path):
    cmd = shlex.split(command)

    proc = subprocess.Popen(cmd,
                            stdout=temp_file,
                            stderr=temp_file,
                            universal_newlines=True)

    proc.wait()
    ret_code = proc.returncode
    if ret_code != 0:
        copyfile(temp_file.name, error_log_path)
        return ret_code

    return ret_code


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--path', help='Build path.')
    parser.add_argument('--prebuilts', help='Build prebuilts.')
    parser.add_argument('--command', help='Build command.')
    parser.add_argument('--enable', help='enable python.', nargs='*')
    parser.add_argument('--target_dir', nargs=1)
    parser.add_argument('--out_dir', nargs=1)
    args = parser.parse_args()

    if args.enable:
        if args.enable[0] == 'false':
            return

    if args.path:
        curr_dir = os.getcwd()
        os.chdir(args.path)
        with NamedTemporaryFile(mode='wt') as temp_file:
            if args.prebuilts:
                status = cmd_exec(args.prebuilts, temp_file, args.out_dir[0])
                if status != 0:
                    return status
            if args.command:
                if '&&' in args.command:
                    command = args.command.split('&&')
                    for data in command:
                        status = cmd_exec(data, temp_file, args.out_dir[0])
                        if status != 0:
                            return status
                else:
                    status = cmd_exec(args.command, temp_file, args.out_dir[0])
                    if status != 0:
                        return status
            copyfile(temp_file.name, args.target_dir[0])

        os.chdir(curr_dir)
    return 0


if __name__ == '__main__':
    sys.exit(main())
