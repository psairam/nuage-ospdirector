#!/bin/bash
set -x
declare -A fast_path_params
fast_path_params=( ["FP_MASK"]="$FP_MASK" ["FP_PORTS"]="$FP_PORTS" ["CORE_PORT_MAPPING"]="$CORE_PORT_MAPPING" ["FP_MEMORY"]="$FP_MEMORY" ["VM_MEMORY"]="$VM_MEMORY" ["NB_MBUF"]="$NB_MBUF" ["FP_OFFLOAD"]="$FP_OFFLOAD" ["FPNSDK_OPTIONS"]="$FPNSDK_OPTIONS" ["DPVI_MASK"]=$DPVI_MASK ["FP_OPTIONS"]=$FP_OPTIONS)
for param in "${!fast_path_params[@]}" ; do
    FP_VAR=${fast_path_params[$param]}
    if [[ ! -z $FP_VAR ]] ; then
        echo ": \${$param:=$FP_VAR}" >> /usr/local/etc/fast-path.env
    fi
done
crudini --set /var/lib/config-data/puppet-generated/nova_libvirt/etc/nova/nova.conf DEFAULT monkey_patch true
crudini --set /var/lib/config-data/puppet-generated/nova_libvirt/etc/nova/nova.conf DEFAULT monkey_patch_modules nova.virt.libvirt.vif:openstack_6wind_extensions.queens.nova.virt.libvirt.vif.decorator
crudini --set /etc/fp-vdev.ini pmd-vhost sockfolder /var/lib/vhost_sockets
systemctl enable avrs
systemctl start avrs
docker restart nova_libvirt
docker restart nova_compute
