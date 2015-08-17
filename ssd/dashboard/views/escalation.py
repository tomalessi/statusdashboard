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


"""This module contains all of the escalation functions of SSD."""


import logging
from django.core.cache import cache
from django.db import IntegrityError
from ssd.dashboard.decorators import staff_member_required_ssd
from django.shortcuts import render_to_response
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseBadRequest
from django.template import RequestContext
from django.db.models import F
from django.contrib import messages
from ssd.dashboard.models import Config_Escalation, Escalation
from ssd.dashboard.forms import AddContactForm, EscalationConfigForm, XEditableModifyForm, SwitchContactForm, RemoveContactForm


# Get an instance of the ssd logger
logger = logging.getLogger(__name__)


def escalation(request):
    """Escalation page

    Print an escalation page should a user want additional information
    on who to contact when incidents occur

    """

    logger.debug('%s view being executed.' % 'escalation.escalation')

    # If this functionality is disabled in the admin, let the user know
    enable_escalation = cache.get('enable_escalation')
    if enable_escalation == None:
        enable_escalation = Config_Escalation.objects.filter(id=Config_Escalation.objects.values('id')[0]['id']).values('enabled')[0]['enabled']
        cache.set('enable_escalation', enable_escalation)
    if enable_escalation == 0:
        # Escalation is disabled, send them to the homepage with an error message
        messages.add_message(request, messages.ERROR, 'Your system administrator has disabled the escalation path functionality')
        return HttpResponseRedirect('/')

    # Obtain the escalation contacts
    contacts = Escalation.objects.filter(hidden=False).values('id','name','contact_details').order_by('order')

    # Print the page
    return render_to_response(
       'escalation/escalation.html',
       {
          'title':'System Status Dashboard | Escalation Path',
          'contacts':contacts,
          'instructions':Config_Escalation.objects.filter(id=Config_Escalation.objects.values('id')[0]['id']).values('instructions')[0]['instructions']
       },
       context_instance=RequestContext(request)
    )


@staff_member_required_ssd
def escalation_config(request):
    """Main admin index view
 
    """

    logger.debug('%s view being executed.' % 'escalation.escalation_config')

    # If this is a POST, then validate the form and save the data
    if request.method == 'POST':

        # Check the form elements
        form = EscalationConfigForm(request.POST)
        logger.debug('Form submit (POST): %s, with result: %s' % ('EscalationConfigForm',form))

        if form.is_valid():
            # Obtain the cleaned data
            enabled = form.cleaned_data['enabled']
            instructions = form.cleaned_data['instructions']

            # There should only ever be one record in this table
            Config_Escalation.objects.filter(id=Config_Escalation.objects.values('id')[0]['id']).update(enabled=enabled,instructions=instructions)

            # Clear the cache
            cache.delete('enable_escalation')

            # Set a success message
            messages.add_message(request, messages.SUCCESS, 'Escalation configuration saved successfully')
        else:
            messages.add_message(request, messages.ERROR, 'Invalid data entered, please correct the errors below:')


    # Not a POST or a failed form submit
    else:
        # Create a blank form
        form = EscalationConfigForm

    # Obtain the escalation config
    escalation_config = Config_Escalation.objects.filter(id=Config_Escalation.objects.values('id')[0]['id']).values('enabled','instructions')

    # Print the page
    return render_to_response(
       'escalation/config.html',
       {
          'title':'System Status Dashboard | Escalation Admin',
          'escalation_config':escalation_config,
          'form':form,
          'nav_section':'escalation',
          'nav_sub':'escalation_config'
       },
       context_instance=RequestContext(request)
    )


