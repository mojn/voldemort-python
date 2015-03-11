try:
    from setuptools import setup
except:
    from distutils.core import setup

dependency_links = [
  'git+https://github.com/bartdag/py4j#egg=py4j'
]

install_requires = [
  'py4j'
]

import jvoldemort
__version__ = jvoldemort.__version__
    

setup(
    name='jvoldemort',
    version=__version__,
    packages=['jvoldemort'],
    package_data={ 
      'jvoldemort': [ 'voldemort-python.jar' ]
    },
    description = 'py4j voldemort bindings',
    author = 'Soren Holbech',
    author_email = 'sh@mojn.com',
    url = 'https://github.com/mojn/voldemort-python',
    license='Apache License 2.0',
    install_requires=install_requires,
    dependency_links=dependency_links
)
