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
import platform
import itertools
from os.path import join, isfile, isdir

if platform.system() == 'Windows':
    try:
        import winreg
    except:
        import _winreg as winreg
    from os import environ
else:
    # Mock winreg and environ so the module can be imported on this platform.
    class winreg:
        HKEY_USERS = None
        HKEY_CURRENT_USER = None
        HKEY_LOCAL_MACHINE = None
        HKEY_CLASSES_ROOT = None

    environ = {}

def log(*args, **kwargs):
    """Flushing log function"""
    print(*args, **kwargs)
    sys.stdout.flush()

def die(message):
    """Just raise an exception with a message"""
    log(message)
    sys.exit(1)

def remove(path):
    """Remove a file or directory recursively"""
    if not os.path.exists(path):
        return
    if isfile(path) or os.path.islink(path):
        os.remove(path)
        return

    for name in os.listdir(path):
        if isdir(join(path, name)):
            remove(join(path, name))
        else:
            os.remove(join(path, name))
    os.rmdir(path)

def mkdir(newdir):
    """works the way a good mkdir should :)
        - already exists, silently complete
        - regular file in the way, raise an exception
        - parent directory(ies) does not exist, make them as well
    """
    if isdir(newdir):
        pass
    elif isfile(newdir):
        raise OSError("a file with the same name as the desired " \
                      "dir, '%s', already exists." % newdir)
    else:
        head, tail = os.path.split(newdir)
        if head and not isdir(head):
            mkdir(head)
        if tail:
            os.mkdir(newdir)

def msvc14_find_vc2015():
    try:
        key = winreg.OpenKey(
            winreg.HKEY_LOCAL_MACHINE,
            r"Software\Microsoft\VisualStudio\SxS\VC7",
            0,
            winreg.KEY_READ | winreg.KEY_WOW64_32KEY
        )
    except OSError:
        return None

    best_version = 0
    best_dir = None
    with key:
        for i in itertools.count():
            try:
                v, vc_dir, vt = winreg.EnumValue(key, i)
            except OSError:
                break
            if v and vt == winreg.REG_SZ and isdir(vc_dir):
                try:
                    version = int(float(v))
                except (ValueError, TypeError):
                    continue
                if version >= 14 and version > best_version:
                    best_version, best_dir = version, vc_dir
    return best_dir

def msvc14_find_vc2017():
    root = environ.get("ProgramFiles(x86)") or environ.get("ProgramFiles")
    if not root:
        return None

    try:
        path = subprocess.check_output([
            join(root, "Microsoft Visual Studio", "Installer", "vswhere.exe"),
            "-latest",
            "-prerelease",
            "-requiresAny",
            "-requires", "Microsoft.VisualStudio.Component.VC.Tools.x86.x64",
            "-requires", "Microsoft.VisualStudio.Workload.WDExpress",
            "-property", "installationPath",
            "-products", "*",
        ]).decode(encoding="mbcs", errors="strict").strip()
    except (subprocess.CalledProcessError, OSError, UnicodeDecodeError):
        return None

    path = join(path, "VC", "Auxiliary", "Build")
    if isdir(path):
        return path

    return None

def find_vcvarsall():
    best_dir = msvc14_find_vc2017()
    version = "new"
    log("__msvc14_find_vc2017() result: " + str(best_dir))
    if not best_dir:
        best_dir = msvc14_find_vc2015()
        version = "old"
        log("__msvc14_find_vc2015() result: " + str(best_dir))

    if not best_dir:
        return None, None

    vcvarsall = join(best_dir, "vcvarsall.bat")
    if not isfile(vcvarsall):
        return None, None

    return vcvarsall,version


def run_vcvarsall(self, vcvarsall, version):
    if version == "old":
        if self.arguments.use_studio not in  ("any", "vs2015"):
            die("Could only find vs2015")
        cmd = '"{}" {} & set'.format(vcvarsall, self.arguments.arch)
    else:
        if self.arguments.use_studio == "vs2015":
            vcver = "14.0"
        elif self.arguments.use_studio == "vs2017":
            vcver = "14.1"
        elif self.arguments.use_studio == "vs2019":
            vcver = "14.2"
        elif self.arguments.use_studio == "vs2022":
            vcver = "14.3"
        cmd = '"{}" {} -vcvars_ver={} & set'.format(vcvarsall, self.arguments.arch, vcver)

    log("Running '" + cmd + "' to extract environment")
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True)
    output = proc.communicate()[0]
    if proc.returncode != 0:
        die("Failed to fetch environment variables out of vcvarsall.bat: " + output)
    return output

