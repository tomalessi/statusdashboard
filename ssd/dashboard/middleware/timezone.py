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


"""Timezone middleware for the SSD project

	This middleware is responsible for checking for the timezone cookie and if present
	setting the desired timezone in the view before processing the request.  This ensures
	that users around the world are operating in dates/times that are most appropriate to
	them.

"""

import logging
from django.conf import settings
from django.utils import timezone as jtz


# Get an instance of the ssd logger
logger = logging.getLogger(__name__)


class TimezoneMiddleware:

	def process_request(self,request):

		# See if the timezone is set, if not, set the default server timezone
		# (the one in settings.py)
		if request.COOKIES.get('tz_pref') == None:
			set_timezone = settings.TIME_ZONE
			logger.debug('tz_pref cookie is not set, using server timezone: %s' % set_timezone)
		else:
			set_timezone = request.COOKIES.get('tz_pref')
			logger.debug('tz_pref cookie is set to: %s' % set_timezone)

        # Set the current timezone to either the server timezone, or the user requested one.  This will display
        # all times in templates in the desired timezone
		jtz.activate(set_timezone)

		request.timezone = set_timezone

		return None