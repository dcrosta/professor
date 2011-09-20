from setuptools import setup, find_packages

requires = [
    'flask',
    'pymongo',
    'wtforms',
    'pytz',
]

setup(
    name='professor',
    version='0.1',
    description='Painless MongoDB Profiling',
    classifiers=[
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Development Status :: 3 - Alpha',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: BSD License',
        'Topic :: Database',
        'Topic :: Database :: Front-Ends',
        'Topic :: Software Development :: Testing',
        'Topic :: System :: Monitoring',
        'Topic :: System :: Systems Administration',
    ],
    author='Dan Crosta',
    author_email='dcrosta@late.am',
    url='https://github.com/dcrosta/professor',
    keywords='mongodb profiling',
    install_requires=requires,
    packages=find_packages(),
    entry_points={
        'console_scripts': [ 'profess=professor.scripts:profess' ],
    },
)



