#!/usr/bin/env python3

# File: check_linux_metrics.py
# Forked and updated for Python 3 compatibility
# Original project URL: https://github.com/kxr/check_linux_metrics
# Original Author: Khizer Naeem 
# Email: khizernaeem@gmail.com
# Original Release 0.1: 20/05/2015
# Original Release 0.2: 02/06/2015
# Original Release 0.3: 16/07/2015
# 
#
#  Copyright (c) 2015 Khizer Naeem (http://kxr.me)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# Fork Author: Lukáš Hájek aka eastwickcz
# Fork Project URL: https://github.com/eastwickcz/check_linux_metrics
# Fork Purpose: Update the codebase for Python 3 compatibility while preserving original functionality.
# Fork Date: 20.11.2024

import sys
import time
import os
import shutil

INTERIM_DIR = '/var/tmp/linux_metrics'
if not os.path.exists(INTERIM_DIR):
    os.makedirs(INTERIM_DIR)


def check_cpu(warn=None, crit=None):
    status_code = 3
    status_outp = ''
    perfdata = ''

    interim_file = os.path.join(INTERIM_DIR, 'proc_stat')
    if not os.path.isfile(interim_file):
        shutil.copyfile('/proc/stat', interim_file)
        print('This was the first run, run again to get values')
        sys.exit(0)

    sample_period = float(time.time() - os.path.getmtime(interim_file))

    with open(interim_file, 'r') as f1:
        line1 = f1.readline()

    with open('/proc/stat', 'r') as f2:
        line2 = f2.readline()

    deltas = [int(b) - int(a) for a, b in zip(line1.split()[1:], line2.split()[1:])]
    total = sum(deltas)
    percents = [100 - (100 * (float(total - x) / total)) for x in deltas]

    cpu_pcts = {
        'user': percents[0],
        'nice': percents[1],
        'system': percents[2],
        'idle': percents[3],
        'iowait': percents[4],
        'irq': percents[5],
        'softirq': percents[6]
    }
    if len(percents) >= 8:
        cpu_pcts['steal'] = percents[7]
    else:
        cpu_pcts['steal'] = 0

    cpu_pcts['cpu'] = 100 - cpu_pcts['idle']

    status_outp = f"CPU Usage: {cpu_pcts['cpu']:.2f}% [t:{sample_period:.2f}]"

    if warn is not None and crit is not None:
        if float(cpu_pcts['cpu']) >= float(crit):
            status_code = 2
            status_outp += ' (Critical)'
        elif float(cpu_pcts['cpu']) >= float(warn):
            status_code = 1
            status_outp += ' (Warning)'
        else:
            status_code = 0
            status_outp += ' (OK)'
    else:
        status_code = 0

    for x in ['cpu', 'user', 'system', 'iowait', 'nice', 'irq', 'softirq', 'steal']:
        perfdata += f"{x}={cpu_pcts[x]:.2f}%"
        if warn is not None and crit is not None:
            perfdata += f";{warn};{crit}"
        perfdata += ' '

    perfdata = perfdata.strip()

    shutil.copyfile('/proc/stat', interim_file)

    print(f"{status_outp} | {perfdata}")
    sys.exit(status_code)

def check_load(warn=None, crit=None):
    status_code = 3
    status_outp = ''
    perfdata = ''

    with open('/proc/loadavg', 'r') as f:
        line = f.readline()
    load_avgs = [float(x) for x in line.split()[:3]]

    load = {
        'load1': load_avgs[0],
        'load5': load_avgs[1],
        'load15': load_avgs[2]
    }

    status_outp = f"Load1: {load['load1']:.2f} Load5: {load['load5']:.2f} Load15: {load['load15']:.2f}"

    if warn is not None and crit is not None:
        status_code = 0
        for i in range(len(warn)):
            if crit[i] and warn[i]:
                if float(load_avgs[i]) >= float(crit[i]):
                    status_code = 2
                    status_outp += ' (Critical)'
                elif float(load_avgs[i]) >= float(warn[i]):
                    if status_code < 1:
                        status_code = 1
                    status_outp += ' (Warning)'
                else:
                    status_outp += ' (OK)'
    else:
        status_code = 0

    seq = 0
    for x in ['load1', 'load5', 'load15']:
        perfdata += f"{x}={load[x]:.2f}"
        if warn is not None and crit is not None:
            if len(warn) >= seq + 1:
                perfdata += f";{warn[seq]};{crit[seq]}"
        perfdata += ' '
        seq += 1

    perfdata = perfdata.strip()

    print(f"{status_outp} | {perfdata}")
    sys.exit(status_code)

