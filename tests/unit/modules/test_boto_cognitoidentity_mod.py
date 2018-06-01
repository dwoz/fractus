# -*- coding: utf-8 -*-

# Import Python libs
from __future__ import absolute_import, print_function, unicode_literals
import logging

# Import Salt libs
import salt.modules.boto_cognitoidentity as boto_cognitoidentity

# Import Testing libs
import pytest
from mock import MagicMock, patch

boto3 = pytest.importorskip('boto3', minversion='1.2.1')
exceptions = pytest.importorskip('botocore.exceptions')

error_message = 'An error occurred (101) when calling the {0} operation: Test-defined error'
error_content = {
  'Error': {
    'Code': 101,
    'Message': "Test-defined error"
  }
}

first_pool_id = 'first_pool_id'
first_pool_name = 'first_pool'
second_pool_id = 'second_pool_id'
second_pool_name = 'second_pool'
second_pool_name_updated = 'second_pool_updated'
third_pool_id = 'third_pool_id'
third_pool_name = first_pool_name

identity_pools_ret = dict(IdentityPools=[dict(IdentityPoolId=first_pool_id,
                                              IdentityPoolName=first_pool_name),
                                         dict(IdentityPoolId=second_pool_id,
                                              IdentityPoolName=second_pool_name),
                                         dict(IdentityPoolId=third_pool_id,
                                              IdentityPoolName=third_pool_name)])

first_pool_ret = dict(IdentityPoolId=first_pool_id,
                      IdentityPoolName=first_pool_name,
                      AllowUnauthenticatedIdentities=False,
                      SupportedLoginProviders={'accounts.google.com': 'testing123',
                                               'api.twitter.com': 'testing123',
                                               'graph.facebook.com': 'testing123',
                                               'www.amazon.com': 'testing123'},
                      DeveloperProviderName='test_provider',
                      OpenIdConnectProviderARNs=['some_provider_arn',
                                                 'another_provider_arn'])

first_pool_role_ret = dict(IdentityPoolId=first_pool_id,
                           Roles=dict(authenticated='first_pool_auth_role',
                                      unauthenticated='first_pool_unauth_role'))

second_pool_ret = dict(IdentityPoolId=second_pool_id,
                       IdentityPoolName=second_pool_name,
                       AllowUnauthenticatedIdentities=False)

third_pool_ret = dict(IdentityPoolId=third_pool_id,
                      IdentityPoolName=third_pool_name,
                      AllowUnauthenticatedIdentities=False,
                      DeveloperProviderName='test_provider2')

third_pool_role_ret = dict(IdentityPoolId=third_pool_id)

default_pool_ret = dict(IdentityPoolId='default_pool_id',
                        IdentityPoolName='default_pool_name',
                        AllowUnauthenticatedIdentities=False,
                        DeveloperProviderName='test_provider_default')

default_pool_role_ret = dict(IdentityPoolId='default_pool_id')

log = logging.getLogger(__name__)


def setup_module():
    pytest.helpers.setup_loader({boto_cognitoidentity: {'__utils__': pytest.utils}})
    boto_cognitoidentity.__init__(pytest.opts)


def _describe_identity_pool_side_effect(*args, **kwargs):
    if kwargs.get('IdentityPoolId') == first_pool_id:
        return first_pool_ret
    elif kwargs.get('IdentityPoolId') == third_pool_id:
        return third_pool_ret
    else:
        return default_pool_ret

def test_that_when_describing_a_named_identity_pool_and_pool_exists_the_describe_identity_pool_method_returns_pools_properties(boto_conn):
    '''
    Tests describing identity pool when the pool's name exists
    '''
    boto_conn.list_identity_pools.return_value = identity_pools_ret
    boto_conn.describe_identity_pool.side_effect = _describe_identity_pool_side_effect
    result = boto_cognitoidentity.describe_identity_pools(IdentityPoolName=first_pool_name, **pytest.conn_parameters)
    assert result.get('identity_pools') == [first_pool_ret, third_pool_ret]

