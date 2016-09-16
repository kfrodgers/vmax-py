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
    packages=find_packages(exclude=['test*']),
    scripts=['scripts/smis_list_devs', 'scripts/smis_list_igs', 'scripts/smis_list_mvs',
             'scripts/smis_list_pgs', 'scripts/smis_list_sgs', 'scripts/smis_list_unmapped_devs',
             'scripts/smis_show_devs', 'scripts/smis_show_sync', 'scripts/smis_del_devs',
             'scripts/smis_add_devs'],
    install_requires=install_requires,
    data_files=[]
)
