# Copyright 2017 IBM Corp.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.


import json
import socket


class SDKClient(object):
    """"""

    def __init__(self, addr='127.0.0.1', port=2000, request_timeout=3600):
        self.addr = addr
        self.port = port
        # request_timeout is used to set the client socket timeout when
        # waiting results returned from server.
        self.timeout = request_timeout

    def call(self, func, *api_args, **api_kwargs):
        """Send API call to SDK server and return results"""
        if not isinstance(func, str) or (func == ''):
            return {'overallRC': 1,
                    'rc': 1,
                    'rs': 5,
                    'errmsg': ('Invalid input for API name, should be a'
                               'string, type: %s specified.') % type(func),
                    'output': ''}
        # Create client socket
        try:
            cs = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        except socket.error as msg:
            return {'overallRC': 1,
                    'rc': 1,
                    'rs': 1,
                    'errmsg': 'Failed to create client socket: %s' % msg,
                    'output': ''}

        try:
            # Set socket timeout
            cs.settimeout(self.timeout)
            # Connect SDK server
            try:
                cs.connect((self.addr, self.port))
            except socket.error as msg:
                return {'overallRC': 1,
                        'rc': 1,
                        'rs': 2,
                        'errmsg': 'Failed to connect SDK server: %s' % msg,
                        'output': ''}

            # Prepare the data to be sent
            api_data = json.dumps((func, api_args, api_kwargs))
            # Send the API call data to SDK server
            sent = 0
            total_len = len(api_data)
            got_error = False
            while (sent < total_len):
                this_sent = cs.send(api_data[sent:])
                if this_sent == 0:
                    got_error = True
                    break
                sent += this_sent
            if got_error or sent != total_len:
                return {'overallRC': 1,
                        'rc': 1,
                        'rs': 3,
                        'errmsg': ('Failed to send API call to SDK server,'
                                   '%d bytes sent. API call: %s') % (sent,
                                                                     api_data),
                        'output': ''}

            # Receive data from server
            return_blocks = []
            while True:
                block = cs.recv(4096)
                if not block:
                    break
                return_blocks.append(block)
        finally:
            # Always close the client socket to avoid too many hanging
            # socket left.
            cs.close()

        # Transform the received stream to standard result form
        # This client assumes that the server would return result in
        # the standard result form, so client just return the received
        # data
        if return_blocks != []:
            results = json.loads(''.join(return_blocks))
        else:
            results = {'overallRC': 1,
                      'rc': 1,
                      'rs': 4,
                      'errmsg': ('Failed to receive API results from'
                                 'SDK server'),
                      'output': ''}
        return results