def test_that_when_describing_a_identity_pool_by_its_id_and_pool_exists_the_desribe_identity_pool_method_returns_pools_properties(boto_conn):
    '''
    Tests describing identity pool when the given pool's id exists
    '''
    boto_conn.describe_identity_pool.return_value = third_pool_ret
    result = boto_cognitoidentity.describe_identity_pools(IdentityPoolName='', IdentityPoolId=third_pool_id, **pytest.conn_parameters)
    assert result.get('identity_pools') == [third_pool_ret]
    assert boto_conn.conn.list_identity_pools.call_count == 0

def test_that_when_describing_a_named_identity_pool_and_pool_does_not_exist_the_describe_identity_pool_method_returns_none(boto_conn):
    '''
    Tests describing identity pool when the pool's name doesn't exist
    '''
    boto_conn.list_identity_pools.return_value = identity_pools_ret
    boto_conn.describe_identity_pool.return_value = first_pool_ret
    result = boto_cognitoidentity.describe_identity_pools(IdentityPoolName='no_such_pool', **pytest.conn_parameters)
    assert result.get('identity_pools', 'no such key') is None

def test_that_when_describing_a_named_identity_pool_and_error_thrown_the_describe_identity_pool_method_returns_error(boto_conn):
    '''
    Tests describing identity pool returns error when there is an exception to boto3 calls
    '''
    boto_conn.list_identity_pools.return_value = identity_pools_ret
    boto_conn.describe_identity_pool.side_effect = exceptions.ClientError(error_content, 'error on describe identity pool')
    result = boto_cognitoidentity.describe_identity_pools(IdentityPoolName=first_pool_name, **pytest.conn_parameters)
    assert result.get('error', {}).get('message') == error_message.format('error on describe identity pool')

def test_that_when_create_identity_pool_the_create_identity_pool_method_returns_created_identity_pool(boto_conn):
    '''
    Tests the positive case where create identity pool succeeds
    '''
    return_val = default_pool_ret.copy()
    return_val.pop('DeveloperProviderName', None)
    boto_conn.create_identity_pool.return_value = return_val
    result = boto_cognitoidentity.create_identity_pool(IdentityPoolName='default_pool_name', **pytest.conn_parameters)
    mock_calls = boto_conn.mock_calls
    #name, args, kwargs = mock_calls[0]
    assert result.get('created') is True
    assert len(mock_calls) == 1
    assert mock_calls[0][0] == 'create_identity_pool'
    assert 'DeveloperProviderName' not in mock_calls[0][2]

def test_that_when_create_identity_pool_and_error_thrown_the_create_identity_pool_method_returns_error(boto_conn):
    '''
    Tests the negative case where create identity pool has a boto3 client error
    '''
    boto_conn.create_identity_pool.side_effect = exceptions.ClientError(error_content, 'create_identity_pool')
    result = boto_cognitoidentity.create_identity_pool(IdentityPoolName='default_pool_name', **pytest.conn_parameters)
    assert result.get('created') is False
    assert result.get('error', {}).get('message') == error_message.format('create_identity_pool')

def test_that_when_delete_identity_pools_with_multiple_matching_pool_names_the_delete_identity_pools_methos_returns_true_and_deleted_count(boto_conn):
    '''
    Tests that given 2 matching pool ids, the operation returns deleted status of true and
    count 2
    '''
    boto_conn.list_identity_pools.return_value = identity_pools_ret
    boto_conn.delete_identity_pool.return_value = None
    result = boto_cognitoidentity.delete_identity_pools(IdentityPoolName=first_pool_name, **pytest.conn_parameters)
    mock_calls = boto_conn.mock_calls
    assert result.get('deleted') is True
    assert result.get('count') == 2
    assert len(mock_calls) == 3
    assert mock_calls[1][0] == 'delete_identity_pool'
    assert mock_calls[2][0] == 'delete_identity_pool'
    assert mock_calls[1][2].get('IdentityPoolId') == first_pool_id
    assert mock_calls[2][2].get('IdentityPoolId') == third_pool_id

def test_that_when_delete_identity_pools_with_no_matching_pool_names_the_delete_identity_pools_method_returns_false(boto_conn):
    '''
    Tests that the given pool name does not exist, the operation returns deleted status of false
    and count 0
    '''
    boto_conn.list_identity_pools.return_value = identity_pools_ret
    result = boto_cognitoidentity.delete_identity_pools(IdentityPoolName='no_such_pool_name', **pytest.conn_parameters)
    mock_calls = boto_conn.mock_calls
    assert result.get('deleted') is False
    assert result.get('count') == 0
    assert len(mock_calls) == 1

