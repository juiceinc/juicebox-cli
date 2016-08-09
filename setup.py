from setuptools import setup, find_packages

requirements = [
    'certifi==2016.8.8',
    'click==6.6',
    'requests==2.11.0'
]

# Have setuptools generate the entry point
# wrapper scripts.
entry_points = '''[console_scripts]
juice=juicebox_cli.cli:cli
'''

setup(
    name='juicebox_cli',
    version='0.1.0',
    description='Juicebox CLI',
    author="Tim O'Guin",
    author_email='tim.oguin@juiceanalytics.com',
    packages=find_packages(),
    install_requires=requirements,
    entry_points=entry_points,
)
