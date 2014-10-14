from setuptools import (find_packages, 
                        setup)
from itertools import chain
import os

if __name__ == "__main__":
    requirements = []
    for module in ('voldemort',):
        with open(os.path.join(module, 'requirements.txt'), 'r') as req_file:
            requirements.extend( l.strip() for l in req_file if l.strip() )
    
    dependency_links = [ r for r in requirements if r.startswith('git') ]
    requirements = [ r for r in requirements if not r.startswith('git') ]
    
    packages = ['voldemort']
    packages = packages + list(chain.from_iterable( tuple( p + '.' + n for n in find_packages(p) ) for p in packages ))
    
    setup(
        name='Voldemort client lib',
        version='0.1dev',
        packages=packages,
        zip_safe=False,
        install_requires=requirements,
        dependency_links=dependency_links
    )
    
