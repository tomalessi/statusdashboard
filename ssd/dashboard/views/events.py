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


"""This module contains all of the generic event functions of SSD."""


import logging
from django.core.cache import cache
from django.contrib.auth.models import User
from ssd.dashboard.decorators import staff_member_required_ssd
from django.contrib import messages
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseBadRequest
from ssd.dashboard.models import Event_Update
from ssd.dashboard.forms import XEditableModifyForm


# Get an instance of the ssd logger
logger = logging.getLogger(__name__)


@staff_member_required_ssd
def update_modify(request):
    """Modify event update
        - This occurs only via AJAX from the i_update or m_update views (it's a POST)

    """

    logger.debug('%s view being executed.' % 'events.update_modify')

    # If this is a POST, then validate the form and save the data, otherise do nothing
    if request.method == 'POST':
        
        # Check the form elements
        form = XEditableModifyForm(request.POST)
        logger.debug('Form submit (POST): %s, with result: %s' % ('XEditableModifyForm',form))

        if form.is_valid():
            pk = form.cleaned_data['pk']
            name = form.cleaned_data['name']
            value = form.cleaned_data['value']

            # Add the column we are updating (but only allow specific values)
            if not name == 'update':
                logger.error('Invalid column specified during event update modification: %s' % name)
                return HttpResponseBadRequest('An error was encountered with this request.')

            filter = {}
            filter[name] = value

            # Add the user who is performing this update
            filter['user'] = User.objects.filter(username=request.user.username).values('id')[0]['id']

            # Update it
            try:
                Event_Update.objects.filter(id=pk).update(**filter)
            except Exception as e:
                logger.error('%s: Error saving update: %s' % ('events.update_modify',e))
                return HttpResponseBadRequest('An error was encountered with this request.')

            # Clear the cache 
            cache.delete('timeline')

            return HttpResponse('Value successfully modified')

        else:
            logger.error('%s: invalid form: %s' % ('events.update_modify',form.errors))
            return HttpResponseBadRequest('Invalid request')
    else:
        logger.error('%s: Invalid request: GET received but only POST accepted.' % ('events.update_modify'))
        messages.add_message(request, messages.ERROR, 'Invalid request.')
        return HttpResponseRedirect('/admin') 