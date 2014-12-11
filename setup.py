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

# if __name__ == "__main__":
    
    # jar_file_name = 'voldemort-python.jar'
    # if 'install' in sys.argv:
    #     try:
    #         check_call('gradle shadowJar', shell=True)
    #     except CalledProcessError:
    #         raise IOError("Could not build java client. Is gradle installed?")
    #     base = os.path.dirname(__file__)
    #     lib_path = os.path.join(base, 'build', 'libs')
    #     lib_file = None
    #     for f in os.listdir(lib_path):
    #         if f.startswith('voldemort-python') and f.endswith('-all.jar'):
    #             lib_file = os.path.join(lib_path, f)
    #             break;
    #     if not lib_file:
    #         raise IOError('Could not find voldemort-python*-all.jar file')
    #     os.rename(lib_file, os.path.join(base, 'jvoldemort', jar_file_name))
    
    # packages = ['jvoldemort']
    # packages = packages + list(chain.from_iterable( tuple( p + '.' + n for n in find_packages(p) ) for p in packages ))
    
