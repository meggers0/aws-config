# This script enables AWS Config in every supported region in an AWS account.
# Default Settings include:
#   AWSServiceRoleForConfig is the IAM Role used
#   Record ALL RESOURCES and Global Resource Types
#   Delivery Frequency is One_Hour other options are Three_Hours, Six_Hours, Twelve_Hours, TwentyFour_Hours
#
# Version 1
# Date 4/30/2020

import boto3

# ***CHANGE THESE VARIABLES *** they are dependant on the customer
config_s3_bucket = "s3BucketName"  # central config S3 bucket name
account_id = "AWSAccountID"  # enter aws account id
profile_name = "bobsprofile"  # enter your profile name

session = boto3.Session(profile_name=profile_name)
DeliveryChannelDetails = {}
# unsupported region: ap-northeast-1, ap-northeast-3,
regions = ['us-east-1', 'us-east-2', 'us-west-1', 'us-west-2',
           'eu-central-1', 'eu-north-1', 'eu-west-3', 'eu-west-2', 'eu-west-1',
           'ap-southeast-1', 'ap-southeast-2', 'ap-northeast-2', 'ap-south-1',
           'sa-east-1',
           'ca-central-1']

for region in regions:
    config = session.client('config', region_name=region)
    DeliveryChannelDetails = config.describe_delivery_channels()

    # AWS Config has not been configured.
    if not DeliveryChannelDetails['DeliveryChannels']:
        config.put_configuration_recorder(
            ConfigurationRecorder={
                'name': 'default',
                'roleARN': 'arn:aws:iam::account_id:role/aws-service-role/config.amazonaws.com/AWSServiceRoleForConfig',
                'recordingGroup': {
                    'allSupported': True,
                    'includeGlobalResourceTypes': True
                }
            }
        )
        config.put_delivery_channel(
            DeliveryChannel={
                'name': 'default',
                's3BucketName': config_s3_bucket,
                'configSnapshotDeliveryProperties': {
                    'deliveryFrequency': 'One_Hour'
                }
            }
        )
        config.start_configuration_recorder(
            ConfigurationRecorderName='default')
        print("AWS Config is now configured in account: ", region)
    else:
        config.start_configuration_recorder(
            ConfigurationRecorderName='default')
        print("AWS Config was already configured in region:", region)
