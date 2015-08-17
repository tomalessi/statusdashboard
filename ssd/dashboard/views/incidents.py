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


"""This module contains all of the incident specific functions of SSD."""


import logging
import datetime
import pytz
import re
from django.conf import settings
from django.core.cache import cache
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.http import HttpResponseRedirect
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.contrib import messages
from django.contrib.auth.models import User
from ssd.dashboard.decorators import staff_member_required_ssd
from ssd.dashboard.models import Event, Type, Status, Event_Service, Event_Update, Event_Email, Event_Impact, Event_Coordinator, Service, Email, Config_Email
from ssd.dashboard.forms import DeleteUpdateForm, AddIncidentForm, DeleteEventForm, UpdateIncidentForm, DetailForm, ListForm
from ssd.dashboard import notify


# Get an instance of the ssd logger
logger = logging.getLogger(__name__)


@staff_member_required_ssd
def incident(request):
    """Create Incident Page

    Create a new incident

    """

    logger.debug('%s view being executed.' % 'incidents.incident')


    # If this is a POST, then validate the form and save the data
    # Some validation must take place manually
    if request.method == 'POST':

        # If this is a form submit that fails, we want to reset whatever services were selected
        # by the user.  Templates do not allow access to Arrays stored in QueryDict objects so we have
        # to determine the list and send back to the template on failed form submits
        affected_svcs = request.POST.getlist('service')

        # Check the form elements
        form = AddIncidentForm(request.POST)
        logger.debug('Form submit (POST): %s, with result: %s' % ('AddIncidentForm',form))

        if form.is_valid():
            # Obtain the cleaned data
            s_date = form.cleaned_data['s_date']
            s_time = form.cleaned_data['s_time']
            e_date = form.cleaned_data['e_date']
            e_time = form.cleaned_data['e_time']
            description = form.cleaned_data['description']
            broadcast = form.cleaned_data['broadcast']
            email_id = form.cleaned_data['email_id']

            # Combine the dates and times into datetime objects and set the timezones
            tz = pytz.timezone(request.timezone)
            start = datetime.datetime.combine(s_date, s_time)
            start = tz.localize(start)
            if e_date and e_time:
                end = datetime.datetime.combine(e_date, e_time)
                end = tz.localize(end)
                # If there is an end date, the status is now closed
                status = 'closed'
            else:
                end = None
                # Status is still open
                status='open'

            # Create the event and obtain the ID                                     
            e = Event.objects.create(
                                     type_id=Type.objects.filter(type='incident').values('id')[0]['id'],
                                     description=description,
                                     status_id=Status.objects.filter(status=status).values('id')[0]['id'],
                                     start=start,
                                     end=end,
                                     user_id=request.user.id
                                    )
            event_id = e.pk

            # Add the email recipient, if requested.
            # Form validation ensures that a valid email is selected if broadcast is selected.  
            if broadcast: 
                Event_Email(event_id=event_id,email_id=email_id).save()

            # Find out which services this impacts and associate the services with the event
            # Form validation confirms that there is at least 1 service
            for service_id in affected_svcs:
                # Should be number only -- can't figure out how to validate
                # multiple checkboxes in the form
                if re.match(r'^\d+$', service_id):
                    Event_Service(service_id=service_id,event_id=event_id).save()


            # Send an email notification to the appropriate list about this issue if requested.  Broadcast won't be
            # allowed to be true if an email address is not defined or if global email is disabled.
            if Config_Email.objects.filter(id=Config_Email.objects.values('id')[0]['id']).values('enabled')[0]['enabled'] == 1 and broadcast:
                email = notify.email()
                email.email_event(event_id,email_id,request.timezone,True)

            # Clear the cache - don't discriminate and just clear everything that impacts events
            cache.delete_many(['timeline','events_ns','event_count_ns'])
            
            # Set a success message
            messages.add_message(request, messages.SUCCESS, 'Incident successfully created.')

            # Send them to the incident detail page for this newly created
            # incident
            return HttpResponseRedirect('/i_detail?id=%s' % event_id)

        else:
            messages.add_message(request, messages.ERROR, 'Invalid data entered, please correct the errors below:')

    # Not a POST so create a blank form
    else:
        # There are no affected services selected yet
        affected_svcs = []

        # Create a blank form
        form = AddIncidentForm()

    # Obtain all services
    services = Service.objects.values('id','service_name').order_by('service_name')

    # Obtain all current email addresses for the selector
    emails = Email.objects.values('id','email')

    # Print the page
    return render_to_response(
       'incidents/incident.html',
       {
          'title':'System Status Dashboard | Create Incident',
          'services':services,
          'emails':emails,
          'affected_svcs':tuple(affected_svcs),
          'form':form,
          'email_enabled':Config_Email.objects.filter(id=Config_Email.objects.values('id')[0]['id']).values('enabled')[0]['enabled'],
          'nav_section':'event',
          'nav_sub':'incident'

       },
       context_instance=RequestContext(request)
    )


