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
"""Handler for the root of the sdk API."""

import json

from zvmsdk import api
from zvmsdk import log
from zvmsdk.sdkwsgi.handlers import tokens
from zvmsdk.sdkwsgi.schemas import vswitch
from zvmsdk.sdkwsgi import util
from zvmsdk.sdkwsgi import validation
from zvmsdk.sdkwsgi import wsgi_wrapper
from zvmsdk import utils


_VSWITCHACTION = None
LOG = log.LOG


class VswitchAction(object):
    def __init__(self):
        self.api = api.SDKAPI(skip_input_check=True)

    def list(self):
        info = self.api.vswitch_get_list()

        return info

    @validation.schema(vswitch.create)
    def create(self, body):
        vsw = body['vswitch']
        name = vsw['name']
        rdev = vsw['rdev']

        self.api.vswitch_create(name, rdev)

    def delete(self, name):
        self.api.vswitch_delete(name)

    @validation.schema(vswitch.update)
    def update(self, name, body):
        vsw = body['vswitch']
        if 'grant_userid' in vsw:
            userid = vsw['grant_userid']
            self.api.vswitch_grant_user(name, userid)

        if 'revoke_userid' in vsw:
            userid = vsw['revoke_userid']
            self.api.vswitch_revoke_user(name, userid)

        if 'user_vlan_id' in vsw:
            userid = vsw['user_vlan_id']['userid']
            vlanid = vsw['user_vlan_id']['vlanid']
            self.api.vswitch_set_vlan_id_for_user(name, userid, vlanid)


def get_action():
    global _VSWITCHACTION
    if _VSWITCHACTION is None:
        _VSWITCHACTION = VswitchAction()
    return _VSWITCHACTION


@wsgi_wrapper.SdkWsgify
@tokens.validate
def vswitch_list(req):
    def _vswitch_list(req):
        action = get_action()
        return action.list()

    info = _vswitch_list(req)
    info_json = json.dumps({'vswlist': info})
    req.response.body = utils.to_utf8(info_json)
    req.response.content_type = 'application/json'
    return req.response


@wsgi_wrapper.SdkWsgify
@tokens.validate
def vswitch_create(req):

    def _vswitch_create(req):
        action = get_action()
        body = util.extract_json(req.body)

        action.create(body=body)

    _vswitch_create(req)

    req.response.status = 200
    req.response.content_type = None
    return req.response


@wsgi_wrapper.SdkWsgify
@tokens.validate
def vswitch_delete(req):

    def _vswitch_delete(name):
        action = get_action()

        action.delete(name)

    name = util.wsgi_path_item(req.environ, 'name')
    _vswitch_delete(name)

    req.response.status = 204
    req.response.content_type = None
    return req.response


@wsgi_wrapper.SdkWsgify
@tokens.validate
def vswitch_update(req):

    def _vswitch_update(name, req):
        body = util.extract_json(req.body)
        action = get_action()

        action.update(name, body=body)

    name = util.wsgi_path_item(req.environ, 'name')

    _vswitch_update(name, req)

    req.response.status = 200
    req.response.content_type = None
    return req.response
