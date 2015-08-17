#!/usr/bin/python

#
# Copyright 2013 - Tom Alessi
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


"""SSD Install Script
   
   Requirements
    - SSD source downloaded from http://code.google.com/p/system-status-dashboard

"""


import django
import os
import random
import re
import shutil


def terminate(e):
    """Print an error and exit"""

    print '\n\n*** Error encountered: %s' % e
    print 'Install script will exit.  Please correct the issue and run the install/upgrade again.'
    exit(2)


def create_log(app_dir,apache_uid):
    """Create the SSD log directory and initialize the log file"""

    # Create the directory
    print 'Creating log directory:%s/log' % app_dir
    if os.path.exists('%s/log' % app_dir):
        print 'Log directory already exists, removing it before recreating.'
        try:
            shutil.rmtree('%s/log' % app_dir)
        except Exception as e:
            terminate(e)
 
    try:
        os.makedirs('%s/log' % app_dir)
    except Exception as e:
        terminate(e)

    # Create the log file and set the permissions
    print 'Creating the initial log file:%s/log/ssd.log' % app_dir
    try:
        fl = open('%s/log/ssd.log' % app_dir,'w')
        os.chown('%s/log/ssd.log' % app_dir,int(apache_uid),-1)
    except Exception as e:
        terminate(e)


def customize_settings(app_dir,dst_local):
    """Customize the SSD settings.tmpl file"""

    print 'Customizing %s/src/settings.tmpl' % app_dir

    try:
        # Open the settings.tmpl file
        s_sp = open('%s/src/settings.tmpl' % app_dir).read()

        # Add the path to the SSD local dir
        s_sp = s_sp.replace('$__local_dir__$',dst_local)

        # Add the path to the SSD app dir
        s_sp = s_sp.replace('$__app_dir__$',app_dir)

        # Write out the new file
        f_sp = open('%s/ssd/settings.py' % app_dir,'w')
        f_sp.write(s_sp)
        f_sp.close() 
    except Exception, e:
        terminate(e)


def customize_local_settings(db_user,db_pass,db_host,db_port,dst_local,app_dir,apache_uid,upload_dir):
    """Customize the SSD local_settings.py file"""

    try:
        # Open the local_settings.py file
        print 'Customizing %s/local_settings.py for your installation' % dst_local
        s_ls = open('%s/local_settings.py' % dst_local).read()

        # Add the database information
        s_ls = s_ls.replace('$__db_user__$',db_user)
        s_ls = s_ls.replace('$__db_pass__$',db_pass)
        s_ls = s_ls.replace('$__db_host__$',db_host)
        s_ls = s_ls.replace('$__db_port__$',db_port)

        # Add the template information
        s_ls = s_ls.replace('$__app_dir__$',app_dir)

        # Add the secret key
        secret_key = "".join([random.choice("abcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*(-_=+)") for i in range(50)])
        s_ls = s_ls.replace('$__secret_key__$',secret_key)

        # Write out the new file
        f_ls = open('%s/local_settings.py' % dst_local,'w')
        f_ls.write(s_ls)
        f_ls.close() 

        # Set permissions to 600 and ownership apache_uid:root
        os.chown('%s/local_settings.py' % dst_local,int(apache_uid),-1)
        os.chmod('%s/local_settings.py' % dst_local,0600)
    except Exception, e:
        terminate(e)


def customize_wsgi_conf(app_dir,django_admin,dst_local,wsgi_dir,upload_dir):
    """Customize the SSD wsgi.conf file"""

    print 'Customizing %s/wsgi.conf for your installation' % dst_local

    try:
        # Open the wsgi.conf file
        s_wc = open('%s/wsgi.conf' % dst_local).read()

        # Add the path to the local wsgi.py file
        s_wc = s_wc.replace('$__dst_local__$',dst_local)

        # Add the path to the SSD html static assets
        s_wc = s_wc.replace('$__app_dir__$',app_dir)

        # Add the path to the DJango admin html static assets
        s_wc = s_wc.replace('$__django_admin__$',django_admin)

        # Add the path to the Apache mod_wsgi.so module
        s_wc = s_wc.replace('$__wsgi_dir__$',wsgi_dir)

        # Add the path to the Screenshot upload directory
        s_wc = s_wc.replace('$__upload_dir__$',upload_dir)

        # Write out the new file
        f_wc = open('%s/wsgi.conf' % dst_local,'w')
        f_wc.write(s_wc)
        f_wc.close() 
    except Exception, e:
        terminate(e)