@staff_member_required_ssd
def escalation_contacts(request):
    """View and Add Escalation Contacts
 
    """

    logger.debug('%s view being executed.' % 'escalation.escalation_contacts')

    # If this is a POST, then validate the form and save the data
    if request.method == 'POST':
       
        # Check the form elements
        form = AddContactForm(request.POST)
        logger.debug('Form submit (POST): %s, with result: %s' % ('AddContactForm',form))

        if form.is_valid():
            name = form.cleaned_data['name']
            contact_details = form.cleaned_data['contact_details']

            # Obtain the last entry
            order = Escalation.objects.values('order').order_by('-order')[:1]
            
            # If there are no entries, this will be 1
            if not order:
                order = 1
            # Increase the order by 1
            else:
                order = order[0]['order'] + 1

            # Don't allow duplicates
            try:
                Escalation(order=order,name=name,contact_details=contact_details,hidden=True).save()
            except IntegrityError:
                pass

            # Send them back so they can see the newly created email addresses
            # incident
            return HttpResponseRedirect('/admin/escalation_contacts')

        # Invalid form
        else:
            print 'Invalid form: AddContactForm: %s' % form.errors

    # Not a POST
    else:
        # Create a blank form
        form = AddContactForm()
    
    # Obtain all current email addresses
    contacts = Escalation.objects.values('id','order','name','contact_details','hidden').order_by('order')
   
    # Print the page
    return render_to_response(
       'escalation/contacts.html',
       {
          'title':'System Status Dashboard | Manage Escalation Contacts',
          'form':form,
          'contacts':contacts,
          'nav_section':'escalation',
          'nav_sub':'escalation_contacts'
       },
       context_instance=RequestContext(request)
    )


@staff_member_required_ssd
def contact_switch(request):
    """Switch Contacts Around or Hide Them"""

    logger.debug('%s view being executed.' % 'escalation.contact_switch')

    # If this is a GET, then validate the form and save the data, otherise send them
    # to the main escalation page
    if request.method == 'GET':
        
        # Check the form elements
        form = SwitchContactForm(request.GET)
        logger.debug('Form submit (GET): %s, with result: %s' % ('SwitchContactForm',form))

        if form.is_valid():
            id = form.cleaned_data['id']
            action = form.cleaned_data['action']    

            # Obtain all id's and orders and put into a dictionary
            orders = Escalation.objects.values('id','order').order_by('order')
            
            # Run through the orders and see if we need to change anything
            # If we are moving up, switch places with the previous
            # If we are moving down, switch places with the next
            # If we are hiding, remove the order
            # If we are unhiding, add to the end

            
            # Move this up, meaning decrease the order (only if greater than 1)
            if action == 'up':

                # Get the order
                id_order = Escalation.objects.filter(id=id).values('order')[0]['order']
                
                # If the order if greater than 1, move it
                if id_order > 1:
                    
                    # Get the id of the one before this one so we can switch places with it
                    after_order = id_order - 1
                    after_id = Escalation.objects.filter(order=after_order).values('id')[0]['id']

                    # Switch places
                    Escalation.objects.filter(id=id).update(order=F('order')-1)
                    Escalation.objects.filter(id=after_id).update(order=F('order')+1)

                # Set a success message
                messages.add_message(request, messages.SUCCESS, 'Escalation contacts successfully modified.')
            
            # Move this down, meaning increase the order
            elif action == "down": 

                # Get the order
                id_order = Escalation.objects.filter(id=id).values('order')[0]['order']

                # If it's already at the bottom, don't do anything
                # Get a count of contacts
                contacts_count = Escalation.objects.count()
                
                # If the order is less than the total, move it down (otherwise it's already at the bottom)
                if id_order < contacts_count:
                    
                    # Get the id of the one after this one so we can switch places with it
                    after_order = id_order + 1
                    after_id = Escalation.objects.filter(order=after_order).values('id')[0]['id']

                    # Switch places
                    Escalation.objects.filter(id=id).update(order=F('order')+1)
                    Escalation.objects.filter(id=after_id).update(order=F('order')-1)

                # Set a success message
                messages.add_message(request, messages.SUCCESS, 'Escalation contacts successfully modified.')

            # Hide
            elif action == 'hide':
                Escalation.objects.filter(id=id).update(hidden=True)
                # Set a success message
                messages.add_message(request, messages.SUCCESS, 'Escalation contacts successfully modified.')

            # Show
            elif action == 'show':
                Escalation.objects.filter(id=id).update(hidden=False)
                # Set a success message
                messages.add_message(request, messages.SUCCESS, 'Escalation contacts successfully modified.')

            # Unknown request
            else:
                # Set an error message
                messages.add_message(request, messages.ERROR, 'Unknown request type - contact not modified.')

        # Invalid form
        else:
            messages.add_message(request, messages.ERROR, 'There was an error processing your request: %s' % form.errors)

    # Send them back so they can see the newly updated services list
    return HttpResponseRedirect('/admin/escalation_contacts')


