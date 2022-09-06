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
from hb_internal import CONFIG_JSON
from hb_internal.common.utils import read_json_file
from hb_internal.common.utils import hb_info
from scripts.tools_checker import check_build_requried_packages, check_os_version
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../")))


OPTIONS_FUN_LIST = [  
        {
            "para": "check", 
            "function":"check_dep"
        }
]


def add_options(parser):
    parser.add_argument('--check',
                        help='compile-time environment dependencies',
                        action='store_true')


def check_dep():
    host_info = check_os_version()
    packages_info = check_build_requried_packages(host_info[1], check=False)
    hb_info('necessary_package: {}'.format(','.join(packages_info[0])))      
    hb_info('installed_package: {}'.format(','.join(packages_info[1])))
    hb_info('uninstalled_package: {}'.format(','.join(packages_info[2])))


def check_os_info():
    json_data = read_json_file(CONFIG_JSON)
    root_path = json_data.get('root_path', 'not set')
    board = json_data.get('board', 'not set')
    kernel = json_data.get('kernel', 'not set')
    product = json_data.get('product', 'not set')
    product_path = json_data.get('product_path', 'not set')
    device_path = json_data.get('device_path', 'not set')
    device_company = json_data.get('device_company', 'not set')

    hb_info('root path: {}'.format(root_path))
    hb_info('board: {}'.format(board))
    hb_info('kernel: {}'.format(kernel))
    hb_info('product: {}'.format(product))
    hb_info('product path: {}'.format(product_path))
    hb_info('device path: {}'.format(device_path))
    hb_info('device company: {}'.format(device_company))


def para_to_function(para):
    for options in OPTIONS_FUN_LIST:
        if options["para"] == para:
            eval(options["function"])()


def exec_command(args):
    args_list = [e for e in dir(args) if not e.startswith('_')]
    for para in args_list:
        options_list = []
        options_list.append("args.{}".format(para))
        for _options in options_list:
            if eval(_options):
                para_to_function(para)
                break
        else:
            check_os_info()
