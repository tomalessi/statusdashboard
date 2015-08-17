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


"""This module contains all of the user preference setting functions of SSD."""


import logging
from django.http import HttpResponseRedirect
from django.contrib import messages
from ssd.dashboard.forms import JumpToForm, UpdateTZForm


# Get an instance of the ssd logger
logger = logging.getLogger(__name__)


def set_timezone(request):
    """Process a form submit to set the timezone

    Supported timezones are from pytz

    """

    logger.debug('%s view being executed.' % 'prefs.set_timezone')

    if request.method == 'POST':
        # Check the form elements
        form = UpdateTZForm(request.POST)
        logger.debug('Form submit (POST): %s, with result: %s' % ('UpdateTZForm',form))

        if form.is_valid():
            # Obtain the cleaned data
            tz_pref = form.cleaned_data['tz_pref']

            # Set the timezone in a cookie and redirect
            # If the referer is set, use that, otherwise the homepage
            if 'HTTP_REFERER' in request.META:
                response = HttpResponseRedirect(request.META['HTTP_REFERER'])
            else:
                response = HttpResponseRedirect('/')

            # Set the cookie
            response.set_cookie('tz_pref',
                                tz_pref,
                                max_age=157680000,
                                expires=157680000,
                                path='/',
                                domain=None,
                                secure=None,
                                httponly=False)

            # Set a success message
            messages.add_message(request, messages.SUCCESS, 'Timezone successfully updated.')

            # Return the response
            return response

        else:
            messages.add_message(request, messages.ERROR, 'Invalid request, cannot update timezone.')

    # Not a POST 
    else:
        messages.add_message(request, messages.ERROR, 'Invalid request, cannot update timezone.')


    # Redirect them to the homepage.
    return HttpResponseRedirect('/')


def jump(request):
    """Process a form submit to jump to a specific date

    Any date can be processed

    """

    logger.debug('%s view being executed.' % 'prefs.jump')

    if request.method == 'POST':
        # Check the form elements
        form = JumpToForm(request.POST)
        logger.debug('Form submit (POST): %s, with result: %s' % ('JumpToForm',form))

        if form.is_valid():
            # Obtain the cleaned data
            jump_to = form.cleaned_data['jump_to']

            # Send to the specified date
            return HttpResponseRedirect('/?ref=%s' % jump_to)
        else:
            messages.add_message(request, messages.ERROR, 'Invalid request, cannot jump to date.')
    else:
        messages.add_message(request, messages.ERROR, 'Invalid request, cannot jump to date.')

    # Either its not a POST, or the form was not valid
    # Redirect to the homepage and they'll get the standard view
    return HttpResponseRedirect('/')
