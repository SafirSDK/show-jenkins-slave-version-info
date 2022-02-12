#!/usr/bin/env python
# -*- coding: utf-8 -*-
###############################################################################
#
# Copyright Saab AB, 2016,2022 (http://safirsdkcore.com)
#
# Created by: Lars Hagstrom / lars.hagstrom@consoden.se
#
###############################################################################
#
# This file is part of Safir SDK Core.
#
# Safir SDK Core is free software: you can redistribute it and/or modify
# it under the terms of version 3 of the GNU General Public License as
# published by the Free Software Foundation.
#
# Safir SDK Core is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Safir SDK Core.  If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
"""Script to collate the output from show_versions into a nice table"""
from __future__ import print_function
import sys, re, os

def log(*args, **kwargs):
    print(*args, **kwargs)
    sys.stdout.flush()


def main():
    info = dict()
    for file in os.listdir("."):
        if not os.path.isfile(file):
            continue
        match = re.match(r"(.*)-versions.txt",file)
        if match is None:
            log("Skipping",file)
            continue
        name = match.group(1)
        info[name] = dict()
        with open(file) as f:
            for line in f:
                match = re.match(r"(.*): *(.*)",line)
                info[name][match.group(1)] = match.group(2)
    log (info)

    with open("build_summary.xml","w") as b, open("test_summary.xml","w") as t:
        b.write("<table sorttable=\"yes\"><tr>\n  <td fontattribute='bold' value='Build Slave'/>\n")
        t.write("<table sorttable=\"yes\"><tr>\n  <td fontattribute='bold' value='Test Slave'/>\n")
        try: #get first key in both py2 and 3
            firstkey = next(info.iterkeys())
        except:
            firstkey = next(iter(info.keys()))

        for sw in info[firstkey]:
            b.write("  <td fontattribute='bold' value='" + sw + "'/>\n")
            t.write("  <td fontattribute='bold' value='" + sw + "'/>\n")
        b.write("</tr>\n")
        t.write("</tr>\n")

        for slave in info:
            f = b if slave.find("-build") != -1 else t
            f.write("<tr>\n")
            f.write("  <td fontattribute='bold' value='" + slave + "'/>\n")
            for sw in info[slave]:
                f.write("  <td value='" + info[slave][sw] + "'/>\n")
            f.write("</tr>\n")

        b.write("</table>")
        t.write("</table>")

if __name__ == "__main__":
    sys.exit(main())
