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


"""This module contains all of the maintenance specific functions of SSD."""


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
from django.db.models import Q
from django.contrib.auth.models import User
from ssd.dashboard.decorators import staff_member_required_ssd
from ssd.dashboard.models import Event, Type, Status, Event_Service, Event_Update, Event_Email, Event_Impact, Event_Coordinator, Service, Email,Config_Email
from ssd.dashboard.forms import DeleteUpdateForm, DetailForm, DeleteEventForm,UpdateMaintenanceForm, EmailMaintenanceForm, AddMaintenanceForm, ListForm
from ssd.dashboard import notify


# Get an instance of the ssd logger
logger = logging.getLogger(__name__)


@staff_member_required_ssd
def maintenance(request):
    """Schedule maintenance page

    """

    logger.debug('%s view being executed.' % 'maintenance.maintenance')

    # If this is a POST, then validate the form and save the data
    # Some validation must take place manually
    if request.method == 'POST':

        # If this is a form submit that fails, we want to reset whatever services were selected
        # by the user.  Templates do not allow access to Arrays stored in QueryDict objects so we have
        # to determine the list and send back to the template on failed form submits
        affected_svcs = request.POST.getlist('service')

        # Check the form elements
        form = AddMaintenanceForm(request.POST)
        logger.debug('Form submit (POST): %s, with result: %s' % ('AddMaintenanceForm',form))

        if form.is_valid():
            # Obtain the cleaned data
            s_date = form.cleaned_data['s_date']
            s_time = form.cleaned_data['s_time']
            e_date = form.cleaned_data['e_date']
            e_time = form.cleaned_data['e_time']
            description = form.cleaned_data['description']
            impact = form.cleaned_data['impact']
            coordinator = form.cleaned_data['coordinator']
            broadcast = form.cleaned_data['broadcast']
            email_id = form.cleaned_data['email_id']
                        
            # Combine the dates and times into datetime objects
            start = datetime.datetime.combine(s_date, s_time)
            end = datetime.datetime.combine(e_date, e_time)

            # Set the timezone
            tz = pytz.timezone(request.timezone)
            start = tz.localize(start)
            end = tz.localize(end)
            
            # Create the event and obtain the ID                                     
            e = Event.objects.create(type_id=Type.objects.filter(type='maintenance').values('id')[0]['id'],
                                     description=description,
                                     status_id=Status.objects.filter(status='planning').values('id')[0]['id'],
                                     start=start,
                                     end=end,
                                     user_id=request.user.id
                                    )
            event_id = e.pk

            # Save the impact analysis
            Event_Impact(event_id=event_id,impact=impact).save()

            # Save the coordinator, if requested
            Event_Coordinator(event_id=event_id,coordinator=coordinator).save()

            # Add the email recipient, if requested
            if email_id: 
                Event_Email(event_id=event_id,email_id=email_id).save()

            # Find out which services this impacts and associate the services with the event
            # Form validation confirms that there is at least 1
            for service_id in affected_svcs:
                # Should be number only -- can't figure out how to validate
                # multiple checkboxes in the form
                if re.match(r'^\d+$', service_id):
                    Event_Service(service_id=service_id,event_id=event_id).save()

            # Send an email notification to the appropriate list about this maintenance, if requested.  Broadcast won't be
            # allowed to be true if an email address is not defined or if global email is disabled.
            if Config_Email.objects.filter(id=Config_Email.objects.values('id')[0]['id']).values('enabled')[0]['enabled'] == 1 and broadcast:
                email = notify.email()
                email.email_event(event_id,email_id,request.timezone,True)

            # Clear the cache - don't discriminate and just clear everything that impacts events
            cache.delete_many(['timeline','events_ns','event_count_ns'])
            
            # Set a success message
            messages.add_message(request, messages.SUCCESS, 'Maintenance successfully created.')

            # Send them to the maintenance detail page for this newly created
            # maintenance
            return HttpResponseRedirect('/m_detail?id=%s' % event_id)

        else:
            messages.add_message(request, messages.ERROR, 'Invalid data entered, please correct the errors below:')

    # Not a POST so create a blank form
    else:

        # There are no affected services selected yet
        affected_svcs = []
        
        # Create a blank form
        form = AddMaintenanceForm() 
    
    # Obtain all current email addresses
    emails = Email.objects.values('id','email')

    # Obtain all services
    services = Service.objects.values('id','service_name').order_by('service_name')
    
    # Print the page
    return render_to_response(
       'maintenance/maintenance.html',
       {
          'title':'System Status Dashboard | Scheduled Maintenance',
          'form':form,
          'services':services,
          'affected_svcs':tuple(affected_svcs),
          'emails':emails,
          'email_enabled':Config_Email.objects.filter(id=Config_Email.objects.values('id')[0]['id']).values('enabled')[0]['enabled'],
          'nav_section':'event',
          'nav_sub':'maintenance'
       },
       context_instance=RequestContext(request)
    )


