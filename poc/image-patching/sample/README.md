1) Fill in the variables inside vars.yml   

2) Run the below command by to start the patching   

ansible-playbook --module-path=../lib/ansible/modules/ patching.yml --extra-vars @vars.yml   
