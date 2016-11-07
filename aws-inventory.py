#!/usr/bin/env python3
'''
Script: aws-inventory.py
Author: JP <jp@lazyadm.in>
Date: 2016-09-20
Prerequisites:
> Python 3.5+
> Boto3 (pip3 install boto3)
> Your AWS Access Key ID and Secret Access Key configured in awscli or IAM Role
'''

# Modules
import boto3
import csv
import glob
import logging
import os
import sys
import xlwt
from botocore.client import Config
from datetime import datetime
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart

# Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s - %(funcName)s - %(message)s',
    datefmt='%Y-%b-%d %I:%M:%S %p'
)
logger = logging.getLogger(__name__)

# About
script_title = 'AWS Inventory'
version = 'v1.0'

# Reports
now = datetime.now()
report_date = '{:02d}{:02d}{:04d}-{:02d}{:02d}{:02d}'.format(
    now.month,
    now.day,
    now.year,
    now.hour,
    now.minute,
    now.second
)

# Email
sender_name = 'AWS@Stratpoint'
mail_from = 'aws@stratpoint.com'
mail_to = 'jdoria@stratpoint.com'

# Check Python version
if sys.version_info < (3, 5, 0):
    logger.warning(
        'You must use Python version 3.5 or later to use this script.'
    )
    sys.exit(1)

# Print script name and version
logger.info('{0} {1}'.format(script_title, version))


def send_email(subject, msg):
    '''
    Email report to recipient
    '''
    try:
        client = boto3.client('ses')

        client.send_raw_email(
            Source=mail_from,
            Destinations=[
                mail_to
            ],
            RawMessage={
                'Data': msg
            }
        )
        logger.info('Report sent to {}'.format(mail_to))
    except (SystemExit, KeyboardInterrupt):
        raise
    except Exception as e:
        logger.error(e, exc_info=True)


def mail_csv(report_file):
    '''
    Compose an email
    '''
    try:
        subject = '{0} {1} {2}'.format(script_title, version, report_date)
        header = 'Content-Disposition', 'attachment; filename={0}'.format(
            os.path.basename
            (report_file)
        )
        msg = MIMEMultipart()
        msg['From'] = '{0} <{1}>'.format(sender_name, mail_from)
        msg['To'] = mail_to
        msg['Subject'] = subject
        attachment = MIMEBase('application', 'octet-stream')

        # Attach the report_file
        with open(report_file, 'rb') as fh:
            data = fh.read()
        attachment.set_payload(data)
        encoders.encode_base64(attachment)
        attachment.add_header(*header)
        msg.attach(attachment)
        send_email(subject, msg.as_string())
    except (SystemExit, KeyboardInterrupt):
        raise
    except Exception as e:
        logger.error(e, exc_info=True)


def compile_csv_files():
    '''
    Compile CSV file
    '''
    try:
        wb = xlwt.Workbook()

        for filename in glob.glob('/tmp/*.csv'):
            (f_path, f_name) = os.path.split(filename)
            (f_short_name, f_extension) = os.path.splitext(f_name)

            ws = wb.add_sheet(f_short_name)

            reader = csv.reader(open(filename, 'rt', encoding='utf-8'))

            for rowx, row in enumerate(reader):
                for colx, value in enumerate(row):
                    ws.write(rowx, colx, value)

        wb.save('/tmp/AWSInventory-{}.xls'.format(report_date))

        final_report = '/tmp/AWSInventory-{}.xls'.format(report_date)

        return final_report
    except (SystemExit, KeyboardInterrupt):
        raise
    except Exception as e:
        logger.error(e, exc_info=True)


def export_csv(service, *args):
    '''
    Export to a CSV file
    '''
    try:
        report_file = '/tmp/{}.csv'.format(service)

        for arg in args:
            with open(report_file, 'a') as csv_file:
                csv_writer = csv.writer(csv_file, delimiter=',')
                csv_writer.writerow(arg)
    except (SystemExit, KeyboardInterrupt):
        raise
    except Exception as e:
        logger.error(e, exc_info=True)


def count_resources(service, count):
    '''
    Print total number of resources
    '''
    logger.info('Total number of {0} resources: {1}'.format(service, count))


