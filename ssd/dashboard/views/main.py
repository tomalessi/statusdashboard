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


"""This module the main dashboard for SSD."""


import logging
import datetime
import pytz
import re
from django.conf import settings
from django.core.cache import cache
from django.db.models import Q
from django.http import HttpResponseRedirect
from django.contrib import messages
from django.shortcuts import render_to_response
from django.template import RequestContext
from ssd.dashboard.models import Event, Event_Update, Service, Config_Message
from ssd.dashboard import functions


# Get an instance of the ssd logger
logger = logging.getLogger(__name__)


def index(request):
    """Index Page View

    The main dashboard view

    """


    logger.debug('%s view being executed.' % 'main.index')

    # -------------------------------------------------------- #
    # OBTAIN AND CONFIGURE DATE INFORMATION

    # Get the reference date (if its not given, then its today)
    try:
        ref = request.GET['ref']
    # Not there, so set it
    except KeyError:
        # Create a datetime object for right now
        ref = datetime.datetime.now()

        # Add the server's timezone (whatever DJango is set to)
        ref = pytz.timezone(settings.TIME_ZONE).localize(ref)

        # Now convert to the requested timezone
        ref = ref.astimezone(pytz.timezone(request.timezone))

        # Format for just the year, month, day.  We'll add the entire day later
        ref = ref.strftime("%Y-%m-%d")

    # The reference date we use in the query to find relevant incidents
    # is different than the reference date we use for the calendar
    # because the query needs to go through 23:59:59
    ref_q = ref + ' 23:59:59'
    # If the reference date is not in the proper form, provide an error and redirect to the 
    # standard homepage
    try:
        ref_q = datetime.datetime.strptime(ref_q,'%Y-%m-%d %H:%M:%S')
    except ValueError:
        # Set an error message
        messages.add_message(request, messages.ERROR, 'Improperly formatted reference date.')
        # Redirect to the homepage
        return HttpResponseRedirect('/') 
    ref_q = pytz.timezone(request.timezone).localize(ref_q)

    # The reference date is the last date displayed in the calendar
    # so add that and create a datetime object in the user's timezone
    # (or the server timezone if its not set)
    ref += ' 00:00:00'
    ref = datetime.datetime.strptime(ref,'%Y-%m-%d %H:%M:%S') 
    ref = pytz.timezone(request.timezone).localize(ref)

    # Obtain the current 7 days
    dates = []
    headings = ['Status','Service']
    # Subtract successive days (the reference date is the first day)
    for i in [6,5,4,3,2,1]:
       delta = ref - datetime.timedelta(days=i)

       # Add each date
       dates.append(delta)
       headings.append(delta)
 
    # Add the ref date
    dates.append(ref)
    headings.append(ref)

    # The forward and back buttons will be -7 (back) and +7 (forward)
    backward = (ref - datetime.timedelta(days=7)).strftime('%Y-%m-%d')
    backward_link = '/?ref=%s' % (backward)
    forward = (ref + datetime.timedelta(days=7)).strftime('%Y-%m-%d')
    forward_link = '/?ref=%s' % (forward)
    # END DATE INFORMATION
    # -------------------------------------------------------- #


    # -------------------------------------------------------- #
    # OBTAIN ACTIVE INCIDENT INFORMATION
    #
    # This information will be used to build the timelines and also as lookups
    # to set the service status in the main dashboard
    #
    # We'll use the following data structure
    # timeline = {
    #              'events': {
    #                            incident':{
    #                                        '1': {
    #                                               'start':'2013-01-01 10:28:25 PDT',
    #                                               'description':'We are having an issue with the exchange server',
    #                                               'services':['service1','service2'],                                
    #                                               'updates': [
    #                                                            ['2013-01-01 10:29:25 PDT','We are having an issue'],
    #                                                            ['2013-01-01 10:30:25 PDT','Resolved now']
    #                                                           ]
    #                                              }
    #                                       },
    #                            
    #                            maintenance':{
    #                                           '5': {
    #                                                  'start':'2013-01-01 10:28:25 PDT',
    #                                                  'description':'We are having an issue with the exchange server',
    #                                                  'services':['service1','service2'],                                
    #                                                  'updates': [
    #                                                               ['2013-01-01 10:29:25 PDT','We are having an issue'],
    #                                                               ['2013-01-01 10:30:25 PDT','Resolved now']
    #                                                             ]
    #                                                 }
    #                                         }
    #
    #
    #                        },
    #               'lookup': {
    #                           'incident': {
    #                                           'service1': '',
    #                                           'service2': ''
    #                                       },
    #                           'maintenance': {
    #                                                'service3': '',
    #                                                'service4': ''
    #                                            }
    #                         }
    #            }
    #          
    timeline = cache.get('timeline')
    if timeline == None:
        logger.debug('cache miss: %s' % 'timeline')

        # Create the timeline structure
        timeline = {
                    'events': {},
                    'lookup': {
                                'incident': {},
                                'maintenance': {}
                    }
        }

        
        # Get the events
        timeline_events = Event.objects.filter(Q(status__status='open') | Q(status__status='started')).values('id','start','type__type','description').order_by('start')

        # Build the timeline data structure
        for event in timeline_events:

            # Add the type to the timeline if not there
            if not event['type__type'] in timeline['events']:
                timeline['events'][event['type__type']] = {}
            
            # Add the event id to the timeline if not there
            if not event['id'] in timeline['events'][event['type__type']]:
                timeline['events'][event['type__type']][event['id']] = {}

            # Add the event data to the timeline
            timeline['events'][event['type__type']][event['id']]['start'] = event['start']
            timeline['events'][event['type__type']][event['id']]['description'] = event['description']

            # Find out which services this event impacts and add to the timeline
            # We need to cast this to a list so that it's evaluated and caching works properly
            services_impacted = list(Event.objects.filter(id=event['id']).values('event_service__service__service_name'))

            # Add the services to the timeline
            timeline['events'][event['type__type']][event['id']]['services'] = services_impacted

            # Check each service impacted and add to the events_lookup table
            for service in services_impacted:

                if not service['event_service__service__service_name'] in timeline['lookup'][event['type__type']]:
                    timeline['lookup'][event['type__type']][service['event_service__service__service_name']] = ''            

        # Now get the updates
        timeline_updates = Event_Update.objects.filter(Q(event_id__status__status='open') | Q(event_id__status__status='started')).values('event_id','event_id__type__type','date','update').order_by('id')

        for update in timeline_updates:

            # Add the updates array to the timeline if not there
            if not 'updates' in timeline['events'][update['event_id__type__type']][update['event_id']]:
                timeline['events'][update['event_id__type__type']][update['event_id']]['updates'] = []

            # Add the update to the timeline
            timeline['events'][update['event_id__type__type']][update['event_id']]['updates'].append([update['date'],update['update']])

        # Put in cache
        cache.set('timeline', timeline)
    else:
        logger.debug('cache hit: %s' % 'timeline')
    
    # END ACTIVE INCIDENT INFORMATION
    # -------------------------------------------------------- #



    # -------------------------------------------------------- #
    # MAIN DASHBOARD TABLE INFORMATION
    #
    # In order to build this table, we need to look through all events, regardless of status
    # within the requested time frame
    #
    # We'll print 7 days of dates at any time
    # Construct a dictionary like this to pass to the template
    # [
    #  [service][2012-10-11][2012-10-12],
    #  [{service:www.domain.com,status:1},['green'],['green']],
    #  [{service:www.domain1.com,status:0},['green'],[{'open':,'closed':,'type':,'id':}]]
    # ]

    # Put together the first row, which are the headings
    data = []
    data.append(headings)


    # Grab all services
    services = cache.get('services')
    if services == None:
        logger.debug('cache miss: %s' % 'services')
        services = Service.objects.values('service_name').order_by('service_name')
        cache.set('services', services)
    else:
        logger.debug('cache hit: %s' % 'services')


    # Grab all events within the time range requested (for the specific time range):
    # 
    # The memcache key will be:
    # events_[ns]_[from]_[to]
    #

    # Obtain the memcached namespace for the key events_
    events_ns = functions.namespace_get(logger, 'events_ns')
    events_key = 'events_%s_%s_%s' % (events_ns,dates[0].strftime('%Y%m%d%Z'),ref.strftime('%Y%m%d%Z'))
    logger.debug('events key: %s' % events_key)
    
    events = cache.get(events_key)
    if events == None:
        logger.debug('cache miss: %s' % events_key)
        # The only thing we don't want shown here are maintenances that are in the planning stage
        events = Event.objects.filter(start__range=[dates[0],ref_q]).exclude(status__status='planning').values(
                                                                                                              'id',
                                                                                                              'type__type',
                                                                                                              'description',
                                                                                                              'start',
                                                                                                              'end',
                                                                                                              'event_service__service__service_name',
                                                                                                              'status__status'
                                                                                                              ).order_by('id')
        cache.set(events_key, list(events))
    else:
        logger.debug('cache hit: %s' % events_key)


    # Run through each service and see if it had an incident during the time range
    for service in services:
        # Make a row for this service, which looks like this:
        # {service:www.domain1.com,status:0},['green'],[{'id':foo, 'description':foo,'open':foo,'closed':foo,'type':foo}]
        # The service will initially be green and incidents trump maintenances
        # Statuses are as follows:
        #   - 0 = green
        #   - 1 = active incident
        #   - 2 = active maintenance
        row = [{'service':service['service_name'],'status':0}]

        # Set the status from our lookup table first
        # Incidents over-ride everything for setting the status of the service
        if service['service_name'] in timeline['lookup']['incident']:
            row[0]['status'] = 1
        elif service['service_name'] in timeline['lookup']['maintenance']:
            row[0]['status'] = 2

        # Run through each date for each service
        for date in dates:

            # Check each event to see if there is a match
            # There could be more than one event per day
            row_event = []

            # First the incidents
            for event in events:
                if service['service_name'] == event['event_service__service__service_name']:

                    # This event affected our service
                    # Convert to the requested timezone
                    event_date = event['start']
                    event_date = event_date.astimezone(pytz.timezone(request.timezone))

                    # If the event closed date is there, make sure the time zone is correct
                    end_date = event['end']
                    if event['end']:
                        end_date = end_date.astimezone(pytz.timezone(request.timezone))

                    # If this is our date, add it
                    if date.date() == event_date.date():
                        # This is our date so add the incident information
                        e = {
                                 'id':event['id'],
                                 'type':event['type__type'],
                                 'description':event['description'],
                                 'open':event_date,
                                 'closed':end_date,
                                 'status':event['status__status']
                                 }
                        row_event.append(e)
            
            # If the row_event is empty, this indicates there were no incidents so mark this date/service as green
            if not row_event:
                row_event.append('green')
                

            # Add the event row to the main row
            row.append(row_event)

        # Add the main row to our data dict
        data.append(row)
    
    # END MAIN DASHBOARD TABLE INFORMATION
    # -------------------------------------------------------- #


    # -------------------------------------------------------- #
    # OBTAIN GRAPH COUNT DATA GOING BACK/FORWARD 15 DAYS (FROM REF)
    #
    # The reference date is set to midnight of the day, in the user's timezone
    #
    # First populate all of the dates into an array so we can iterate through 
    graph_dates = []
    
    # The back dates (including today)
    day_range = 15
    counter = day_range
    while counter >= 0:
        day = datetime.timedelta(days=counter)
        day = ref - day
        day = day.strftime("%Y-%m-%d")
        graph_dates.append(day)
        counter -= 1

    # Now the forward dates
    counter = 1
    while counter <= day_range:
        day = datetime.timedelta(days=counter)
        day = ref + day
        day = day.strftime("%Y-%m-%d")
        graph_dates.append(day)
        counter += 1


    # Obtain the back and forward dates for the query    
    back = datetime.timedelta(days=day_range)
    back_date = ref - back
    forward = datetime.timedelta(days=day_range)
    forward_date = ref_q + forward

    # Obtain the memcached namespace for the key event_count_
    event_count_ns = functions.namespace_get(logger, 'event_count_ns')
    event_count_key = 'event_count_%s_%s_%s' % (event_count_ns,back_date.strftime('%Y%m%d%Z'),forward_date.strftime('%Y%m%d%Z'))
    logger.debug('event_count key: %s' % event_count_key)

    # Check the cache
    event_count = cache.get(event_count_key)
    if event_count == None:
        logger.debug('cache miss: %s ' % event_count_key)
        event_count = Event.objects.filter(start__range=[back_date,forward_date]).values('type__type','start')
        cache.set(event_count_key, event_count)
    else:
        logger.debug('cache hit: %s ' % event_count_key)

    # Iterate through the graph_dates and find matching events
    # This data structure will look like this:
    # count_data = [
    #               {'date' : '2013-09-01', 'incidents':0, 'maintenances':0, 'reports':1}
    #              ]
    count_data = []

    # Boolean which turns true if we have maintenances or incidents
    # If not, the graph on the home page will not be shown
    show_graph = False

    for day in graph_dates:

        # Create a tuple to hold this data series
        t = {'date':day, 'incident':0, 'maintenance':0}

        # Check for events that match this date
        for row in event_count:
            if row['start'].astimezone(pytz.timezone(request.timezone)).strftime("%Y-%m-%d") == day:
                t[row['type__type']] += 1
                show_graph = True

        # Add the tuple
        count_data.append(t)
    
    # END GRAPH COUNT DATA
    # -------------------------------------------------------- #


    # -------------------------------------------------------- #
    # OBTAIN ALERT AND INFORMATION TEXT
    alerts = cache.get('alerts')
    if alerts == None:
        logger.debug('cache miss: %s' % 'alerts')
        alerts = Config_Message.objects.filter(id=Config_Message.objects.values('id')[0]['id']).values('alert_enabled','alert','main_enabled','main')
        cache.set('alerts', alerts)
    else:
        logger.debug('cache hit: %s' % 'alerts')

    # If we are showing the alert, obtain the alert text
    if alerts[0]['alert_enabled'] == 1:
        alert = alerts[0]['alert']
    else:
        alert = None

    # If we are showing the information message, obtain the text
    if alerts[0]['main_enabled'] == 1:
        information = alerts[0]['main']
    else:
        information = None
    # END ALERT AND INFORMATION TEXT
    # -------------------------------------------------------- #


    # Print the page
    return render_to_response(
       'main/index.html',
       {
          'title':'System Status Dashboard | Home',
          'data':data,
          'backward_link':backward_link,
          'forward_link':forward_link,
          'alert':alert,
          'information':information,
          'count_data':count_data,
          'timeline':timeline,
          'show_graph':show_graph,
          'ref':ref
       },
       context_instance=RequestContext(request)
    )
    
   