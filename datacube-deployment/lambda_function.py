import os
import sys
import boto3

from alembic.config import main

SSM = boto3.client('ssm')
ENVIRONMENT = os.environ['Environment']

MASTERUSERNAME = SSM.get_parameter(
    Name = '/' + ENVIRONMENT + '/rds/MasterUsername',
    WithDecryption = True or False
)

MASTERPASSWORD = SSM.get_parameter(
    Name = '/' + ENVIRONMENT + '/rds/MasterPassword',
    WithDecryption = True
)

os.environ['POSTGRES_USER'] = MASTERUSERNAME['Parameter']['Value']
os.environ['POSTGRES_PASS'] = MASTERPASSWORD['Parameter']['Value']

def lambda_handler(event, context):
    main(argv=[event['command'], event['revision']])
    #main(argv=['upgrade', 'head'])
    return 0