def test_that_when_delete_identity_pools_and_error_thrown_the_delete_identity_pools_method_returns_false_and_the_error(boto_conn):
    '''
    Tests that the delete_identity_pool method throws an exception
    '''
    boto_conn.delete_identity_pool.side_effect = exceptions.ClientError(error_content, 'delete_identity_pool')
    # try to delete an unexistent pool id "no_such_pool_id"
    result = boto_cognitoidentity.delete_identity_pools(IdentityPoolName=first_pool_name, IdentityPoolId='no_such_pool_id', **pytest.conn_parameters)
    mock_calls = boto_conn.mock_calls
    assert result.get('deleted') is False
    assert result.get('count') is None
    assert result.get('error', {}).get('message') == error_message.format('delete_identity_pool')
    assert len(mock_calls) == 1

def _get_identity_pool_roles_side_effect(*args, **kwargs):
    if kwargs.get('IdentityPoolId') == first_pool_id:
        return first_pool_role_ret
    elif kwargs.get('IdentityPoolId') == third_pool_id:
        return third_pool_role_ret
    else:
        return default_pool_role_ret

def test_that_when_get_identity_pool_roles_with_matching_pool_names_the_get_identity_pool_roles_method_returns_pools_role_properties(boto_conn):
    '''
    Tests that the given 2 pool id's matching the given pool name, the results are
    passed through as a list of identity_pool_roles
    '''
    boto_conn.list_identity_pools.return_value = identity_pools_ret
    boto_conn.get_identity_pool_roles.side_effect = _get_identity_pool_roles_side_effect
    result = boto_cognitoidentity.get_identity_pool_roles(IdentityPoolName=first_pool_name, **pytest.conn_parameters)
    id_pool_roles = result.get('identity_pool_roles')
    assert id_pool_roles is not None
    assert result.get('error', 'key_should_not_be_there') == 'key_should_not_be_there'
    assert len(id_pool_roles) == 2
    assert id_pool_roles[0] == first_pool_role_ret
    assert id_pool_roles[1] == third_pool_role_ret

def test_that_when_get_identity_pool_roles_with_no_matching_pool_names_the_get_identity_pool_roles_method_returns_none(boto_conn):
    '''
    Tests that the given no pool id's matching the given pool name, the results returned is
    None and get_identity_pool_roles should never be called
    '''
    boto_conn.list_identity_pools.return_value = identity_pools_ret
    result = boto_cognitoidentity.get_identity_pool_roles(IdentityPoolName="no_such_pool_name", **pytest.conn_parameters)
    mock_calls = boto_conn.mock_calls
    assert result.get('identity_pool_roles', 'key_should_be_there') is None
    assert len(mock_calls) == 1
    assert result.get('error', 'key_should_not_be_there') == 'key_should_not_be_there'

def test_that_when_get_identity_pool_roles_and_error_thrown_due_to_invalid_pool_id_the_get_identity_pool_roles_method_returns_error(boto_conn):
    '''
    Tests that given an invalid pool id, we properly handle error generated from get_identity_pool_roles
    '''
    boto_conn.get_identity_pool_roles.side_effect = exceptions.ClientError(error_content, 'get_identity_pool_roles')
    # try to delete an unexistent pool id "no_such_pool_id"
    result = boto_cognitoidentity.get_identity_pool_roles(IdentityPoolName='', IdentityPoolId='no_such_pool_id', **pytest.conn_parameters)
    mock_calls = boto_conn.mock_calls
    assert result.get('error', {}).get('message') == error_message.format('get_identity_pool_roles')
    assert len(mock_calls) == 1

def test_that_when_set_identity_pool_roles_with_invalid_pool_id_the_set_identity_pool_roles_method_returns_set_false_and_error(boto_conn):
    '''
    Tests that given an invalid pool id, we properly handle error generated from set_identity_pool_roles
    '''
    boto_conn.set_identity_pool_roles.side_effect = exceptions.ClientError(error_content, 'set_identity_pool_roles')
    result = boto_cognitoidentity.set_identity_pool_roles(IdentityPoolId='no_such_pool_id', **pytest.conn_parameters)
    mock_calls = boto_conn.mock_calls
    assert result.get('set') is False
    assert result.get('error', {}).get('message') == error_message.format('set_identity_pool_roles')
    assert len(mock_calls) == 1

