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


"""This module contains all of the email configuration functions of SSD."""

import logging
from django.db import IntegrityError
from ssd.dashboard.decorators import staff_member_required_ssd
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseBadRequest
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.contrib import messages
from ssd.dashboard.models import Config_Email, Email, Event
from ssd.dashboard.forms import AddRecipientForm, DeleteRecipientForm, EmailConfigForm, XEditableModifyForm


# Get an instance of the ssd logger
logger = logging.getLogger(__name__)


@staff_member_required_ssd
def email_config(request):
    """Main admin index view

    """

    logger.debug('%s view being executed.' % 'email.email_config')

    # If this is a POST, then validate the form and save the data
    if request.method == 'POST':

        # Check the form elements
        form = EmailConfigForm(request.POST)
        logger.debug('Form submit (POST): %s, with result: %s' % ('EmailConfigForm',form))

        if form.is_valid():
            # Obtain the cleaned data
            enabled = form.cleaned_data['enabled']
            email_format = form.cleaned_data['email_format']
            from_address = form.cleaned_data['from_address']
            text_pager = form.cleaned_data['text_pager']
            incident_greeting = form.cleaned_data['incident_greeting']
            incident_update = form.cleaned_data['incident_update']
            maintenance_greeting = form.cleaned_data['maintenance_greeting']
            maintenance_update = form.cleaned_data['maintenance_update']
            email_footer = form.cleaned_data['email_footer']


            # There should only ever be one record in this table
            Config_Email.objects.filter(id=Config_Email.objects.values('id')[0]['id']).update(
                                                        enabled=enabled,
                                                        email_format=email_format,
                                                        from_address=from_address,
                                                        text_pager=text_pager,
                                                        incident_greeting=incident_greeting,
                                                        incident_update=incident_update,
                                                        maintenance_greeting=maintenance_greeting,
                                                        maintenance_update=maintenance_update,
                                                        email_footer=email_footer
                                                    )

            messages.add_message(request, messages.SUCCESS, 'Email configuration saved successfully')
        else:
            messages.add_message(request, messages.ERROR, 'Invalid data entered, please correct the errors below:')



    # Not a POST or a failed form submit
    else:
        # Create a blank form
        form = EmailConfigForm

    # Obtain the email config
    email_config = Config_Email.objects.filter(id=Config_Email.objects.values('id')[0]['id']).values(
                                                                                    'enabled',
                                                                                    'email_format',
                                                                                    'from_address',
                                                                                    'text_pager',
                                                                                    'incident_greeting',
                                                                                    'incident_update',
                                                                                    'maintenance_greeting',
                                                                                    'maintenance_update',
                                                                                    'email_footer'
                                                                                    )

    # Print the page
    return render_to_response(
       'email/config.html',
       {
          'title':'System Status Dashboard | Admin',
          'email_config':email_config,
          'form':form,
          'nav_section':'email',
          'nav_sub':'email_config'
       },
       context_instance=RequestContext(request)
    )


@staff_member_required_ssd
def email_recipients(request):
    """Manage Recipient Email Addresses

    """

    logger.debug('%s view being executed.' % 'email.email_recipients')

    # If this is a POST, then validate the form and save the data
    if request.method == 'POST':

        # Check the form elements
        form = AddRecipientForm(request.POST)
        logger.debug('Form submit (POST): %s, with result: %s' % ('AddRecipientForm',form))

        if form.is_valid():

            email = form.cleaned_data['email']

            # Don't allow duplicates
            try:
                Email(email=email).save()
            except IntegrityError:
                pass

            messages.add_message(request, messages.SUCCESS, 'Recipient saved successfully')

            # Send them back so they can see the newly created email addresses
            return HttpResponseRedirect('/admin/email_recipients')
        else:
            messages.add_message(request, messages.ERROR, 'Invalid data entered, please correct the errors below:')

    # Not a POST
    else:
        # Create a blank form
        form = AddRecipientForm()

    # Obtain all current email addresses
    emails = Email.objects.all()

    # Print the page
    return render_to_response(
       'email/email_recipients.html',
       {
          'title':'System Status Dashboard | Manage Email Recipients',
          'form':form,
          'emails':emails,
          'nav_section':'email',
          'nav_sub':'recipients'
       },
       context_instance=RequestContext(request)
    )