def check_threads(warn=None, crit=None):
    status_code = 3
    status_outp = ''
    perfdata = ''

    with open('/proc/loadavg', 'r') as f:
        line = f.readline()
    t = line.split()[3]
    threads = {
        'running': int(t.split('/')[0]),
        'total': int(t.split('/')[1])
    }

    status_outp = f"Threads: {t}"

    if warn is not None and crit is not None:
        if threads['running'] >= int(crit):
            status_code = 2
            status_outp += ' (Critical)'
        elif threads['running'] >= int(warn):
            status_code = 1
            status_outp += ' (Warning)'
        else:
            status_code = 0
            status_outp += ' (OK)'
    else:
        status_code = 0

    for x in ['running', 'total']:
        perfdata += f"{x}={threads[x]:.2f}"
        if warn is not None and crit is not None and x == 'running':
            perfdata += f";{warn};{crit}"
        perfdata += ' '

    perfdata = perfdata.strip()

    print(f"{status_outp} | {perfdata}")
    sys.exit(status_code)

def check_openfiles(warn=None, crit=None):
    status_code = 3
    status_outp = ''
    perfdata = ''

    with open('/proc/sys/fs/file-nr', 'r') as f:
        line = f.readline()
    fd = [int(x) for x in line.split()]

    ofiles = {
        'open': fd[0],
        'free': fd[1],
        'total': fd[2]
    }

    status_outp = f"Open Files: {ofiles['open']} (free: {ofiles['free']})"

    if warn is not None and crit is not None:
        if float(ofiles['open']) >= float(crit):
            status_code = 2
            status_outp += ' (Critical)'
        elif float(ofiles['open']) >= float(warn):
            status_code = 1
            status_outp += ' (Warning)'
        else:
            status_code = 0
            status_outp += ' (OK)'
    else:
        status_code = 0

    for x in ['open', 'free']:
        perfdata += f"{x}={ofiles[x]:.2f}"
        if warn is not None and crit is not None and x == 'open':
            perfdata += f";{warn};{crit};0;{ofiles['total']}"
        perfdata += ' '

    perfdata = perfdata.strip()

    print(f"{status_outp} | {perfdata}")
    sys.exit(status_code)

def check_procs(warn=None, crit=None):
    status_code = 3
    status_outp = ''
    perfdata = ''

    forks = 0
    interim_file = os.path.join(INTERIM_DIR, 'proc_stat_processes')
    if not os.path.isfile(interim_file):
        shutil.copyfile('/proc/stat', interim_file)
        print('This was the first run, run again to get values')
        sys.exit(0)

    sample_period = float(time.time() - os.path.getmtime(interim_file))

    curr_forks = 0
    for file in ['/proc/stat', interim_file]:
        with open(file, 'r') as f:
            for line in f:
                if line.startswith('processes '):
                    if file == '/proc/stat':
                        curr_forks = int(line.split()[1])
                    elif file == interim_file:
                        forks = curr_forks - int(line.split()[1])

    forks_ps = float(forks / sample_period)
    states_procs = {}
    p_total = 0

    for proc_dir in os.listdir('/proc'):
        if proc_dir.isdigit():
            p_total += 1
            try:
                with open(f'/proc/{proc_dir}/stat', 'r') as f:
                    line = f.readline().split()[1:3]
            except:
                continue
            if line[1] not in states_procs:
                states_procs[line[1]] = []
            states_procs[line[1]].append(line[0])

    p = {
        'total': p_total,
        'forks': forks_ps,
        'running': 0,
        'sleeping': 0,
        'waiting': 0,
        'zombie': 0,
        'others': 0
    }

    for state in states_procs:
        if state == 'R':
            p['running'] += len(states_procs[state])
        elif state == 'S':
            p['sleeping'] += len(states_procs[state])
        elif state == 'D':
            p['waiting'] += len(states_procs[state])
        elif state == 'Z':
            p['zombie'] += len(states_procs[state])
        else:
            p['others'] += len(states_procs[state])

    status_outp += f"Total: {p['total']} Running: {p['running']} Sleeping: {p['sleeping']} Waiting: {p['waiting']} Zombie: {p['zombie']} Others: {p['others']} New_Forks: {p['forks']:.2f}/s"

    if warn is not None and crit is not None:
        status_code = 0
        param = ['total', 'running', 'waiting']
        for i in range(len(warn)):
            if crit[i] != '' and warn[i] != '':
                if float(p[param[i]]) >= float(crit[i]):
                    status_code = 2
                    status_outp += f" (Critical {param[i]})"
                elif float(p[param[i]]) >= float(warn[i]):
                    if status_code < 1:
                        status_code = 1
                    status_outp += f" (Warning {param[i]})"
                else:
                    status_outp += ' (OK)'
    else:
        status_code = 0

    seq = 0
    for x in ['total', 'forks', 'sleeping', 'running', 'waiting', 'zombie', 'others']:
        perfdata += f"{x}={p[x]:.2f}"
        if warn is not None and crit is not None:
            if x in ['total', 'running', 'waiting']:
                if len(warn) >= seq + 1:
                    perfdata += f";{warn[seq]};{crit[seq]}"
                    seq += 1
        perfdata += ' '

    perfdata = perfdata.strip()
    shutil.copyfile('/proc/stat', interim_file)

    print(f"{status_outp} | {perfdata}")
    sys.exit(status_code)

