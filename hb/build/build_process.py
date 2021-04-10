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
from collections import defaultdict

from hb.common.utils import exec_command
from hb.common.utils import makedirs
from hb.common.utils import remove_path
from hb.common.utils import hb_info
from hb.common.utils import hb_warning
from hb.common.config import Config
from hb.cts.cts import CTS
from hb.common.device import Device
from hb.common.product import Product
from hb.build.fs_process import Packer


class Build():
    def __init__(self):
        self.config = Config()

        # Get gn args ready
        self._args_list = []
        self._target = None
        self._compiler = None
        self._test = None

    @property
    def target(self):
        return self._target

    @target.setter
    def target(self, component):
        cts = CTS()
        cts.init_from_json()
        for subsystem_cls in cts:
            for cname, component_cls in subsystem_cls:
                if cname == component:
                    if component_cls.adapted_board is None or\
                       self.config.board in component_cls.adapted_board:
                        if component_cls.adapted_kernel is None or\
                           self.config.kernel in component_cls.adapted_kernel:
                            self._target = component_cls.targets
                            self.register_args('ohos_build_target',
                                               self._target)
                            return

        raise Exception('Component {} not found'.format(component))

    @property
    def compiler(self):
        return self._compiler

    @compiler.setter
    def compiler(self, value):
        self._compiler = value
        self.register_args('ohos_build_compiler_specified', self._compiler)
        if self._compiler == 'clang':
            self.register_args('ohos_build_compiler_dir',
                               self.config.clang_path)

    @property
    def test(self):
        return self._test

    @test.setter
    def test(self, test_args):
        cmd_list = ['xts']
        if test_args[0] in cmd_list:
            self._test = test_args[1]
            if len(test_args) > 1:
                self.register_args('ohos_xts_test_args', self._test)
        else:
            raise Exception('Error: wrong input of test')

    def register_args(self, args_name, args_value, quota=True):
        if quota:
            if isinstance(args_value, list):
                self._args_list += ['{}="{}"'.format(args_name,
                                                     "&&".join(args_value))]
            else:
                self._args_list += ['{}="{}"'.format(args_name, args_value)]
        else:
            self._args_list += ['{}={}'.format(args_name, args_value)]
        if args_name == 'ohos_build_target' and len(args_value):
            self.config.fs_attr = None

    def build(self, full_compile, ninja=True, cmd_args=None):
        self.check_in_device()
        cmd_list = self.get_cmd(full_compile, ninja)

        if cmd_args is None:
            cmd_args = defaultdict(list)
        for exec_cmd in cmd_list:
            exec_cmd(cmd_args)

        return 0

    def get_cmd(self, full_compile, ninja):
        if not ninja:
            self.register_args('ohos_full_compile', 'true', quota=False)
            return [self.gn_build]

        build_ninja = os.path.join(self.config.out_path, 'build.ninja')
        packer = Packer()
        if not os.path.isfile(build_ninja):
            self.register_args('ohos_full_compile', 'true', quota=False)
            makedirs(self.config.out_path)
            return [self.gn_build, self.ninja_build, packer.fs_make]
        if full_compile:
            self.register_args('ohos_full_compile', 'true', quota=False)
            remove_path(self.config.out_path)
            makedirs(self.config.out_path)
            return [self.gn_build, self.ninja_build, packer.fs_make]

        self.register_args('ohos_full_compile', 'false', quota=False)
        return [self.ninja_build, packer.fs_make]

    def gn_build(self, cmd_args):
        # Clean out path
        remove_path(self.config.out_path)
        makedirs(self.config.out_path)

        # Gn cmd init and execute
        gn_path = self.config.gn_path
        gn_args = cmd_args.get('gn', [])
        gn_cmd = [gn_path,
                  'gen',
                  self.config.out_path,
                  '--root={}'.format(self.config.root_path),
                  '--dotfile={}/.gn'.format(self.config.build_path),
                  f'--script-executable={sys.executable}',
                  '--args={}'.format(" ".join(self._args_list))] + gn_args
        exec_command(gn_cmd, log_path=self.config.log_path)

    def gn_clean(self, out_path=None):
        # Gn cmd init and execute
        gn_path = self.config.gn_path

        if out_path is not None:
            self.config.out_path = os.path.abspath(out_path)
        else:
            self.config.out_path = os.path.join(self.config.root_path,
                                                'out',
                                                self.config.board,
                                                self.config.product)

        if not os.path.isdir(self.config.out_path):
            hb_warning('{} not found'.format(self.config.out_path))
            return

        gn_cmd = [gn_path,
                  '--root={}'.format(self.config.root_path),
                  '--dotfile={}/.gn'.format(self.config.build_path),
                  'clean',
                  self.config.out_path]
        exec_command(gn_cmd, log_path=self.config.log_path)

    def ninja_build(self, cmd_args):
        ninja_path = self.config.ninja_path

        ninja_args = cmd_args.get('ninja', [])
        ninja_cmd = [ninja_path,
                     '-w',
                     'dupbuild=warn',
                     '-C',
                     self.config.out_path] + ninja_args
        exec_command(ninja_cmd, log_path=self.config.log_path, log_filter=True)

        hb_info('{} build success'.format(
            os.path.basename(self.config.out_path)))

    def check_in_device(self):
        if self._target is None and Device.is_in_device():
            # Compile device board
            device_path, kernel, board = Device.device_menuconfig()
            # xxx: build device, no need to set root manually, so set it speculatively.
            self.config.root_path = os.path.dirname(os.path.dirname(os.path.dirname(os.getcwd())))
            self.config.out_path = os.path.join(self.config.root_path,
                                                'out',
                                                board)
            gn_device_path = os.path.dirname(device_path)
            gn_kernel_path = device_path
            self.register_args('ohos_build_target', [gn_device_path])
            self.register_args('device_path', gn_kernel_path)
            self.register_args('ohos_kernel_type', kernel)
        else:
            # Compile product in "hb set"
            self.register_args('product_path', self.config.product_path)
            self.register_args('device_path', self.config.device_path)
            self.register_args('ohos_kernel_type', self.config.kernel)

            product_json = os.path.join(self.config.product_path,
                                        'config.json')
            self._args_list += Product.get_features(product_json)
            self.config.out_path = os.path.join(self.config.root_path,
                                                'out',
                                                self.config.board,
                                                self.config.product)