@staff_member_required_ssd
def m_update(request):
    """Update Maintenance Page

    Accept input to update the scheduled maintenance

    """

    logger.debug('%s view being executed.' % 'maintenance.m_update')

    # If this is a POST, then validate the form and save the data
    # Some validation must take place manually (service
    # addition/subtraction
    if request.method == 'POST':

        # If this is a form submit that fails, we want to reset whatever services were selected
        # by the user.  Templates do not allow access to Arrays stored in QueryDict objects so we have
        # to determine the list and send back to the template on failed form submits
        affected_svcs = request.POST.getlist('service')

        # Check the form elements
        form = UpdateMaintenanceForm(request.POST)
        logger.debug('Form submit (POST): %s, with result: %s' % ('UpdateMaintenanceForm',form))


        if form.is_valid():
            # Obtain the cleaned data
            id = form.cleaned_data['id']
            s_date = form.cleaned_data['s_date']
            s_time = form.cleaned_data['s_time']
            e_date = form.cleaned_data['e_date']
            e_time = form.cleaned_data['e_time']
            description = form.cleaned_data['description']
            impact = form.cleaned_data['impact']
            coordinator = form.cleaned_data['coordinator']
            update = form.cleaned_data['update']
            broadcast = form.cleaned_data['broadcast']
            email_id = form.cleaned_data['email_id']
            started = form.cleaned_data['started']
            completed = form.cleaned_data['completed']

            # Combine the dates and times into datetime objects
            start = datetime.datetime.combine(s_date, s_time)
            end = datetime.datetime.combine(e_date, e_time)

            # Set the timezone
            tz = pytz.timezone(request.timezone)
            start = tz.localize(start)
            end = tz.localize(end)

            # Determine the status (form validation ensures the logic here)
            if completed:
                status='completed'
            elif started:
                status='started'
            else:
                status='planning'

            # Update the event                                     
            Event.objects.filter(id=id).update(
                                     description=description,
                                     status=Status.objects.filter(status=status).values('id')[0]['id'],
                                     start=start,
                                     end=end)

            # Update the impact analysis (if it's blank, make sure it's deleted, maybe they added it previously)
            if impact:
                Event_Impact.objects.filter(event_id=id).update(impact=impact)
            else:
                Event_Impact.objects.filter(event_id=id).delete()

            # Update the coordinator (if it's blank, make sure it's deleted, maybe they added it previously)
            if coordinator:
                Event_Coordinator.objects.filter(event_id=id).update(coordinator=coordinator)
            else:
                Event_Coordinator.objects.filter(event_id=id).delete()

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
           
            # Send an email notification to the appropriate list about this maintenance, if requested.  Broadcast won't be
            # allowed to be true if an email address is not defined or if global email is disabled.
            if Config_Email.objects.filter(id=Config_Email.objects.values('id')[0]['id']).values('enabled')[0]['enabled'] == 1 and broadcast:
                email = notify.email()
                email.email_event(id,email_id,request.timezone,False)

            # Clear the cache - don't discriminate and just clear everything that impacts events
            cache.delete_many(['timeline','events_ns','event_count_ns'])

            # Set a success message
            messages.add_message(request, messages.SUCCESS, 'Maintenance successfully updated')

            # All done so redirect to the maintenance detail page so
            # the new data can be seen.
            return HttpResponseRedirect('/m_detail?id=%s' % id)
    
        else:
            messages.add_message(request, messages.ERROR, 'Invalid data entered, please correct the errors below:')

            # Obtain the id so we can print the update page again
            if 'id' in request.POST: 
                if re.match(r'^\d+$', request.POST['id']):
                    id = request.POST['id']
                else:
                    messages.add_message(request, messages.ERROR, 'Improperly formatted maintenance ID - cannot update maintenance')
                    return HttpResponseRedirect('/admin') 
            else:
                messages.add_message(request, messages.ERROR, 'No maintenance ID given - cannot update maintenance') 
                return HttpResponseRedirect('/admin')

    # Not a POST
    else:

        # Obtain the id 
        if 'id' in request.GET: 
            if re.match(r'^\d+$', request.GET['id']):
                id = request.GET['id']
            else:
                messages.add_message(request, messages.ERROR, 'Improperly formatted maintenance ID - cannot update maintenance')
                return HttpResponseRedirect('/admin') 
        else:
            messages.add_message(request, messages.ERROR, 'No maintenance ID given - cannot update maintenance') 
            return HttpResponseRedirect('/admin')

        # In the case of a GET, we can acquire the proper services from the DB
        affected_svcs_tmp = Event.objects.filter(id=id).values('event_service__service_id')
        affected_svcs = []
        for service_id in affected_svcs_tmp:
            affected_svcs.append(service_id['event_service__service_id'])
        affected_svcs = list(affected_svcs)

        # Create a blank form
        form = UpdateMaintenanceForm()

    # Obtain the details
    # Obain the maintenance detail
    details = Event.objects.filter(id=id).values(
                                                'start',
                                                'end',
                                                'status__status',
                                                'description',
                                                'event_impact__impact',
                                                'event_coordinator__coordinator',
                                                'event_email__email__id',
                                                'user__first_name',
                                                'user__last_name'
                                                )
    # If nothing was returned, send back to the home page
    if not details:
        messages.add_message(request, messages.ERROR, 'Invalid request: no such maintenance id.')
        return HttpResponseRedirect('/')

    # Obtain all current email addresses
    emails = Email.objects.values('id','email')

    # Obtain all services
    services = Service.objects.values('id','service_name').order_by('service_name')

    start = details[0]['start']
    end = details[0]['end']

    # Set the timezone
    start = start.astimezone(pytz.timezone(request.timezone))
    end = end.astimezone(pytz.timezone(request.timezone))
    
    # Format the start/end date/time
    s_date = start.strftime("%Y-%m-%d")   
    s_time = start.strftime("%H:%M")
    e_date = end.strftime("%Y-%m-%d")
    e_time = end.strftime("%H:%M")

    # Obtain any updates
    updates = Event_Update.objects.filter(event_id=id).values('id','date','update').order_by('id')
    
    # Print the page
    return render_to_response(
       'maintenance/m_update.html',
       {
          'title':'System Status Dashboard | Scheduled Maintenance Update',
          'details':details,
          'affected_svcs':affected_svcs,
          'services':services,
          'id':id,
          'form':form,
          's_date':s_date,
          's_time':s_time,
          'e_date':e_date,
          'e_time':e_time,
          'emails':emails,
          'email_enabled':Config_Email.objects.filter(id=Config_Email.objects.values('id')[0]['id']).values('enabled')[0]['enabled'],
          'updates':updates,
          'nav_section':'event',
          'nav_sub':'m_update'
       },
       context_instance=RequestContext(request)
    )


