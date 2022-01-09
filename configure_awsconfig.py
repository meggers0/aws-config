""" This script accepts a YAML file named accounts.yaml which includes a list of AWS account-ids
    enables AWS Config in every supported region for those accounts.

    Default Settings include:
    - Assumes a specific S3 bucket in a central account is used.
    Note you must update the Bucket policy of this bucket
    to ensure all accounts listedin your account.yaml file have access to that central bucket.
    Instructions for updated the
    bucket policy are here:
    https://docs.aws.amazon.com/config/latest/developerguide/s3-bucket-policy.html#granting-access-in-another-account
    - AWSServiceRoleForConfig is the IAM Role used
    - Record ALL RESOURCES and Global Resource Types
    - Delivery Frequency is One_Hour other options are:
        Three_Hours, Six_Hours, Twelve_Hours, TwentyFour_Hours
    - Assumes cross account account for Role "arn:aws:iam::{accountid}:role/ConfigUpdateRole"

    Version 3
    Date 01/09/2022
"""

import boto3
import yaml

# ***CHANGE THESE VARIABLES *** they are dependant on the customer
CONFIG_S3_BUCKET = "config-bucket-name"  # central config S3 bucket name
PROFILE = "Profile"  # enter your PROFILE name
FILENAME = "accounts.yaml"
MAIN_SESSION = boto3.Session(profile_name=PROFILE)
REGIONS = MAIN_SESSION.client('ec2', region_name='us-east-1').describe_REGIONS()['REGIONS']
REGION_NAMES = list(map(lambda REGIONS: REGIONS['RegionName'], REGIONS))
print('AWS Config available REGIONS include -->>'+'\n', REGION_NAMES)
STS_CLIENT = MAIN_SESSION.client('sts')


def setup_awsconfig(accounts_file):
    """
    This function processses all AWS accounts in the yaml file across all active REGIONS.
    """
    with open(accounts_file) as file:
        accountids = yaml.load(file, Loader=yaml.FullLoader)

    print('Account IDs: ' + ' '.join(accountids))
    for accountid in accountids:
        print('Processing account ID: ' + accountid)
        assume_role_session = create_assume_role_session(accountid)

        for region in REGIONS:
            configure_and_enable_awsconfig(region, accountid, assume_role_session)


def create_assume_role_session(accountid):
    """
    Assume role
    """
    assumed_role_object = STS_CLIENT.assume_role(RoleArn=f"arn:aws:iam::{accountid}:role/MegRole",
                                                 RoleSessionName="AssumeRoleSession1")
    creds = assumed_role_object['Credentials']
    session = boto3.Session(aws_access_key_id=creds['AccessKeyId'],
                            aws_secret_access_key=creds['SecretAccessKey'],
                            aws_session_token=creds['SessionToken'])
    return session


def configure_and_enable_awsconfig(region, accountid, session):
    """
    This function configures AWS Config for all active REGIONS for an account.
    """
    config = session.client('config', REGION_NAMES=region['RegionName'])
    print("Processing region: " + region['RegionName'])
    config_enabled = config.describe_delivery_channels()['DeliveryChannels']

    if not config_enabled:
        config.put_configuration_recorder(
            ConfigurationRecorder={
                'name': 'default',
                'roleARN': f"arn:aws:iam::{accountid}:role/aws-service-role/config.amazonaws.com/AWSServiceRoleForConfig",
                'recordingGroup': {
                    'allSupported': True,
                    'includeGlobalResourceTypes': True
                }
            }
        )
        config.put_delivery_channel(
            DeliveryChannel={
                'name': 'default',
                's3BucketName': CONFIG_S3_BUCKET,
                's3KeyPrefix': accountid + "-" + region['RegionName'],
                'configSnapshotDeliveryProperties': {
                    'deliveryFrequency': 'One_Hour'
                }
            }
        )

    config.start_configuration_recorder(ConfigurationRecorderName='default')
    print("Confirmed AWS Config default recorder is running.")


if __name__ == '__main__':
    setup_awsconfig(FILENAME)
