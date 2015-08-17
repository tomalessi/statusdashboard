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


"""Context processor for SSD

   This context processor is responsible for setting the user desired
   display characteristics of the header (e.g. don't show the top nav)

"""


import logging
import pytz
from django.core.cache import cache
from ssd.dashboard.models import Config_Admin, Config_Logo, Config_Escalation, Config_Ireport
from django.conf import settings


# Get an instance of the ssd logger
logger = logging.getLogger(__name__)


def prefs(request):
    """Set the display characteristics"""

    # Hold the values we'll check in a dict
    values = {}

    # Application Version?
    # This is a constant from the settings file
    if hasattr(settings, 'APP_VERSION'):
        if not settings.APP_VERSION == False:
            values['app_version'] = settings.APP_VERSION
        else:
            values['app_version'] = False
    else:
        values['app_version'] = False

        
    # -- LOGO DISPLAY -- #
    display_logo = cache.get('display_logo')
    if display_logo == None:
        logger.debug('cache miss: %s' % 'display_logo')
        display_logo = Config_Logo.objects.filter(id=Config_Logo.objects.values('id')[0]['id']).values('logo_enabled')[0]['logo_enabled']
        cache.set('display_logo', display_logo)
    else:
        logger.debug('cache hit: %s' % 'display_logo')
    if display_logo == 1:
        # Yes, display it, what's the url
        logo_url = cache.get('logo_url')
        if logo_url == None:
            logo_url = Config_Logo.objects.filter(id=Config_Logo.objects.values('id')[0]['id']).values('url')[0]['url']
            cache.set('logo_url', logo_url)
        values['logo'] = logo_url
    else:
        values['logo'] = False
    # -- LOGO DISPLAY -- #


    # -- INCIDENT REPORT -- #
    enable_ireport = cache.get('enable_ireport')
    if enable_ireport == None:
        logger.debug('cache miss: %s' % 'enable_ireport')
        enable_ireport = Config_Ireport.objects.filter(id=Config_Ireport.objects.values('id')[0]['id']).values('enabled')[0]['enabled']
        cache.set('enable_ireport', enable_ireport)
    else:
        logger.debug('cache hit: %s' % 'enable_ireport')
    if enable_ireport == 1:    
        values['ireport'] = True
    else:
        values['ireport'] = False
    # -- INCIDENT REPORT DISPLAY -- #


    # -- ESCALATION PATH --#
    enable_escalation = cache.get('enable_escalation')
    if enable_escalation == None:
        logger.debug('cache miss: %s' % 'enable_escalation')
        enable_escalation = Config_Escalation.objects.filter(id=Config_Escalation.objects.values('id')[0]['id']).values('enabled')[0]['enabled']
        cache.set('enable_escalation', enable_escalation)
    else:
        logger.debug('cache hit: %s' % 'enable_escalation')
    if enable_escalation == 1:
        values['escalation'] = True
    else:
        values['escalation'] = False
    # -- ESCALATION PATH --#


    # -- ADMIN LINK --#
    display_admin = cache.get('display_admin')
    if display_admin == None:
        logger.debug('cache miss: %s' % 'display_admin')
        display_admin = Config_Admin.objects.filter(id=Config_Admin.objects.values('id')[0]['id']).values('link_enabled')[0]['link_enabled']
        setit = cache.set('display_admin', display_admin)
    else:
        logger.debug('cache hit: %s' % 'display_admin')
    if display_admin == 1:
        values['admin_link'] = True
    else:
        values['admin_link'] = False
    # -- ADMIN LINK --#


    # Return values to the template
    return values


def timezones(request):
    """Populate the timezones in the footer timezone picker"""

    # Obtain all timezones
    timezones = pytz.all_timezones

    return {'timezones': timezones}
