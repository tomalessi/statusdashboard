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


"""This module contains all of the search functions of SSD."""


import logging
import datetime
import pytz
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.contrib import messages
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.http import HttpResponseRedirect
from ssd.dashboard.models import Event
from ssd.dashboard.forms import SearchForm, GSearchForm


# Get an instance of the ssd logger
logger = logging.getLogger(__name__)


def graph(request):
    """Event Search View (Graph)

    Show events for a specific date, when clicked through from the summary graph

    """

    logger.debug('%s view being executed.' % 'search.gsearch')

    form = GSearchForm(request.GET)
    logger.debug('Form submit (GET): %s, with result: %s' % ('GSearchForm',form))

    if form.is_valid():
        # Obtain the cleaned data (only validate the dates)
        date = form.cleaned_data['date']
        type = form.cleaned_data['type']
        page = form.cleaned_data['page']

        # Combine the dates and times into datetime objects
        start = datetime.datetime.combine(date, datetime.datetime.strptime('00:00:00','%H:%M:%S').time())
        end = datetime.datetime.combine(date, datetime.datetime.strptime('23:59:59','%H:%M:%S').time())

        # Set the timezone
        tz = pytz.timezone(request.timezone)
        start = tz.localize(start)
        end = tz.localize(end)

        results_all = Event.objects.filter(type__type=type,start__range=[start,end]
                                          ).values('id','type__type','start','description','status__status'
                                          ).order_by('-start')

        # Create a paginator and paginate the list w/ 10 messages per page
        paginator = Paginator(results_all, 10)

        # Paginate them
        try:
            results = paginator.page(page)
        except PageNotAnInteger:
            # If page is not an integer, or is not given deliver first page.
            results = paginator.page(1)
        except EmptyPage:
            # If page is out of range (e.g. 9999), deliver last page of results.
            results = paginator.page(paginator.num_pages)

        # Put together the query params
        query_params = 'date=%s&type=%s' % (date,type)

        # Print the page
        return render_to_response(
           'search/graph.html',
           {
              'title':'System Status Dashboard | Graph Search',
              'results':results,
              'type':type,
              'date':date,
              'query_params':query_params
           },
           context_instance=RequestContext(request)
        )
    
    # Invalid form
    else:
        messages.add_message(request, messages.ERROR, 'Invalid graph search query')
        return HttpResponseRedirect('/') 


def events(request):
    """Event List View 

    Show a listing of all events

    """

    logger.debug('%s view being executed.' % 'search.events')

    form = SearchForm(request.GET)
    logger.debug('Form submit (GET): %s, with result: %s' % ('SearchForm',form))

    # Check the params
    if form.is_valid():

        page = form.cleaned_data['page']
        start = form.cleaned_data['start']
        end = form.cleaned_data['end']
        text = form.cleaned_data['text']
        type = form.cleaned_data['type']

        # Build the filter for the search query
        filter = {}

        # Start/End
        if start and end:
            # Combine the dates and times into datetime objects
            start_tmp = datetime.datetime.combine(start, datetime.datetime.strptime('00:00:00','%H:%M:%S').time())
            end_tmp = datetime.datetime.combine(end, datetime.datetime.strptime('23:59:59','%H:%M:%S').time())

            # Set the timezone
            tz = pytz.timezone(request.timezone)
            start_tmp = tz.localize(start_tmp)
            end_tmp = tz.localize(end_tmp)

            filter['start__range'] = [start_tmp,end_tmp] 

        # Type
        if type:
            filter['type__type'] = '%s' % type
        
        # Text
        if text:
            filter['description__contains'] = '%s' % text

        # Obtain filtered incidents
        if filter:
            events_all = Event.objects.filter(**filter).values('id','status__status','type__type','start','end','description').order_by('-id')

        # Obtain all incidents
        else:
            events_all = Event.objects.values('id','status__status','type__type','start','end','description').order_by('-id')

        # Create a paginator and paginate the list w/ 10 messages per page
        paginator = Paginator(events_all, 10)

        # Paginate them
        try:
            events = paginator.page(page)
        except PageNotAnInteger:
            # If page is not an integer, or is not given deliver first page.
            events = paginator.page(1)
        except EmptyPage:
            # If page is out of range (e.g. 9999), deliver last page of results.
            events = paginator.page(paginator.num_pages)

        # Put together the query params
        query_params = None
        if start and end:
            query_params = 'start=%s&end=%s' % (start,end)

        if text:
            if query_params:
                query_params += '&text=%s' % text
            else:
                query_params = 'text=%s' % text

        if type:
            if query_params:
                query_params += '&type=%s' % type
            else:
                query_params = 'type=%s' % type

        # Print the page
        return render_to_response(
           'search/events.html',
           {
              'title':'System Status Dashboard | Events Search',
              'events':events,
              'page':page,
              'start':start,
              'end':end,
              'text':text,
              'type':type,
              'query_params':query_params
           },
           context_instance=RequestContext(request)
        )

    # Invalid form
    else:

        # Print the page
        return render_to_response(
           'search/events.html',
           {
              'title':'System Status Dashboard | Events Search',
              'form':form,
           },
           context_instance=RequestContext(request)
        )