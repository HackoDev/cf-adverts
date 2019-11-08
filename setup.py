import os
from setuptools import setup, find_packages

PACKAGE_NAME = 'cf_adverts'
DIRNAME = os.path.dirname(os.path.abspath(__file__))

with open(os.path.join(DIRNAME, 'README.md')) as f:
    README = f.read()

# allow setup.py to be run from any path
os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

setup(
    name=PACKAGE_NAME,
    version='0.0.1',
    packages=find_packages(exclude=['test_project']),
    package_data={
        '': ['*.json'],
    },
    description='crowd funding adverts module',
    long_description=README,
    include_package_data=True,
    install_requires=[
        'Django==1.11.5',
        'Pillow==6.2.0',
        'django-filter==1.0.4',
        'celery==4.1.0',
        'django-admin-sortable2==0.6.16',
        'django-model-utils==3.0.0',
        'django-phonenumber-field==1.3.0',
        'djangorestframework==3.9.1',
        'easy-thumbnails==2.4.2',
        'phonenumberslite==8.8.3',
        'pytz==2017.2',
        'cf_users==0.0.1',
        'cf_core==0.0.1',
    ],
    dependency_links=[
        'git+https://github.com/HackoDev/cf-users.git@master#egg=cf_users-0.0.1',
        'git+https://github.com/HackoDev/cf-core.git@master#egg=cf_core-0.0.1',
    ]

)
