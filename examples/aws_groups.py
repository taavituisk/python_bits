# as_aws_groups.py
import logging
import boto.s3.connection
import as_aws

# prepare logging
logger = logging.getLogger(__name__)

class EC2Groups:
  '''
  Use to modify EC2 security group rules.

  :type aws: :class:`as_aws.AWS_Connections`
  :param aws: Our wrapper to various connect to aws service calls.

  :type conf: dict
  :param conf: Configuration for security group modification.

  '''

  def __init__(self, **kwargs):
    self.aws = kwargs['aws']
    self.conf = kwargs['conf']
    self.extip = kwargs['extip']
    self._retval = None

  def get_group

  def add(self):
    logger.debug("aws group authorize %s to connect to port %s/%s" % (self.extip, self.protocol, self.port))
    self._retval = self.group.authorize(ip_protocol = self.protocol,
                                         from_port = self.port,
                                         to_port = self.port,
                                         cidr_ip = self.extip + '/32')
  def remove(self):
    logger.debug("Groupmod - remove - aws group revoke %s to connect to port %s/%s" % (self.extip, self.protocol, self.port))
    self._retval = self.group.revoke(ip_protocol = self.protocol,
                                      from_port = self.port,
                                      to_port = self.port,
                                      cidr_ip = self.extip + '/32')

