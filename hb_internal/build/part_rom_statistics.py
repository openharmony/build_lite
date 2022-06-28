#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
Copyright (c) 2021 Huawei Device Co., Ltd.
Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

"""

import sys
import os
import argparse
import re
import json


file_paths = []
part_names = []
part_modules_path = {}
part_modules_paths = []
standard_part_rom = {}
standard_part_roms = []


def part_size_compare(out_path,part_name,part_size,fp):
    for standard_part in standard_part_roms:
        if standard_part['part_name'] == part_name and standard_part['part_size'] != 'None':
            sta_size = re.findall(r"\d+",standard_part['part_size'])
            rea_size = re.findall(r"\d+",part_size)
            if int(sta_size[0]) > int(rea_size[0]):
                print(("部件名:"+ part_name).ljust(45),("实际大小:"+ part_size).ljust(25),("标准大小:"+ standard_part['part_size']).ljust(25), " rom合规")
                print(("部件名:"+ part_name).ljust(45),("实际大小:"+ part_size).ljust(25),("标准大小:"+ standard_part['part_size']).ljust(25), " rom合规",file=fp)
            elif int(sta_size[0]) == int(rea_size[0]):
                print(("部件名:"+ part_name).ljust(45),("实际大小:"+ part_size).ljust(25),("标准大小:"+ standard_part['part_size']).ljust(25), " rom合规")
                print(("部件名:"+ part_name).ljust(45),("实际大小:"+ part_size).ljust(25),("标准大小:"+ standard_part['part_size']).ljust(25), " rom合规",file=fp)
            elif int(sta_size[0]) < int(rea_size[0]):
                print(("部件名:"+ part_name).ljust(45),("实际大小:"+ part_size).ljust(25),("标准大小:"+ standard_part['part_size']).ljust(25), " rom超标")
                print(("部件名:"+ part_name).ljust(45),("实际大小:"+ part_size).ljust(25),("标准大小:"+ standard_part['part_size']).ljust(25), " rom超标",file=fp)
        else:
            if standard_part['part_name'] == part_name and standard_part['part_size'] == 'None':
                print(("部件名:"+ part_name).ljust(45),("实际大小:"+ part_size).ljust(50),'此部件尚未标准rom'.ljust(25))
                print(("部件名:"+ part_name).ljust(45),("实际大小:"+ part_size).ljust(50),'此部件尚未标准rom'.ljust(25),file=fp)



def collect_part_name(root_path):
    file_path = os.path.join(root_path, "packages/phone/system_install_parts.json")  
    if os.path.isfile(file_path):
        with open(file_path, 'r') as file:
            file_json = json.load(file)
            for part_list in file_json:
                part_name = part_list["part_name"]
                part_names.append(part_name)


def _colletct_modules_json_path(root_path,part_name):
    for file in os.listdir(root_path):
        file_path = os.path.join(root_path, file)
        if file == f'{part_name}_modules.json':
            part_modules_path = {}
            part_modules_path["part_name"] = part_name 
            part_modules_path["part_path"] = file_path
            part_modules_paths.append(part_modules_path)
        if os.path.isdir(file_path):
            _colletct_modules_json_path(file_path,part_name)   


def actual_rom_statistics(out_path,board):
    collect_part_name(out_path)
    module_json_path = os.path.join(out_path,'gen/out',board)
    for part_name in part_names:
        _colletct_modules_json_path(module_json_path,part_name)
    file_path = os.path.join(out_path,'rom_statistics_table.log')
    fp = open(file_path,"a+")
    fp.seek(0)
    fp.truncate()
    for part_name_json_path in part_modules_paths:
        with open(part_name_json_path['part_path'], 'r') as file:
            file_json = json.load(file)
            part_so_size = 0
            for module_info in file_json:
                module_info_path = module_info['module_info_file']    
                with open(os.path.join(out_path, module_info_path), 'r') as file:             
                    file_json = json.load(file)
                    so_file_dir = os.path.join(out_path, file_json["source"])
                    if os.path.isfile(so_file_dir):                                       # 此处只判断有.so文件的rom    在*_module_info.json文件的"source"字段
                        so_file_size = os.path.getsize(so_file_dir)
                        part_so_size += so_file_size
            part_so_size = f'{round(part_so_size/1024)}KB'
            part_size_compare(out_path,part_name_json_path["part_name"], part_so_size,fp)
    fp.seek(0)
    fp.close()


def read_bundle_json_file(file_path):
    with open(file_path, 'r') as file:
        file_json = json.load(file)
        standard_part_rom = {}
        standard_part_rom["part_name"] = file_json["component"]["name"]
        if 'rom' not in file_json["component"].keys() or file_json["component"]["rom"] == '':           
            standard_part_rom["part_size"] = 'None'
        else:
            standard_part_rom["part_size"] = file_json["component"]["rom"]
        standard_part_roms.append(standard_part_rom)


def collect_bundle_json_path(part_root_path):
    for file in os.listdir(part_root_path):
        file_path = os.path.join(part_root_path, file)
        if file == 'bundle.json':
            file_paths.append(file_path)
        if os.path.isdir(file_path):
            collect_bundle_json_path(file_path)


def read_subsystem_config(root_path):
    part_json_paths = []
    part_json_path = os.path.join(root_path,'build/subsystem_config.json')
    if os.path.isfile(part_json_path):
        with open(part_json_path, 'r') as file:
            file_json = json.load(file)
            for part_info_valule in file_json.values():
                for path_k,path_v in part_info_valule.items():
                    if path_k == "path":
                        part_json_paths.append(path_v)
    return part_json_paths
                      

def read_ohos_config(root_path):
    file_path = os.path.join(root_path, "ohos_config.json")
    with open(file_path, 'r') as file:
        file_json = json.load(file)
        out_path = file_json["out_path"]
        board = file_json["board"]
        product = file_json["product"]
    return (out_path,board,product)


def output_part_rom_status(root_path):
    ohos_config = read_ohos_config(root_path)
    part_paths = read_subsystem_config(root_path)
    for part_path in part_paths:
        part_root_path = os.path.join(root_path,part_path)
        if os.path.isdir(part_root_path):
            collect_bundle_json_path(part_root_path)

    for json_file in file_paths:
        read_bundle_json_file(json_file)
    actual_rom_statistics(ohos_config[0],ohos_config[1])

