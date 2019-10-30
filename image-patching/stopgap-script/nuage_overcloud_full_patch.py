# !/usr/bin/python
# Copyright 2019 NOKIA
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import argparse
import subprocess
import sys
import logging
import os
import yaml
from utils.constants import *
from utils.common import *

'''
This script is used to patch an existing OpenStack
image with Nuage components
This script takes in following input parameters:
 RhelUserName      : User name for the RHEL subscription
 RhelPassword      : Password for the RHEL subscription
 RhelPool          : RHEL Pool to subscribe
 RepoFile          : Name for the file repo hosting the Nuage RPMs
 DeploymentType    : ["ovrs"] --> OVRS deployment
                     ["avrs"] --> AVRS + VRS deployment
                     ["vrs"]  --> VRS deployment
 VRSRepoNames      : Name for the repo hosting the Nuage O/VRS RPMs 
 AVRSRepoNames     : Name for the repo hosting the Nuage AVRS RPMs
 MellanoxRepoNames : Name for the repo hosting the Mellanox RPMs
 KernelRepoNames   : Name for the repo hosting the Kernel RPMs
 RpmPublicKey      : RPM GPG Key 
 logFile           : Log file name
The following sequence is executed by the script
 1. Subscribe to RHEL and the pool
 2. Uninstall OVS
 3. Download AVRS packages to the image if AVRS is enabled
 4. Install NeutronClient, Nuage-BGP, Selinux Policy Nuage, 
    Nuage Puppet Module, Redhat HF and Mellanox packages.
 5. Install O/VRS, Nuage Metadata Agent
 6. Unsubscribe from RHEL
'''

logger = logging.getLogger(LOG_FILE_NAME)
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
consoleHandler = logging.StreamHandler(sys.stdout)
consoleHandler.setFormatter(formatter)
logger.addHandler(consoleHandler)


#####
# Decorator function to enable and disable repos for
# NuageMajorVersion "5.0" and skip this for "6.0"
#####

def repos_decorator(func):
    def repos_wrapper(version, reponames):
        install_cmds = func()
        if version == "5.0":
            enable_repos_cmd = "yum-config-manager --enable"
            for repo in reponames:
                enable_repos_cmd += " %s" % (repo)
            disable_repos_cmd = enable_repos_cmd.replace("enable",
                                                             "disable")
            full_cmds = enable_repos_cmd + install_cmds + disable_repos_cmd
        else:
            full_cmds = install_cmds
        write_to_file(SCRIPT_NAME, full_cmds)
        write_to_file(SCRIPT_NAME, '\n')
    return repos_wrapper


#####
# Function to install Nuage packages that are required
#####

@repos_decorator
def install_nuage_packages():

    cmds = '''
#### Installing Nuage Packages
yum install --setopt=skip_missing_names_on_install=False -y %s
yum install --setopt=skip_missing_names_on_install=False -y %s
yum install --setopt=skip_missing_names_on_install=False -y %s
''' % (NUAGE_DEPENDENCIES, NUAGE_VRS_PACKAGE,
       NUAGE_PACKAGES)
    return cmds

#####
# Function to install Mellanox packages that are required
#####

@repos_decorator
def install_mellanox():

    cmds = '''
#### Installing Mellanox OFED and os-net-config Packages
yum clean all
yum install --setopt=skip_missing_names_on_install=False -y %s
systemctl disable mlnx-en.d
''' % (MLNX_OFED_PACKAGES)
    return cmds


#####
# Updating kernel to Red Hat Hot Fix
#####

@repos_decorator
def update_kernel():

    cmds = '''
#### Installing Kernel Hot Fix Packages
yum clean all
yum install --setopt=skip_missing_names_on_install=False -y %s
''' % (KERNEL_PACKAGES)
    return cmds


#####
# Function to install Nuage AVRS packages that are required
#####

@repos_decorator
def download_avrs_packages():

    cmds = '''
#### Downloading Nuage Avrs and 6wind Packages
mkdir -p /6wind
rm -rf /var/cache/yum/Nuage
yum clean all
touch /kernel-version
rpm -q kernel | awk '{ print substr($1,8) }' > /kernel-version
yum install --setopt=skip_missing_names_on_install=False -y createrepo
yum install --setopt=skip_missing_names_on_install=False 
--downloadonly --downloaddir=/6wind kernel-headers-$(awk 'END{print}' /kernel-version) kernel-devel-$(awk 'END{print}' /kernel-version) python-pyelftools* dkms* 6windgate* %s nuage-metadata-agent virtual-accelerator*
yum install --setopt=skip_missing_names_on_install=False --downloadonly --downloaddir=/6wind selinux-policy-nuage-avrs*
yum install --setopt=skip_missing_names_on_install=False --downloadonly --downloaddir=/6wind 6wind-openstack-extensions
rm -rf /kernel-version
yum clean all
''' %(NUAGE_AVRS_PACKAGE)
    return cmds


####
# Image Patching
####