def test_that_when_set_identity_pool_roles_with_no_roles_specified_the_set_identity_pool_roles_method_unset_the_roles(boto_conn):
    '''
    Tests that given a valid pool id, and no other roles given, the role for the pool is cleared.
    '''
    boto_conn.set_identity_pool_roles.return_value = None
    result = boto_cognitoidentity.set_identity_pool_roles(IdentityPoolId='some_id', **pytest.conn_parameters)
    mock_calls = boto_conn.mock_calls
    assert result.get('set') is True
    assert len(mock_calls) == 1
    assert mock_calls[0][2].get('Roles') == {}

def test_that_when_set_identity_pool_roles_with_only_auth_role_specified_the_set_identity_pool_roles_method_only_set_the_auth_role(boto_conn):
    '''
    Tests that given a valid pool id, and only other given role is the AuthenticatedRole, the auth role for the
    pool is set and unauth role is cleared.
    '''
    boto_conn.set_identity_pool_roles.return_value = None
    with patch.dict(boto_cognitoidentity.__salt__, {'boto_iam.describe_role': MagicMock(return_value={'arn': 'my_auth_role_arn'})}):
        expected_roles = dict(authenticated='my_auth_role_arn')
        result = boto_cognitoidentity.set_identity_pool_roles(IdentityPoolId='some_id', AuthenticatedRole='my_auth_role', **pytest.conn_parameters)
        mock_calls = boto_conn.mock_calls
        assert result.get('set') is True
        assert len(mock_calls) == 1
        assert mock_calls[0][2].get('Roles') == expected_roles

def test_that_when_set_identity_pool_roles_with_only_unauth_role_specified_the_set_identity_pool_roles_method_only_set_the_unauth_role(boto_conn):
    '''
    Tests that given a valid pool id, and only other given role is the UnauthenticatedRole, the unauth role for the
    pool is set and the auth role is cleared.
    '''
    boto_conn.set_identity_pool_roles.return_value = None
    with patch.dict(boto_cognitoidentity.__salt__, {'boto_iam.describe_role': MagicMock(return_value={'arn': 'my_unauth_role_arn'})}):
        expected_roles = dict(unauthenticated='my_unauth_role_arn')
        result = boto_cognitoidentity.set_identity_pool_roles(IdentityPoolId='some_id', UnauthenticatedRole='my_unauth_role', **pytest.conn_parameters)
        mock_calls = boto_conn.mock_calls
        assert result.get('set') is True
        assert len(mock_calls) == 1
        assert mock_calls[0][2].get('Roles') == expected_roles

def test_that_when_set_identity_pool_roles_with_both_roles_specified_the_set_identity_pool_role_method_set_both_roles(boto_conn):
    '''
    Tests setting of both roles to valid given roles
    '''
    boto_conn.set_identity_pool_roles.return_value = None
    with patch.dict(boto_cognitoidentity.__salt__, {'boto_iam.describe_role': MagicMock(return_value={'arn': 'my_unauth_role_arn'})}):
        expected_roles = dict(authenticated='arn:aws:iam:my_auth_role',
                              unauthenticated='my_unauth_role_arn')
        result = boto_cognitoidentity.set_identity_pool_roles(IdentityPoolId='some_id', AuthenticatedRole='arn:aws:iam:my_auth_role', UnauthenticatedRole='my_unauth_role', **pytest.conn_parameters)
        mock_calls = boto_conn.mock_calls
        assert result.get('set') is True
        assert len(mock_calls) == 1
        assert mock_calls[0][2].get('Roles') == expected_roles

def test_that_when_set_identity_pool_roles_given_invalid_auth_role_the_set_identity_pool_method_returns_set_false_and_error(boto_conn):
    '''
    Tests error handling for invalid auth role
    '''
    with patch.dict(boto_cognitoidentity.__salt__, {'boto_iam.describe_role': MagicMock(return_value=False)}):
        result = boto_cognitoidentity.set_identity_pool_roles(IdentityPoolId='some_id', AuthenticatedRole='no_such_auth_role', **pytest.conn_parameters)
        mock_calls = boto_conn.mock_calls
        assert result.get('set') is False
        assert 'no_such_auth_role' in result.get('error', '')
        assert len(mock_calls) == 0

