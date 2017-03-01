import json
import time

import botocore.session
from boto import ec2
import boto.sqs

import tower_cli

# use the undocumented API client from the tower-cli tool
group_resource = tower_cli.get_resource('group')
host_resource = tower_cli.get_resource('host')

CREATE_TOWER_GROUPS = True
SQS_QUEUE_NAME = 'ansible-tower'
AWS_REGION = 'us-west-2'
DEFAULT_INVENTORY = 1

# set up our AWS endpoints
ec2_conn = ec2.connect_to_region(AWS_REGION)
sqs_conn = boto.sqs.connect_to_region(AWS_REGION)

# we use botocore instead of boto for the newest ASG feature, as most of the
# SDKs lag botocore.
bc_session = botocore.session.get_session()
bc_asg = bc_session.get_service('autoscaling')
bc_endpoint = bc_asg.get_endpoint(AWS_REGION)

msg_queue = sqs_conn.get_queue(SQS_QUEUE_NAME)


def get_instance(instance_id):
    reservations = ec2_conn.get_all_instances(instance_ids=[instance_id])
    # TODO catch error if instance does not exist
    return reservations[0].instances[0]


def get_tower_group(group_name, create=True):
    """
    Given a group name, find or optionally create a corresponding Tower group.
    This is used to pair an AWS autoscaling group to a Tower inventory group.
    """
    groups = group_resource.list(all_pages=True)['results']
    matching_groups = [g for g in groups if g['name'] == group_name]

    if not matching_groups:
        # no matching group
        if create:
            tower_group = group_resource.create(name=group_name,
                                        inventory=DEFAULT_INVENTORY,
                                        description="auto created ASG group")
        else:
            raise RuntimeError("no matching group")
    else:
        tower_group = matching_groups[0]
    return tower_group


def get_tower_host(host_name_or_ip, inventory=1):
    hosts = host_resource.list(inventory=inventory, all_pages=True)['results']
    matching_hosts = [h for h in hosts if h['name'] == host_name_or_ip]
    if matching_hosts:
        return matching_hosts[0]
    return None


def add_instance_to_inventory(msg):
    tower_group = get_tower_group(msg['AutoScalingGroupName'],
                                  create=CREATE_TOWER_GROUPS)
    instance = get_instance(msg['EC2InstanceId'])

    new_host = host_resource.create(
                    name=instance.private_ip_address,
                    description=instance.tags.get('Name', '<no name>'),
                    instance_id=msg['EC2InstanceId'],
                    inventory=tower_group['inventory']
                    )

    host_resource.associate(new_host['id'], tower_group['id'])


def remove_instance_from_inventory(msg):
    # get group
    tower_group = get_tower_group(msg['AutoScalingGroupName'],
                                  create=CREATE_TOWER_GROUPS)

    instance = get_instance(msg['EC2InstanceId'])
    host = get_tower_host(instance.private_ip_address)

    # The Tower API does not allow the removal or disabling of a host
    # so the best we can do for now is dissociate it from the group
    # dissacociate? or does it cascade delete?

    if host:
        host_resource.disassociate(host['id'], tower_group['id'])


def lifecycle_response(msg, cont=True):
    # requires the use of botocore
    operation = bc_asg.get_operation('CompleteLifecycleAction')
    result = "CONTINUE" if cont else "ABORT"
    http_response, response_data = operation.call(bc_endpoint,
                            auto_scaling_group_name=msg['AutoScalingGroupName'],
                            lifecycle_action_token=msg['LifecycleActionToken'],
                            lifecycle_action_result=result,
                            lifecycle_hook_name=msg['LifecycleHookName']
                            )


def main():
    while True:
        m = msg_queue.read()
        if m:
            msg = json.loads(m.get_body())
            if "LifecycleHookName" not in msg:
                # TODO - there should only be lifecycle messages on this
                # queue, but should handle a graceful way of putting them back
                # set visibility to 5 sec?
                continue
            print "responding to lifecycle"
            try:
                if msg['LifecycleHookName'] == "NewHost":
                    add_instance_to_inventory(msg)
                elif msg['LifecycleHookName'] == "RemoveHost":
                    remove_instance_from_inventory(msg)
                msg_queue.delete_message(m)
                lifecycle_response(msg)
            except Exception as e:
                # TODO handle more specific errors
                print e
                # abort the lifecycle step
                lifecycle_response(msg, cont=False)
        else:
            # no messages on queue
            print "pausing"
            time.sleep(5)

if __name__ == "__main__":
    main()