@staff_member_required_ssd
def recipient_delete(request):
    """Remove Email Recipients"""

    logger.debug('%s view being executed.' % 'email.recipient_delete')

    # If this is a POST, then validate the form and save the data, otherise send them
    # to the main recipients page
    if request.method == 'POST':

        # Check the form elements
        form = DeleteRecipientForm(request.POST)
        logger.debug('Form submit (POST): %s, with result: %s' % ('DeleteRecipientForm',form))

        if form.is_valid():

            # Remove the recipient
            id = form.cleaned_data['id']

            # If this recipient is currently tied to incidents or maintenances,
            # Do not allow it to be deleted w/o removing it from the relevant
            # events first
            if Event.objects.filter(event_email__email__id=id):

                # Set a message that the delete failed
                messages.add_message(request, messages.ERROR, 'The recipient you are attempting to delete is currently part of an incident or maintenance.  Please remove the recipient from the incident/maintenance, or delete the incident/maintenance and then delete the recipient.')

            # Ok, remove it
            else:
                Email.objects.filter(id=id).delete()

                # Set a message that delete was successful
                messages.add_message(request, messages.SUCCESS, 'Recipient successfully removed.')

            # Redirect to the email recipients page
            return HttpResponseRedirect('/admin/email_recipients')

    # If we get this far, it's a GET

    # Make sure we have an ID and we are confirming that the recipient should be removed
    form = DeleteRecipientForm(request.GET)
    logger.debug('Form submit (GET): %s, with result: %s' % ('DeleteRecipientForm',form))

    if form.is_valid():

        # Obtain the cleaned data
        id = form.cleaned_data['id']

        # Obtain the email
        email_name = Email.objects.filter(id=id).values('email')

        # If someone already deleted it, set an error message and send back to the email recipient listing
        if not email_name:
            messages.add_message(request, messages.ERROR, 'That email recipient has already been removed, perhaps someone else deleted it?')
            return HttpResponseRedirect('/admin/email_recipients')

        # Print the page (confirm they want to delete the recipient)
        return render_to_response(
           'email/recipient_delete.html',
           {
              'title':'System Status Dashboard | Confirm Delete',
              'id':id,
              'email_name':email_name,
              'nav_section':'email',
              'nav_sub':'recipient_delete'
           },
           context_instance=RequestContext(request)
        )

    # Invalid request
    else:

        # Set a message that the delete failed and send back to the services page
        messages.add_message(request, messages.ERROR, 'Invalid request.')
        return HttpResponseRedirect('/admin/email_recipients')


@staff_member_required_ssd
def recipient_modify(request):
    """Modify an email recipient
        - This occurs only via AJAX from the manage recipients view (it's a POST)

    """

    logger.debug('%s view being executed.' % 'email.recipient_modify')

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
            if not name == 'email':
                logger.error('Invalid column specified during recipient modification: %s' % name)
                return HttpResponseBadRequest('An error was encountered with this request.')

            filter = {}
            filter[name] = value

            # Make sure the email is value
            try:
                validate_email(value)
            except ValidationError:
                return HttpResponseBadRequest('Enter a valid email address.')

            # Update it
            try:
                Email.objects.filter(id=pk).update(**filter)
            except Exception as e:
                logger.error('%s: Error saving update: %s' % ('email.recipient_modify',e))
                return HttpResponseBadRequest('An error was encountered with this request.')

            return HttpResponse('Value successfully modified')

        else:
            logger.error('%s: invalid form: %s' % ('email.recipient_modify',form.errors))
            return HttpResponseBadRequest('Invalid request')
    else:
        logger.error('%s: Invalid request: GET received but only POST accepted.' % ('email.recipient_modify'))
        messages.add_message(request, messages.ERROR, 'Invalid request.')
        return HttpResponseRedirect('/admin/email_recipients')
