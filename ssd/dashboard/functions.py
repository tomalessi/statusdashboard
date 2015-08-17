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


"""Miscellaneous helper functions for the SSD project


"""


from django.core.cache import cache
import uuid


def namespace_get(logger, key):
	"""Acquire the current namespace for a specified set of keys

	"""

	logger.debug('Checking namespace for %s' % key)

	# Check the cache for the key in question
	# e.g. 'events_ns'
	ns = cache.get(key)

	# If the namespace does not exist, set it with a unique number
	# created with UUID
	if ns == None:
		logger.debug('cache miss: %s' % key)

		# Create the unique namespace
		ns = uuid.uuid4().hex
		logger.debug('Unique namespace created for %s: %s' % (key, ns))

		# We'll use add here instead of set just in case someone beat us
		# to adding it
		ns_add = cache.add(key, ns)
		if not ns_add:
			logger.debug('Could not add unique namespace for %s: %s.  The key was already added' % (key, ns))
			# Ok then get it from memcached
			ns = cache.get(key)
		else:
			logger.debug('Unique namespace successfully added for %s: %s.' % (key, ns))
	else:
		logger.debug('cache hit: %s' % key)

	logger.debug('Namespace for %s: %s' % (key, ns))
	return ns