@staff_member_required_ssd
def i_update(request):
    """Update Incident Page

    Update an incident

    """

    logger.debug('%s view being executed.' % 'incidents.i_update')

    # If this is a POST, then validate the form and save the data
    # Some validation must take place manually (service
    # addition/subtraction
    if request.method == 'POST':

        # If this is a form submit that fails, we want to reset whatever services were selected
        # by the user.  Templates do not allow access to Arrays stored in QueryDict objects so we have
        # to determine the list and send back to the template on failed form submits
        affected_svcs = request.POST.getlist('service')

        # Check the form elements
        form = UpdateIncidentForm(request.POST)
        logger.debug('Form submit (POST): %s, with result: %s' % ('UpdateIncidentForm',form))

        if form.is_valid():

            # Obtain the cleaned data
            id = form.cleaned_data['id']
            description = form.cleaned_data['description']
            s_date = form.cleaned_data['s_date']
            s_time = form.cleaned_data['s_time']
            e_date = form.cleaned_data['e_date']
            e_time = form.cleaned_data['e_time']
            update = form.cleaned_data['update']
            broadcast = form.cleaned_data['broadcast']
            email_id = form.cleaned_data['email_id']

            # Combine the dates and times into datetime objects and set the timezones
            tz = pytz.timezone(request.timezone)
            start = datetime.datetime.combine(s_date, s_time)
            start = tz.localize(start)
            if e_date and e_time:
                end = datetime.datetime.combine(e_date, e_time)
                end = tz.localize(end)
                # If there is an end date, the status is now closed
                status = 'closed'
            else:
                end = None
                # Status is still open
                status='open'

            # Update the event                                     
            Event.objects.filter(id=id).update(
                                     description=description,
                                     status=Status.objects.filter(status=status).values('id')[0]['id'],
                                     start=start,
                                     end=end)
            
            # Add the update, if there is one, using the current time
            if update:
                # Create a datetime object for right now and add the server's timezone (whatever DJango has)
                time_now = datetime.datetime.now()
                time_now = pytz.timezone(settings.TIME_ZONE).localize(time_now)
                Event_Update(event_id=id, date=time_now, update=update, user_id=request.user.id).save()

            # Add the email recipient.  If an email recipient is missing, then the broadcast email will not be checked.
            # In both cases, delete the existing email (because it will be re-added)
            Event_Email.objects.filter(event_id=id).delete()
            if email_id: 
                Event_Email(event_id=id,email_id=email_id).save()

            # See if we are adding or subtracting services
            # The easiest thing to do here is remove all affected  
            # services and re-add the ones indicated here

            # Remove first
            Event_Service.objects.filter(event_id=id).delete()
    
            # Now add (form validation confirms that there is at least 1)
            for service_id in affected_svcs:
                # Should be number only -- can't figure out how to validate
                # multiple checkboxes in the form
                if re.match(r'^\d+$', service_id):
                    Event_Service(event_id=id,service_id=service_id).save()

            # Send an email notification to the appropriate list about this issue if requested.  Broadcast won't be
            # allowed to be true if an email address is not defined or if global email is disabled.
            if Config_Email.objects.filter(id=Config_Email.objects.values('id')[0]['id']).values('enabled')[0]['enabled'] == 1 and broadcast:
                email = notify.email()
                email.email_event(id,email_id,request.timezone,False)

            # Clear the cache - don't discriminate and just clear everything that impacts events
            cache.delete_many(['timeline','events_ns','event_count_ns'])

            # Set a success message
            messages.add_message(request, messages.SUCCESS, 'Incident successfully updated')

            # All done so redirect to the incident detail page so
            # the new data can be seen.
            return HttpResponseRedirect('/i_detail?id=%s' % id)
        
        else:
            messages.add_message(request, messages.ERROR, 'Invalid data entered, please correct the errors below:')

            # Obtain the id so we can print the update page again
            if 'id' in request.POST: 
                if re.match(r'^\d+$', request.POST['id']):
                    id = request.POST['id']
                else:
                    messages.add_message(request, messages.ERROR, 'Improperly formatted incident ID - cannot update incident')
                    return HttpResponseRedirect('/admin') 
            else:
                messages.add_message(request, messages.ERROR, 'No incident ID given - cannot update incident') 
                return HttpResponseRedirect('/admin')

    # Not a POST so create a blank form
    else:
        # Obtain the id 
        if 'id' in request.GET: 
            if re.match(r'^\d+$', request.GET['id']):
                id = request.GET['id']
            else:
                messages.add_message(request, messages.ERROR, 'Improperly formatted incident ID - cannot update incident')
                return HttpResponseRedirect('/admin')
        else:
            messages.add_message(request, messages.ERROR, 'No incident ID given - cannot update incident') 
            return HttpResponseRedirect('/admin')

        # In the case of a GET, we can acquire the proper services from the DB
        affected_svcs_tmp = Event.objects.filter(id=id).values('event_service__service_id')
        affected_svcs = []
        for service_id in affected_svcs_tmp:
            affected_svcs.append(service_id['event_service__service_id'])
        affected_svcs = list(affected_svcs)
        
        # Create a blank form
        form = UpdateIncidentForm()

    # Obtain the details (and make sure it's an incident)
    details = Event.objects.filter(id=id,type__type='incident').values(
                                                'description',
                                                'status__status',
                                                'event_email__email__id',
                                                'start',
                                                'end',
                                                'status__status'
                                                )
    # If nothing was returned, send back to the home page
    if not details:
        messages.add_message(request, messages.ERROR, 'Invalid request: no such incident id.')
        return HttpResponseRedirect('/')

    # Obtain all services
    services = Service.objects.values('id','service_name').order_by('service_name')

    # Obtain all current email addresses
    emails = Email.objects.values('id','email')

    # Obtain any updates
    updates = Event_Update.objects.filter(event_id=id).values('id','date','update').order_by('id')

    # Print the page
    return render_to_response(
       'incidents/i_update.html',
       {
          'title':'System Status Dashboard | Update Incident',
          'details':details,
          'services':services,
          'affected_svcs':affected_svcs,
          'id':id,
          'form':form,
          'updates':updates,
          'emails':emails,
          'email_enabled':Config_Email.objects.filter(id=Config_Email.objects.values('id')[0]['id']).values('enabled')[0]['enabled'],
          'nav_section':'event',
          'nav_sub':'i_update'
       },
       context_instance=RequestContext(request)
    )


