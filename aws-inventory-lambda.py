#!/usr/bin/env python3

'''
Script: aws-inventory-lambda.py
Author: JP <jp@lazyadm.in>
Date: 2016-09-20
Prerequisites:
> Python 3.5+
> Boto3 (pip3 install boto3)
> Your AWS Access Key ID and Secret Access Key configured in awscli or IAM Role
==============================
How to use this on AWS Lambda?
- Simply copy lines 17-199 and paste it to AWS Lambda
==============================
'''

# Modules
import boto3, csv, os, sys
from datetime import datetime
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart

# Generic
script_name = os.path.basename(__file__)
script_title = 'AWS Inventory'
version = 'v1.0'

# Reports
now = datetime.now()
report_date = '{:02d}{:02d}{:04d}-{:02d}{:02d}{:02d}'.format(now.month, now.day, now.year, now.hour, now.minute, now.second)
report_file = '/tmp/{0}-{1}.csv'.format(os.path.splitext(script_name)[0], report_date)

# Email
sender_name = 'AWS@Stratpoint'
mail_from = 'aws@stratpoint.com'
mail_to = 'jdoria@stratpoint.com'

# AWS
count = 0
aws_regions = []

# Check Python version
if sys.version_info < (3, 5, 0):
	print('You must use Python version 3.5 or later to use this script.')
	sys.exit(1)

# Print script name and version
print(script_title, version)

# Print start time
print('Start Time:', now)

# Print total number of instance_state instances
def count_instances():
	print('\nTotal number of instances: {0}'.format(count))

# Send email
def send_email(subject, msg):
	try:
		client = boto3.client('ses')
		response = client.send_raw_email(
			Source=mail_from,
			Destinations=[
				mail_to
			],
			RawMessage={
				'Data': msg
			}
		)
	except:
		print('ERROR: Message sending failed.')
		sys.exit(1)

# Prepare email
def mail_csv():
	subject = '{0} {1} {2}'.format(script_title, version, report_date)
	header = 'Content-Disposition', 'attachment; filename={0}'.format(os.path.basename(report_file))	
	msg = MIMEMultipart()
	msg['From'] = '{0} <{1}>'.format(sender_name, mail_from)
	msg['To'] = mail_to
	msg['Subject'] = subject
	attachment = MIMEBase('application', 'octet-stream')

	# Attach the report_file
	try:
		with open(report_file, 'rb') as fh:
			data = fh.read()
		attachment.set_payload(data)
		encoders.encode_base64(attachment)
		attachment.add_header(*header)
		msg.attach(attachment)
	except:
		print('ERROR: Unable to open file: \'{0}\''.format(report_file))
		sys.exit(1)

	send_email(subject, msg.as_string())

# Export to a CSV file
def export_csv(*values):
	for value in values:
		with open(report_file, 'a') as csv_file:
			csv_writer = csv.writer(csv_file, delimiter=',')
			csv_writer.writerow(value)

# List the available regions in AWS then add them to aws_regions list
def describe_regions():
	client = boto3.client('ec2')
	regions = client.describe_regions()['Regions']

	for region in regions:
		aws_regions.append((region['RegionName']))

# Describe instances
def describe_ec2():
	# Make count variable as global
	global count

	instance_state = ['running', 'stopped']
	headers = [
			'Region',
			'InstanceId',
			'InstanceType',
			'PrivateIp',
			'PublicIp',
			'InstanceState',
			'Name',
			'CostCenter'
	]

	export_csv(headers)

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
			# Initialize list and variables
			details = []
			name_tag = None
			costcenter_tag = None
			
			# Append elements to details list
			print('\n{0}:\t\t'.format(headers[0]), instance.placement['AvailabilityZone'])
			details.append(instance.placement['AvailabilityZone'])

			print('{0}:\t'.format(headers[1]), instance.id)
			details.append(instance.id)

			print('{0}:\t'.format(headers[2]), instance.instance_type)
			details.append(instance.instance_type)

			print('{0}:\t'.format(headers[3]), instance.private_ip_address)
			details.append(instance.private_ip_address)

			print('{0}:\t'.format(headers[4]), instance.public_ip_address)
			details.append(instance.public_ip_address)

			print('{0}:\t'.format(headers[5]), instance.state['Name'])
			details.append(instance.state['Name'])

			for tag in instance.tags:
				if tag['Key'] == 'Name':
					name_tag = tag['Value']
				elif tag['Key'] == 'CostCenter' or tag['Key'] == 'Cost Center':
					costcenter_tag = tag['Value']

			print('{0}:\t\t'.format(headers[6]), name_tag)
			details.append(name_tag)

			print('{0}:\t'.format(headers[7]), costcenter_tag)
			details.append(costcenter_tag)

			count += 1 # Increment counter
			export_csv(details)

	count_instances()

# List of functions
def main(event, context):
	describe_regions()
	describe_ec2()
	mail_csv()

# Code will run only when executed as primary script (or call it from another script), no importing!
if __name__ == '__main__':
	main()

# Print end time
print('End Time:', now)