def describe_cf():
    try:
        service = 'CloudFront'
        count = 0
        cf = boto3.client('cloudfront')
        response = cf.list_distributions()
        headers = (
            'Id',
            'Origin',
            'Domain',
            'CNAMEs',
            'Status',
            'Enabled',
            'PriceClass'
        )

        export_csv(service, headers)

        distribution_list = response['DistributionList']['Items']

        for distribution in distribution_list:
            details = []
            distribution_id = distribution['Id']
            origin = distribution['Origins']['Items'][0]['DomainName']
            domain = distribution['DomainName']
            cnames_qty = distribution['Aliases']['Quantity']
            status = distribution['Status']
            enabled = distribution['Enabled']
            price_class = distribution['PriceClass']

            logger.info('Fetching {} info...'.format(distribution_id))

            logger.info('DistributionId: {}'.format(distribution_id))
            details.append(distribution_id)

            logger.info('Origin: {}'.format(origin))
            details.append(origin)

            logger.info('Domain: {}'.format(domain))
            details.append(domain)

            if cnames_qty != 0:
                cnames = distribution['Aliases']['Items'][0]
                logger.info('CNAMEs: {}'.format(cnames))
                details.append(cnames)
            else:
                logger.info(
                    'CNAMEs: no CNAMEs defined for {}'.format(distribution_id)
                )
                details.append('None')

            logger.info('Status: {}'.format(status))
            details.append(status)

            logger.info('Enabled: {}'.format(enabled))
            details.append(enabled)

            logger.info('PriceClass: {}'.format(price_class))
            details.append(price_class)

            logger.info('{} info received!'.format(distribution_id))

            count += 1
            export_csv(service, details)

        count_resources(service, count)
    except (SystemExit, KeyboardInterrupt):
        raise
    except Exception as e:
        logger.error(e, exc_info=True)


def describe_s3():
    '''
    Describe S3
    '''
    try:
        service = 'S3'
        count = 0
        s3 = boto3.client(
            's3',
            config=Config(signature_version='s3v4')
        )
        buckets = s3.list_buckets()
        headers = (
            'BucketName',
            'Location',
            'BucketSize (Bytes)'
        )

        export_csv(service, headers)

        for bucket in buckets['Buckets']:
            details = []
            bucket_name = bucket['Name']
            bucket_location = s3.get_bucket_location(
                Bucket=bucket_name
            )

            # Get BucketName
            logger.info('{0}: {1}'.format(headers[0], bucket_name))
            details.append(bucket_name)

            # Get Location
            us_standard_region = 'us-east-1'

            if bucket_location['LocationConstraint'] is None:
                logger.info('{0}: {1}'.format(headers[1], us_standard_region))
                details.append(us_standard_region)
            else:
                logger.info('{0}: {1}'.format(
                        headers[1],
                        bucket_location['LocationConstraint'])
                )
                details.append(bucket_location['LocationConstraint'])

            # Get BucketSize
            object_sizes = []

            objects = s3.list_objects_v2(
                Bucket=bucket_name
            )

            if objects['KeyCount'] != 0:
                for key in objects['Contents']:
                    object_sizes.append(key['Size'])

            logger.info('BucketSize: {} B'.format(sum(object_sizes)))
            details.append(sum(object_sizes))

            count += 1
            export_csv(service, details)

        count_resources(service, count)
    except (SystemExit, KeyboardInterrupt):
        raise
    except Exception as e:
        logger.error(e, exc_info=True)


