import pyvklass, json, client, pygmail, os, time
class Notifier:
	configuration_filename = "notifier.conf"
	sessions               = []
	running                = True

	def conf(self):
	#	return json.loads(client.load(self.configuration_filename))
		return json.loads(client.load(self.configuration_filename).replace("\r", "").replace("\n", ""))
	
	def saved_messages(self):
		return client.load(self.conf()['files']['saved_messages'])
	
	def ensure_configuration_files(self):
		for key, filename in self.conf()['files'].items():
			if os.path.exists(filename) == False:
				f = open(filename, 'w')
				f.close()

	def loop(self):
		self.ensure_configuration_files()
		pygmail.login(self.conf()['accounts']['mail']['username'], self.conf()['accounts']['mail']['password'])

		for account in self.conf()['accounts']['vklass']:
			client.log("Spawning vklass session with username: %s, email: %s" % (account['username'], account['email']))
			vklass_session = pyvklass.Vklass()
			vklass_session.notification_email = account['email']
			vklass_session.login(account['username'], account['password'])
			self.sessions.append(vklass_session)
		
		while self.running:
			for session in self.sessions:
				for message in session.first_messages():
					if json.dumps(message) not in self.saved_messages():
						subject = message['title']
						body    = message['body']
						if len(message['posts']) > 0:
							body += "\n Posts: \n"
						for post in message['posts']:
							body += "  |  %s  |  %s  |\n" % (post['date'], post['username'])
							body += "  --> %s" % post['body']

						pygmail.send(session.notification_email, subject, body)
						client.append(self.conf()['files']['saved_messages'], json.dumps(message) + "\n")
			time.sleep(120)
n = Notifier()
n.loop()
