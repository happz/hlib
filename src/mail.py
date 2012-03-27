"""
Functions for sending e-mails.

@type hlib.config.mail.server:		C{string}
@var hlib.config.mail.server:		Hostname (or IP address) of SMTP server we use for sending our e-mails. Default is C{localhost}.
"""

__author__              = 'Milos Prchlik'
__copyright__           = 'Copyright 2010 - 2012, Milos Prchlik'
__contact__             = 'happz@happz.cz'
__license__             = 'http://www.php-suit.com/dpl'

import smtplib
import email
import email
import email.Utils

import hlib

hlib.config.mail = hlib.Config()
hlib.config.mail.server = 'localhost'

def send_email(sender, recipient, subject, body):
  if not sender.startswith('From: '):
    sender = 'From: ' + sender

  if not recipient.startswith('To: '):
    recipient = 'To: ' + recipient

  header_charset = 'ISO-8859-1'

  for body_charset in 'UTF-8', 'US-ASCII', 'ISO-8859-1':
    try:
      body.encode(body_charset)
    except UnicodeError:
      pass
    else:
      break

  sender_name, sender_addr = parseaddr(sender)
  recipient_name, recipient_addr = parseaddr(recipient)

  sender_name = str(email.Header(unicode(sender_name), header_charset))
  recipient_name = str(email.Header(unicode(recipient_name), header_charset))

  sender_addr = sender_addr.encode('ascii')
  recipient_addr = recipient_addr.encode('ascii')

  # pylint: disable-msg=W0631
  msg = email.MIMEText(body.encode(body_charset), 'plain', body_charset)
  msg['From'] = email.Utils.formataddr((sender_name, sender_addr))
  msg['To'] = email.Utils.formataddr((recipient_name, recipient_addr))
  msg['Subject'] = email.Header(unicode(subject), header_charset)

  smtp = smtplib.SMTP(hlib.config.mail.server)
  smtp.sendmail(sender, recipient, msg.as_string())
  smtp.quit()
