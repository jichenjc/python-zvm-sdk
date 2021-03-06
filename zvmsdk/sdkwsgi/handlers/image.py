#    licensed under the Apache License, Version 2.0 (the "License"); you may
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
"""Handler for the image of the sdk API."""

import json

from zvmsdk import api
from zvmsdk import log
from zvmsdk import utils
from zvmsdk.sdkwsgi.handlers import tokens
from zvmsdk.sdkwsgi.schemas import image
from zvmsdk.sdkwsgi import util
from zvmsdk.sdkwsgi import validation
from zvmsdk.sdkwsgi import wsgi_wrapper

_IMAGEACTION = None
LOG = log.LOG


class ImageAction(object):

    def __init__(self):
        self.api = api.SDKAPI(skip_input_check=True)

    @validation.schema(image.create)
    def create(self, body):
        image = body['image']
        image_name = image['image_name']
        url = image['url']
        remote_host = image.get('remotehost', None)
        image_meta = image['image_meta']

        self.api.image_import(image_name, url, image_meta, remote_host)

    def get_root_disk_size(self, name):
        # FIXME: this param need combined image nameg, e.g the profile
        # name, not the given image name from customer side
        return self.api.image_get_root_disk_size(name)

    def delete(self, name):
        self.api.image_delete(name)

    def query(self, imagename):
        return self.api.image_query(imagename)


def get_action():
    global _IMAGEACTION
    if _IMAGEACTION is None:
        _IMAGEACTION = ImageAction()
    return _IMAGEACTION


@wsgi_wrapper.SdkWsgify
@tokens.validate
def image_create(req):

    def _image_create(req):
        action = get_action()
        body = util.extract_json(req.body)
        action.create(body=body)

    _image_create(req)

    req.response.status = 200
    req.response.content_type = None
    return req.response


@wsgi_wrapper.SdkWsgify
@tokens.validate
def image_get_root_disk_size(req):

    def _image_get_root_disk_size(name):
        action = get_action()
        return action.get_root_disk_size(name)

    name = util.wsgi_path_item(req.environ, 'name')
    info = _image_get_root_disk_size(name)

    info_json = json.dumps({'size': info})
    req.response.body = utils.to_utf8(info_json)
    req.response.content_type = 'application/json'
    return req.response


@wsgi_wrapper.SdkWsgify
@tokens.validate
def image_delete(req):

    def _image_delete(name):
        action = get_action()
        action.delete(name)

    name = util.wsgi_path_item(req.environ, 'name')
    _image_delete(name)

    req.response.status = 204
    req.response.content_type = None
    return req.response


@wsgi_wrapper.SdkWsgify
@tokens.validate
def image_query(req):

    def _image_query(imagename):
        action = get_action()
        return action.query(imagename)

    imagename = None
    if 'imagename' in req.GET:
        imagename = req.GET['imagename']
    info = _image_query(imagename)

    info_json = json.dumps({'images': info})
    req.response.body = utils.to_utf8(info_json)
    req.response.content_type = 'application/json'
    return req.response
