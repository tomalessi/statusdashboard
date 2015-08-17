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


"""Custom decorators for the SSD application"""


from functools import wraps
from django.utils.translation import ugettext as _
from django.contrib.admin.forms import AdminAuthenticationForm
from django.contrib.auth.views import login
from django.contrib.auth import REDIRECT_FIELD_NAME


def staff_member_required_ssd(view_func):
    """
    Decorator for views that checks that the user is logged in and is a staff
    member, displaying the custom SSD login page if necessary.

    - This is really just a copy of the staff_member_required decorator from the DJango project
      with the template name changed.
    """
    @wraps(view_func)
    def _checklogin(request, *args, **kwargs):
        if request.user.is_active and request.user.is_staff:
            # The user is valid. Continue to the admin page.
            return view_func(request, *args, **kwargs)

        assert hasattr(request, 'session'), "The Django admin requires session middleware to be installed. Edit your MIDDLEWARE_CLASSES setting to insert 'django.contrib.sessions.middleware.SessionMiddleware'."
        defaults = {
            'template_name': 'registration/login.html',
            'authentication_form': AdminAuthenticationForm,
            'extra_context': {
                'title': _('Log in'),
                'app_path': request.get_full_path(),
                REDIRECT_FIELD_NAME: request.get_full_path(),
            },
        }
        return login(request, **defaults)
    return _checklogin