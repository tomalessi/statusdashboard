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


"""This module contains all of the service configuration functions of SSD."""


import logging
from django.db import IntegrityError
from django.core.cache import cache
from ssd.dashboard.decorators import staff_member_required_ssd
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseBadRequest
from django.contrib import messages
from ssd.dashboard.models import Service, Event_Service
from ssd.dashboard.forms import AddServiceForm, RemoveServiceForm, XEditableModifyForm


# Get an instance of the ssd logger
logger = logging.getLogger(__name__)


@staff_member_required_ssd
def services(request):
    """View and Add Services
 
    """

    logger.debug('%s view being executed.' % 'services.services')

    # If this is a POST, then validate the form and save the data
    if request.method == 'POST':
       
        # Check the form elements
        form = AddServiceForm(request.POST)
        logger.debug('Form submit (POST): %s, with result: %s' % ('AddServiceForm',form))

        if form.is_valid():
            service = form.cleaned_data['service']

            # Don't allow duplicates
            try:
                Service(service_name=service).save()
            except IntegrityError:
                messages.add_message(request, messages.ERROR, 'That service name already exists.')
                pass
            else:
                messages.add_message(request, messages.SUCCESS, 'Service saved successfully.')

            # Clear the cache so the new services show up in the dashboard immediately
            cache.delete('services')

            # Send them back so they can see the newly created service
            return HttpResponseRedirect('/admin/services')

        else:
            messages.add_message(request, messages.ERROR, 'Invalid data entered, please correct the errors below:')

    # Not a POST
    else:
        # Create a blank form
        form = AddServiceForm()
    
    # Obtain all current email addresses
    services = Service.objects.values('id','service_name')
    
    # Print the page
    return render_to_response(
       'services/services.html',
       {
          'title':'System Status Dashboard | Manage Services',
          'form':form,
          'services':services,
          'nav_section':'services',
          'nav_sub':'services'
       },
       context_instance=RequestContext(request)
    )


@staff_member_required_ssd
def service_delete(request):
    """Remove Service"""

    logger.debug('%s view being executed.' % 'services.service_delete')

    # If it's a POST, then we are going to delete it after confirmation
    if request.method == 'POST':
        
        # Check the form elements
        form = RemoveServiceForm(request.POST)
        logger.debug('Form submit (POST): %s, with result: %s' % ('RemoveServiceForm',form))

        if form.is_valid():
            id = form.cleaned_data['id']
            # Remove the service
            
            # If this service is currently tied to incidents or maintenances,
            # Do not allow them to be deleted w/o removing them from the relevant
            # services first

            # Part of any incidents or maintenances?
            if Event_Service.objects.filter(service_id=id):

                # Set a message that the delete failed
                messages.add_message(request, messages.ERROR, 'The service you are attempting to delete is currently part of an event.  Please remove the service from the event, or delete the event and then delete the service.')

            # Ok, remove it
            else:
                Service.objects.filter(id=id).delete()

                # Clear the cache so the modified service listing shows up in the dashboard immediately
                cache.delete('services')

                # Set a message that delete was successful
                messages.add_message(request, messages.SUCCESS, 'Service successfully removed.')

            # Redirect to the services page
            return HttpResponseRedirect('/admin/services')

    # If we get this far, it's a GET and we are confirming that the service should be removed.

    # Make sure we have an ID
    form = RemoveServiceForm(request.GET)
    logger.debug('Form submit (GET): %s, with result: %s' % ('RemoveServiceForm',form))

    if form.is_valid():

        # Obtain the cleaned data
        id = form.cleaned_data['id']

        # Obtain the service name
        service_name = Service.objects.filter(id=id).values('service_name')

        # If someone already deleted it, set an error message and send back to the services listing
        if not service_name:
            messages.add_message(request, messages.ERROR, 'That service has already been removed, perhaps someone else deleted it?')
            return HttpResponseRedirect('/admin/services')

        # Print the page (confirm they want to delete the service)
        return render_to_response(
           'services/service_delete.html',
           {
              'title':'System Status Dashboard | Confirm Delete',
              'id':id,
              'service_name':service_name,
              'nav_section':'services',
              'nav_sub':'service_delete'
           },
           context_instance=RequestContext(request)
        )

    # Invalid request
    else:

        # Set a message that the delete failed and send back to the services page
        messages.add_message(request, messages.ERROR, 'Invalid request.')
        return HttpResponseRedirect('/admin/services')
  

@staff_member_required_ssd
def service_modify(request):
    """Modify the name of Services
        - This occurs only via AJAX from the services view (it's a POST)

    """

    logger.debug('%s view being executed.' % 'services.service_modify')

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
            if not name == 'service_name':
                logger.error('Invalid column specified during service modification: %s' % name)
                return HttpResponseBadRequest('An error was encountered with this request.')

            filter = {}
            filter[name] = value

            # Update it
            try:
                Service.objects.filter(id=pk).update(**filter)
            except Exception as e:
                logger.error('%s: Error saving update: %s' % ('services.service_modify',e))
                return HttpResponseBadRequest('An error was encountered with this request.')

            # Clear the cache so the modified service listing shows up in the dashboard immediately
            cache.delete('services')

            return HttpResponse('Value successfully modified')

        else:
            logger.error('%s: invalid form: %s' % ('services.service_modify',form.errors))
            return HttpResponseBadRequest('Invalid request')
    else:
        logger.error('%s: Invalid request: GET received but only POST accepted.' % ('services.service_modify'))
        messages.add_message(request, messages.ERROR, 'Invalid request.')
        return HttpResponseRedirect('/admin/services')     
    
