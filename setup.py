from setuptools import setup
from pip.req import parse_requirements

install_reqs = parse_requirements('requirements.txt')

setup(
    name='jvoldemort',
    version='0.5dev',
    packages=['jvoldemort'],
    package_data={ 'jvoldemort': [ 'voldemort-python.jar' ] },
    description = 'py4j voldemort bindings',
    author = 'Soren Holbech',
    author_email = 'sh@mojn.com',
    url = 'https://github.com/mojn/voldemort-python',
    install_requires=[str(ir.req) for ir in install_reqs]
)
