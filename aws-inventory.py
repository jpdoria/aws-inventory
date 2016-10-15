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
import os
import sys
import xlwt
from botocore.client import Config
from datetime import datetime
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart

# About
script_title = 'AWS Inventory'
version = 'v1.0'

# Reports
now = datetime.now()
report_date = '{:02d}{:02d}{:04d}-{:02d}{:02d}{:02d}'.format(now.month, now.day, now.year, now.hour, now.minute, now.second)

# Email
sender_name = 'AWS@Stratpoint'
mail_from = 'aws@stratpoint.com'
mail_to = 'jdoria@stratpoint.com'

# Check Python version
if sys.version_info < (3, 5, 0):
    print('You must use Python version 3.5 or later to use this script.')
    sys.exit(1)

# Print script name and version
print(script_title, version)


# Send email
def send_email(subject, msg):
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
    except:
        raise


# Prepare email
def mail_csv(report_file):
    try:
        subject = '{0} {1} {2}'.format(script_title, version, report_date)
        header = 'Content-Disposition', 'attachment; filename={0}'.format(os.path.basename(report_file))
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
    except:
        raise


# Compile CSV files
def compile_csv_files():
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
    except:
        raise


# Export to a CSV file
def export_csv(service, *args):
    try:
        report_file = '/tmp/{}.csv'.format(service)

        for arg in args:
            with open(report_file, 'a') as csv_file:
                csv_writer = csv.writer(csv_file, delimiter=',')
                csv_writer.writerow(arg)
    except:
        raise


# Print total number of resources
def count_resources(service, count):
    print('\nTotal number of {0} resources: {1}'.format(service, count))


# Describe S3
def describe_s3():
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
            print('\n{}:\t'.format(headers[0]), bucket_name)
            details.append(bucket_name)

            # Get Location
            us_standard_region = 'us-east-1'

            if bucket_location['LocationConstraint'] is None:
                print('{}:\t'.format(headers[1]), us_standard_region)
                details.append(us_standard_region)
            else:
                print('{}:\t'.format(headers[1]), bucket_location['LocationConstraint'])
                details.append(bucket_location['LocationConstraint'])

            # Get BucketSize
            object_sizes = []

            objects = s3.list_objects_v2(
                Bucket=bucket_name
            )

            if objects['KeyCount'] != 0:
                for key in objects['Contents']:
                    object_sizes.append(key['Size'])

            print('BucketSize:\t {0} B'.format(sum(object_sizes)))
            details.append(sum(object_sizes))

            count += 1
            export_csv(service, details)

        count_resources(service, count)
    except:
        raise


# Describe RDS
def describe_rds(aws_regions):
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

                print('\n{}:\t\t\t'.format(headers[0]), region)
                details.append(region)

                print('{}:\t'.format(headers[1]), instance[headers[1]])
                details.append(instance[headers[1]])

                print('{}:\t'.format(headers[2]), instance[headers[2]])
                details.append(instance[headers[2]])

                print('{}:\t\t\t'.format(headers[3]), instance[headers[3]])
                details.append(instance[headers[3]])

                print('{}:\t'.format(headers[4]), instance[headers[4]])
                details.append(instance[headers[4]])

                print('{}:\t\t'.format(headers[5]), instance[headers[5]]['Address'])
                details.append(instance[headers[5]]['Address'])

                print('{}:\t\t'.format(headers[6]), instance[headers[6]])
                details.append(instance[headers[6]])

                rds_arn = instance['DBInstanceArn']
                response = rds.list_tags_for_resource(
                    ResourceName=rds_arn
                )

                for tag in response['TagList']:
                    if tag['Key'] == headers[7] or tag['Key'] == 'Cost Center':
                        costcenter_tag = tag['Value']

                print('{}\t\t'.format(headers[7]), costcenter_tag)
                details.append(costcenter_tag)

                count += 1
                export_csv(service, details)

        count_resources(service, count)
    except:
        raise


# Describe EC2
def describe_ec2(aws_regions):
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
                print('\n{}:\t\t'.format(headers[0]), instance.placement['AvailabilityZone'])
                details.append(instance.placement['AvailabilityZone'])

                print('{}:\t'.format(headers[1]), instance.id)
                details.append(instance.id)

                print('{}:\t'.format(headers[2]), instance.instance_type)
                details.append(instance.instance_type)

                print('{}:\t'.format(headers[3]), instance.private_ip_address)
                details.append(instance.private_ip_address)

                print('{}:\t'.format(headers[4]), instance.public_ip_address)
                details.append(instance.public_ip_address)

                print('{}:\t'.format(headers[5]), instance.state['Name'])
                details.append(instance.state['Name'])

                for tag in instance.tags:
                    if tag['Key'] == 'Name':
                        name_tag = tag['Value']
                    elif tag['Key'] == headers[7] or tag['Key'] == 'Cost Center':
                        costcenter_tag = tag['Value']

                print('{}:\t\t'.format(headers[6]), name_tag)
                details.append(name_tag)

                print('{}:\t'.format(headers[7]), costcenter_tag)
                details.append(costcenter_tag)

                count += 1
                export_csv(service, details)

        count_resources(service, count)
    except:
        raise


# List the available regions in AWS then add them to aws_regions list
def describe_regions():
    try:
        client = boto3.client('ec2')
        regions = client.describe_regions()['Regions']
        region_list = []

        for region in regions:
            region_list.append((region['RegionName']))

        return(region_list)
    except:
        raise


# List of functions
def main():
    aws_regions = describe_regions()
    describe_ec2(aws_regions)
    describe_rds(aws_regions)
    describe_s3()
    mail_csv(compile_csv_files())

# Execute
if __name__ == '__main__':
    main()
