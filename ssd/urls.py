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


from django.conf.urls import patterns, include, url
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',

    # Main Dashboard
    url(r'^$',                              'ssd.dashboard.views.main.index'),

    # Escalation Path
    url(r'^escalation$',                    'ssd.dashboard.views.escalation.escalation'),

    # Search
    url(r'^search/events$',                 'ssd.dashboard.views.search.events'),
    url(r'^search/graph$',                  'ssd.dashboard.views.search.graph'),

    # Preferences
    url(r'^prefs/set_timezone$',            'ssd.dashboard.views.prefs.set_timezone'),
    url(r'^prefs/jump$',                    'ssd.dashboard.views.prefs.jump'),

    # Incident Events
    url(r'^i_detail$',                      'ssd.dashboard.views.incidents.i_detail'),

    # Maintenance Events
    url(r'^m_detail$',                      'ssd.dashboard.views.maintenance.m_detail'),

    # Incident Reports
    url(r'^ireport$',                       'ssd.dashboard.views.ireport.ireport'),



    # -- from here down, it's all admin functionality -- #

   # User login
    url(r'^accounts/login/$',               'django.contrib.auth.views.login'),

    # User logout
    url(r'^accounts/logout/$',              'django.contrib.auth.views.logout',{'next_page': '/'}),

    # Standard Django admin site
    url(r'^djadmin/',                       include(admin.site.urls)),

    # SSD Admin 
    url(r'^admin$',                         'ssd.dashboard.views.admin.main'),
    url(r'^admin/admin_config$',            'ssd.dashboard.views.admin.admin_config'),
    url(r'^admin/cache_status$',            'ssd.dashboard.views.admin.cache_status'),

    # Incident Events (admin functionality)
    url(r'^admin/incident$',                'ssd.dashboard.views.incidents.incident'),
    url(r'^admin/i_delete$',                'ssd.dashboard.views.incidents.i_delete'),
    url(r'^admin/i_list$',                  'ssd.dashboard.views.incidents.i_list'),
    url(r'^admin/i_update$',                'ssd.dashboard.views.incidents.i_update'),
    url(r'^admin/i_update_delete$',         'ssd.dashboard.views.incidents.i_update_delete'),
    
    # Maintenance Events (admin functionality)
    url(r'^admin/maintenance$',             'ssd.dashboard.views.maintenance.maintenance'),
    url(r'^admin/m_delete$',                'ssd.dashboard.views.maintenance.m_delete'),
    url(r'^admin/m_list$',                  'ssd.dashboard.views.maintenance.m_list'),
    url(r'^admin/m_email$',                 'ssd.dashboard.views.maintenance.m_email'),
    url(r'^admin/m_update$',                'ssd.dashboard.views.maintenance.m_update'),
    url(r'^admin/m_update_delete$',         'ssd.dashboard.views.maintenance.m_update_delete'),

    # Email Configuration (admin functionality)
    url(r'^admin/email_config$',            'ssd.dashboard.views.email.email_config'),
    url(r'^admin/email_recipients$',        'ssd.dashboard.views.email.email_recipients'),
    url(r'^admin/recipient_delete$',        'ssd.dashboard.views.email.recipient_delete'),
    url(r'^admin/recipient_modify$',        'ssd.dashboard.views.email.recipient_modify'),
 
    # Services Configuration (admin functionality)
    url(r'^admin/services$',                'ssd.dashboard.views.services.services'),
    url(r'^admin/service_delete$',          'ssd.dashboard.views.services.service_delete'),
    url(r'^admin/service_modify$',          'ssd.dashboard.views.services.service_modify'),

    # Messages Configuration (admin functionality)
    url(r'^admin/messages_config$',         'ssd.dashboard.views.messages.messages_config'),

    # Logo Configuration (admin functionality)
    url(r'^admin/logo_config$',             'ssd.dashboard.views.logo.logo_config'),

    # Url Configuration (admin functionality)
    url(r'^admin/systemurl_config$',        'ssd.dashboard.views.systemurl.systemurl_config'),

    # Incident Reports (admin functionality)
    url(r'^admin/ireport_config$',          'ssd.dashboard.views.ireport.ireport_config'),
    url(r'^admin/ireport_detail$',          'ssd.dashboard.views.ireport.ireport_detail'),
    url(r'^admin/ireport_delete$',          'ssd.dashboard.views.ireport.ireport_delete'),
    url(r'^admin/ireport_list$',            'ssd.dashboard.views.ireport.ireport_list'),

    # Escalation
    url(r'^admin/escalation_config$',       'ssd.dashboard.views.escalation.escalation_config'),
    url(r'^admin/escalation_contacts$',     'ssd.dashboard.views.escalation.escalation_contacts'),
    url(r'^admin/contact_switch$',          'ssd.dashboard.views.escalation.contact_switch'),
    url(r'^admin/contact_delete$',          'ssd.dashboard.views.escalation.contact_delete'),
    url(r'^admin/contact_modify$',          'ssd.dashboard.views.escalation.contact_modify'),

    # Events
    url(r'^admin/update_modify$',           'ssd.dashboard.views.events.update_modify'),
)
