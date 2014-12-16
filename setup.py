try:
    from setuptools import setup
except:
    from distutils.core import setup

dependency_links = [
  'git+https://github.com/bartdag/py4j#egg=py4j-0.9'
]

install_requires = [
  'py4j==0.9'
]

setup(
    name='jvoldemort',
    version='0.1dev',
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
