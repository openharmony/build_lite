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

import os
from collections import defaultdict

from hb.common.utils import read_json_file
from hb.common.config import Config
from hb.cts.menuconfig import Menuconfig


class Product():
    @staticmethod
    def get_products():
        config = Config()
        for company in os.listdir(config.vendor_path):
            company_path = os.path.join(config.vendor_path, company)
            if not os.path.isdir(company_path):
                continue

            for product in os.listdir(company_path):
                product_path = os.path.join(company_path, product)
                config_path = os.path.join(product_path, 'config.json')

                if os.path.isfile(config_path):
                    product_name = read_json_file(config_path).\
                                   get('product_name')
                    if product_name is not None:
                        yield company, product_name, product_path

    @staticmethod
    def get_device_info(product_json):
        product_content = read_json_file(product_json)
        return product_content.get('board', None),\
            product_content.get('kernel_type', None),\
            product_content.get('kernel_version', None),\
            product_content.get('device_company', None)

    @staticmethod
    def get_features(product_json):
        if not os.path.isfile(product_json):
            raise Exception('{} not found'.format(product_json))

        features_list = []
        subsystems = read_json_file(product_json).get('subsystems', [])
        for subsystem in subsystems:
            for component in subsystem.get('components', []):
                features = component.get('features', [])
                features_list += [feature for feature in features
                                  if len(feature)]

        return features_list

    @staticmethod
    def get_components(product_json, subsystems):
        if not os.path.isfile(product_json):
            raise Exception('{} not found'.format(product_json))

        components_dict = defaultdict(list)
        product_data = read_json_file(product_json)
        for subsystem in product_data.get('subsystems', []):
            sname = subsystem.get('subsystem', '')
            if not len(subsystems) or sname in subsystems:
                components_dict[sname] += [comp['component'] for comp in
                                           subsystem.get('components', [])]

        return components_dict, product_data.get('board', ''),\
            product_data.get('kernel_type', '')

    @staticmethod
    def get_product_path(product_name, company):
        for cur_company, cur_product, product_path in Product.get_products():
            if cur_company == company and cur_product == product_name:
                return product_path

        raise Exception('product {}@{} not found'.
                        format(product_name, company))

    @staticmethod
    def product_menuconfig():
        product_path_dict = {}
        for company, product, product_path in Product.get_products():
            product_path_dict['{}@{}'.format(product, company)] = product_path

        if not len(product_path_dict):
            raise Exception('no valid product found')

        choices = [{'name': product} for product in product_path_dict.keys()]
        menu = Menuconfig()
        product = menu.list_promt('product',
                                  'Which product do you need?',
                                  choices).get('product')

        return product_path_dict.get(product), product.split('@')[0]
