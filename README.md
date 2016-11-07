# About #

[![forthebadge](http://forthebadge.com/images/badges/built-with-love.svg)](http://forthebadge.com)
[![forthebadge](http://forthebadge.com/images/badges/powered-by-oxygen.svg)](http://forthebadge.com)
[![forthebadge](http://forthebadge.com/images/badges/fuck-it-ship-it.svg)](http://forthebadge.com)

This script will check all active instances in EC2 in your AWS account

# Prerequisites #
* Python 3.5+
* Boto3 (pip3 install boto3)
* XLWT (pip3 install xlwt)
* SES SMTP Account
* Your AWS Access Key ID and Secret Access Key configured in awscli or IAM Role

# How to send email using smtplib?

Make sure to `import smtplib` first then find these lines...

```python
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
```

And replace them with...

```python
def send_email(subject, msg):
    '''
    Email report to recipient
    '''
	smtp_server = 'smtpserver'
	smtp_port = <port>
	smtp_id = 'username'
	smtp_password = 'password'

	try:
		with smtplib.SMTP(smtp_server, smtp_port) as s:
			s.ehlo()
			s.starttls()
			s.ehlo()
			s.login(smtp_id, smtp_password)
			s.sendmail(mail_from, mail_to, msg)
			s.quit()
		logger.info('Report sent to {}'.format(mail_to))
	except (SystemExit, KeyboardInterrupt):
        raise
    except Exception as e:
        logger.error(e, exc_info=True)
```

# Checklist
- [x] EC2
- [x] RDS
- [x] S3
- [ ] VPC
- [x] CloudFront
- [ ] Route 53