def create_upload(upload_dir,apache_uid):
    print 'Creating upload directory:%s/uploads' % upload_dir
    # Create the upload directory if its not already there
    if not os.path.exists('%s/uploads' % upload_dir):
        try:
            os.makedirs('%s/uploads' % upload_dir)
        except Exception, e:
            terminate(e)
    else:
        print 'Upload directory already exists'

    # Ensure this is writeable by the Apache user
    print 'Setting permissions on upload directory'
    os.chown('%s/uploads' % upload_dir,int(apache_uid),-1)
    os.chmod('%s/uploads' % upload_dir,0700)


def customize_wsgi_py(app_dir,dst_local):
    """Customize the SSD wsgi.conf file"""

    print 'Customizing %s/wsgi.py for your installation' % dst_local

    try:
        # Open the wsgi.py file
        s_wp = open('%s/wsgi.py' % dst_local).read()

        # Add the path to the SSD project dir
        s_wp = s_wp.replace('$__app_dir__$',app_dir)

        # Write out the new file
        f_wp = open('%s/wsgi.py' % dst_local,'w')
        f_wp.write(s_wp)
        f_wp.close() 
    except Exception, e:
        terminate(e)


def apache_symlink(dst_local,web_conf):
    """Create a symlink in the apache configuration directory to wsgi.conf"""

    print 'Creating Apache symlink to %s/wsgi.conf' % dst_local

    # Create the symlink
    # If the symlink is already there, remove it
    try:
        if os.path.exists('%s/wsgi.conf' % web_conf):
            print '%s/wsgi.conf symlink exists, removing and recreating it' % dst_local
            os.unlink('%s/wsgi.conf' % web_conf)
        os.symlink('%s/wsgi.conf' % dst_local,'%s/wsgi.conf' % web_conf)
    except Exception, e:
        terminate(e)


def ssd_symlink(app_dir,ssd_src):
    """Create the generic SSD symlink to the source directory"""

    # If the symlink is already there, remove it
    print 'Creating ssd symlink: %sssd -> %s' % (app_dir,ssd_src)

    try:
        if os.path.exists('%sssd' % app_dir):
            if os.path.islink('%sssd' % app_dir):
                print 'ssd symlink exists, removing and recreating it'
                os.unlink('%sssd' % app_dir)

        # Create the symlink
        os.symlink(ssd_src,'%sssd' % app_dir)
    except Exception, e:
        terminate(e)


def split_directories(ssd_src):
    """Split the source directory from its path"""

    # Determine the source and application directory names
    src_match = re.search('^\/(\S+\/)*(\S+)$',ssd_src)
    
    if src_match is None:
        terminate('The SSD source directory could not be determined.')

    app_dir = src_match.group(1)
    app_dir = "/" + app_dir
    ssd_src_dir = src_match.group(2)
    print 'SSD application directory: %s' % app_dir
    print 'SSD source directory: %s' % ssd_src_dir

    return(app_dir,ssd_src_dir)


def copy_local(src_local,dst_local):
    """Copy the generic SSD local.tmpl so that it can be customized"""

    # If the ssd-local directory already exists, remove it
    print 'Checking for existing ssd-local directory at %s' % dst_local
    if os.path.exists(dst_local):
        print '%s exists, removing and recopying it.' % dst_local
        try:
            shutil.rmtree(dst_local)
        except Exception, e:
            terminate(e)

    # Copy the local.tmpl directory to the new ssd-local directory
    print 'Copying %s to %s' % (src_local,dst_local)
    try:
        shutil.copytree(src_local,dst_local)
    except Exception, e:
        print 'Error occurred: %s' % e
        terminate(e)