def image_patching(nuage_config):

    start_script()

    if nuage_config.get("RpmPublicKey"):
        logger.info("Importing gpgkey(s) to overcloud image")
        importing_gpgkeys(nuage_config["ImageName"],
                          nuage_config["RpmPublicKey"])


    if nuage_config.get("RhelUserName") and nuage_config.get(
            "RhelPassword") and nuage_config.get("RhelPool"):
        if nuage_config.get("ProxyHostname") and nuage_config.get("ProxyPort"):
            rhel_subscription(
                nuage_config["RhelUserName"], nuage_config["RhelPassword"],
                nuage_config["RhelPool"], nuage_config["ProxyHostname"],
                nuage_config["ProxyPort"])
        else:
            rhel_subscription(
                nuage_config["RhelUserName"], nuage_config["RhelPassword"],
                nuage_config["RhelPool"])
    uninstall_packages()

    logger.info("Copying RepoFile to the overcloud image")
    copy_repo_file(nuage_config["ImageName"], nuage_config["RepoFile"])

    if nuage_config['KernelHF']:
        update_kernel(nuage_config["NuageMajorVersion"], nuage_config[
            "KernelRepoNames"])

    if "ovrs" in nuage_config["DeploymentType"]:
        install_mellanox(nuage_config["NuageMajorVersion"],
                         nuage_config["MellanoxRepoNames"])

    if "avrs" in nuage_config["DeploymentType"]:
        download_avrs_packages(nuage_config["NuageMajorVersion"],
                               nuage_config["AVRSRepoNames"])

    install_nuage_packages(nuage_config["NuageMajorVersion"],
                           nuage_config["VRSRepoNames"])

    if nuage_config.get("RhelUserName") and nuage_config.get(
            "RhelPassword") and nuage_config.get("RhelPool"):
        rhel_remove_subscription()

    logger.info("Running the patching script on Overcloud image")
    virt_customize_run(
        ' %s -a %s --memsize %s --selinux-relabel' % (
            SCRIPT_NAME, nuage_config["ImageName"],
            VIRT_CUSTOMIZE_MEMSIZE))
    logger.info("Reset the Machine ID")
    cmds_run([VIRT_CUSTOMIZE_ENV + "virt-sysprep --operation machine-id -a %s" % nuage_config["ImageName"]])
    logger.info("Done")


def check_config(nuage_config):
    missing_config = []
    for key in ["ImageName", "RepoFile", "VRSRepoNames"]:
        if not (nuage_config.get(key)):
            missing_config.append(key)
    if missing_config:
        logger.error("Please provide missing config %s value "
                     "in your config file. \n" % missing_config)
        sys.exit(1)
    file_exists(nuage_config["ImageName"])
    if nuage_config.get("KernelHF"):
        if not nuage_config.get("KernelRepoNames"):
            logger.error(
                "Please provide KernelRepoNames for Kernel Hot Fix")
            sys.exit(1)
    msg = "DeploymentType config option %s is not correct or supported " \
          " Please enter:\n ['vrs'] --> for VRS deployment\n " \
          "['avrs'] --> for AVRS + VRS deployment\n " \
          "['ovrs'] --> for OVRS deployment" % nuage_config["DeploymentType"]
    if len(nuage_config["DeploymentType"]) > 1:
        new_msg = "Multiple " + msg
        logger.error(new_msg)
        sys.exit(1)
    elif "vrs" in nuage_config["DeploymentType"]:
        logger.info("Overcloud Image will be patched with Nuage VRS rpms")
    elif "avrs" in nuage_config["DeploymentType"]:
        logger.info("Overcloud Image will be patched with Nuage VRS & AVRS rpms")
        if not nuage_config.get("AVRSRepoNames"):
            logger.error("Please provide AVRSRepoNames for AVRS deployment")
            sys.exit(1)
    elif  "ovrs" in nuage_config["DeploymentType"]:
        logger.info("Overcloud Image will be patched with OVRS rpms")
        if not nuage_config.get("MellanoxRepoNames"):
            logger.error(
                "Please provide MellanoxRepoNames for OVRS deployment")
            sys.exit(1)
    else:
        logger.error(msg)
        sys.exit(1)
    logger.info("Verifying pre-requisite packages for script")
    libguestfs = cmds_run(['rpm -q libguestfs-tools-c'])
    if 'not installed' in libguestfs:
        logger.info("Please install libguestfs-tools-c package for the script to run")
        sys.exit(1)
    if nuage_config["NuageMajorVersion"] == "5.0":
        NUAGE_AVRS_PACKAGE = "nuage-openvswitch"

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--nuage-config",
        dest="nuage_config",
        type=str,
        required=True,
        help="path to nuage_patching_config.yaml")
    args = parser.parse_args()

    with open(args.nuage_config) as nuage_config:
        try:
            nuage_config = yaml.load(nuage_config)
        except yaml.YAMLError as exc:
            logger.error(
                'Error parsing file {filename}: {exc}. Please fix and try '
                'again with correct yaml file.'.format(filename=args.nuage_config, exc=exc))
            sys.exit(1)
    logger.info("nuage_overcloud_full_patch.py was run with following config options %s " % nuage_config)
    check_config(nuage_config)
    image_patching(nuage_config)


if __name__ == "__main__":
    main()
