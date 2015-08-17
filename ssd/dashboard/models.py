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


"""Models for the SSD Project

    General Notes:
        - All name fields will have a max_length of 50 characters
        - All email addresses will have a max_length of 50 characters
        - All date fields will have blank=False (cannot be blank)
        - All boolean fields will have blank=False (cannot be blank)
        - All fields that are allowed to be blank will have null=False (stored in DB as empty string)
        - Form validation will match the max_length restriction in all cases
"""


import os
import time
import uuid
from django.db import models
from django.contrib.auth.models import User
from django.core.files.storage import FileSystemStorage


class Service(models.Model):
    """Services that will be monitored"""

    service_name = models.CharField(blank=False, max_length=50, unique=True)


class Email(models.Model):
    """Email addresses that will be used for alerting"""

    email = models.CharField(blank=False, max_length=100, unique=True)


class Type(models.Model):
    """Event Types

        Current Types:
        - incident
        - maintenance
    """

    type = models.CharField(max_length=15, unique=True)


class Status(models.Model):
    """Event Status

        Current Statuses:
        - planning (maintenance only, when a maintenance is being planned but it's not started or completed)
        - open (incident only)
        - closed (incident only)
        - started (maintenance only)
        - completed (maintenance only)

    """
    
    status = models.CharField(max_length=10, unique=True)


class Event(models.Model):
    """Events that have been logged"""

    type = models.ForeignKey(Type)
    date = models.DateTimeField(blank=False, auto_now=True)
    description = models.CharField(blank=False, max_length=1000)
    start = models.DateTimeField(blank=False)
    end = models.DateTimeField(null=True, blank=True)
    status = models.ForeignKey(Status)
    user = models.ForeignKey(User)


class Event_Service(models.Model):
    """Tie services to events"""

    event = models.ForeignKey(Event)
    service = models.ForeignKey(Service)


class Event_Impact(models.Model):
    """Event Impact Analysis (maintenance specific)
        - only one entry allowed per event

    """

    event = models.ForeignKey(Event, unique=True)
    impact = models.CharField(blank=False, max_length=1000)


class Event_Coordinator(models.Model):
    """Event Coordinator (maintenance specific)
        - only one entry allowed per event

    """

    event = models.ForeignKey(Event, unique=True)
    coordinator = models.CharField(blank=False, max_length=250)


class Event_Email(models.Model):
    """Event Email Recipient
        - only one entry allowed per event

    """

    event = models.ForeignKey(Event, unique=True)
    email = models.ForeignKey(Email)


class Event_Update(models.Model):
    """Updates to Events"""

    event = models.ForeignKey(Event)
    date = models.DateTimeField(blank=False, auto_now=True)
    update = models.CharField(blank=False, max_length=1000)
    user = models.ForeignKey(User)


class Escalation(models.Model):
    """Escalation Contacts"""

    order = models.PositiveIntegerField(blank=False)
    name = models.CharField(blank=False, max_length=50)
    contact_details = models.CharField(blank=False, max_length=200)
    hidden = models.BooleanField(blank=False)


#-- Configuration Models -- #


class Config_Admin(models.Model):
    """Admin Configuration

    """

    link_enabled = models.BooleanField(blank=False)


class Config_Email(models.Model):
    """Email Configuration

    """

    enabled = models.BooleanField(blank=False)
    email_format = models.BooleanField(blank=False)
    from_address = models.CharField(null=False, blank=True, max_length=50)
    text_pager = models.CharField(null=False, blank=True, max_length=50)
    incident_greeting = models.CharField(null=False, blank=True, max_length=1000)
    incident_update = models.CharField(null=False, blank=True, max_length=1000)
    maintenance_greeting = models.CharField(null=False, blank=True, max_length=1000)
    maintenance_update = models.CharField(null=False, blank=True, max_length=1000)
    email_footer = models.CharField(null=False, blank=True, max_length=250)


class Config_Message(models.Model):
    """System Message Configuration

    """

    main = models.CharField(null=False, blank=True, max_length=1000)
    main_enabled = models.BooleanField(blank=False)
    alert = models.CharField(null=False, blank=True, max_length=1000)
    alert_enabled = models.BooleanField(blank=False)


class Config_Logo(models.Model):
    """System Logo Configuration

    """

    url = models.CharField(null=False, blank=True, max_length=1000)
    logo_enabled = models.BooleanField(blank=False)


class Config_Escalation(models.Model):
    """Escalation Path Configuration

    """

    enabled = models.BooleanField(blank=False)
    instructions = models.CharField(null=False, blank=True, max_length=1000)


class Config_Systemurl(models.Model):
    """System Url Configuration

    """

    url = models.CharField(null=False, blank=True, max_length=250)
    url_enabled = models.BooleanField(blank=False)


class Config_Ireport(models.Model):
    """System Incident Report Configuration

    """

    enabled = models.BooleanField(blank=False)
    email_enabled = models.BooleanField(blank=False)
    instructions = models.CharField(blank=False, max_length=1000)
    submit_message = models.CharField(blank=False, max_length=100)
    upload_enabled = models.BooleanField(blank=False)
    upload_path = models.CharField(null=False, blank=True, max_length=100)
    file_size = models.IntegerField(blank=False, max_length=5)


class Ireport(models.Model):
    """User reported issues"""

    # Obtain the user defined upload location
    # This needs to match the wsgi.conf staticly served location or else images will not be viewable
    fs = FileSystemStorage(Config_Ireport.objects.filter(id=Config_Ireport.objects.values('id')[0]['id']).values('upload_path')[0]['upload_path'])

    def _upload_to(instance, filename):
        """Rename uploaded images to a random (standard) name"""

        # Setup the file path to be unique so we don't fill up directories
        file_path = time.strftime('%Y/%m/%d')

        # Create a unique filename
        file_name = uuid.uuid4().hex

        # Save the original extension, if its there
        extension = os.path.splitext(filename)[1]

        # Return the path and file
        return '%s/%s%s' % (file_path,file_name,extension)

    date = models.DateTimeField(blank=False)
    name = models.CharField(blank=False, max_length=50)
    email = models.CharField(blank=False, max_length=50)
    detail = models.CharField(blank=False, max_length=160)
    extra = models.CharField(null=False, blank=True, max_length=1000)
    screenshot1 = models.ImageField(null=False, blank=True, storage=fs, upload_to=_upload_to)
    screenshot2 = models.ImageField(null=False, blank=True, storage=fs, upload_to=_upload_to)

    