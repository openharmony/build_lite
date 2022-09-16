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

import subprocess
import os
import re
from hb_internal.common.utils import OHOSException, read_json_file
from hb.__main__ import find_top


def add_options(parser):
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--ls",
                        action='store_true',
                        default=False,
                        help='lists all targets matching the given pattern for the given build directory, '
                        'refer to gn ls. '
                        'eg1: hb tool --ls '
                        'eg2: hb tool --ls --all-toolchains')
    group.add_argument('--desc',
                        action='store_true',
                        default=False,
                        help='displays information about a given target or config, refer to gn desc, '
                        'The --tree and --blame options are enabled by default. '
                        'eg1: hb tool --desc init:innergroup '
                        'eg2: hb tool --desc ai_engine:ai --all')
    group.add_argument('--path',
                        action='store_true',
                        default=False,
                        help='finds paths of dependencies between two targets, refer to gn path, '
                        'The --all options are enabled by default. '
                        'eg1: hb tool --path init:innergroup screenlock_mgr:screenlock_utils '
                        'eg2: hb tool --path init:innergroup screenlock_mgr:screenlock_utils --public')
    parser.add_argument('--out-path',
                        nargs=1,
                        help='specify the build directory, '
                        'eg: hb tool --ls --out-path out/rk3568')


class Tool():
    def __init__(self, out_path=None):
        self.cmd_list = []
        self.gn_default = {'ls': [], 'desc': ['--tree', '--blame'], 'path': ['--all']}
        if out_path:
            self.out_path = out_path[0]
        else:
            self.out_path = read_json_file(os.path.join(find_top(), 'ohos_config.json'))['out_path']
        if not os.path.isdir(self.out_path):
            raise OHOSException(f"{self.out_path} doesn't exist.")
        
    def register_target(self, component, module):
        target_name = self.get_target_name(component, module)
        if target_name:
            self.cmd_list.append(target_name)
        else:
            raise OHOSException(f'The input {component}:{module} matches no targets, configs or files.')

    def get_target_name(self, component, module):
        root_path = os.path.join(self.out_path, "build_configs")
        target_info = ""
        module_list = []
        for file in os.listdir(root_path):
            if len(target_info):
                break
            file_path = os.path.join(root_path, file)
            if not os.path.isdir(file_path):
                continue
            for component_name in os.listdir(file_path):
                if os.path.isdir(os.path.join(file_path, component_name)) and component_name == component:
                    target_info = self.read_gn_file(os.path.join(file_path, component_name, "BUILD.gn"))
                    break
        pattern = re.compile(r'(?<=module_list = )\[([^\[\]]*)\]')  
        results = pattern.findall(target_info)
        for each_tuple in results:
            module_list = each_tuple.replace('\n', '').replace(' ', '').replace('\"', '').split(',')
        for target_path in module_list:
            if target_path != '':
                path, target = target_path.split(":")
                if target == module:
                    return target_path
        return 0
            
    def read_gn_file(self, input_file):
        if not os.path.exists(input_file):
            raise OHOSException("file '{}' doesn't exist.".format(input_file))
        data = None
        with open(input_file, 'r') as input_f:
            data = input_f.read()
        return data

    def get_gn_path(self):
        gn_path = ""
        config_data = read_json_file(os.path.join(find_top(), 'build/prebuilts_download_config.json'))
        copy_config_list = config_data[os.uname().sysname.lower()][os.uname().machine.lower()]['copy_config']
        for config in copy_config_list:
            if config['unzip_filename'] == 'gn':
                gn_path = os.path.join(find_top(), config['unzip_dir'], 'gn')
        return gn_path
        

    def exec_gn_cmd(self, gn_cmd):
        gn_path = self.get_gn_path()
        for arg in self.gn_default.get(gn_cmd):
            if arg not in self.cmd_list:
                self.cmd_list.append(arg)
        cmds = [gn_path, gn_cmd, self.out_path]
        cmds.extend(self.cmd_list)
        pipe = subprocess.Popen(
            cmds,
            stdout=subprocess.PIPE,
            shell=False,
            encoding='utf8'
        )
        while pipe.poll() is None:
            out = pipe.stdout.readline()
            if out != "":
                print(out, end="")


def exec_command(args):
    tool = Tool(args[0].out_path)
    gn_args = args[1]
    if args[0].ls:
        tool.cmd_list.extend(gn_args)
        tool.exec_gn_cmd('ls')

    if args[0].desc:
        try:
            component, module = gn_args[0].split(':')
            tool.register_target(component, module)
            gn_args.remove(gn_args[0])
        except Exception:
            raise OHOSException(f'Invalid desc args: {gn_args[0]} ,need <component:module>')
        tool.cmd_list.extend(gn_args)
        tool.exec_gn_cmd('desc')

    if args[0].path:
        try:
            for i in range(2):
                component, module = gn_args[0].split(':')
                tool.register_target(component, module)
                gn_args.remove(gn_args[0])
        except Exception:
            raise OHOSException('Invalid path args: need <component_one:module_one> <component_two:module_two>')
        tool.cmd_list.extend(gn_args)
        tool.exec_gn_cmd('path')
    