def check_diskio(dev, warn=None, crit=None):
    status_code = 3
    status_outp = ''
    perfdata = ''

    if dev.startswith('/'):
        real_path = os.path.realpath(dev)
        if not real_path.startswith('/dev/'):
            print(f"Plugin Error: Block device not found: {dev}")
            sys.exit(3)
        else:
            device = real_path[5:]
    else:
        device = dev

    with open('/proc/diskstats', 'r') as f2:
        proc_content = f2.read()

    sep = f"{device} "
    found = False
    for line in proc_content.splitlines():
        if sep in line:
            found = True
            proc_line = line.strip().split(sep)[1].split()
            break

    if not found:
        print(f"Plugin Error: Block device not found: ({device})")
        sys.exit(3)

    interim_file = os.path.join(INTERIM_DIR, f'proc_diskstats_{device.replace("/", "_")}')
    if not os.path.isfile(interim_file):
        shutil.copyfile('/proc/diskstats', interim_file)
        print(f"This was the first run, run again to get values: diskio({device})")
        sys.exit(0)

    sample_period = float(time.time() - os.path.getmtime(interim_file))

    with open(interim_file, 'r') as f1:
        interim_content = f1.read()

    for line in interim_content.splitlines():
        if sep in line:
            interim_line = line.strip().split(sep)[1].split()
            break

    d = {
        'read_operations': (int(proc_line[0]) - int(interim_line[0])) / sample_period,
        'read_sectors': (int(proc_line[2]) - int(interim_line[2])) / sample_period,
        'read_time': (int(proc_line[3]) - int(interim_line[3])) / sample_period,
        'write_operations': (int(proc_line[4]) - int(interim_line[4])) / sample_period,
        'write_sectors': (int(proc_line[6]) - int(interim_line[6])) / sample_period,
        'write_time': (int(proc_line[7]) - int(interim_line[7])) / sample_period
    }

    status_outp += f"{dev} ({device}) Read: {d['read_sectors']:.2f} sec/s ({d['read_operations']:.2f} t/s) Write: {d['write_sectors']:.2f} sec/s ({d['write_operations']:.2f} t/s) [t:{sample_period:.2f}]"

    if warn is not None and crit is not None:
        if float(d['read_sectors']) >= float(crit[0]) or float(d['write_sectors']) >= float(crit[1]):
            status_code = 2
            status_outp += ' (Critical)'
        elif float(d['read_sectors']) >= float(warn[0]) or float(d['write_sectors']) >= float(warn[1]):
            status_code = 1
            status_outp += ' (Warning)'
        else:
            status_code = 0
            status_outp += ' (OK)'
    else:
        status_code = 0

    for x in ['read_operations', 'read_sectors', 'read_time', 'write_operations', 'write_sectors', 'write_time']:
        perfdata += f"{x}={d[x]:.2f}"
        if warn is not None and crit is not None:
            if x == 'read_sectors':
                perfdata += f";{warn[0]};{crit[0]}"
            elif x == 'write_sectors':
                perfdata += f";{warn[1]};{crit[1]}"
        perfdata += ' '

    perfdata = perfdata.strip()
    shutil.copyfile('/proc/diskstats', interim_file)

    print(f"{status_outp} | {perfdata}")
    sys.exit(status_code)