def test_that_when_set_identity_pool_roles_given_invalid_unauth_role_the_set_identity_pool_method_returns_set_false_and_error(boto_conn):
    '''
    Tests error handling for invalid unauth role
    '''
    with patch.dict(boto_cognitoidentity.__salt__, {'boto_iam.describe_role': MagicMock(return_value=False)}):
        result = boto_cognitoidentity.set_identity_pool_roles(IdentityPoolId='some_id', AuthenticatedRole='arn:aws:iam:my_auth_role', UnauthenticatedRole='no_such_unauth_role', **pytest.conn_parameters)
        mock_calls = boto_conn.mock_calls
        assert result.get('set') is False
        assert 'no_such_unauth_role' in result.get('error', '')
        assert len(mock_calls) == 0

def test_that_when_update_identity_pool_given_invalid_pool_id_the_update_identity_pool_method_returns_updated_false_and_error(boto_conn):
    '''
    Tests error handling for invalid pool id
    '''
    boto_conn.describe_identity_pool.side_effect = exceptions.ClientError(error_content, 'error on describe identity pool with pool id')
    result = boto_cognitoidentity.update_identity_pool(IdentityPoolId='no_such_pool_id', **pytest.conn_parameters)
    assert result.get('updated') is False
    assert result.get('error', {}).get('message') == error_message.format('error on describe identity pool with pool id')

def test_that_when_update_identity_pool_given_only_valid_pool_id_the_update_identity_pool_method_returns_udpated_identity(boto_conn):
    '''
    Tests the base case of calling update_identity_pool with only the pool id, verify
    that the passed parameters into boto3 update_identity_pool has at least all the
    expected required parameters in IdentityPoolId, IdentityPoolName and AllowUnauthenticatedIdentities
    '''
    boto_conn.describe_identity_pool.return_value = second_pool_ret
    boto_conn.update_identity_pool.return_value = second_pool_ret
    expected_params = second_pool_ret
    result = boto_cognitoidentity.update_identity_pool(IdentityPoolId=second_pool_id, **pytest.conn_parameters)
    assert result.get('updated') is True
    assert result.get('identity_pool') == second_pool_ret
    boto_conn.update_identity_pool.assert_called_with(**expected_params)

def test_that_when_update_identity_pool_given_valid_pool_id_and_pool_name_the_update_identity_pool_method_returns_updated_identity_pool(boto_conn):
    '''
    Tests successful update of a pool's name
    '''
    boto_conn.describe_identity_pool.return_value = second_pool_ret
    second_pool_updated_ret = second_pool_ret.copy()
    second_pool_updated_ret['IdentityPoolName'] = second_pool_name_updated
    boto_conn.update_identity_pool.return_value = second_pool_updated_ret
    expected_params = second_pool_updated_ret
    result = boto_cognitoidentity.update_identity_pool(IdentityPoolId=second_pool_id, IdentityPoolName=second_pool_name_updated, **pytest.conn_parameters)
    assert result.get('updated') is True
    assert result.get('identity_pool') == second_pool_updated_ret
    boto_conn.update_identity_pool.assert_called_with(**expected_params)

def test_that_when_update_identity_pool_given_empty_dictionary_for_supported_login_providers_the_update_identity_pool_method_is_called_with_proper_request_params(boto_conn):
    '''
    Tests the request parameters to boto3 update_identity_pool's AllowUnauthenticatedIdentities is {}
    '''
    boto_conn.describe_identity_pool.return_value = first_pool_ret
    first_pool_updated_ret = first_pool_ret.copy()
    first_pool_updated_ret.pop('SupportedLoginProviders')
    boto_conn.update_identity_pool.return_value = first_pool_updated_ret
    expected_params = first_pool_ret.copy()
    expected_params['SupportedLoginProviders'] = {}
    expected_params.pop('DeveloperProviderName')
    expected_params.pop('OpenIdConnectProviderARNs')
    result = boto_cognitoidentity.update_identity_pool(IdentityPoolId=first_pool_id, SupportedLoginProviders={}, **pytest.conn_parameters)
    assert result.get('updated') is True
    assert result.get('identity_pool') == first_pool_updated_ret
    boto_conn.update_identity_pool.assert_called_with(**expected_params)

