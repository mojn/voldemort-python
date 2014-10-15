from setuptools import (find_packages, 
                        setup)
from itertools import chain
import os
from subprocess import (CalledProcessError,
                        check_call)
import sys

if __name__ == "__main__":
    
    jar_file_name = 'voldemort-python.jar'   
    if 'install' in sys.argv:
        maven_url = os.environ.get('VOLDEMORT_MAVEN_URL')
        maven_username = os.environ.get('VOLDEMORT_USERNAME')
        maven_password = os.environ.get('VOLDEMORT_PASSWORD')
        assert maven_url, "Url for maven repository holding voldemort-jar must be specified in environment variable VOLDEMORT_MAVEN_URL"
        assert maven_username, "Username for maven repository holding voldemort-jar must be specified in environment variable VOLDEMORT_USERNAME"
        assert maven_password, "Password for maven repository holding voldemort-jar must be specified in environment variable VOLDEMORT_PASSWORD"
        try:
            check_call('gradle shadowJar -PrepoUrl=%s -PrepoUser=%s -PrepoPass=%s' % (maven_url, maven_username, maven_password), shell=True)
        except CalledProcessError:
            raise IOError("Could not build java client. Is gradle installed?")
        base = os.path.dirname(__file__)
        lib_path = os.path.join(base, 'build', 'libs')
        lib_file = None
        for f in os.listdir(lib_path):
            if f.startswith('voldemort-python') and f.endswith('-all.jar'):
                lib_file = os.path.join(lib_path, f)
                break;
        if not lib_file:
            raise IOError('Could not find voldemort-python*-all.jar file')    
        os.rename(lib_file, os.path.join(base, 'jvoldemort', jar_file_name))
    
    packages = ['jvoldemort']
    requirements = []
    for package in packages:
        with open(os.path.join(package, 'requirements.txt'), 'r') as req_file:
            requirements.extend( l.strip() for l in req_file if l.strip() )
    
    dependency_links = [ r for r in requirements if r.startswith('git') ]
    requirements = [ r for r in requirements if not r.startswith('git') ]
    
    packages = packages + list(chain.from_iterable( tuple( p + '.' + n for n in find_packages(p) ) for p in packages ))
    
    setup(
        name='Voldemort client lib',
        version='0.1dev',
        packages=packages,
        package_data={ 'jvoldemort': [ jar_file_name ] },
        zip_safe=False,
        install_requires=requirements,
        dependency_links=dependency_links
    )
    
