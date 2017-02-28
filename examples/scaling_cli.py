execfile('pyconsole.py')

sconf = conf['scaling_groups'][0]

sqs = as_aws.AWS_SQS(aws, sconf['name'])
queue = sqs.get()

sns = as_aws.AWS_SNS(aws, sconf, queue)
snsarn = sns.create()

lconf = sconf['lconf']
awslc = as_aws.AWS_LConf(aws, lconf)
# lc = awslc.create()
lc = awslc.get()

aws_sg = as_aws.AWS_ASGroup(conf = sconf, aws = aws, lc = lc, topic = snsarn)
# aws_sg.create()
aws_sg.set_notifications()
aws_sg.set_policies()

constr = as_setup.ASG_Constructor(conf, 'test-group')
constr.create()