def m_detail(request):
    """Maintenance Detail View

    Show all available information on a scheduled maintenance

    """

    logger.debug('%s view being executed.' % 'maintenance.m_detail')

    form = DetailForm(request.GET)
    logger.debug('Form submit (GET): %s, with result: %s' % ('DetailForm',form))


    if form.is_valid():
        # Obtain the cleaned data
        id = form.cleaned_data['id']

    # Bad form
    else:
        messages.add_message(request, messages.ERROR, 'Improperly formatted maintenance ID, cannot display maintenance detail') 
        return HttpResponseRedirect('/')

    # Obain the maintenance detail (and make sure it's a maintenance)
    details = Event.objects.filter(id=id,type__type='maintenance').values(
                                                'start',
                                                'end',
                                                'status__status',
                                                'description',
                                                'event_impact__impact',
                                                'event_coordinator__coordinator',
                                                'event_email__email__email',
                                                'user_id__first_name',
                                                'user_id__last_name'
                                                )
    # If nothing was returned, send back to the home page
    if not details:
        messages.add_message(request, messages.ERROR, 'Invalid request: no such maintenance id.')
        return HttpResponseRedirect('/')

    # Which services were impacted
    services = Event.objects.filter(id=id).values('event_service__service__service_name')

    # Obain any maintenance updates
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
       'maintenance/m_detail.html',
       {
          'title':'System Status Dashboard | Scheduled Maintenance Detail',
          'services':services,
          'id':id,
          'details':details,
          'updates':updates,
       },
       context_instance=RequestContext(request)
    )
    

