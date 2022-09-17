from setuptools import setup, find_packages
import glob
import os
import stat

s = setup(
    #this will be the package name you will see, e.g. the output of 'conda list' in anaconda prompt
    name = 'workon', 
    #some version number you may wish to add - increment this after every update
    version='1.0', 

    summary='The workon tool enables quick, repeatable context switching between collections of tools.',
    url='https://github.com/jarrielcook/workon',
    author='Jarriel Cook',
    license='MIT License',

    # Use one of the below approach to define package and/or module names:
  
    #if there are only handful of modules placed in root directory, and no packages/directories exist then can use below syntax
    packages=['workon'], #have to import modules directly in code after installing this wheel, like import mod2 (respective file name in this case is mod2.py) - no direct use of distribution name while importing
  
    include_package_data=True,
    package_data={'workon': ['Kanban-Template.json', 'bash_complete.txt', 'kanban_dir.zip', 'template_dir/*']},

)

def create_link(src, dst):
    installation_path = s.command_obj['install'].install_lib
    installation_egg = os.path.basename(glob.glob('dist/workon*egg')[0])
    script_path = os.path.join(installation_path, installation_egg, 'workon', src)
    
    try:
        os.unlink(dst)
    except:
        pass

    os.symlink(script_path, dst)
    os.chmod(dst, stat.S_IRWXU|stat.S_IRGRP|stat.S_IXGRP|stat.S_IROTH|stat.S_IXOTH)

create_link('workon.py', '/usr/bin/workon')
create_link('parse_workon_export.py', '/usr/bin/parse_workon_export')