@staff_member_required_ssd
def contact_delete(request):
    """Remove Contact"""

    logger.debug('%s view being executed.' % 'escalation.contact_delete')

    # If it's a POST, then we are going to delete it after confirmation
    if request.method == 'POST':
        
        # Check the form elements
        form = RemoveContactForm(request.POST)
        logger.debug('Form submit (POST): %s, with result: %s' % ('RemoveContactForm',form))

        if form.is_valid():
            id = form.cleaned_data['id']

            # Delete the contact and then re-order what's left (if there's more than 1)
            Escalation.objects.filter(id=id).delete()

            # Get the orders
            orders = Escalation.objects.values('id','order').order_by('order')

            # If there's more than 1, re-order
            if orders > 1:
                # Start a counter at 1 and reset the orders
                counter = 1
                for contact in orders:
                    Escalation.objects.filter(id=contact['id']).update(order=counter)
                    counter += 1
            # There is only 1 so set it's order to 1
            else:
                Escalation.objects.filter(id=id).update(order=1)

            # Set a message that delete was successful
            messages.add_message(request, messages.SUCCESS, 'Contact successfully removed.')

            # Redirect to the escalation contacts page
            return HttpResponseRedirect('/admin/escalation_contacts')

    # If we get this far, it's a GET and we are confirming that the contact should be removed.

    # Make sure we have an ID
    form = RemoveContactForm(request.GET)
    logger.debug('Form submit (GET): %s, with result: %s' % ('RemoveContactForm',form))
    
    if form.is_valid():

        # Obtain the cleaned data
        id = form.cleaned_data['id']

        # Obtain the contact name
        contact_name = Escalation.objects.filter(id=id).values('name')

        # If someone already deleted it, set an error message and send back to the services listing
        if not contact_name:
            messages.add_message(request, messages.ERROR, 'That contact has already been removed, perhaps someone else deleted it?')
            return HttpResponseRedirect('/admin/escalation_contacts')

        # Print the page (confirm they want to delete the service)
        return render_to_response(
           'escalation/contact_delete.html',
           {
              'title':'System Status Dashboard | Confirm Delete',
              'id':id,
              'contact_name':contact_name,
              'nav_section':'escalation',
              'nav_sub':'contact_delete'
           },
           context_instance=RequestContext(request)
        )

    # Invalid request
    else:

        # Set a message that the delete failed and send back to the services page
        messages.add_message(request, messages.ERROR, 'Invalid request.')
        return HttpResponseRedirect('/admin/escalation_contacts')


@staff_member_required_ssd
def contact_modify(request):
    """Modify contact properties
        - This occurs only via AJAX from the escalation_contacts view (it's a POST)

    """

    logger.debug('%s view being executed.' % 'escalation.contact_modify')

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
            if name == 'name' or name == 'contact_details':
                pass
            else:
                logger.error('Invalid column specified during contact modification: %s' % name)
                return HttpResponseBadRequest('An error was encountered with this request.')

            filter = {}
            filter[name] = value

            # Update it
            try:
                Escalation.objects.filter(id=pk).update(**filter)
            except Exception as e:
                logger.error('%s: Error saving update: %s' % ('escalation.contact_modify',e))
                return HttpResponseBadRequest('An error was encountered with this request.')

            return HttpResponse('Value successfully modified')

        else:
            logger.error('%s: invalid form: %s' % ('escalation.contact_modify',form.errors))
            return HttpResponseBadRequest('Invalid request')
    else:
        logger.error('%s: Invalid request: GET received but only POST accepted.' % ('escalation.contact_modify'))
        messages.add_message(request, messages.ERROR, 'Invalid request.')
        return HttpResponseRedirect('/admin/escalation_contacts') 