@staff_member_required_ssd
def m_email(request):
    """Send an Email Notification about a Maintenance"""

    logger.debug('%s view being executed.' % 'maintenance.m_email')

    # Check the form elements
    form = EmailMaintenanceForm(request.GET)
    logger.debug('Form submit (GET): %s, with result: %s' % ('EmailMaintenanceForm',form))

    if form.is_valid():
        # Obtain the cleaned data
        id = form.cleaned_data['id']

        # Obtain the email address id
        recipient_id = Event.objects.filter(id=id).values('event_email__email__id')[0]['event_email__email__id']

        # If there is no recipient defined, give them an error message and send back to the list view
        if not recipient_id:
            messages.add_message(request, messages.ERROR, 'There is no recipient defined for maintenance id:%s.  Please add one before sending email notifications.' % id)

        # Only send the email if email functionality is enabled.
        if Config_Email.objects.filter(id=Config_Email.objects.values('id')[0]['id']).values('enabled')[0]['enabled'] == 1:
            email = notify.email()
            email_status = email.email_event(id,recipient_id,request.timezone,False)

            if email_status == 'success':
                messages.add_message(request, messages.SUCCESS, 'Email successfully sent for maintenance id:%s.' % id)
            else:
                messages.add_message(request, messages.ERROR, 'Email failed for maintenance id:%s.  Error message: %s' % (id,email_status))
        else:
            messages.add_message(request, messages.ERROR, 'Email functionality is disabled.')
    else:
        messages.add_message(request, messages.ERROR, 'Request failed.')

    # Redirect to the open incidents page
    return HttpResponseRedirect('/admin/m_list')


