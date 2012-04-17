#!/usr/bin/python
import time, smtplib, client

def login(new_username, new_password):
	global username, password	
	username = new_username
	password = new_password

def send_to_many(recipients, subject, message):
	for recipient in recipients:
		send(recipient, subject, message)

def send(to, subject, message):
	global username, password
	client.log("Sending email to %s" % to)
	try:
		server = smtplib.SMTP('smtp.gmail.com:587')  
		server.starttls()  
		server.login(username,password)  
	except:
		client.log("Authentication error!")
		return False
	try:
		server.sendmail(username, to, "Subject: %s\r\n%s" % (subject,message))  
		server.quit()
		client.log("Email sent to %s" % to)
	except:
		client.log("Could not send email to %s" % to)