def check_disku(mount, warn=None, crit=None):
    status_code = 3
    status_outp = ''
    perfdata = ''

    if os.path.ismount(mount):
        statvfs = os.statvfs(mount)
    else:
        print(f"Plugin Error: Mount point not valid: ({mount})")
        sys.exit(3)

    du = {
        'size': float(statvfs.f_frsize * statvfs.f_blocks / 1024.00 / 1024 / 1024),
        'free': float(statvfs.f_frsize * statvfs.f_bfree / 1024.00 / 1024 / 1024),
        'avail': float(statvfs.f_frsize * statvfs.f_bavail / 1024.00 / 1024 / 1024)
    }
    du['used_pc'] = (du['size'] - du['avail']) / du['size'] * 100

    status_outp += f"{mount} Used: {du['size'] - du['avail']:.2f} GB / {du['size']:.2f} GB ({du['used_pc']:.2f}%)"

    if warn is not None and crit is not None:
        if du['used_pc'] >= float(crit):
            status_code = 2
            status_outp += ' (Critical)'
        elif du['used_pc'] >= float(warn):
            status_code = 1
            status_outp += ' (Warning)'
        else:
            status_code = 0
            status_outp += ' (OK)'
    else:
        status_code = 0

    perfdata += f"used={du['used_pc']:.2f}%"
    if warn is not None and crit is not None:
        perfdata += f";{warn};{crit}"

    print(f"{status_outp} | {perfdata}")
    sys.exit(status_code)

def check_memory(warn=None, crit=None):
    status_code = 3
    status_outp = ''
    perfdata = ''
    mem = {}

    with open('/proc/meminfo', 'r') as f:
        for line in f:
            if line.startswith('MemTotal: '):
                mem['total'] = int(line.split()[1])
            elif line.startswith('Active: '):
                mem['active'] = int(line.split()[1])
            elif line.startswith('MemFree: '):
                mem['free'] = int(line.split()[1])
            elif line.startswith('Cached: '):
                mem['cached'] = int(line.split()[1])
            elif line.startswith('Buffers: '):
                mem['buffers'] = int(line.split()[1])

    m = {
        'total': float(mem['total'] / 1024.00),
        'active': float(mem['active'] / 1024.00),
        'cached': float((mem['cached'] + mem['buffers']) / 1024.00),
        'used': float((mem['total'] - mem['free'] - mem['cached'] - mem['buffers']) / 1024.00),
        'used_p': float((mem['total'] - mem['free'] - mem['cached'] - mem['buffers'])) / mem['total'] * 100.00
    }

    status_outp += f"Memory Used: {m['used']:.2f}MB / {m['total']:.2f}MB ({m['used_p']:.2f}%)"

    if warn is not None and crit is not None:
        if m['used_p'] >= float(crit):
            status_code = 2
            status_outp += ' (Critical)'
        elif m['used_p'] >= float(warn):
            status_code = 1
            status_outp += ' (Warning)'
        else:
            status_code = 0
            status_outp += ' (OK)'
    else:
        status_code = 0

    for x in ['used', 'cached', 'active']:
        perfdata += f"{x}={m[x]:.2f}"
        if x == 'used':
            if warn is not None and crit is not None:
                warn_mb = int(m['total'] * float(warn) / 100)
                crit_mb = int(m['total'] * float(crit) / 100)
                perfdata += f";{warn_mb};{crit_mb}"
            else:
                perfdata += ';;'
            perfdata += f";0;{int(m['total'])}"
        perfdata += ' '

    perfdata = perfdata.strip()

    print(f"{status_outp} | {perfdata}")
    sys.exit(status_code)

def check_swap(warn=None, crit=None):
    status_code = 3
    status_outp = ''
    perfdata = ''
    swap = {}

    with open('/proc/meminfo', 'r') as f:
        for line in f:
            if line.startswith('SwapTotal: '):
                swap['total'] = int(line.split()[1])
            elif line.startswith('SwapFree: '):
                swap['free'] = int(line.split()[1])
            elif line.startswith('SwapCached: '):
                swap['cached'] = int(line.split()[1])

    if swap['total'] == 0:
        status_outp = "No swap space configured on this system"
        status_code = 0
        print(f"{status_outp} | {perfdata}")
        sys.exit(status_code)

    s = {
        'total': float(swap['total'] / 1024.00),
        'cached': float(swap['cached'] / 1024.00),
        'used': float((swap['total'] - swap['free'] - swap['cached']) / 1024.00),
        'used_p': float(swap['total'] - swap['free'] - swap['cached']) / swap['total'] * 100.00
    }

    status_outp += f"Swap Used: {s['used']:.2f}MB / {s['total']:.2f}MB ({s['used_p']:.2f}%)"

    if warn is not None and crit is not None:
        if s['used_p'] >= float(crit):
            status_code = 2
            status_outp += ' (Critical)'
        elif s['used_p'] >= float(warn):
            status_code = 1
            status_outp += ' (Warning)'
        else:
            status_code = 0
            status_outp += ' (OK)'
    else:
        status_code = 0

    for x in ['used', 'cached']:
        perfdata += f"{x}={s[x]:.2f}"
        if x == 'used':
            if warn is not None and crit is not None:
                warn_mb = int(s['total'] * float(warn) / 100)
                crit_mb = int(s['total'] * float(crit) / 100)
                perfdata += f";{warn_mb};{crit_mb}"
            else:
                perfdata += ';;'
            perfdata += f";0;{int(s['total'])}"
        perfdata += ' '

    perfdata = perfdata.strip()

    print(f"{status_outp} | {perfdata}")
    sys.exit(status_code)

