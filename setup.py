from setuptools import setup, find_packages
from setuptools.command import sdist

from itertools import chain
import os
import shutil
import tempfile

if __name__ == "__main__":
    requirements = []
    packages = ['jvoldemort']
    for module in packages:
        req_file = os.path.join(module, 'requirements.txt') 
        if os.path.exists(req_file):
            with open(req_file, 'r') as req_file:
                requirements.extend( l.strip() for l in req_file if l.strip() )
    
    dependency_links = [ r for r in requirements if r.startswith('git') ]
    requirements = [ r.partition('egg=')[2] if r.startswith('git') else r for r in requirements ]
    
    packages = packages + list(chain.from_iterable( tuple( p + '.' + n for n in find_packages(p) ) for p in packages ))

    if '__version__' not in globals():
        import jvoldemort
        __version__ = jvoldemort.__version__

    class CustomSDist(sdist.sdist):
        def make_release_tree(self, base_dir, files):
            sdist.sdist.make_release_tree(self, base_dir, files)
            with tempfile.NamedTemporaryFile(delete=True) as new_setup:
                new_setup.write('__version__ = "%s"\n' % (__version__,))
                with open(os.path.join(base_dir, 'setup.py'), 'r') as old_setup:
                    shutil.copyfileobj(old_setup, new_setup)
                new_setup.flush()
                dest = os.path.join(base_dir, 'setup.py')
                self.copy_file(new_setup.name, dest)
    
    setup(
        name='jvoldemort',
        version=__version__,
        author='Soren Holbech',
        author_email='sh@mojn.com',
        url='https://github.com/mojn/voldemort-python',
        packages=packages,
        package_data={ 'jvoldemort': [ 'voldemort-python.jar', 'requirements.txt' ] },
        description = 'py4j voldemort bindings',
        long_description=open('README.md').read(),
        license='Apache License 2.0',
        install_requires=requirements,
        dependency_links=dependency_links,
        cmdclass={ 'sdist': CustomSDist }
    )
