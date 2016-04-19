from setuptools import setup

from aplt import __version__

setup(
    name='aplt',
    version=__version__,
    description='Autopush Load-Tester',
    url='http://github.com/mozilla-services/ap-loadtester',
    author='Ben Bangert',
    author_email='bbangert@mozilla.com',
    license='MPL2',
    packages=['aplt'],
    zip_safe=False,
    install_requires=[
        "autobahn==0.13.0",
        "Twisted==16.0.0",
        "docopt>=0.6.2",
        "service-identity>=14.0.0",
        "treq>=15.0.0",
        "pyOpenSSL>=0.15.1",
        "txaio==2.2.2",
        "txStatsD==1.0.0",
        "ecdsa==0.13",
        "python-jose==0.6.1",
    ],
    entry_points="""
    [console_scripts]
    aplt_scenario = aplt.runner:run_scenario
    aplt_testplan = aplt.runner:run_testplan
    """
)
