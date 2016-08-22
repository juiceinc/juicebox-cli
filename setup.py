from setuptools import setup, find_packages

requirements = [
    'certifi==2016.8.8',
    'click==6.6',
    'requests==2.11.0'
]

# Have setuptools generate the entry point
# wrapper scripts.
entry_points = {
    'console_scripts': [
        'juice=juicebox_cli.cli:cli',
    ],
}

setup(
    name='juicebox_cli',
    version='0.1.0',
    description='Juicebox CLI',
    author='Juice Analytics',
    author_email='tim.oguin@juiceanalytics.com',
    packages=find_packages(exclude=['contrib', 'docs', 'tests*']),
    install_requires=requirements,
    entry_points=entry_points,
    classifiers=[
          'Development Status :: 4 - Beta',
          'Environment :: Console',
          'Intended Audience :: End Users/Desktop',
          'Intended Audience :: Developers',
          'Intended Audience :: System Administrators',
          'License :: OSI Approved :: Apache 2.0 License',
          'Operating System :: MacOS :: MacOS X',
          'Operating System :: Microsoft :: Windows',
          'Operating System :: POSIX',
          'Programming Language :: Python',
          'Programming Language :: Python :: 2'
          'Programming Language :: Python :: 2.7'
          'Programming Language :: Python :: 3'
          'Programming Language :: Python :: 3.4'
          'Programming Language :: Python :: 3.5'
          'Topic :: Office/Business',
    ],
)
