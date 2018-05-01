# ------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for 
# license information.
# ------------------------------------------------------------------------------

# -*- coding: utf-8; tab-width: 4; indent-tabs-mode: t; python-indent: 4 -*-

from __future__ import absolute_import

import sys
import logging

from six import iteritems
from six.moves import http_client as httplib


def singleton(cls, *args, **kw):
    instances = {}

    def _singleton():
        if cls not in instances:
            instances[cls] = cls(*args, **kw)
        return instances[cls]
    return _singleton


@singleton
class Configuration(object):
    """
    Configuration
    """

    def __init__(self):
        """
        Constructor
        """
        
        # Temp file folder for downloading files
        self.temp_folder_path = None

        # --- Authentication Settings ---        
        # dict to store API prefix (e.g. Bearer)
        self.api_key_prefix = 'Bearer' # default
        self.access_token = None

        # --- Logging Settings ---
        self.logger = {}        
        self.logger['package_logger'] = logging.getLogger('azure')
        self.logger['urllib3_logger'] = logging.getLogger('urllib3')
        # Log format
        self.logger_format = '%(asctime)s %(levelname)s %(message)s'
        # Log stream handler
        self.logger_stream_handler = None
        # Log file handler
        self.logger_file_handler = None
        # Debug file location
        self.logger_file = None
        # Debug switch
        self.debug = False
        
        # --- SSL/TLS verification ---
        # Set this to false to skip verifying SSL certificate when calling API
        # from https server.
        # Options:
        # --------
        # verify -- (optional) Either a boolean, in which case it controls 
        # whether we verify the server's TLS certificate, or a string, in which 
        # case it must be a path to a CA bundle to use
        # Example:
        # verify_ssl = True (default)
        # verify_ssl = False
        # verify_ssl = '/etc/ssl/certs/ca-certificates.crt'
        self.verify_ssl = True
                         
        # Set this to customize the certificate file to verify the peer.
        # SSL client certificate default, if String, path to ssl client cert 
        # file (.pem). If Tuple ('client certificate file, 'client key') pair.
        # Example:
        # cert = ''
        # cert = ('cert.pem', 'key.pem')
        self.cert = None

        # Proxy URL
        self.proxies = None

    @property
    def api_key_prefix(self):
        """
        Gets the api_key_prefix (ex. Bearer).
        """
        return self.__api_key_prefix

    @api_key_prefix.setter
    def api_key_prefix(self, value):
        self.__api_key_prefix = value

    @property
    def logger_file(self):
        """
        Gets the logger_file.
        """
        return self.__logger_file

    @logger_file.setter
    def logger_file(self, value):
        """
        Sets the logger_file.

        If the logger_file is None, then add stream handler and remove file
        handler. Otherwise, add file handler and remove stream handler.

        :param value: The logger_file path.
        :type: str
        """
        self.__logger_file = value
        if self.__logger_file:
            # If set logging file,
            # then add file handler and remove stream handler.
            self.logger_file_handler = logging.FileHandler(self.__logger_file)
            self.logger_file_handler.setFormatter(self.logger_formatter)
            for _, logger in iteritems(self.logger):
                logger.addHandler(self.logger_file_handler)
                if self.logger_stream_handler:
                    logger.removeHandler(self.logger_stream_handler)
        else:
            # If not set logging file,
            # then add stream handler and remove file handler.
            self.logger_stream_handler = logging.StreamHandler()
            self.logger_stream_handler.setFormatter(self.logger_formatter)
            for _, logger in iteritems(self.logger):
                logger.addHandler(self.logger_stream_handler)
                if self.logger_file_handler:
                    logger.removeHandler(self.logger_file_handler)

    @property
    def debug(self):
        """
        Gets the debug status.
        """
        return self.__debug

    @debug.setter
    def debug(self, value):
        """
        Sets the debug status.

        :param value: The debug status, True or False.
        :type: bool
        """
        self.__debug = value
        if self.__debug:
            # if debug status is True, turn on debug logging
            for _, logger in iteritems(self.logger):
                logger.setLevel(logging.DEBUG)
            # turn on httplib debug
            httplib.HTTPConnection.debuglevel = 1
        else:
            # if debug status is False, turn off debug logging,
            # setting log level to default `logging.WARNING`
            for _, logger in iteritems(self.logger):
                logger.setLevel(logging.WARNING)
            # turn off httplib debug
            httplib.HTTPConnection.debuglevel = 0

    @property
    def logger_format(self):
        """
        Gets the logger_format.
        """
        return self.__logger_format

    @logger_format.setter
    def logger_format(self, value):
        """
        Sets the logger_format.

        The logger_formatter will be updated when sets logger_format.

        :param value: The format string.
        :type: str
        """
        self.__logger_format = value
        self.logger_formatter = logging.Formatter(self.__logger_format)

    def to_debug_report(self):
        """
        Gets the essential information for debugging.

        :return: The report for debugging.
        """
        return "Python SDK Debug Report:\n"\
               "OS: {env}\n"\
               "Python Version: {pyversion}\n"\
               "Version of the API: {version}\n"\
               "SDK Package {name} Version: {version}".\
               format(
                   name=__title__,
                   version=__version__,
                   env=sys.platform,                   
                   pyversion=sys.version)
