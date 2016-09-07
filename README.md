# VMAX-py

#### A python module for interacting with EMC Solutions Enabler's SMI-S API

###### Install OpenStack Cinder
```bash
git clone https://github.com/kfrodgers/vmax-py
sudo pip install ./vmax-py/
```

###### Set Environment Variables for Commands
```
SMIS_HOST - Hostname or IP address, no default
SMIS_SID - Symmetrix Id, no default
SMIS_USER - User name defaults to 'admin'
SMIS_PASSWORD - Password defaults to '#1Password'
```
Note there are also command line options for each of the above.
 
###### Run Commands
```
smis_list_devs - list devices
smis_list_mvs  - list masking views
smis_list_sgs  - list storage groups
smis_list_igs  - list initiator groups
smis_list_pgs  - list port groups
```