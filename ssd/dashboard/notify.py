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


"""Email class for SSD

   This class handles the sending of emails and pages to the appropriate recipients

"""

import logging
from django.core.mail import EmailMessage, EmailMultiAlternatives
from django.template.loader import get_template
from django.template import Context
from django.utils import timezone as jtz
from ssd.dashboard.models import Email
from ssd.dashboard.models import Event
from ssd.dashboard.models import Config_Email, Config_Systemurl


# Get an instance of the ssd logger
logger = logging.getLogger(__name__)


class email:

    """
    Email and Pager helper class for SSD
    """

    def __init__(self):
        """
        Constructor

        """

    def page(self,message):
        """
        Send a short text message/page in text format
        The required format of EmailMessage is as follows:
          - EmailMessage(subject,body,from_email,[to_email],[bcc_email],headers,[cc_email]
          - If there is an error, the user will be notified and an Apache error log will be generated
          
        """

        # Obtain the recipient email address
        text_pager = Config_Email.objects.filter(id=Config_Email.objects.values('id')[0]['id']).values('text_pager')[0]['text_pager']

        # Obtain the sender email address and instantiate the message
        from_address = Config_Email.objects.filter(id=Config_Email.objects.values('id')[0]['id']).values('from_address')[0]['from_address']
        pager = EmailMessage('Incident Alert',message,from_address,[text_pager],None,None,None)

        # If there is an issue, the user will be notified
        try:
            pager.send()
        except Exception, e:
            # Log to the error log and return the error to the caller
            logger.error('Error sending text page: %s' % e)
        
    
    def email_event(self,id,email_id,set_timezone,new):
        """
        Send an email message in HTML or TEXT format about a new or existing incident
           - If HTML formatting is selected, a multi-part MIME message will be sent w/ the text
             version as well
        """


        logger.debug('Sending email for event: %s' % id)

        # Obain the incident detail
        details = Event.objects.filter(id=id).values(
                                                    'status__status',
                                                    'start',
                                                    'end',
                                                    'description',
                                                    'type__type',
                                                    'event_impact__impact',
                                                    'event_coordinator__coordinator'
                                                    )

        # Which services were impacted
        services = Event.objects.filter(id=id).values('event_service__service__service_name')

        # Obain any incident updates
        updates = Event.objects.filter(id=id).values(
                                                'event_update__id',
                                                'event_update__date',
                                                'event_update__update',
                                                ).order_by('event_update__id')

        # If there are no updates, set to None
        if len(updates) == 1 and updates[0]['event_update__date'] == None:
            updates = None

        # Obtain the recipient email address
        recipient = Email.objects.filter(id=email_id).values('email')[0]['email']

        # Obtain the sender email address
        email_from = Config_Email.objects.filter(id=Config_Email.objects.values('id')[0]['id']).values('from_address')[0]['from_address']

        # Obtain the ssd url
        ssd_url = Config_Systemurl.objects.filter(id=Config_Systemurl.objects.values('id')[0]['id']).values('url')[0]['url']

        # HTML (true) or text (false) formatting and footer
        email_config = Config_Email.objects.filter(id=Config_Email.objects.values('id')[0]['id']).values('email_format','email_footer')

        # Obtain the greeting
        if new == True:
            if details[0]['type__type'] == 'incident':
                greeting = Config_Email.objects.filter(id=Config_Email.objects.values('id')[0]['id']).values('incident_greeting')[0]['incident_greeting']
                email_subject = 'Incident Notification'
            elif details[0]['type__type'] == 'maintenance':
                greeting = Config_Email.objects.filter(id=Config_Email.objects.values('id')[0]['id']).values('maintenance_greeting')[0]['maintenance_greeting']
                email_subject = 'Maintenance Notification'
            else:
                logger.error('Unknown event type, exiting')
                return
        else:
            if details[0]['type__type'] == 'incident':
                greeting = Config_Email.objects.filter(id=Config_Email.objects.values('id')[0]['id']).values('incident_update')[0]['incident_update']
                email_subject = 'Incident Update'
            elif details[0]['type__type'] == 'maintenance':
                greeting = Config_Email.objects.filter(id=Config_Email.objects.values('id')[0]['id']).values('maintenance_update')[0]['maintenance_update']
                email_subject = 'Maintenance Update'
            else:
                logger.error('Unknown event type, exiting')
                return


        # Setup the context and interpolate the values in the template
        d = Context({ 
                     'details':details,
                     'greeting':greeting,
                     'services':services,
                     'updates':updates,
                     'ssd_url':ssd_url,
                     'email_footer':email_config[0]['email_footer']
                    })


        # Setup and send the message
        try:
            # Render the text template
            # If html formatting is requested, we'll render that one later
            rendered_template_txt = get_template('email/email.txt').render(d)
           
            msg = EmailMultiAlternatives(
                                            email_subject, 
                                            rendered_template_txt, 
                                            email_from, 
                                            [recipient]
                                        )

            # If HTML is requested, setup a multipart message
            if email_config[0]['email_format'] == 1:
                # Render the html template and attach it
                rendered_template_html = get_template('email/email.html').render(d)
                msg.attach_alternative(rendered_template_html, "text/html")
            
            # Send the message
            msg.send()
        except Exception, e:
            # Log to the error log and return the error to the caller
            logger.error('Error sending event email: %s' % e)
            return

        return 'success'


    