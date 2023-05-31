#!/usr/bin/env python3

# Script to test CPU load imposed by a simple disk read operation
# refactored in Python3
# Copyright (c) 2016 Canonical Ltd.
#
# Authors
#   Rod Smith <rod.smith@canonical.com>
#   Lucian Perniciaro <perniciaro.lucian@gmail.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 3,
# as published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# The purpose of this script is to run disk stress tests using the
# stress-ng program.
#
# Usage:
#   disk_cpu_load.py [ --max-load <load> ] [ --xfer <mebibytes> ]
#                    [ --verbose ] [ <device-filename> ]
#
# Parameters:
#  --max-load <load> -- The maximum acceptable CPU load, as a percentage.
#                       Defaults to 30.
#  --xfer <mebibytes> -- The amount of data to read from the disk, in
#                        mebibytes. Defaults to 4096 (4 GiB).
#  --verbose -- If present, produce more verbose output
#  <device-filename> -- This is the WHOLE-DISK device filename (with or
#                       without "/dev/"), e.g. "sda" or "/dev/sda". The
#                       script finds a filesystem on that device, mounts
#                       it if necessary, and runs the tests on that mounted
#                       filesystem. Defaults to /dev/sda.

import sys
import subprocess
import re
import os


def get_params(args):
    disk_device = "/dev/sda"
    verbose = False
    max_load = 30
    xfer = 4096

    while args:
        arg = args.pop(0)

        if arg == "--max-load":
            max_load = int(args.pop(0))
        elif arg == "--xfer":
            xfer = int(args.pop(0))
        elif arg == "--verbose":
            verbose = True
        else:
            disk_device = "/dev/" + arg
            disk_device = re.sub(r'/dev//dev', '/dev', disk_device)

            if not os.path.exists(disk_device):
                print(f"Unknown block device \"{disk_device}\"")
                print(
                    "Usage: <script_name> [ --max-load <load> ] [ --xfer <mebibytes> ] [ device-file ]")
                sys.exit(1)

    return disk_device, verbose, max_load, xfer


def sum_array(array):
    total = 0
    for i in array:
        total += int(i)
    return total


def compute_cpu_load(start_use, end_use, verbose):
    start_total = sum_array(start_use)
    end_total = sum_array(end_use)
    diff_idle = int(end_use[3]) - int(start_use[3])
    diff_total = end_total - start_total
    diff_used = diff_total - diff_idle

    if verbose:
        print(f"Start CPU time = {start_total}")
        print(f"End CPU time = {end_total}")
        print(f"CPU time used = {diff_used}")
        print(f"Total elapsed time = {diff_total}")

    if diff_total != 0:
        # keep as int as original bash script
        cpu_load = int((diff_used * 100) / diff_total)
    else:
        cpu_load = 0

    return cpu_load


def main():
    disk_device, verbose, max_load, xfer = get_params(sys.argv[1:])
    retval = 0
    print(f"Testing CPU load when reading {xfer} MiB from {disk_device}")
    print(f"Maximum acceptable CPU load is {max_load}")
    subprocess.run(["blockdev", "--flushbufs", disk_device])
    start_load = subprocess.check_output(
        ["grep", "cpu ", "/proc/stat"]).decode().strip().split()[1:]
    if verbose:
        print("Beginning disk read....")
    subprocess.run(["dd",
                    "if=" + disk_device,
                    "of=/dev/null",
                    "bs=1048576",
                    "count=" + str(xfer)],
                   stdout=subprocess.DEVNULL,
                   stderr=subprocess.DEVNULL)
    if verbose:
        print("Disk read complete!")
    end_load = subprocess.check_output(
        ["grep", "cpu ", "/proc/stat"]).decode().strip().split()[1:]
    cpu_load = compute_cpu_load(start_load, end_load, verbose)
    print(f"Detected disk read CPU load is {cpu_load}")
    if cpu_load > max_load:
        retval = 1
        print("*** DISK CPU LOAD TEST HAS FAILED! ***")
    sys.exit(retval)


if __name__ == "__main__":
    main()
