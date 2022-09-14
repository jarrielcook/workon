from setuptools import setup, find_packages

setup(
    #this will be the package name you will see, e.g. the output of 'conda list' in anaconda prompt
    name = 'workon', 
    #some version number you may wish to add - increment this after every update
    version='1.0', 
  
    summary: UNKNOWN
    home-page: UNKNOWN
    author: Jarriel Cook
    author-email: UNKNOWN
    license: UNKNOWN

    # Use one of the below approach to define package and/or module names:
  
    #if there are only handful of modules placed in root directory, and no packages/directories exist then can use below syntax
    packages=['workon'], #have to import modules directly in code after installing this wheel, like import mod2 (respective file name in this case is mod2.py) - no direct use of distribution name while importing
  
    include_package_data=True,
    package_data={'workon': ['bash_alias.txt', 'bashrc_complete.txt', 'kanban_dir.zip', 'template_dir/*']},
)
