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

from collections import defaultdict

from hb.build.build_process import Build
from hb.set.set import set_product
from hb.common.device import Device


def add_options(parser):
    parser.add_argument('component', help='name of the component', nargs='*',
                        default=[])
    parser.add_argument('-b', '--build_type', help='release or debug version',
                        nargs=1, default=['debug'])
    parser.add_argument('-c', '--compiler', help='specify compiler',
                        nargs=1, default=['clang'])
    parser.add_argument('-t', '--test', help='compile test suit', nargs='*')
    parser.add_argument('--dmverity', help='Enable dmverity',
                        action="store_true")
    parser.add_argument('--tee', help='Enable tee',
                        action="store_true")
    parser.add_argument('-p', '--product', help='build a specified product '
                        'with {product_name}@{company}, eg: camera@huawei',
                        nargs=1, default=[])
    parser.add_argument('-f', '--full',
                        help='full code compilation', action='store_true')
    parser.add_argument('-n', '--ndk', help='compile ndk',
                        action='store_true')
    parser.add_argument('-T', '--target', help='Compile single target',
                        nargs='*', default=[])
    parser.add_argument('-v', '--verbose',
                        help='show all command lines while building',
                        action='store_true')
    parser.add_argument('-shs', '--sign_haps_by_server',
                        help='sign haps by server', action='store_true')


def exec_command(args):
    build = Build()
    cmd_args = defaultdict(list)

    if len(args.component):
        build.target = args.component[0]

    build.register_args('ohos_build_type', args.build_type[0])

    if args.test is not None:
        build.test = args.test

    if args.dmverity:
        build.register_args('enable_ohos_security_dmverity',
                            'true',
                            quota=False)
        build.config.fs_attr.add('dmverity_enable')

    if args.tee:
        build.register_args('tee_enable', 'true', quota=False)
        build.config.fs_attr.add('tee_enable')

    if len(args.product):
        product, company = args.product[0].split('@')
        set_product(product_name=product, company=company)

    build.compiler = Device.get_compiler(build.config.device_path)

    if args.ndk:
        build.register_args('ohos_build_ndk', 'true', quota=False)

    if hasattr(args, 'target') and len(args.target):
        build.register_args('ohos_build_target', args.target)

    if hasattr(args, 'verbose') and args.verbose:
        cmd_args['gn'].append('-v')
        cmd_args['ninja'].append('-v')

    if hasattr(args, 'ninja'):
        return build.build(args.full, ninja=args.ninja)

    if args.sign_haps_by_server:
        build.register_args('ohos_sign_haps_by_server',
                            'true',
                            quota=False)

    return build.build(args.full, cmd_args=cmd_args)
