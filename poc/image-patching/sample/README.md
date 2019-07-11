## Prerequisites:   
   
On Ansible Host:   
* gcc   
* libguestfs   
* libguestfs-devel   
* Python >= 2.7.5 || Python >= 3.4    
* libguestfs python bindings:   
    * System:
      If your distribution's package manager contains 'python-libguestfs', install it (via `yum`, `apt` ...)   


## Steps for image patching:   

1) Fill in the variables inside vars.yml   

2) Create a repo file which has all repositories information   

3) Run the below command by to start the patching   

ansible-playbook --module-path=../lib/ansible/modules/ patching.yml --extra-vars @vars.yml   
