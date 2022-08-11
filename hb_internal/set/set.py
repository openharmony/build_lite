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

from hb_internal.common.config import Config
from hb_internal.common.utils import get_input
from hb_internal.common.utils import OHOSException
from hb_internal.common.utils import hb_info
from hb_internal.common.product import Product
from hb_internal.common.device import Device


def add_options(parser):
    parser.add_argument('-root',
                        '--root_path',
                        nargs='?',
                        default=None,
                        help='Set OHOS root path')
    parser.add_argument('-p', '--product', help='Set OHOS board and kernel')


def exec_command(args):
    ret = set_root_path(root_path=args.root_path)
    if ret != 0:
        return ret
    if args.product:
        return set_product(product_name=args.product) == 0
    else:
        return set_product() == 0


def set_root_path(root_path=None):
    config = Config()
    if root_path is None:
        try:
            hb_info(f'hb root path: {config.root_path}')
            return 0
        except OHOSException:
            root_path = get_input('[OHOS INFO] Input code path: ')
    config.root_path = root_path
    return 0


def set_product(product_name=None, company=None):
    if product_name is None and company is None:
        product_info = Product.product_menuconfig()
    elif product_name is None:
        product_info = Product.get_product_info(product_name)
    else:
        product_info = Product.get_product_info(product_name, company)

    config = Config()
    config.product = product_info.get('name')
    config.product_path = product_info.get('product_path')
    config.version = product_info.get('version')
    config.os_level = product_info.get('os_level')
    config.product_json = product_info.get('config')
    config.component_type = product_info.get('component_type')
    if product_info.get('product_config_path'):
        config.product_config_path = product_info.get('product_config_path')
    else:
        config.product_config_path = product_info('product_path')

    device_info = Product.get_device_info(config.product_json)
    config.board = device_info.get('board')
    config.kernel = device_info.get('kernel')
    config.target_cpu = device_info.get('target_cpu')
    config.target_os = device_info.get('target_os')
    kernel_version = device_info.get('kernel_version')
    config.device_company = device_info.get('company')
    board_path = device_info.get('board_path')

    if product_info.get('build_out_path'):
        config.out_path = os.path.join(config.root_path,
                                       product_info.get('build_out_path'))
    else:
        if config.os_level == 'standard':
            config.out_path = os.path.join(config.root_path, 'out',
                                           config.board)
        else:
            config.out_path = os.path.join(config.root_path, 'out',
                                           config.board, config.product)

    if product_info.get('subsystem_config_json'):
        config.subsystem_config_json = product_info.get(
            'subsystem_config_json')
    else:
        config.subsystem_config_json = 'build/subsystem_config.json'

    if config.version == '2.0':
        config.device_path = board_path
    else:
        if config.os_level == "standard":
            config.device_path = board_path
        else:
            config.device_path = Device.get_device_path(
                board_path, config.kernel, kernel_version)

    if device_info.get('board_config_path'):
        config.device_config_path = device_info.get('board_config_path')
    else:
        config.device_config_path = config.device_path

    return 0
