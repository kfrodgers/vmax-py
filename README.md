# VMAX-py

#### A python module for interacting with EMC Solutions Enabler's SMI-S API

###### Install OpenStack Cinder
First install required libraries and utilities.
```bash
sudo apt-get -y install git python-dev python-pip
sudo apt-get -y install libpq-dev libxslt1-dev
sudo apt-get -y install swig
sudp pip install -U pip
```
Then install VMAX-py
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
SMIS_SSL - Enable SSL defaults to 'False'
```
Note there are also command line options for each of the above.
 
###### Run Commands
```
smis_add_devs   - Add new devices
smis_add_mv     - Add masking view
smis_del_devs   - Delete devices
smis_del_mv     - Delete masking view
smis_list_devs  - List devices
smis_list_dirs  - List front end directors
smis_list_igs   - List initiator groups
smis_list_mvs   - List maskign views
smis_list_pgs   - List port groups
smis_list_pools - List storage pools
smis_list_sgs   - List storage groups
smis_list_unmapped_devs  - List unmapped devices
smis_mod_ig     - Add/Delete/Modify initiator groups
smis_mod_pg     - Add/Delete/Modify port groups
smis_mod_sg     - Add/Delete/Modify storage groups
smis_show_devs  - Show device attributes
smis_show_sync  - Show copy/sync partners
```