@staff_member_required_ssd
def m_delete(request):
    """Delete Maintenance Page

    Delete a maintenance given an id

    """

    logger.debug('%s view being executed.' % 'maintenance.m_delete')

    # If it's a POST, then we are going to delete it after confirmation
    if request.method == 'POST':
        
        # Check the form elements
        form = DeleteEventForm(request.POST)
        logger.debug('Form submit (POST): %s, with result: %s' % ('DeleteEventForm',form))


        if form.is_valid():

            # Obtain the cleaned data
            id = form.cleaned_data['id']

            # Delete the maintenance
            Event.objects.filter(id=id).delete()

            # Clear the cache - don't discriminate and just clear everything that impacts events
            cache.delete_many(['timeline','events_ns','event_count_ns'])

            # Set a message that the delete was successful
            messages.add_message(request, messages.SUCCESS, 'Maintenance id:%s successfully deleted' % id)

        # Invalid form submit
        else:
            # Set a message that the delete was not successful
            messages.add_message(request, messages.ERROR, 'Maintenance id:%s not deleted' % id)

        # Redirect to the open incidents page
        return HttpResponseRedirect('/admin/m_list')

    # If we get this far, it's a GET
   
    # Make sure we have an ID
    form = DeleteEventForm(request.GET)
    logger.debug('Form submit (GET): %s, with result: %s' % ('DeleteEventForm',form))
    
    if form.is_valid():

        # Obtain the cleaned data
        id = form.cleaned_data['id']

        # Print the page (confirm they want to delete the incident)
        return render_to_response(
           'maintenance/m_delete.html',
           {
              'title':'System Status Dashboard | Confirm Delete',
              'id':id,
              'nav_section':'event',
              'nav_sub':'m_delete'
           },
           context_instance=RequestContext(request)
        )

    # Invalid request
    else:

        # Set a message that the delete failed and send back to the maintenance page
        messages.add_message(request, messages.ERROR, 'Invalid request.')
        return HttpResponseRedirect('/admin/m_list')
   

@staff_member_required_ssd   
def m_list(request):
    """Maintenance List View

    Show all open maintenances

    """

    logger.debug('%s view being executed.' % 'maintenance.m_list')

    form = ListForm(request.GET)
    logger.debug('Form submit (GET): %s, with result: %s' % ('ListForm',form))

    # Check the params
    if form.is_valid():

        page = form.cleaned_data['page']

        # Obtain all open incidents
        maintenances_all = Event.objects.filter(Q(type=2,status__status='planning') | Q(type=2,status__status='started')).values('id','start','description','event_email__email__email').order_by('-id')

        # Create a paginator and paginate the list w/ 10 messages per page
        paginator = Paginator(maintenances_all, 10)

        # Paginate them
        try:
            maintenances = paginator.page(page)
        except PageNotAnInteger:
            # If page is not an integer, or is not given deliver first page.
            maintenances = paginator.page(1)
        except EmptyPage:
            # If page is out of range (e.g. 9999), deliver last page of results.
            maintenances = paginator.page(paginator.num_pages)


        # Print the page
        return render_to_response(
           'maintenance/m_list.html',
           {
              'title':'System Status Dashboard | Open Maintenance',
              'maintenances':maintenances,
              'email_enabled':Config_Email.objects.filter(id=Config_Email.objects.values('id')[0]['id']).values('enabled')[0]['enabled'],
              'nav_section':'event',
              'nav_sub':'m_list'
           },
           context_instance=RequestContext(request)
        )

    # Invalid request
    else:
        messages.add_message(request, messages.ERROR, 'Invalid request, please submit your request again.')
        return HttpResponseRedirect('/admin/m_list')


@staff_member_required_ssd
def m_update_delete(request):
    """Delete Maintenance Update Page

    Delete a maintenance update given an id

    """

    logger.debug('%s view being executed.' % 'maintenance.m_update_delete')

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
            messages.add_message(request, messages.SUCCESS, 'Maintenance update id:%s successfully deleted' % id)

        # Invalid form submit
        else:
            # Set a message that the delete was not successful
            messages.add_message(request, messages.ERROR, 'Maintenance update id:%s not deleted' % id)
            
        # Redirect back to the incident page
        return HttpResponseRedirect('/admin/m_update?id=%s' % event_id)

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
           'maintenance/m_update_delete.html',
           {
              'title':'System Status Dashboard | Confirm Delete',
              'id':id,
              'event_id':event_id,
              'nav_section':'event',
              'nav_sub':'m_delete'
           },
           context_instance=RequestContext(request)
        )

    # Invalid request
    else:

        # Set a message that the delete failed and send back to the incidents page
        messages.add_message(request, messages.ERROR, 'Invalid request.')
        return HttpResponseRedirect('/admin/m_list')