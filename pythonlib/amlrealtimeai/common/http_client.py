# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.
from __future__ import absolute_import

import jwt
import json as jsonFuncs
import time
import requests
import logging

from collections import namedtuple
from requests import RequestException, ConnectionError, HTTPError

# python 2 and python 3 compatibility library

from .configuration import Configuration

log = logging.getLogger(__name__)


class HttpClient(object):
    """
    Generic Http client for MLDeploy client library.

    This client handles the client-server communication and is invariant across 
    implementations. 

    :param host: The base path for the server to call including port is needed.    
    :param access_token: a header value to pass when making calls to the API.
    """

    def __init__(self, host, access_token_fn=None):
        """
        Constructor of the class.
        """        
        self._session = requests.Session()
        
        # --- Host base url ---
        self.host = host
        if self.host and self.host.endswith('/'):
            self.host = self.host[:-1]

        # --- Default headers ---
        self.headers = {}
        
        # --- Set common defaults: User-Agent, Content-Type, Accept ---
        if not access_token_fn is None:
            access_token = access_token_fn()
            print(jwt.decode(access_token, verify=False))
            self.authorization = access_token
            self.access_token_fn = access_token_fn    

        self.content_type = 'application/json' #; charset=utf-8'
        self.accept = 'application/json'        
        # self.user_agent = '{title}/{version}/python'.format(
        #     title=__title__, version=__version__)

        # --- SSL ---
        
        # verify -- (optional) Either a boolean, in which case it controls 
        # whether we verify the server's TLS certificate, or a string, in which 
        # case it must be a path to a CA bundle to use
        if not Configuration().verify_ssl:
            verify = False
        else:  # default is `True`
            verify = Configuration().verify_ssl  # True|'/path/to/certfile'
        self._session.verify = verify

        # SSL client certificate default, if String, path to ssl client cert 
        # file (.pem). If Tuple, ('cert', 'key') pair.
        if Configuration().cert:
            self._session.cert = Configuration().cert
        
        # Proxies: Dictionary mapping protocol or protocol and hostname to the 
        # URL of the proxy.        
        if Configuration().proxies:
            self._session.proxy = Configuration().proxies

    @property
    def authorization(self):
        """
        Gets Authorization header
        """
        return self.headers['Authorization']

    @authorization.setter
    def authorization(self, value):
        """
        Sets Authorization header..
        """
        prefix = Configuration().api_key_prefix

        if prefix is None:
            prefix = ''            
        else:
            prefix = prefix + ' '            
        
        self.token = value
        self.headers['Authorization'] = prefix + value        

    @property
    def user_agent(self):
        """
        Gets User-Agent header.
        """
        return self.headers['User-Agent']

    @user_agent.setter
    def user_agent(self, value):
        """
        Sets User-Agent.
        """
        self.headers['User-Agent'] = value        

    @property
    def accept(self):
        """
        Gets Accept.
        """
        return self.headers['Accept']
        
    @accept.setter
    def accept(self, accepts):
        """
        Sets Accept.
        """
        if not isinstance(accepts, list):
            accepts = [accepts]

        # flattens `Accept` based on an array of accepts provided into string
        accepts = [accept.lower() for accept in accepts]
        self.headers['Accept'] = ', '.join(accepts)

    @property
    def content_type(self):
        """
        Gets Content-Type.
        """
        return self.headers['Content-Type']

    @content_type.setter
    def content_type(self, content_types):
        """
        Sets content-type
        """

        if not isinstance(content_types, list):
            content_types = [content_types]
        
        content_types = [ct.lower() for ct in content_types]

        if 'application/json' in content_types or '*/*' in content_types:
            content_type = 'application/json'
        else:
            content_type = content_types[0]

        self.headers['Content-Type'] = content_type

    def mount(self, prefix, adapter):
        self._session.mount(prefix, adapter)

    def set_header(self, name, value):
        self.headers[name] = value

    def get_header(self, name):
        return self.headers[name]
    
    def delete(self, resource_path, headers=None, raw_response=False, **kwargs):        
        return self.__send('DELETE', resource_path, headers=headers, raw_response=raw_response, **kwargs)

    def get(self, resource_path, headers=None, raw_response=False, **kwargs):
        return self.__send('GET', resource_path, headers=headers, raw_response=raw_response, **kwargs)

    def patch(self, resource_path, data=None, headers=None, raw_response=False, **kwargs):
        return self.__send('PATCH', resource_path, data=data, headers=headers, raw_response=raw_response, **kwargs)
        
    def post(self, resource_path, data=None, json=None, headers=None, raw_response=False, **kwargs):
        return self.__send('POST', resource_path, data=data, json=json, headers=headers, raw_response=raw_response, **kwargs)

    def put(self, resource_path, data=None, json=None, headers=None, raw_response=False, **kwargs):        
        return self.__send('PUT', resource_path, data=data, json=json, headers=headers, raw_response=raw_response, **kwargs)
        
    def __exit__(self, *args):
        self._session.close()
        
    def close(self):
        """Closes all adapters and as such the session"""
        for v in self._session.adapters.values():
            v.close()

    def __send(self, method, resource_path, data=None, json=None, headers=None, raw_response=False, **kwargs):
        """
        Makes the HTTP request using `requests`
        """

        url = self.host + resource_path

        if headers is None:
            headers = {}

        retry_count = 5
        sleep_delay = 1

        while True:

            # merge default headers with this request's headers for override
            h = self.headers.copy()
            h.update(headers)

            log.debug('-----------------------------------------------------------')
            log.debug('Request')
            log.debug('-----------------------------------------------------------')
            log.debug('     url: %s', url)
            log.debug('  method: %s', method)
            log.debug(' headers: %s', h)
            log.debug('    data: %s', data)
            log.debug('    json: %s', json)
            log.debug('**kwargs: %s', kwargs)
            log.debug('-----------------------------------------------------------')

            if method == 'GET':
                response = self._session.get(url, headers=h, **kwargs)

            elif method == 'HEAD':
                response = self._session.head(url, headers=h, **kwargs)

            elif method == 'OPTIONS':
                response = self._session.options(url, headers=h, **kwargs)

            elif method == 'POST':
                response = self._session.post(url, data, json, headers=h, **kwargs)
            
            elif method == 'PUT':
                response = self._session.put(url, data=jsonFuncs.dumps(json), headers=h, **kwargs)

            elif method == 'PATCH':
                response = self._session.patch(url, data,  headers=h, **kwargs)

            elif method == 'DELETE':
                response = self._session.delete(url, headers=h, **kwargs)

            else:
                raise ValueError(
                    'http method must be `GET`, `HEAD`, `OPTIONS`,'
                    ' `POST`, `PATCH`, `PUT` or `DELETE`.'
                )

            log.debug('-----------------------------------------------------------')
            log.debug('-----------------------------------------------------------')
            log.debug('Response')
            log.debug('-----------------------------------------------------------')
            log.debug(response.content if response is not None else '<NO-RESPONSE>')
            log.debug('-----------------------------------------------------------')

            if response.status_code == 500 or response.status_code == 408:
                retry_count = retry_count - 1
                if retry_count > 0:
                    time.sleep(sleep_delay)
                    sleep_delay = sleep_delay * 2
                    continue

            if response.status_code == 401 and not self.access_token_fn is None:
                authorization_uri_override = None

                if response.json()['error']['code'] == 'InvalidAuthenticationTokenTenant':
                    parsed_headers = dict(map(lambda x: x.split('='), response.headers['WWW-Authenticate'].split(', ')))
                    if('Bearer authorization_uri' in parsed_headers):
                        uri = parsed_headers['Bearer authorization_uri']
                        authorization_uri_override = uri[1:len(uri)-1]

                retry_count = retry_count - 1
                if retry_count > 0:
                    self.authorization = self.access_token_fn(authorization_uri_override)
                    continue

            try:
                response.raise_for_status()

            except (RequestException, ConnectionError, HTTPError) as e:
                log.error(e)
                raise HttpException(resp=response)
            
            if not raw_response and self.accept == 'application/json':
                #response = response.json()
                pass

            return response


class HttpException(Exception):

    def __init__(self, status=None, reason=None, resp=None):
        if resp is not None:
            self.status = resp.status_code
            self.reason = resp.reason
            self.body = resp.text
            self.headers = resp.headers
        else:
            self.status = status
            self.reason = reason
            self.body = None
            self.headers = None

    def __str__(self):
        """        
        Creates and returns a string representation of the current exception.
        """
        error = '({0})\n'\
            'Reason: {1}\n'.format(self.status, self.reason)
        if self.headers:
            error += 'HTTP response headers: {0}\n'.format(self.headers)

        if self.body:
            error += 'HTTP response body: {0}\n'.format(self.body)

        return error
