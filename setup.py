# Copyright Hybrid Logic Ltd.
# Copyright 2015 EMC Corporation
# See LICENSE file for details.

from setuptools import setup, find_packages
import codecs  # To use a consistent encoding

# Get the long description from the relevant file
with codecs.open('DESCRIPTION.rst', encoding='utf-8') as f:
    long_description = f.read()

with open("requirements.txt") as requirements:
    install_requires = requirements.readlines()

setup(
    name='emc_vmax_smis',
    version='0.1.0',
    description='EMC VMAX Flocker SMI-S Library',
    long_description=long_description,
    author='Kevin Rodgers',
    author_email='kevin.rodgers@dell.com',
    url='https://github.com/kfrodgers/vmax-py',
    license='Apache 2.0',

    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: System Administrators',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python :: 2.7',
    ],

    keywords='vmax, pywbem, python',
    packages=find_packages(exclude=['test*', 'examples*']),
    scripts=[],
    entry_points={
        'console_scripts': ['smis_add_dev = emc_vmax_smis.vmax_smis_commands:add_devs',
                            'smis_add_mv = emc_vmax_smis.vmax_smis_commands:add_mv',
                            'smis_del_devs = emc_vmax_smis.vmax_smis_commands:del_devs',
                            'smis_del_mv = emc_vmax_smis.vmax_smis_commands:del_mv',
                            'smis_list_devs = emc_vmax_smis.vmax_smis_commands:list_devs',
                            'smis_list_dirs = emc_vmax_smis.vmax_smis_commands:list_dirs',
                            'smis_list_igs = emc_vmax_smis.vmax_smis_commands:list_igs',
                            'smis_list_mvs = emc_vmax_smis.vmax_smis_commands:list_mvs',
                            'smis_list_pgs = emc_vmax_smis.vmax_smis_commands:list_pgs',
                            'smis_list_pools = emc_vmax_smis.vmax_smis_commands:list_pools',
                            'smis_list_sgs = emc_vmax_smis.vmax_smis_commands:list_sgs',
                            'smis_list_unmapped_devs = emc_vmax_smis.vmax_smis_commands:list_unmapped_devs',
                            'smis_mod_ig = emc_vmax_smis.vmax_smis_commands:mod_ig',
                            'smis_mod_pg = emc_vmax_smis.vmax_smis_commands:mod_pg',
                            'smis_mod_sg = emc_vmax_smis.vmax_smis_commands:mod_sg',
                            'smis_show_devs = emc_vmax_smis.vmax_smis_commands:show_devs',
                            'smis_show_sync = emc_vmax_smis.vmax_smis_commands:show_sync']
    },
    install_requires=install_requires,
    data_files=[]
)