def test_that_when_update_identity_pool_given_empty_list_for_openid_connect_provider_arns_the_update_identity_pool_method_is_called_with_proper_request_params(boto_conn):
    '''
    Tests the request parameters to boto3 update_identity_pool's OpenIdConnectProviderARNs is []
    '''
    boto_conn.describe_identity_pool.return_value = first_pool_ret
    first_pool_updated_ret = first_pool_ret.copy()
    first_pool_updated_ret.pop('OpenIdConnectProviderARNs')
    boto_conn.update_identity_pool.return_value = first_pool_updated_ret
    expected_params = first_pool_ret.copy()
    expected_params.pop('SupportedLoginProviders')
    expected_params.pop('DeveloperProviderName')
    expected_params['OpenIdConnectProviderARNs'] = []
    result = boto_cognitoidentity.update_identity_pool(IdentityPoolId=first_pool_id, OpenIdConnectProviderARNs=[], **pytest.conn_parameters)
    assert result.get('updated') is True
    assert result.get('identity_pool') == first_pool_updated_ret
    boto_conn.update_identity_pool.assert_called_with(**expected_params)

def test_that_when_update_identity_pool_given_developer_provider_name_when_developer_provider_name_was_set_previously_the_udpate_identity_pool_method_is_called_without_developer_provider_name_param(boto_conn):
    '''
    Tests the request parameters do not include 'DeveloperProviderName' if this was previously set
    for the given pool id
    '''
    boto_conn.describe_identity_pool.return_value = first_pool_ret
    boto_conn.update_identity_pool.return_value = first_pool_ret
    expected_params = first_pool_ret.copy()
    expected_params.pop('SupportedLoginProviders')
    expected_params.pop('DeveloperProviderName')
    expected_params.pop('OpenIdConnectProviderARNs')
    result = boto_cognitoidentity.update_identity_pool(IdentityPoolId=first_pool_id, DeveloperProviderName='this should not change', **pytest.conn_parameters)
    assert result.get('updated') is True
    assert result.get('identity_pool') == first_pool_ret
    boto_conn.update_identity_pool.assert_called_with(**expected_params)

def test_that_when_update_identity_pool_given_developer_provider_name_is_included_in_the_params_when_associated_for_the_first_time(boto_conn):
    '''
    Tests the request parameters include 'DeveloperProviderName' when the pool did not have this
    property set previously.
    '''
    boto_conn.describe_identity_pool.return_value = second_pool_ret
    second_pool_updated_ret = second_pool_ret.copy()
    second_pool_updated_ret['DeveloperProviderName'] = 'added_developer_provider'
    boto_conn.update_identity_pool.return_value = second_pool_updated_ret
    expected_params = second_pool_updated_ret.copy()
    result = boto_cognitoidentity.update_identity_pool(IdentityPoolId=second_pool_id, DeveloperProviderName='added_developer_provider', **pytest.conn_parameters)
    assert result.get('updated') is True
    assert result.get('identity_pool') == second_pool_updated_ret
    boto_conn.update_identity_pool.assert_called_with(**expected_params)

def test_that_the_update_identity_pool_method_handles_exception_from_boto3(boto_conn):
    '''
    Tests the error handling of exception generated by boto3 update_identity_pool
    '''
    boto_conn.describe_identity_pool.return_value = second_pool_ret
    second_pool_updated_ret = second_pool_ret.copy()
    second_pool_updated_ret['DeveloperProviderName'] = 'added_developer_provider'
    boto_conn.update_identity_pool.side_effect = exceptions.ClientError(error_content, 'update_identity_pool')
    result = boto_cognitoidentity.update_identity_pool(IdentityPoolId=second_pool_id, DeveloperProviderName='added_developer_provider', **pytest.conn_parameters)
    assert result.get('updated') is False
    assert result.get('error', {}).get('message') == error_message.format('update_identity_pool')