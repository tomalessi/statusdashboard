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


"""SSD Local Configuration File

   Required Configuration
    - Database username
    - Database password
      (note: database host/port can be ignored if its local and using the standard port)
    - Secret key
    - Full path to template directory
   
"""


DATABASES = {
    'default': {
        'ENGINE'   : 'django.db.backends.mysql',
        'NAME'     : 'ssd',
        'USER'     : '$__db_user__$',    
        'PASSWORD' : '$__db_pass__$', 
        'HOST'     : '$__db_host__$', 
    }
}
SECRET_KEY = '$__secret_key__$'
TEMPLATE_DIRS = ( 
    '$__app_dir__$/templates',
)

# Set the timezone to match the server's timezone
# TIME_ZONE = 'US/Pacific'



# -- MEMCACHED CONFIGURATION  -- #
# Uncomment and set the location to your server(s) and port(s)
# Do not change the KEY_PREFIX
"""
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.memcached.MemcachedCache',
        'LOCATION': [
            'localhost:11211'
        ],
        'TIMEOUT': 300,
        'KEY_PREFIX':'ssd'

    }
}
"""

# -- SESSION CACHE
# If you have memcache installed/configured, then you can use a write-through cache
# to store session information.  If you'd rather not use the write-through cache and
# just want to use memcache then set SESSION_ENGINE to 'django.contrib.sessions.backends.cache'
# Keep in mind that sessions could be evicted or you could lose your session store if memcached
# is restarted.
# SESSION_ENGINE = 'django.contrib.sessions.backends.cached_db'