@staff_member_required_ssd
def i_delete(request):
    """Delete Incident Page

    Delete an incident given an id

    """

    logger.debug('%s view being executed.' % 'incidents.i_delete')

    # If it's a POST, then we are going to delete it after confirmation
    if request.method == 'POST':
        
        # Check the form elements
        form = DeleteEventForm(request.POST)
        logger.debug('Form submit (POST): %s, with result: %s' % ('DeleteEventForm',form))

        if form.is_valid():

            # Obtain the cleaned data
            id = form.cleaned_data['id']

            # Delete the incident
            Event.objects.filter(id=id).delete()

            # Clear the cache - don't discriminate and just clear everything that impacts events
            cache.delete_many(['timeline','events_ns','event_count_ns'])

            # Set a message that the delete was successful
            messages.add_message(request, messages.SUCCESS, 'Incident id:%s successfully deleted' % id)

        # Invalid form submit
        else:
            # Set a message that the delete was not successful
            messages.add_message(request, messages.ERROR, 'Incident id:%s not deleted' % id)
            
        # Redirect to the open incidents page
        return HttpResponseRedirect('/admin/i_list')

    # If we get this far, it's a GET
   
    # Make sure we have an ID
    form = DeleteEventForm(request.GET)
    logger.debug('Form submit (GET): %s, with result: %s' % ('DeleteEventForm',form))
    
    if form.is_valid():

        # Obtain the cleaned data
        id = form.cleaned_data['id']

        # Print the page (confirm they want to delete the incident)
        return render_to_response(
           'incidents/i_delete.html',
           {
              'title':'System Status Dashboard | Confirm Delete',
              'id':id,
              'nav_section':'event',
              'nav_sub':'i_delete'
           },
           context_instance=RequestContext(request)
        )

    # Invalid request
    else:

        # Set a message that the delete failed and send back to the incidents page
        messages.add_message(request, messages.ERROR, 'Invalid request.')
        return HttpResponseRedirect('/admin/i_list')


