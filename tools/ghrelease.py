#!/usr/bin/env python
# -*- encoding: utf-8 -*-

import os
import mimetypes
from pygithub3.services.base import Service
from pygithub3.requests.base import Request
from pygithub3.resources.base import Resource
from pygithub3.resources.repos import Author

#
# Resources objects for releases requests
#

class Uploader(Resource):
    pass

class Asset(Resource):
    _dates = ("created_at", "published_at")
    _maps = {'uploader': Uploader}

class Release(Resource):
    _dates = ("created_at", "published_at")
    _maps = {'author': Author}
    _collection_maps = {'assets': Asset}

    def upload(self, filename):
        basename = os.path.basename(filename)
        url = self.upload_url.split("assets")[0] + "assets?name=%s" % basename
        print 'url:', url
        f = open(filename, 'rb')
        response = self._client.requester.request('post', url,
                   headers={'Content-Type':'application/octet-stream'},
                   data=f.read(), verify=False)
        return Asset.loads(response.content)

    def has_asset(self, filename):
        basename = os.path.basename(filename)
        for asset in self.assets:
            if asset.name == basename:
                return True
        return False


#
# Release requests
#

class List(Request):
    uri = 'repos/{user}/{repo}/releases'
    resource = Release

class Get(Request):
    uri = 'repos/{user}/{repo}/releases/{id}'
    resource = Release

class Tags(Request):
    uri = 'repos/{user}/{repo}/releases/tags/{tag}'
    resource = Release

class Create(Request):
    uri = 'repos/{user}/{repo}/releases'
    resource = Release
    body_schema = {
        'schema': ('tag_name', 'target_commitish', 'name', 'body', 'draft',
                   'prerelease'),
        'required': ('tag_name', )
    }


#
# Main 'Releases' service object
#

class Releases(Service):
    """ Consume `Repo Collaborators API
    <http://developer.github.com/v3/repos/releases>`_ """

    def _consolidate(self, user, repo):
        user = user or self.get_user()
        repo = repo or self.get_repo()
        return user, repo

    def list(self, user=None, repo=None):
        user, repo = self._consolidate(user, repo)
        request = List(user=user, repo=repo)
        return self._get_result(request)

    def get(self, release_id, user=None, repo=None):
        user, repo = self._consolidate(user, repo)
        request = Get(id=release_id, user=user, repo=repo)
        return self._get(request)

    def tags(self, tag, user=None, repo=None):
        user, repo = self._consolidate(user, repo)
        request = Tags(tag=tag, user=user, repo=repo)
        release = self._get(request)
        release._client = self._client
        return release

    def create(self, data, user=None, repo=None):
        """
        Create a release defined by 'data' in the form:
            {
              "tag_name": "v1.0.0",
              "target_commitish": "master",
              "name": "v1.0.0",
              "body": "Description of the release",
              "draft": false,
              "prerelease": false
            }
        """
        user, repo = self._consolidate(user, repo)
        request = Create(body=data, user=user, repo=repo)
        release = self._post(request)
        release._client = self._client
        return release
 
 