def check_net(interface, warn=None, crit=None):
    status_code = 0
    status_outp = ''
    perfdata = ''

    interim_file = os.path.join(INTERIM_DIR, f'proc_net_dev_{interface}')
    if not os.path.isfile(interim_file):
        shutil.copyfile('/proc/net/dev', interim_file)
        print(f"This was the first run, run again to get values: net:{interface}")
        sys.exit(0)

    sample_period = float(time.time() - os.path.getmtime(interim_file))

    int_t = {}
    int_d = {}

    for file in ['/proc/net/dev', interim_file]:
        with open(file, 'r') as f:
            for line in f:
                line = line.strip()
                if line.startswith(f"{interface}:"):
                    seq = 0
                    for x in [
                        'r_bytes', 'r_packets', 'r_errs', 'r_drop', 'r_fifo', 'r_frame', 'r_compressed', 'r_multicast',
                        't_bytes', 't_packets', 't_errs', 't_drop', 't_fifo', 't_colls', 't_carrier', 't_compressed'
                    ]:
                        if file == '/proc/net/dev':
                            int_t[x] = int(line.split(f"{interface}:")[1].split()[seq])
                        elif file == interim_file:
                            interim_value = int(line.split(f"{interface}:")[1].split()[seq])
                            int_d[x] = int_t[x] - interim_value
                        seq += 1
                    break

    if not int_t or not int_d:
        print(f"Plugin Error: Network device not found: ({interface})")
        sys.exit(3)

    int_d['RX_MBps'] = float(int_d['r_bytes'] / 1024.00 / 1024.00 / sample_period)
    int_d['TX_MBps'] = float(int_d['t_bytes'] / 1024.00 / 1024.00 / sample_period)
    int_d['RX_PKps'] = float(int_d['r_packets'] / sample_period)
    int_d['TX_PKps'] = float(int_d['t_packets'] / sample_period)

    status_outp += f"{interface} Rx: {int_d['RX_MBps']:.2f} MB/s ({int_d['RX_PKps']:.2f} p/s)"
    status_outp += f" Tx: {int_d['TX_MBps']:.2f} MB/s ({int_d['TX_PKps']:.2f} p/s)"
    status_outp += f" [t:{sample_period:.2f}]"

    int_d['PK_ERRORS'] = 0
    for x in ['r_errs', 'r_drop', 'r_fifo', 'r_frame', 't_errs', 't_drop', 't_fifo', 't_colls', 't_carrier']:
        if float(int_d[x]) > 0:
            int_d['PK_ERRORS'] += int_d[x]
            status_code = 2
            status_outp += f" (Critical {x}:{int_d[x]})"

    if warn is not None and crit is not None and int_d['PK_ERRORS'] == 0:
        if float(int_d['RX_MBps']) >= float(crit[0]) or float(int_d['TX_MBps']) >= float(crit[1]):
            status_code = 2
            status_outp += ' (Critical BW)'
        elif float(int_d['RX_MBps']) >= float(warn[0]) or float(int_d['TX_MBps']) >= float(warn[1]):
            if status_code < 1:
                status_code = 1
            status_outp += ' (Warning BW)'
        else:
            status_outp += ' (OK)'

    for x in ['RX_MBps', 'RX_PKps', 'TX_MBps', 'TX_PKps', 'PK_ERRORS']:
        perfdata += f"{x}={int_d[x]:.2f}"
        if warn is not None and crit is not None:
            if x == 'RX_MBps':
                perfdata += f";{warn[0]};{crit[0]}"
            elif x == 'TX_MBps':
                perfdata += f";{warn[1]};{crit[1]}"
        perfdata += ' '

    perfdata = perfdata.strip()
    shutil.copyfile('/proc/net/dev', interim_file)

    print(f"{status_outp} | {perfdata}")
    sys.exit(status_code)

