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


"""This module contains all of the system messages configuration functions of SSD."""


import logging
from ssd.dashboard.decorators import staff_member_required_ssd
from django.shortcuts import render_to_response
from django.core.cache import cache
from django.template import RequestContext
from django.http import HttpResponseRedirect
from django.contrib import messages
from ssd.dashboard.models import Config_Message
from ssd.dashboard.forms import MessagesConfigForm


# Get an instance of the ssd logger
logger = logging.getLogger(__name__)


@staff_member_required_ssd
def messages_config(request):
    """Main messages view

    """

    logger.debug('%s view being executed.' % 'messages.messages_config')

    # If this is a POST, then validate the form and save the data
    if request.method == 'POST':

        # Check the form elements
        form = MessagesConfigForm(request.POST)
        logger.debug('Form submit (POST): %s, with result: %s' % ('MessagesConfigForm',form))

        if form.is_valid():
            # Obtain the cleaned data
            main = form.cleaned_data['main']
            main_enabled = form.cleaned_data['main_enabled']
            alert = form.cleaned_data['alert']
            alert_enabled = form.cleaned_data['alert_enabled']


            # There should only ever be one record in this table
            Config_Message.objects.filter(id=Config_Message.objects.values('id')[0]['id']).update(
                                                        main=main,
                                                        main_enabled=main_enabled,
                                                        alert=alert,
                                                        alert_enabled=alert_enabled
                                                    )

            # Clear the cache
            cache.delete('alerts')

            # Set a success message
            messages.add_message(request, messages.SUCCESS, 'Preferences saved successfully')
        else:
            messages.add_message(request, messages.ERROR, 'Invalid data entered, please correct the errors below:')



    # Not a POST or a failed form submit
    else:
        # Create a blank form
        form = MessagesConfigForm

    # Obtain the email config
    messages_config = Config_Message.objects.filter(id=Config_Message.objects.values('id')[0]['id']).values(
                                                                                    'main',
                                                                                    'main_enabled',
                                                                                    'alert',
                                                                                    'alert_enabled'
                                                                                    )

    # Print the page
    return render_to_response(
       'messages/config.html',
       {
          'title':'System Status Dashboard | Messages Configuration',
          'messages_config':messages_config,
          'form':form,
          'nav_section':'messages',
          'nav_sub':'messages_config'
       },
       context_instance=RequestContext(request)
    )