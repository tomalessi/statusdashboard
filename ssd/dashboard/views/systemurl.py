#
# Copyright 2015 - Tom Alessi
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


"""This module contains all of the system url configuration functions of SSD."""


import logging
from ssd.dashboard.decorators import staff_member_required_ssd
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.http import HttpResponseRedirect
from django.contrib import messages
from ssd.dashboard.models import Config_Systemurl
from ssd.dashboard.forms import SystemurlConfigForm


# Get an instance of the ssd logger
logger = logging.getLogger(__name__)


@staff_member_required_ssd
def systemurl_config(request):
    """Main system url view

    """

    logger.debug('%s view being executed.' % 'systemurl.systemurl_config')

    # If this is a POST, then validate the form and save the data
    if request.method == 'POST':

        # Check the form elements
        form = SystemurlConfigForm(request.POST)
        logger.debug('Form submit (POST): %s, with result: %s' % ('SystemurlConfigForm',form))

        if form.is_valid():
            # Obtain the cleaned data
            url = form.cleaned_data['url']
            url_enabled = form.cleaned_data['url_enabled']

            # There should only ever be one record in this table
            Config_Systemurl.objects.filter(id=Config_Systemurl.objects.values('id')[0]['id']).update(url=url,url_enabled=url_enabled)

            messages.add_message(request, messages.SUCCESS, 'Preferences saved successfully')
        else:
            messages.add_message(request, messages.ERROR, 'Invalid data entered, please correct the errors below:')

    # Not a POST or a failed form submit
    else:
        # Create a blank form
        form = SystemurlConfigForm

    # Obtain the email config

    systemurl_config = Config_Systemurl.objects.filter(id=Config_Systemurl.objects.values('id')[0]['id']).values('url','url_enabled')

    # Print the page
    return render_to_response(
       'systemurl/config.html',
       {
          'title':'System Status Dashboard | System Url Configuration',
          'systemurl_config':systemurl_config,
          'form':form,
          'nav_section':'systemurl',
          'nav_sub':'systemurl_config'
       },
       context_instance=RequestContext(request)
    )