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
import re
import subprocess
import shutil
import sys
import json
from collections import namedtuple
import yaml


def encode(data, encoding='utf-8'):
    if sys.version_info.major == 2:
        return data.encode(encoding)
    return data


def decode(data, encoding='utf-8'):
    if sys.version_info.major == 2:
        return data.decode(encoding)
    return data


def remove_path(path):
    if os.path.exists(path):
        shutil.rmtree(path)


# Read json file data
def read_json_file(input_file):
    if not os.path.isfile(input_file):
        raise OSError('{} not found'.format(input_file))

    with open(input_file, 'rb') as input_f:
        try:
            data = json.load(input_f)
            return data
        except json.JSONDecodeError:
            raise Exception('{} parsing error!'.format(input_file))


def dump_json_file(dump_file, json_data):
    with open(dump_file, 'wt', encoding='utf-8') as json_file:
        json.dump(json_data,
                  json_file,
                  ensure_ascii=False,
                  indent=2)


def read_yaml_file(input_file):
    if not os.path.isfile(input_file):
        raise OSError('{} not found'.format(input_file))

    with open(input_file, 'rt', encoding='utf-8') as yaml_file:
        try:
            return yaml.safe_load(yaml_file)
        except yaml.YAMLError as exc:
            if hasattr(exc, 'problem_mark'):
                mark = exc.problem_mark
                raise Exception(f'{input_file} load failed, error position:'
                                f' {mark.line + 1}:{mark.column + 1}')


def get_input(msg):
    try:
        user_input = input
    except NameError:
        raise Exception('python2.x not supported')
    return user_input(msg)


def exec_command(cmd, log_path='out/build.log', **kwargs):
    useful_info_pattern = re.compile(r'\[\d+/\d+\].+')
    is_log_filter = kwargs.pop('log_filter', False)

    with open(log_path, 'at', encoding='utf-8') as log_file:
        process = subprocess.Popen(cmd,
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE,
                                   encoding='utf-8',
                                   **kwargs)
        for line in iter(process.stdout.readline, ''):
            if is_log_filter:
                info = re.findall(useful_info_pattern, line)
                if len(info):
                    hb_info(info[0])
            else:
                hb_info(line)
            log_file.write(line)

    process.wait()
    ret_code = process.returncode

    if ret_code != 0:
        with open(log_path, 'at', encoding='utf-8') as log_file:
            for line in iter(process.stderr.readline, ''):
                if 'ninja: warning' in line:
                    log_file.write(line)
                    continue
                hb_error(line)
                log_file.write(line)

        if is_log_filter:
            get_failed_log(log_path)

        hb_error('you can check build log in {}'.format(log_path))
        if isinstance(cmd, list):
            cmd = ' '.join(cmd)
        raise Exception("{} failed, return code is {}".format(cmd, ret_code))


def get_failed_log(log_path):
    with open(log_path, 'rt', encoding='utf-8') as log_file:
        data = log_file.read()
    failed_pattern = re.compile(r'(\[\d+/\d+\].*?)(?=\[\d+/\d+\]|'
                                'ninja: build stopped)', re.DOTALL)
    failed_log = failed_pattern.findall(data)
    for log in failed_log:
        if 'FAILED:' in log:
            hb_error(log)

    error_log = os.path.join(os.path.dirname(log_path), 'error.log')
    if os.path.isfile(error_log):
        with open(error_log, 'rt', encoding='utf-8') as log_file:
            hb_error(log_file.read())


def check_output(cmd, **kwargs):
    try:
        ret = subprocess.check_output(cmd,
                                      stderr=subprocess.STDOUT,
                                      universal_newlines=True,
                                      **kwargs)
    except subprocess.CalledProcessError as called_exception:
        ret = called_exception.output
        if isinstance(cmd, list):
            cmd = ' '.join(cmd)
        raise Exception("{} failed, failed log is {}".format(cmd, ret))

    return ret


def makedirs(path, exist_ok=True, with_rm=False):
    try:
        os.makedirs(path)
    except OSError:
        if not os.path.isdir(path):
            raise Exception("{} makedirs failed".format(path))
        if with_rm:
            remove_path(path)
            return os.makedirs(path)
        if not exist_ok:
            raise Exception("{} exists, makedirs failed".format(path))


def get_project_path(json_path):
    json_data = read_json_file(json_path)

    return json_data.get('root_path')


def args_factory(args_dict):
    if not len(args_dict):
        raise Exception('at least one k_v param is required in args_factory')

    args_cls = namedtuple('Args', [key for key in args_dict.keys()])
    args = args_cls(**args_dict)
    return args


def hb_info(msg):
    level = 'info'
    for line in str(msg).splitlines():
        sys.stdout.write(message(level, line))
        sys.stdout.flush()


def hb_warning(msg):
    level = 'warning'
    for line in str(msg).splitlines():
        sys.stderr.write(message(level, line))
        sys.stderr.flush()


def hb_error(msg):
    level = 'error'
    for line in str(msg).splitlines():
        sys.stderr.write(message(level, line))
        sys.stderr.flush()


def message(level, msg):
    if isinstance(msg, str) and not msg.endswith('\n'):
        msg += '\n'
    return '[OHOS {}] {}'.format(level.upper(), msg)


class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args,
                                                                 **kwargs)
        return cls._instances[cls]