def i_detail(request):
    """Incident Detail View

    Show all available information on an incident

    """

    logger.debug('%s view being executed.' % 'incidents.i_detail')

    form = DetailForm(request.GET)
    logger.debug('Form submit (GET): %s, with result: %s' % ('DetailForm',form))

    if form.is_valid():
        # Obtain the cleaned data
        id = form.cleaned_data['id']

    # Bad form
    else:
        messages.add_message(request, messages.ERROR, 'Improperly formatted incident ID, cannot display incident detail') 
        return HttpResponseRedirect('/')

    # Obain the incident detail (and make sure it's an incident)
    details = Event.objects.filter(id=id,type__type='incident').values(
                                                'status__status',
                                                'start',
                                                'end',
                                                'description',
                                                'user_id__first_name',
                                                'user_id__last_name'
                                                )
    # If nothing was returned, send back to the home page
    if not details:
        messages.add_message(request, messages.ERROR, 'Invalid request: no such incident id.')
        return HttpResponseRedirect('/')

    # Which services were impacted
    services = Event.objects.filter(id=id).values('event_service__service__service_name')

    # Obain any incident updates
    updates = Event.objects.filter(id=id).values(
                                                'event_update__id',
                                                'event_update__date',
                                                'event_update__update',
                                                'event_update__user__first_name',
                                                'event_update__user__last_name'
                                                ).order_by('event_update__id')
    # If there are no updates, set to None
    if len(updates) == 1 and updates[0]['event_update__date'] == None:
        updates = None

    # Print the page
    return render_to_response(
       'incidents/i_detail.html',
       {
          'title':'System Status Dashboard | Incident Detail',
          'services':services,
          'id':id,
          'details':details,
          'updates':updates
       },
       context_instance=RequestContext(request)
    )


@staff_member_required_ssd
def i_list(request):
    """Incident List View

    Show all open incidents

    """

    logger.debug('%s view being executed.' % 'incidents.i_list')

    form = ListForm(request.GET)
    logger.debug('Form submit (GET): %s, with result: %s' % ('ListForm',form))

    # Check the params
    if form.is_valid():

        page = form.cleaned_data['page']

        # Obtain all open incidents
        incidents_all = Event.objects.filter(type__type='incident',status__status='open').values('id','start','description').order_by('-id')

        # Create a paginator and paginate the list w/ 10 messages per page
        paginator = Paginator(incidents_all, 10)

        # Paginate them
        try:
            incidents = paginator.page(page)
        except PageNotAnInteger:
            # If page is not an integer, or is not given deliver first page.
            incidents = paginator.page(1)
        except EmptyPage:
            # If page is out of range (e.g. 9999), deliver last page of results.
            incidents = paginator.page(paginator.num_pages)

        # Print the page
        return render_to_response(
           'incidents/i_list.html',
           {
              'title':'System Status Dashboard | Open Incidents',
              'incidents':incidents,
              'nav_section':'event',
              'nav_sub':'i_list'
           },
           context_instance=RequestContext(request)
        )

    # Invalid form
    else:
        messages.add_message(request, messages.ERROR, 'Invalid request, please submit your request again.')
        return HttpResponseRedirect('/admin/i_list')


@staff_member_required_ssd
def i_update_delete(request):
    """Delete Incident Update Page

    Delete an incident update given an id

    """

    logger.debug('%s view being executed.' % 'incidents.i_update_delete')

    # If it's a POST, then we are going to delete it after confirmation
    if request.method == 'POST':
        
        # Check the form elements
        form = DeleteUpdateForm(request.POST)
        logger.debug('Form submit (POST): %s, with result: %s' % ('DeleteUpdateForm',form))

        if form.is_valid():

            # Obtain the cleaned data
            id = form.cleaned_data['id']
            event_id = form.cleaned_data['event_id']

            # Delete the event update
            Event_Update.objects.filter(id=id).delete()

            # Clear the cache 
            cache.delete('timeline')

            # Set a message that the delete was successful
            messages.add_message(request, messages.SUCCESS, 'Incident update id:%s successfully deleted' % id)

        # Invalid form submit
        else:
            # Set a message that the delete was not successful
            messages.add_message(request, messages.ERROR, 'Incident update id:%s not deleted' % id)
            
        # Redirect back to the incident page
        return HttpResponseRedirect('/admin/i_update?id=%s' % event_id)

    # If we get this far, it's a GET
   
    # Make sure we have an ID
    form = DeleteUpdateForm(request.GET)
    logger.debug('Form submit (GET): %s, with result: %s' % ('DeleteUpdateForm',form))
    
    if form.is_valid():

        # Obtain the cleaned data
        id = form.cleaned_data['id']
        event_id = form.cleaned_data['event_id']

        # Print the page (confirm they want to delete the event update)
        return render_to_response(
           'incidents/i_update_delete.html',
           {
              'title':'System Status Dashboard | Confirm Delete',
              'id':id,
              'event_id':event_id,
              'nav_section':'event',
              'nav_sub':'i_delete'
           },
           context_instance=RequestContext(request)
        )

    # Invalid request
    else:

        # Set a message that the delete failed and send back to the incidents page
        messages.add_message(request, messages.ERROR, 'Invalid request.')
        return HttpResponseRedirect('/admin/i_list')