def describe_rds(aws_regions):
    '''
    Describe RDS
    '''
    try:
        service = 'RDS'
        count = 0
        headers = (
            'Region',
            'DBInstanceIdentifier',
            'DBInstanceClass',
            'Engine',
            'DBInstanceStatus',
            'Endpoint',
            'MultiAZ',
            'CostCenter'
        )

        export_csv(service, headers)

        for region in aws_regions:
            rds = boto3.client('rds', region_name=region)
            instances = rds.describe_db_instances()

            for instance in instances['DBInstances']:
                details = []
                costcenter_tag = None

                logger.info('{0}: {1}'.format(headers[0], region))
                details.append(region)

                logger.info('{0}: {1}'.format(
                    headers[1],
                    instance[headers[1]])
                )
                details.append(instance[headers[1]])

                logger.info('{0}: {1}'.format(
                    headers[2],
                    instance[headers[2]])
                )
                details.append(instance[headers[2]])

                logger.info('{0}: {1}'.format(
                    headers[3],
                    instance[headers[3]])
                )
                details.append(instance[headers[3]])

                logger.info('{0}: {1}'.format(
                    headers[4],
                    instance[headers[4]])
                )
                details.append(instance[headers[4]])

                logger.info('{0}: {1}'.format(
                        headers[5],
                        instance[headers[5]]['Address'])
                )
                details.append(instance[headers[5]]['Address'])

                logger.info('{0}: {1}'.format(
                    headers[6],
                    instance[headers[6]])
                )
                details.append(instance[headers[6]])

                rds_arn = instance['DBInstanceArn']
                response = rds.list_tags_for_resource(
                    ResourceName=rds_arn
                )

                for tag in response['TagList']:
                    if tag['Key'] == headers[7] or tag['Key'] == 'Cost Center':
                        costcenter_tag = tag['Value']

                logger.info('{0}: {1}'.format(headers[7], costcenter_tag))
                details.append(costcenter_tag)

                count += 1
                export_csv(service, details)

        count_resources(service, count)
    except (SystemExit, KeyboardInterrupt):
        raise
    except Exception as e:
        logger.error(e, exc_info=True)


def describe_ec2(aws_regions):
    '''
    Describe EC2
    '''
    try:
        service = 'EC2'
        count = 0
        instance_state = ('running', 'stopped')
        headers = (
                'Region',
                'InstanceId',
                'InstanceType',
                'PrivateIp',
                'PublicIp',
                'InstanceState',
                'Name',
                'CostCenter'
        )

        export_csv(service, headers)

        # Get the updated list of AWS regions
        for region in aws_regions:
            ec2 = boto3.resource('ec2', region_name=region)
            instances = ec2.instances.filter(
                Filters=[
                    {
                        'Name': 'instance-state-name',
                        'Values': instance_state
                    }
                ]
            )

            for instance in instances:
                details = []
                name_tag = None
                costcenter_tag = None

                # Append elements to details list
                logger.info('{0}: {1}'.format(
                    headers[0],
                    instance.placement['AvailabilityZone'])
                )
                details.append(instance.placement['AvailabilityZone'])

                logger.info('{0}: {1}'.format(headers[1], instance.id))
                details.append(instance.id)

                logger.info('{0}: {1}'.format(
                    headers[2],
                    instance.instance_type)
                )
                details.append(instance.instance_type)

                logger.info('{0}: {1}'.format(
                        headers[3],
                        instance.private_ip_address)
                )
                details.append(instance.private_ip_address)

                logger.info('{0}: {1}'.format(
                        headers[4],
                        instance.public_ip_address)
                )
                details.append(instance.public_ip_address)

                logger.info('{0}: {1}'.format(
                    headers[5],
                    instance.state['Name'])
                )
                details.append(instance.state['Name'])

                for tag in instance.tags:
                    if tag['Key'] == 'Name':
                        name_tag = tag['Value']
                    elif tag['Key'] == headers[7] \
                            or tag['Key'] == 'Cost Center':
                        costcenter_tag = tag['Value']

                logger.info('{0}: {1}'.format(headers[6], name_tag))
                details.append(name_tag)

                logger.info('{0}: {1}'.format(headers[7], costcenter_tag))
                details.append(costcenter_tag)

                count += 1
                export_csv(service, details)

        count_resources(service, count)
    except (SystemExit, KeyboardInterrupt):
        raise
    except Exception as e:
        logger.error(e, exc_info=True)


def describe_regions():
    '''
    List the available regions in AWS then add them to aws_regions list
    '''
    try:
        client = boto3.client('ec2')
        regions = client.describe_regions()['Regions']
        region_list = []

        for region in regions:
            region_list.append((region['RegionName']))

        return(region_list)
    except (SystemExit, KeyboardInterrupt):
        raise
    except Exception as e:
        logger.error(e, exc_info=True)


def main():
    '''
    Main function that will invoke other functions
    '''
    aws_regions = describe_regions()
    describe_ec2(aws_regions)
    describe_rds(aws_regions)
    describe_s3()
    describe_cf()
    mail_csv(compile_csv_files())


if __name__ == '__main__':
    main()
