import setuptools
import sys
import os

versionedModule = {}
versionedModule['urllib'] = 'urllib'
if sys.version_info.major < 3:
    versionedModule['urllib'] = 'urllib2'

install_requires = [
    "hierosoft @ git+https://github.com/Hierosoft/hierosoft.git"
]

description = (
    "Parse and modify Python code."
)
long_description = description
if os.path.isfile("readme.md"):
    with open("readme.md", "r") as fh:
        long_description = fh.read()

setuptools.setup(
    name='pycodetool',
    version='0.9.0',
    description=description,
    long_description=long_description,
    long_description_content_type="text/markdown",
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Programming Language :: Python :: 3',
        ('License :: OSI Approved ::'
         ' GNU General Public License v2 or later (GPLv2+)'),
        'Operating System :: POSIX :: Linux',
        'Topic :: Software Development :: Code Generators',
    ],
    keywords='python code parsing development parser IronPython',
    url="https://github.com/poikilos/pycodetool",
    author="Jake Gustafson",
    author_email='7557867+poikilos@users.noreply.github.com',
    license='GPLv2+',
    # packages=setuptools.find_packages(),
    packages=['pycodetool'],
    include_package_data=True,  # look for MANIFEST.in
    # scripts=['example'] ,
    # See <https://stackoverflow.com/questions/27784271/
    # how-can-i-use-setuptools-to-generate-a-console-scripts-entry-
    # point-which-calls>
    entry_points={
        'console_scripts': [
            'changes=pycodetool.changes:main',
        ],
    },
    install_requires=install_requires,
    #     versionedModule['urllib'],
    # ^ "ERROR: Could not find a version that satisfies the requirement
    #   urllib (from nopackage) (from versions: none)
    # ERROR: No matching distribution found for urllib"
    test_suite='nose.collector',
    tests_require=['nose', 'nose-cover3'],
    zip_safe=False,  # It can't run zipped due to needing data files.
 )
