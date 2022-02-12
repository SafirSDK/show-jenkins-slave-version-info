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
"""Script to print out versions of some softwares. Used on Jenkins slaves."""
from __future__ import print_function
import sys
import subprocess
import re
import os
import argparse

def log(*args, **kwargs):
    """Flushing log function"""
    print(*args, **kwargs)
    sys.stdout.flush()

def remove(path):
    """Remove a file or directory recursively"""
    if not os.path.exists(path):
        return
    if os.path.isfile(path) or os.path.islink(path):
        os.remove(path)
        return

    for name in os.listdir(path):
        if os.path.isdir(os.path.join(path, name)):
            remove(os.path.join(path, name))
        else:
            os.remove(os.path.join(path, name))
    os.rmdir(path)

def mkdir(newdir):
    """works the way a good mkdir should :)
        - already exists, silently complete
        - regular file in the way, raise an exception
        - parent directory(ies) does not exist, make them as well
    """
    if os.path.isdir(newdir):
        pass
    elif os.path.isfile(newdir):
        raise OSError("a file with the same name as the desired " \
                      "dir, '%s', already exists." % newdir)
    else:
        head, tail = os.path.split(newdir)
        if head and not os.path.isdir(head):
            mkdir(head)
        if tail:
            os.mkdir(newdir)


def python(f):
    f.write("Python: {0}.{1}.{2}\n".format(*sys.version_info))

def cmake(f):
    try:
        output = subprocess.check_output(("cmake","--version")).decode("utf-8")
        f.write("CMake: " + re.search(r"cmake version (.*)",output).group(1).strip() + "\n")
    except:
        f.write("CMake: N/A\n")

def conan(f):
    try:
        output = subprocess.check_output(("conan","--version")).decode("utf-8")
        f.write("Conan: " + re.search(r"Conan version (.*)",output).group(1).strip() + "\n")
    except:
        f.write("Conan: N/A\n")

def ninja(f):
    try:
        output = subprocess.check_output(("ninja","--version")).decode("utf-8").strip()
        f.write("Ninja: " + output + "\n")
    except:
        f.write("Ninja: N/A\n")


def java(f):
    try:
        output = subprocess.check_output(("java","-version"),stderr=subprocess.STDOUT).decode("utf-8")
        f.write("Java: " + re.search(r"(java|openjdk) version \"([0-9\._]*).*\"",output).group(2).strip() + "\n")
    except:
        f.write("Java: N/A\n")



def gcc(f):
    try:
        output = subprocess.check_output(("gcc","-dumpversion"),stderr=subprocess.STDOUT).decode("utf-8")
        f.write("GCC: " + output.strip() + "\n")
    except:
        f.write("GCC: N/A\n")

def mono(f):
    try:
        output = subprocess.check_output(("mono","--version")).decode("utf-8")
        f.write("Mono: " + re.search(r"Mono JIT compiler version ([\.0-9]*)",output).group(1).strip() + "\n")
    except:
        f.write("Mono: N/A\n")

def qt(f):
    try:
        try:
            output = subprocess.check_output(("qmake","-version")).decode("utf-8")
        except:
            output = subprocess.check_output(("qmake-qt5","-version")).decode("utf-8")
        f.write("Qt: " + re.search(r"Using Qt version ([\.0-9]*)",output).group(1).strip() + "\n")
    except:
        f.write("Qt: N/A\n")

def msvc(f):
    olddir = os.getcwd()
    try:
        remove("msvc_test")
        mkdir("msvc_test")
        os.chdir("msvc_test")
        cm = open("CMakeLists.txt","w")
        cm.write("project(foo CXX)\n")
        cm.close()
        output = subprocess.check_output(("cmake",".")).decode("utf-8")
        f.write("MSVC: " + re.search(r"The CXX compiler identification is MSVC ([\.0-9]*)",output).group(1).strip() + "\n")
    except:
        f.write("MSVC: N/A\n")
    os.chdir(olddir)

def boost(f):
    olddir = os.getcwd()
    try:
        remove("boost_test")
        mkdir("boost_test")
        os.chdir("boost_test")
        cm = open("CMakeLists.txt","w")
        cm.write("project(foo CXX)\ncmake_minimum_required(VERSION 3.10)\nfind_package(Boost REQUIRED)\n")
        cm.close()
        output = subprocess.check_output(("cmake",".")).decode("utf-8")
        f.write("Boost: " + re.search(r"Found Boost: .* \(found version \"([\.0-9]*)\"\)",output).group(1).strip() + "\n")
    except:
        f.write("Boost: N/A\n")
    os.chdir(olddir)

def doxygen(f):
    try:
        output = subprocess.check_output(("doxygen","--version"),stderr=subprocess.STDOUT).decode("utf-8")
        f.write("Doxygen: " + output.strip() + "\n")
    except:
        f.write("Doxygen: N/A\n")

def graphviz(f):
    try:
        output = subprocess.check_output(("dot","-V"),stderr=subprocess.STDOUT).decode("utf-8")
        f.write("Graphviz: " + re.search(r"dot - graphviz version ([\.0-9]*)",output).group(1).strip() + "\n")
    except:
        f.write("Graphviz: N/A\n")

def nsis(f):
    try:
        output = subprocess.check_output(("makensis","-version"),stderr=subprocess.STDOUT).decode("utf-8")
        f.write("NSIS: " + output.strip() + "\n")
    except:
        f.write("NSIS: N/A\n")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output",
                        default="version.txt",
                        help="Name of output file")
    arguments = parser.parse_args()
    with open(arguments.output,"w") as f:
        conan(f)
        python(f)
        cmake(f)
        ninja(f)
        java(f)
        gcc(f)
        mono(f)
        doxygen(f)
        graphviz(f)
        qt(f)
        boost(f)
        msvc(f)
        nsis(f)
        #msvcrt
        #msvcrtd

if __name__ == "__main__":
    sys.exit(main())