def install():
    """Perform fresh install of SSD"""

    print 'PERFORMING FRESH INSTALL:\n'  

    # SOURCE DIRECTORY
    ssd_source = re.search('^(\S+)\/src\/install$',os.getcwd())
    if ssd_source:
        default_source = ssd_source.group(1)
    else:
        default_source = 'ERROR: source could not be automatically determined, enter manually'

    ssd_src = raw_input('1: Enter the path to the SSD source [%s]\n#>' % default_source).strip()
    ssd_src = ssd_src or default_source
    print 'SSD source set to: %s\n' % ssd_src

    # LOCAL DIRECTORY
    default_local_dir = '/opt'
    local_dir = raw_input('2: Enter the desired local directory location [%s]\n#>' % default_local_dir).strip()
    local_dir = local_dir or default_local_dir
    print 'Local directory set to: %s\n' % local_dir

    # APACHE WEB CONFIGURATION
    web_conf=raw_input('3: Enter the Apache configuration directory\n#>').strip()
    print 'Apache configuration directory set to: %s\n' % web_conf

    # DB USER
    db_user=raw_input('4: Enter the database username\n#>').strip()
    print 'Database username set to: %s\n' % db_user

    # DB PASSWORD
    db_pass=raw_input('5: Enter the database password\n#>').strip()
    print 'Database password set to: %s\n' % db_pass

    # DB HOST
    db_host=raw_input('6: Enter the database server fully qualified hostname or IP address\n#>').strip()
    print 'Database server set to: %s\n' % db_host

    # DB PORT
    db_port=raw_input('7: Enter the database port\n#>').strip()
    print 'Database port set to: %s\n' % db_port
    
    # DJANGO ADMIN DIRECTORY
    django_path = re.search('^\[\'(\S+)\'\]',str(django.__path__))
    if django_path:
        django_admin_path = '%s/contrib/admin/static/admin' % django_path.group(1)
    else:
        django_admin_path = 'ERROR: django path could not be automatically determined, enter manually'
    
    django_admin=raw_input('8: Enter the path to the DJango admin static files [%s]\n#>' % django_admin_path).strip()
    django_admin = django_admin or django_admin_path
    print 'DJango admin static files set to: %s\n' % django_admin
    
    # APACHE UID
    apache_uid=raw_input('9: Enter the uid of the Apache user\n#>').strip()
    print 'Apache uid set to: %s\n' % apache_uid
    
    # APACHE WSGI MODULE DIRECTORY
    # Search for it?
    mod_wsgi_search = raw_input('The location of the apache mod_wsgi.so module is required, search for it (y/n)?\n#>').strip()
    if mod_wsgi_search =='y':
        print 'Searching for module...'
        found = False
        for d, s, f in os.walk('/'):
            if 'mod_wsgi.so' in f:
                print 'Module found at %s' % d
                mod_wsgi_path = d
                found = True
                break
        if found == False:
            print 'mod_wsgi.so could not be found'
            mod_wsgi_path = 'ERROR: mod_wsgi.so path unknown, enter manually'
    else:
        mod_wsgi_path = 'ERROR: mod_wsgi.so path unknown, enter manually'
    
    wsgi_dir=raw_input('10: Enter the path to the Apache mod_wsgi.so module [%s]\n#>' % mod_wsgi_path).strip()
    wsgi_dir = wsgi_dir or mod_wsgi_path
    print 'Apache mod_wsgi directory set to: %s\n' % wsgi_dir

    # SCREENSHOT UPLOAD DIRECTORY
    default_upload_dir = '/opt/ssd-local'
    upload_dir=raw_input('11: Enter the path to the screenshot upload directory [%s]\n#>' % default_upload_dir).strip()
    upload_dir = upload_dir or default_upload_dir 
    print 'Upload directory set to: %s\n' % upload_dir

    install_text = """You have entered the following options:\n
            - SSD Source            : %s
            - Local Directory       : %s
            - Apache Conf Directory : %s
            - Database Username     : %s
            - Database Password     : ********
            - Database Host         : %s
            - Database Port         : %s
            - DJango Admin Location : %s
            - Apache UID            : %s
            - Path to mod_wsgi.so   : %s
            - Screenshot Directory  : %s

         """ % (ssd_src,local_dir,web_conf,db_user,db_host,db_port,django_admin,apache_uid,wsgi_dir,upload_dir)

    print install_text
    proceed=raw_input('Proceed with installation (y/n)\n#>').strip()

    if proceed == 'y':
        print 'proceeding...'
    else:
        print 'Exiting installation without modifying anything.'
        exit(0)

    # Write out the install file for debugging issues later
    install_file = open('install.txt','w')
    install_file.write(install_text)
    install_file.close() 

    # Determine the SSD source directory and path
    app_dir,ssd_src_dir = split_directories(ssd_src)

    # Create the generic ssd symlink
    ssd_symlink(app_dir,ssd_src)

    # Add 'ssd' to the app dir for the remainder of this script
    app_dir = app_dir + 'ssd'

    # Setup the log directory and file
    create_log(app_dir,apache_uid)

    # Source and Destination local directories
    src_local = app_dir + '/src/local.tmpl'
    dst_local = local_dir + '/ssd-local'

    # Copy the local.tmpl directory out of the source directory so it can be customized
    copy_local(src_local,dst_local)

    # Customize the new local_setting.py file
    customize_local_settings(db_user,db_pass,db_host,db_port,dst_local,app_dir,apache_uid,upload_dir)

    # Customize the new wsgi.conf file
    customize_wsgi_conf(app_dir,django_admin,dst_local,wsgi_dir,upload_dir)

    # Customize the new wsgi.py file
    customize_wsgi_py(app_dir,dst_local)

    # Setup the Apache symlink
    apache_symlink(dst_local,web_conf)

    # Customize settings.tmpl to add the path the local_settings.py file
    customize_settings(app_dir,dst_local)

    # Create the screenshot upload directory
    create_upload(upload_dir,apache_uid)


