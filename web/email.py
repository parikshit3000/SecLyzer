#!/usr/bin/env python
# -*- coding: utf_8 -*-
"""Email integration."""
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from threading import Thread

from flask import render_template

from seclyzer import (
    filters,
    settings,
    utils,
)


def send_mail(config, html, text):
    """Send Email."""
    msg = MIMEMultipart('alternative')
    msg['Subject'] = (
        f'seclyzer report ⚡ '
        f'scan completed on {utils.get_timestamp()}')
    msg['From'] = config['from']
    msg['To'] = config['to']
    part1 = MIMEText(text, 'plain')
    part2 = MIMEText(html, 'html')
    msg.attach(part1)
    msg.attach(part2)
    if config.get('port'):
        if config['port'] == 465:
            smtp_server = smtplib.SMTP_SSL(
                config['server'],
                config['port'])
        else:
            smtp_server = smtplib.SMTP(
                config['server'],
                config['port'])
    else:
        smtp_server = smtplib.SMTP(config['server'])
    if config.get('starttls') is True:
        smtp_server.ehlo()
        smtp_server.starttls()
        smtp_server.ehlo()
    if config.get('user') and config.get('pass'):
        smtp_server.login(config['user'], config['pass'])
    smtp_server.sendmail(msg['From'], msg['To'], msg.as_string())
    smtp_server.quit()


def email_alert(filename, sha2, base_url, message):
    """Create an email alert."""
    smtp_config = {}
    smtp_server = os.getenv('SMTP_SERVER', settings.SMTP_SERVER)
    from_email = os.getenv('NJS_FROM_EMAIL', settings.NJS_FROM_EMAIL)
    to_email = os.getenv('NJS_TO_EMAIL', settings.NJS_TO_EMAIL)
    if not (smtp_server and from_email and to_email):
        return
    text = f'Report Generated by seclyzer v{settings.VERSION}'
    severity, total_issues = filters.get_metrics(message)
    context = {
        'version': settings.VERSION,
        'scan_file': filename,
        'total_issues': total_issues,
        'total_files': len(message['files']),
        'url': f'{base_url}scan/{sha2}',
        'error': severity['error'],
        'warning': severity['warning'],
        'info': severity['info'],
        'nodejs': message['nodejs'],
        'templates': message['templates'],
    }
    html = render_template('email.html', **context)
    smtp_config['server'] = smtp_server
    smtp_config['from'] = from_email
    smtp_config['to'] = to_email
    smtp_config['port'] = os.getenv('SMTP_PORT', settings.SMTP_PORT)
    smtp_config['user'] = os.getenv('SMTP_USER', settings.SMTP_USER)
    smtp_config['pass'] = os.getenv('SMTP_PASS', settings.SMTP_PASS)
    stls = os.getenv('SMTP_STARTTLS', settings.SMTP_STARTTLS)
    if str(stls) in ['0', 'False', 'false']:
        smtp_config['starttls'] = False
    else:
        smtp_config['starttls'] = True
    process = Thread(target=send_mail, args=(smtp_config, html, text))
    process.start()
    process.join()
