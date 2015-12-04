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
    entry_points="""
    [console_scripts]
    aplt_scenario = aplt.runner:run_scenario
    """
)
