# -*- coding: utf-8 -*-
'''
    :codeauthor: :email:`Jayesh Kariya <jayeshk@saltstack.com>`
'''
# Import Python libs
from __future__ import absolute_import, print_function, unicode_literals

# Import Fractus Libs
import fractus.cloudstates.boto_cloudwatch_alarm as boto_cloudwatch_alarm

# Import Testing Libs
import pytest
from mock import patch, MagicMock



def setup_module():
    pytest.helpers.setup_loader({boto_cloudwatch_alarm: {}})

# 'present' function tests: 1

def test_present():
    '''
    Test to ensure the cloudwatch alarm exists.
    '''
    name = 'my test alarm'
    attributes = {'metric': 'ApproximateNumberOfMessagesVisible',
                  'namespace': 'AWS/SQS'}

    ret = {'name': name,
           'result': None,
           'changes': {},
           'comment': ''}

    mock = MagicMock(side_effect=[['ok_actions'], [], []])
    mock_bool = MagicMock(return_value=True)
    with patch.dict(boto_cloudwatch_alarm.__salt__,
                    {'boto_cloudwatch.get_alarm': mock,
                     'boto_cloudwatch.create_or_update_alarm': mock_bool}):
        with patch.dict(boto_cloudwatch_alarm.__opts__, {'test': True}):
            comt = ('alarm my test alarm is to be created/updated.')
            ret.update({'comment': comt})
            assert boto_cloudwatch_alarm.present(name, attributes) == ret

            comt = ('alarm my test alarm is to be created/updated.')
            ret.update({'comment': comt})
            assert boto_cloudwatch_alarm.present(name, attributes) == ret

        with patch.dict(boto_cloudwatch_alarm.__opts__, {'test': False}):
            changes = {'new':
                       {'metric': 'ApproximateNumberOfMessagesVisible',
                        'namespace': 'AWS/SQS'}}
            comt = ('alarm my test alarm is to be created/updated.')
            ret.update({'changes': changes, 'comment': '', 'result': True})
            assert boto_cloudwatch_alarm.present(name, attributes) == ret

# 'absent' function tests: 1

def test_absent():
    '''
    Test to ensure the named cloudwatch alarm is deleted.
    '''
    name = 'my test alarm'

    ret = {'name': name,
           'result': None,
           'changes': {},
           'comment': ''}

    mock = MagicMock(side_effect=[True, False])
    with patch.dict(boto_cloudwatch_alarm.__salt__,
                    {'boto_cloudwatch.get_alarm': mock}):
        with patch.dict(boto_cloudwatch_alarm.__opts__, {'test': True}):
            comt = ('alarm {0} is set to be removed.'.format(name))
            ret.update({'comment': comt})
            assert boto_cloudwatch_alarm.absent(name) == ret

            comt = ('my test alarm does not exist in None.')
            ret.update({'comment': comt, 'result': True})
            assert boto_cloudwatch_alarm.absent(name) == ret
