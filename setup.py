from setuptools import setup

setup(
    name='jvoldemort',
    version='0.5dev',
    packages=['jvoldemort'],
    package_data={ 'jvoldemort': [ 'voldemort-python.jar' ] },
    description = 'py4j voldemort bindings',
    author = 'Soren Holbech',
    author_email = 'sh@mojn.com',
    url = 'https://github.com/mojn/voldemort-python'
)
