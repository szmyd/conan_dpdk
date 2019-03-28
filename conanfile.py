#!/usr/bin/env python
# -*- coding: utf-8 -*-

from conans import ConanFile, AutoToolsBuildEnvironment
from conans import tools
import os

class LibDPDKConan(ConanFile):
    name = "dpdk"
    version = "20.05"
    description = "Data Plane Development Kit"
    url = "https://github.com/szmyd/conan_dpdk"
    homepage = "https://github.com/szmyd/conan_dpdk"
    license = "BSD-3"
    exports = ["LICENSE.md"]
    source_subfolder = "source_subfolder"
    settings = "os", "compiler", "build_type", "arch"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "numa": [True, False],
        "native_build": [True, False],
    }
    default_options = (
        "shared=False",
        "fPIC=True",
        "numa=False",
        "native_build=False",
    )
    scm = {"type"       : "git",
           "subfolder"  : source_subfolder,
           "url"        : "https://github.com/spdk/dpdk.git",
           "revision"   : "a38450c5ae4a20f6966872b1a4f5d797c65951d7"}

    def configure(self):
        del self.settings.compiler.libcxx

    def build(self):
        env_vars = AutoToolsBuildEnvironment(self).vars
        env_vars.update({"EXTRA_CFLAGS" : env_vars["CFLAGS"],
                         "EXTRA_LDFLAGS" : env_vars["LDFLAGS"],
                         "EXTRA_LDLIBS" : env_vars["LIBS"],})
        print(env_vars)
        with tools.environment_append(env_vars):
            with tools.chdir(self.source_subfolder):
                self.run("make defconfig")
                tools.replace_in_file("GNUmakefile",
                                      "ROOTDIRS-y := buildtools lib kernel drivers app",
                                      "ROOTDIRS-y := buildtools lib drivers")
                if not self.options.numa:
                    tools.replace_in_file("build/.config",
                                          "CONFIG_RTE_EAL_NUMA_AWARE_HUGEPAGES=y",
                                          "CONFIG_RTE_EAL_NUMA_AWARE_HUGEPAGES=n")
                    tools.replace_in_file("build/.config",
                                          "CONFIG_RTE_LIBRTE_VHOST_NUMA=y",
                                          "CONFIG_RTE_LIBRTE_VHOST_NUMA=n")
                if not self.options.native_build:
                    tools.replace_in_file("build/.config",
                                          "CONFIG_RTE_MACHINE=\"native\"",
                                          "CONFIG_RTE_MACHINE=\"default\"")
                self.run("make")

    def package(self):
        with tools.chdir(self.source_subfolder):
            tools.mkdir("installed")
            with tools.environment_append({"DESTDIR": "installed"}):
                    self.run("make prefix=/ install")
        instfld="{}/installed".format(self.source_subfolder)
        self.copy("*.a", dst="lib", src="{}/lib".format(instfld), symlinks=False)
        self.copy("rte_*.h", dst="include/", src="{}/lib/librte_ethdev".format(self.source_subfolder), keep_path=False)
        self.copy("*.h", dst="include/", src="{}/include/dpdk".format(instfld), keep_path=True)

    def package_info(self):
        self.cpp_info.libs = [
                              "-Wl,--whole-archive -lrte_eal",
                              "rte_mempool",
                              "rte_ring",
                              "rte_mbuf",
                              "rte_mempool_ring",
                              "rte_telemetry",
                              "rte_bus_pci",
                              "rte_pci",
                              "rte_kvargs",
                              "rte_net",
                              "-lrte_cryptodev -Wl,--no-whole-archive"
                              ]
        if self.options.numa:
            self.cpp_info.libs.append("numa")
        if self.settings.os == "Linux":
            self.cpp_info.libs.extend(["pthread", "dl"])
        self.env_info.RTE_SDK = self.package_folder
