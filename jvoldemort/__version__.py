import os
__version__ = "1.0." + os.environ.get('BUILD_NUMBER', '0').strip()
