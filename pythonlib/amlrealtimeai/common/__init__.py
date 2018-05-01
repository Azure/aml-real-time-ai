# ------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for 
# license information.
# ------------------------------------------------------------------------------

# -*- coding: utf-8; tab-width: 4; indent-tabs-mode: t; python-indent: 4 -*-

from __future__ import absolute_import

__path__ = __import__('pkgutil').extend_path(__path__, __name__)

# import into common package
from .http_client import HttpClient
from .configuration import Configuration

configuration = Configuration()