def upgrade():
    """Perform an upgrade of SSD"""

    print 'PERFORMING SSD UPGRADE:\n'  

    # SOURCE DIRECTORY
    ssd_source = re.search('^(\S+)\/src\/install$',os.getcwd())
    if ssd_source:
        default_source = ssd_source.group(1)
    else:
        default_source = 'ERROR: source could not be automatically determined, enter manually'

    ssd_src = raw_input('1: Enter the path to the SSD source [%s]\n#>' % default_source).strip()
    ssd_src = ssd_src or default_source
    print 'SSD source set to: %s\n' % ssd_src

    # LOCAL DIRECTORY
    default_local_dir = '/opt'
    local_dir = raw_input('2: Enter the existing local directory location [%s]\n#>' % default_local_dir).strip()
    local_dir = local_dir or default_local_dir
    print 'Local directory set to: %s\n' % local_dir

    # APACHE UID
    apache_uid=raw_input('3: Enter the uid of the Apache user\n#>').strip()
    print 'Apache uid set to: %s\n' % apache_uid

    upgrade_text = """You have entered the following options:\n
            - SSD Source            : %s
            - Local Directory       : %s
            - Apache UID            : %s

         """ % (ssd_src,local_dir,apache_uid)

    print upgrade_text
    proceed=raw_input('Proceed with upgrade (y/n)\n#>').strip()

    if proceed == 'y':
        print 'proceeding...'
    else:
        print 'Exiting upgrade without modifying anything.'
        exit(0)

    # Write out the upgrade file for debugging issues later
    upgrade_file = open('upgrade.txt','w')
    upgrade_file.write(upgrade_text)
    upgrade_file.close() 

    # Determine the SSD source directory and path
    app_dir,ssd_src_dir = split_directories(ssd_src)

    # Create the generic ssd symlink
    ssd_symlink(app_dir,ssd_src)

    # Destination local directory
    dst_local = local_dir + '/ssd-local'

    # Add 'ssd' to the app dir for the remainder of this script
    app_dir = app_dir + 'ssd'

    # Setup the log directory and file
    create_log(app_dir,apache_uid)

    # Customize settings.tmpl to add the path to the local_settings.py file
    customize_settings(app_dir,dst_local)


### Main Program Execution ###


type=raw_input("""
**************************************
** SSD AUTOMATED INSTALL SCRIPT     **
**************************************

Before proceeding, please ensure that you have read the installation
documentation available at http://www.system-status-dashboard.com and that you understand
the installation options and expected answers.

During installation, default values will be displayed in [brackets], where available.  To select
default values, simply press enter.

Please select an install option:
1.  Install - install a new instance of SSD
2.  Upgrade - upgrade from an existing SSD installation

#>""").strip()



if type == "1":
    install()
elif type == "2":
    upgrade()
else:
    terminate('Incorrect option specified')

