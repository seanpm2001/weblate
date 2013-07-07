# -*- coding: utf-8 -*-
#
# Copyright © 2012 - 2013 Michal Čihař <michal@cihar.com>
#
# This file is part of Weblate <http://weblate.org/>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

from django.utils.translation import ugettext_lazy as _
from trans.checks.base import TargetCheck
import re

PYTHON_PRINTF_MATCH = re.compile(
    '''
    %(                          # initial %
          (?:\((?P<key>\w+)\))?    # Python style variables, like %(var)s
    (?P<fullvar>
        [+#-]*                  # flags
        (?:\d+)?                # width
        (?:\.\d+)?              # precision
        (hh\|h\|l\|ll)?         # length formatting
        (?P<type>[\w%]))        # type (%s, %d, etc.)
    )''',
    re.VERBOSE
)


PHP_PRINTF_MATCH = re.compile(
    '''
    %(                          # initial %
          (?:(?P<ord>\d+)\$)?   # variable order, like %1$s
    (?P<fullvar>
        [+#-]*                  # flags
        (?:\d+)?                # width
        (?:\.\d+)?              # precision
        (hh\|h\|l\|ll)?         # length formatting
        (?P<type>[\w%]))        # type (%s, %d, etc.)
    )''',
    re.VERBOSE
)


C_PRINTF_MATCH = re.compile(
    '''
    %(                          # initial %
    (?P<fullvar>
        [+#-]*                  # flags
        (?:\d+)?                # width
        (?:\.\d+)?              # precision
        (hh\|h\|l\|ll)?         # length formatting
        (?P<type>[\w%]))        # type (%s, %d, etc.)
    )''',
    re.VERBOSE
)


class BaseFormatCheck(TargetCheck):
    '''
    Base class for fomat string checks.
    '''
    flag = None
    regexp = None

    def check(self, sources, targets, unit):
        '''
        Checks single unit, handling plurals.
        '''
        # Verify unit is properly flagged
        if not self.flag in unit.flags.split(', '):
            return False

        # Special case languages with single plural form
        if len(sources) > 1 and len(targets) == 1:
            return self.check_format(
                sources[1],
                targets[0],
                unit,
                1,
                False
            )

        # Check singular
        singular_check = self.check_format(
            sources[0],
            targets[0],
            unit,
            0,
            len(sources) > 1
        )

        if singular_check:
            if len(sources) == 1:
                return True
            plural_check = self.check_format(
                sources[1],
                targets[0],
                unit,
                1,
                True
            )
            if plural_check:
                return True

        # Do we have more to check?
        if len(sources) == 1:
            return False

        # Check plurals against plural from source
        for target in targets[1:]:
            plural_check = self.check_format(
                sources[1],
                target,
                unit,
                1,
                False
            )
            if plural_check:
                return True

        # Check did not fire
        return False

    def check_format(self, source, target, unit, cache_slot, ignore_missing):
        '''
        Generic checker for format strings.
        '''
        if len(target) == 0 or len(source) == 0:
            return False
        # Try geting source parsing from cache
        src_matches = self.get_cache(unit, cache_slot)
        # Cache miss
        if src_matches is None:
            src_matches = set([x[0] for x in self.regexp.findall(source)])
            self.set_cache(unit, src_matches, cache_slot)
        tgt_matches = set([x[0] for x in self.regexp.findall(target)])
        # We ignore %% as this is really not relevant. However it needs
        # to be matched to prevent handling %%s as %s.
        if '%' in src_matches:
            src_matches.remove('%')
        if '%' in tgt_matches:
            tgt_matches.remove('%')

        if src_matches != tgt_matches:
            # We can ignore missing format strings
            # for first of plurals
            if ignore_missing and tgt_matches < src_matches:
                return False
            return True

        return False


class PythonFormatCheck(BaseFormatCheck):
    '''
    Check for Python format string
    '''
    check_id = 'python_format'
    name = _('Python format')
    description = _('Format string does not match source')
    flag = 'python-format'
    regexp = PYTHON_PRINTF_MATCH


class PHPFormatCheck(BaseFormatCheck):
    '''
    Check for PHP format string
    '''
    check_id = 'php_format'
    name = _('PHP format')
    description = _('Format string does not match source')
    flag = 'php-format'
    regexp = PHP_PRINTF_MATCH


class CFormatCheck(BaseFormatCheck):
    '''
    Check for C format string
    '''
    check_id = 'c_format'
    name = _('C format')
    description = _('Format string does not match source')
    flag = 'c-format'
    regexp = C_PRINTF_MATCH
