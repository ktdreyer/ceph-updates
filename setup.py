from setuptools import setup, find_packages

setup(
    name='ceph_updates',
    version='0.1',
    description='',
    author='Ken Dreyer',
    author_email='kdreyer@redhat.com',
    install_requires=[
        "koji",
        "pecan",
        "jinja2",
    ],
    test_suite='ceph_updates',
    zip_safe=False,
    include_package_data=True,
    packages=find_packages(exclude=['ez_setup'])
)
