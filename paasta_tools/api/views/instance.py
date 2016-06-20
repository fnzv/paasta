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
PaaSTA service instance
"""
import logging
import traceback

from pyramid.view import view_config

from paasta_tools import marathon_tools
from paasta_tools.cli.cmds.status import get_actual_deployments
from paasta_tools.marathon_serviceinit import get_bouncing_status
from paasta_tools.utils import DEFAULT_SOA_DIR
from paasta_tools.utils import load_system_paasta_config
from paasta_tools.utils import PaastaColors
from paasta_tools.utils import validate_service_instance


log = logging.getLogger(__name__)


# WIP
def chronos_service_status(instance_status,
                           service, instance, cluster, soa_dir, verbose):
    return


# WIP
def marathon_service_status(instance_status,
                            service, instance, cluster, soa_dir, verbose):

    marathon_config = marathon_tools.load_marathon_config()
    client = marathon_tools.get_marathon_client(marathon_config.get_url(),
                                                marathon_config.get_username(),
                                                marathon_config.get_password())
    job_config = marathon_tools.load_marathon_service_config(
        service, instance, cluster, soa_dir)

    instance_status['State'] = PaastaColors.decolor(
        get_bouncing_status(service, instance, client, job_config))
    instance_status['Desired state'] = PaastaColors.decolor(
        job_config.get_desired_state_human())


@view_config(route_name='service.instance.status', request_method='GET', renderer='json')
def instance_status(request):
    service = request.matchdict['service']
    instance = request.matchdict['instance']
    verbose = request.params.get('verbose', False)
    soa_dir = request.params.get('soa_dir', DEFAULT_SOA_DIR)

    cluster = load_system_paasta_config().get_cluster()
    actual_deployments = get_actual_deployments(service, soa_dir)

    instance_status = {}
    instance_status['service'] = service
    instance_status['instance'] = instance

    deployment_key = '.'.join([cluster, instance])
    if deployment_key not in actual_deployments:
        instance_status['message'] = '%s not found' % deployment_key
        return instance_status

    version = actual_deployments[deployment_key][:8]
    instance_status['Git sha'] = version

    try:
        instance_type = validate_service_instance(service, instance, cluster, soa_dir)
        if instance_type == 'marathon':
            marathon_service_status(instance_status, service, instance, cluster, soa_dir, verbose)
        elif instance_type == 'chronos':
            chronos_service_status(instance_status, service, instance, cluster, soa_dir, verbose)
        else:
            error_msg = 'Unknown instance_type %s of %s.%s' % (instance_type, service, instance)
            log.error(error_msg)
            instance_status['message'] = error_msg
    except:
        log.error(traceback.format_exc())
        instance_status['message'] = traceback.format_exc()

    return instance_status