def setup_build_environment():
    """
    Find vcvarsall.bat and load the relevant environment variables from it.  This function
    is inspired (but not copied, for licensing reasons) by the one in python's setuptools.
    """

    vcvarsall, version = find_vcvarsall()

    #use uppercase only in this variable!
    required_variables = set(["LIB", "LIBPATH", "PATH", "INCLUDE", "VSINSTALLDIR"])
    optional_variables = set([
        "PLATFORM",
    ])
    wanted_variables = required_variables | optional_variables  #union

    log("Loading Visual Studio Environment", "header")
    output = run_vcvarsall(vcvarsall, version)

    found_variables = set()

    for line in output.split("\n"):
        if '=' not in line:
            continue
        line = line.strip()
        name, value = line.split('=', 1)
        name = name.upper()
        if name in wanted_variables:
            if value.endswith(os.pathsep):
                value = value[:-1]
            if os.environ.get(name) is None:
                log("Will set '" + name + "' to '" + value + "'", "detail")
            else:
                log("Will change '" + name + "' from '" + os.environ.get(name) + "' to '" + value + "'",
                           "detail")
            os.environ[name] = value
            found_variables.add(name)

    if len(required_variables - found_variables) != 0:
        die("Failed to find all expected variables in vcvarsall.bat")


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


def jre(f):
    try:
        output = subprocess.check_output(("java","-version"),stderr=subprocess.STDOUT).decode("utf-8")
        f.write("JRE: " + re.search(r"(java|openjdk) version \"([0-9\._]*).*\"",output).group(2).strip() + "\n")
    except:
        f.write("JRE: N/A\n")

def jdk(f):
    try:
        output = subprocess.check_output(("javac","-version"),stderr=subprocess.STDOUT).decode("utf-8")
        f.write("JDK: " + re.search(r"javac ([0-9\._]*).*",output).group(1).strip() + "\n")
    except:
        f.write("JDK: N/A\n")



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

def vs2015(f):
    if platform.system() != 'Windows':
        f.write("vs2015: N/A\n")
        
def msvc(f):
    olddir = os.getcwd()
    try:
        remove("msvc_test")
        mkdir("msvc_test")
        os.chdir("msvc_test")
        with open("CMakeLists.txt","w", encoding="utf-8") as cmake_file:
            cmake_file.write("cmake_minimum_required(VERSION 3.10)\nproject(foo CXX)\n")
        output = subprocess.check_output(("cmake",".")).decode("utf-8")
        f.write("MSVC: " + re.search(r"The CXX compiler identification is MSVC ([\.0-9]*)",output).group(1).strip() + "\n")
    except:
        f.write("MSVC: N/A\n")
    os.chdir(olddir)

def get_version_using_cmake(package, regex):
    olddir = os.getcwd()
    try:
        remove(package + "_test")
        mkdir(package + "_test")
        os.chdir(package + "_test")
        with open("CMakeLists.txt","w",encoding="utf-8") as cmake_file:
            cmake_file.write("cmake_minimum_required(VERSION 3.10)\nproject(foo CXX)\nfind_package("+package+" REQUIRED)\n")
        output = subprocess.check_output(("cmake",".")).decode("utf-8")
        os.chdir(olddir)
        return re.search(regex,output).group(1).strip()
    except:
        os.chdir(olddir)
        return "N/A"


def boost(f):
    f.write("Boost: " + get_version_using_cmake("Boost",r"Found Boost: .* \(found version \"([\.0-9]*)\"\)") + "\n")

def doxygen(f):
    f.write("Doxygen: " + get_version_using_cmake("Doxygen",r"Found Doxygen: .* \(found version \"([\.0-9]*)(?: \(.*\))?\"\)") + "\n")

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
                        default="versions.txt",
                        help="Name of output file")
    arguments = parser.parse_args()
    with open(arguments.output,"w", encoding="utf-8") as f:
        conan(f)
        python(f)
        cmake(f)
        ninja(f)
        jre(f)
        jdk(f)
        gcc(f)
        mono(f)
        doxygen(f)
        graphviz(f)
        qt(f)
        boost(f)
        vs2015(f)
        #vs2017(f)
        #vs2019(f)
        #vs2022(f)
        nsis(f)
        #msvcrt
        #msvcrtd

if __name__ == "__main__":
    sys.exit(main())