if __name__ == '__main__':
    if len(sys.argv) > 1:
        command = sys.argv[1]
        args = sys.argv[2:]

        if command == 'cpu':
            if len(args) == 0:
                check_cpu()
            elif len(args) == 2 and float(args[1]) > float(args[0]):
                check_cpu(warn=args[0], crit=args[1])
            else:
                print(f"Plugin Error: Invalid arguments for {command}: ({sys.argv})")
                sys.exit(3)

        elif command == 'procs':
            if len(args) == 0:
                check_procs()
            elif len(args) == 2:
                warn_arr = args[0].split(',')
                crit_arr = args[1].split(',')
                if len(warn_arr) != len(crit_arr) or any(float(w) > float(c) for w, c in zip(warn_arr, crit_arr)):
                    print(f"Plugin Error: Invalid arguments for {command}: ({sys.argv})")
                    sys.exit(3)
                check_procs(warn=warn_arr, crit=crit_arr)

        elif command == 'load':
            if len(args) == 0:
                check_load()
            elif len(args) == 2:
                warn_arr = args[0].split(',')
                crit_arr = args[1].split(',')
                if len(warn_arr) != len(crit_arr) or any(float(w) > float(c) for w, c in zip(warn_arr, crit_arr)):
                    print(f"Plugin Error: Invalid arguments for {command}: ({sys.argv})")
                    sys.exit(3)
                check_load(warn=warn_arr, crit=crit_arr)

        elif command == 'threads':
            if len(args) == 0:
                check_threads()
            elif len(args) == 2 and float(args[1]) > float(args[0]):
                check_threads(warn=args[0], crit=args[1])
            else:
                print(f"Plugin Error: Invalid arguments for {command}: ({sys.argv})")
                sys.exit(3)

        elif command == 'files':
            if len(args) == 0:
                check_openfiles()
            elif len(args) == 2 and float(args[1]) > float(args[0]):
                check_openfiles(warn=args[0], crit=args[1])
            else:
                print(f"Plugin Error: Invalid arguments for {command}: ({sys.argv})")
                sys.exit(3)

        elif command == 'diskio':
            if len(args) == 1:
                check_diskio(args[0])
            elif len(args) == 3:
                warn_arr = args[1].split(',')
                crit_arr = args[2].split(',')
                if len(warn_arr) != len(crit_arr) or any(float(w) > float(c) for w, c in zip(warn_arr, crit_arr)):
                    print(f"Plugin Error: Invalid arguments for {command}: ({sys.argv})")
                    sys.exit(3)
                check_diskio(args[0], warn=warn_arr, crit=crit_arr)

        elif command == 'disku':
            if len(args) == 1:
                check_disku(args[0])
            elif len(args) == 3 and float(args[2]) > float(args[1]):
                check_disku(args[0], warn=args[1], crit=args[2])
            else:
                print(f"Plugin Error: Invalid arguments for {command}: ({sys.argv})")
                sys.exit(3)

        elif command == 'memory':
            if len(args) == 0:
                check_memory()
            elif len(args) == 2 and float(args[1]) > float(args[0]):
                check_memory(warn=args[0], crit=args[1])
            else:
                print(f"Plugin Error: Invalid arguments for {command}: ({sys.argv})")
                sys.exit(3)

        elif command == 'swap':
            if len(args) == 0:
                check_swap()
            elif len(args) == 2 and float(args[1]) > float(args[0]):
                check_swap(warn=args[0], crit=args[1])
            else:
                print(f"Plugin Error: Invalid arguments for {command}: ({sys.argv})")
                sys.exit(3)

        elif command == 'network':
            if len(args) == 1:
                check_net(args[0])
            elif len(args) == 3:
                warn_arr = args[1].split(',')
                crit_arr = args[2].split(',')
                if len(warn_arr) != len(crit_arr) or any(float(w) > float(c) for w, c in zip(warn_arr, crit_arr)):
                    print(f"Plugin Error: Invalid arguments for {command}: ({sys.argv})")
                    sys.exit(3)
                check_net(args[0], warn=warn_arr, crit=crit_arr)
        else:
            print(f"Plugin Error: Unknown command {command}")
            sys.exit(3)
