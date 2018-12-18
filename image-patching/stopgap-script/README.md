Steps:

Clone this repo onto the machine that is accessible to the nuage-rpms repo and make sure the machine also has `libguestfs-tools` installed.   

```
git clone https://github.com/nuagenetworks/nuage-ospdirector.git   
git checkout OSPD13   
cd nuage-ospdirector/image-patching/stopgap-script/   
```

Copy the overcloud-full.qcow2 to this location and make a backup of overcloud-full.qcow2   

`cp overcloud-full.qcow2 overcloud-full-bk.qcow2`   

Now run the below command by providing required values   

`python nuage_overcloud_full_patch.py --RhelUserName='<value>' --RhelPassword='<value>' --RhelPool=<pool-id> --RepoName=Nuage --RepoBaseUrl=http://IP/reponame --ImageName='<value>' --Version=13`   

This script takes in following input parameters:   
RhelUserName: User name for the RHEL subscription   
RhelPassword: Password for the RHEL subscription   
RhelPool: RHEL Pool to subscribe to for base packages and instructions to get this can be found here in the 2nd point   
RepoName: Name for the local repo hosting the Nuage RPMs   
RepoBaseUrl: Base URL for the repo hosting the Nuage RPMs   
ImageName: Name of the qcow2 image (overcloud-full.qcow2 for example)    
Version: OSP-Director version (13)    

If image patching fails for some reason then remove the partially patched overcloud-full.qcow2 and create a copy of it from backup image before retrying image patching again.   

```
rm overcloud-full.qcow2   
cp overcloud-full-bk.qcow2 overcloud-full.qcow2   
```

Once the patching is done successfully copy back the patched image to /home/stack/images/ on undercloud director and:   

1. If overcloud images are not uploaded to glance run the below command    
` (undercloud) [stack@director images]$ openstack overcloud image upload --image-path /home/stack/images/`    

2. If overcloud images are uploaded to glance run the below commad   
` (undercloud) [stack@director images]$ openstack overcloud image upload --update-existing --image-path /home/stack/images/`    

