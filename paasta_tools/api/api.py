#!/usr/bin/env python
# Copyright 2015-2016 Yelp Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""
Responds to paasta service and instance requests.
"""
import argparse
import logging
import traceback

import requests_cache
from gevent.wsgi import WSGIServer
from pyramid.config import Configurator


log = logging.getLogger(__name__)


def parse_paasta_api_args():
    parser = argparse.ArgumentParser(description='Runs a PaaSTA API server')
    parser.add_argument('-D', '--debug', action='store_true', dest='debug',
                        default=False, help="output the debug logs")
    parser.add_argument('port', help="port number for the api server")
    args = parser.parse_args()
    return args


def main(argv=None):
    args = parse_paasta_api_args()
    if args.debug:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.WARNING)

    # Set up transparent cache for http API calls. With expire_after, responses
    # are removed only when the same request is made. Expired storage is not a
    # concern here. Thus remove_expired_responses is not needed.
    requests_cache.install_cache("paasta-api", backend="memory", expire_after=60)

    log.info("paasta-api started\n")

    config = Configurator()
    config.add_route('service.instance.status', '/v1/{service}/{instance}/status')
    config.add_route('service.list', '/v1/{service}')
    config.scan()

    try:
        app = config.make_wsgi_app()
        server = WSGIServer(('', int(args.port)), app)
        server.serve_forever()
    except Exception:
        log.error(traceback.format_exc())

if __name__ == '__main__':
    main()
