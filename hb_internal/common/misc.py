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
import subprocess
from datetime import datetime
from distutils.spawn import find_executable
from hb_internal.common.utils import exec_command
from hb_internal.common.utils import hb_warning


class PreBuild:
    def __init__(self, config):
        self._root_path = config.root_path
        self._out_path = config.out_path
        self._log_path = config.log_path

    def set_ccache(self):
        ccache_local_dir = os.environ.get('CCACHE_LOCAL_DIR')
        ccache_log_suffix = os.environ.get('CCACHE_LOG_SUFFIX')
        if not ccache_local_dir:
            ccache_local_dir = '.ccache'
        ccache_base = os.environ.get('CCACHE_BASE')
        if ccache_base is None:
            ccache_base = os.path.join(self._root_path, ccache_local_dir)
            if not os.path.exists(ccache_base):
                os.makedirs(ccache_base)
        ccache_log_file_name = "ccache.log"
        if ccache_log_suffix:
            ccache_log_file_name = "ccache." + ccache_log_suffix + ".log"

        logfile = os.path.join(self._root_path, ccache_log_file_name)
        if os.path.exists(logfile):
            oldfile_name = ccache_log_file_name + ".old"
            oldfile = os.path.join(self._root_path, oldfile_name)
            if os.path.exists(oldfile):
                os.unlink(oldfile)
            os.rename(logfile, oldfile)

        ccache_path = find_executable('ccache')
        if ccache_path is None:
            hb_warning('Failed to find ccache, ccache disabled.')
            return
        os.environ['CCACHE_EXEC'] = ccache_path
        os.environ['CCACHE_LOGFILE'] = logfile
        os.environ['USE_CCACHE'] = '1'
        os.environ['CCACHE_DIR'] = ccache_base
        os.environ['CCACHE_UMASK'] = '002'
        os.environ['CCACHE_BASEDIR'] = self._root_path
        ccache_max_size = os.environ.get('CCACHE_MAXSIZE')
        if not ccache_max_size:
            ccache_max_size = '100G'

        cmd = ['ccache', '-M', ccache_max_size]
        exec_command(cmd, log_path=self._log_path)

    def set_pycache(self):
        pycache_dir = os.path.join(self._root_path, '.pycache')
        os.environ['PYCACHE_DIR'] = pycache_dir
        pyd_start_cmd = [
            'python3',
            '{}/build/scripts/util/pyd.py'.format(self._root_path),
            '--root',
            pycache_dir,
            '--start',
        ]
        cmd = ['/bin/bash', '-c', ' '.join(pyd_start_cmd), '&']
        subprocess.Popen(cmd)

    def rename_last_logfile(self):
        logfile = os.path.join(self._out_path, 'build.log')
        if os.path.exists(logfile):
            mtime = os.stat(logfile).st_mtime
            os.rename(logfile, '{}/build.{}.log'.format(self._out_path, mtime))

    def prepare(self, args):
        actions = [self.set_ccache, self.rename_last_logfile]
        for action in actions:
            action()


class PostBuild:
    def __init__(self, config):
        self._root_path = config.root_path
        self._out_path = config.out_path
        self._log_path = config.log_path

    def clean(self, start_time, disable_post_build_args):
        if not disable_post_build_args or 'stat_ccache' not in disable_post_build_args:
                self.stat_ccache()
        if not disable_post_build_args or 'generate_ninja_trace' not in disable_post_build_args:
                self.generate_ninja_trace(start_time)
        if not disable_post_build_args or 'get_warning_list' not in disable_post_build_args:
                self.get_warning_list()
        if not disable_post_build_args or 'compute_overlap_rate' not in disable_post_build_args:
                self.compute_overlap_rate()
            
    def package_image(self):
        image_path = os.path.join(self._out_path, 'packages/phone/images/')
        if os.path.exists(image_path):
            packaged_file_path = os.path.join(self._out_path, 'images.tar.gz')
            cmd = ['tar', '-zcvf', packaged_file_path, image_path]
            exec_command(cmd, log_path=self._log_path)
            
    def stat_pycache(self):
        cmd = [
            'python3', '{}/build/scripts/util/pyd.py'.format(self._root_path),
            '--stat'
        ]
        exec_command(cmd, log_path=self._log_path)

    def manage_cache_data(self):
        cmd = [
            'python3', '{}/build/scripts/util/pyd.py'.format(self._root_path),
            '--manage'
        ]
        exec_command(cmd, log_path=self._log_path)

    def stop_pyd(self):
        cmd = [
            'python3', '{}/build/scripts/util/pyd.py'.format(self._root_path),
            '--stop'
        ]
        exec_command(cmd, log_path=self._log_path)

    def stat_ccache(self):
        ccache_path = find_executable('ccache')
        if ccache_path is None:
            return

        ccache_log_file_name = "ccache.log"
        ccache_log_suffix = os.environ.get('CCACHE_LOG_SUFFIX')
        if ccache_log_suffix:
            ccache_log_file_name = "ccache." + ccache_log_suffix + ".log"
        cmd = [
            'python3', '{}/build/scripts/summary_ccache_hitrate.py'.format(
                self._root_path), '{}/{}'.format(self._root_path, ccache_log_file_name)
        ]
        exec_command(cmd, log_path=self._log_path)

    def get_warning_list(self):
        cmd = [
            'python3',
            '{}/build/scripts/get_warnings.py'.format(self._root_path),
            '--build-log-file',
            '{}/build.log'.format(self._out_path),
            '--warning-out-file',
            '{}/packages/WarningList.txt'.format(self._out_path),
        ]
        exec_command(cmd, log_path=self._log_path)

    def generate_ninja_trace(self, start_time):
        def get_unixtime(dt):
            epoch = datetime.utcfromtimestamp(0)
            unixtime = '%f' % ((dt - epoch).total_seconds() * 10**9)
            return str(unixtime)

        cmd = [
            'python3',
            '{}/build/scripts/ninja2trace.py'.format(self._root_path),
            '--ninja-log',
            '{}/.ninja_log'.format(self._out_path),
            "--trace-file",
            "{}/build.trace".format(self._out_path),
            "--ninja-start-time",
            get_unixtime(start_time),
            "--duration-file",
            "{}/sorted_action_duration.txt".format(self._out_path),
        ]
        exec_command(cmd, log_path=self._log_path)

    def compute_overlap_rate(self):
        cmd = [
            'python3',
            '{}/build/ohos/statistics/build_overlap_statistics.py'.format(
                self._root_path), "--build-out-dir", self._out_path,
            "--subsystem-config-file",
            "{}/build/subsystem_config.json".format(self._root_path),
            "--root-source-dir", self._root_path
        ]
        exec_command(cmd, log_path=self._log_path)
