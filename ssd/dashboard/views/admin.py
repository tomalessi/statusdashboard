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


"""This module contains all of the admin functions of SSD."""


import logging
from django.conf import settings
from django.core.cache import cache, get_cache
from ssd.dashboard.decorators import staff_member_required_ssd
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.contrib import messages
from django import get_version
from ssd.dashboard.models import Config_Admin
from ssd.dashboard.forms import AdminConfigForm


# Get an instance of the ssd logger
logger = logging.getLogger(__name__)


@staff_member_required_ssd
def main(request):
    """Main admin index view
 
    """

    logger.debug('%s view being executed.' % 'admin.main')

    # Print the page
    return render_to_response(
       'admin/main.html',
       {
          'title':'System Status Dashboard | Admin',
          'django_version':get_version
       },
       context_instance=RequestContext(request)
    )


@staff_member_required_ssd
def cache_status(request):
    """Display cache settings
 
    """

    logger.debug('%s view being executed.' % 'admin.cache_status')

    m_stats = []

    # Table Headings, will look like this:
    # ['Statistic','Server1','Server2','Server3']
    headings = ['Statistic']
    # Table rows, will look like this:
    # {
    #   'auth_cmd':[2,3,4],
    #   'curr_connections':[7,3,2]
    # }
    rows = {}
    m_stats = [headings,rows]

    cache_settings = None
    # Note, headings and rows should have the same number of elements
    # or something is wrong
    if hasattr(settings, 'CACHES'):
        cache_settings = settings.CACHES
        try:
            for c in settings.CACHES:
                stats = get_cache(c)._cache.get_stats()
  
                for server_cache in stats:
                    server = server_cache[0]
                    current_stats = server_cache[1]

                    # Add the server to the headings
                    headings.append(server)

                    # Iterate over the stats and add to the rows dict
                    for key,value in current_stats.items():
                        # If the relevant list does not exist yet, create it
                        if not key in rows:
                            rows[key] = []

                        rows[key].append(value)

        except Exception as e:
            logger.error('Cannot obtain cache settings: %s' % e)
    else:
        logger.debug('No caches are defined.')


    # Print the page
    return render_to_response(
       'admin/cache.html',
       {
          'title':'System Status Dashboard | Admin - Cache',
          'cache_settings':cache_settings,
          'm_stats':m_stats,
          'nav_section':'admin',
          'nav_sub':'cache_status'
       },
       context_instance=RequestContext(request)
    )


@staff_member_required_ssd
def admin_config(request):
    """SSD Admin Configuration View
 
    """

    logger.debug('%s view being executed.' % 'admin.admin_config')

    # If this is a POST, then validate the form and save the data
    if request.method == 'POST':

        # Check the form elements
        form = AdminConfigForm(request.POST)
        logger.debug('Form submit (POST): %s, with result: %s' % ('AdminConfigForm',form))

        if form.is_valid():
            # Obtain the cleaned data
            link_enabled = form.cleaned_data['link_enabled']
        
            # There should only ever be one record in this table
            Config_Admin.objects.filter(id=Config_Admin.objects.values('id')[0]['id']).update(link_enabled=link_enabled)

            # Clear the cache
            cache.delete('display_admin')

            # Set a success message
            messages.add_message(request, messages.SUCCESS, 'Preferences saved successfully')
        else:
            messages.add_message(request, messages.ERROR, 'Invalid data entered, please correct the errors below:')

    # Not a POST or a failed form submit
    else:
        # Create a blank form
        form = AdminConfigForm

    # Obtain the email config

    admin_config = Config_Admin.objects.filter(id=Config_Admin.objects.values('id')[0]['id']).values('link_enabled')

    # Print the page
    return render_to_response(
       'admin/config.html',
       {
          'title':'System Status Dashboard | Admin Configuration',
          'admin_config':admin_config,
          'form':form,
          'nav_section':'admin',
          'nav_sub':'admin_config'
       },
       context_instance=RequestContext(request)
    )