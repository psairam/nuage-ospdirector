# List of Nuage packages
NUAGE_PACKAGES = "nuage-puppet-modules selinux-policy-nuage " \
                 "nuage-bgp nuage-openstack-neutronclient"
NUAGE_DEPENDENCIES = "libvirt perl-JSON lldpad"
NUAGE_VRS_PACKAGE = "python-openvswitch-nuage nuage-openvswitch nuage-metadata-agent"
MLNX_OFED_PACKAGES = "kmod-mlnx-en mlnx-en-utils mstflint os-net-config"
KERNEL_PACKAGES = "kernel kernel-tools kernel-tools-libs python-perf"
VIRT_CUSTOMIZE_MEMSIZE = "2048"
VIRT_CUSTOMIZE_ENV = "export LIBGUESTFS_BACKEND=direct;"
SCRIPT_NAME = 'patching_script.sh'
GPGKEYS_PATH = '/tmp/'