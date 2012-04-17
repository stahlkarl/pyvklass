import pyvklass, client
from cmd2 import *

class Tui(Cmd):
	prompt   = "# "
	days     = ["monday", "tuesday", "wednesday", "thursday", "friday"]
	v        = pyvklass.Vklass()
	messages = []
	client.log("TIP: Type login or help")

	def do_login(self, args):
		username = client.input("Username: ")
		password = client.pwinput("Password (no chars will be shown): ")
		self.v.login(username, password)
	
	def do_status(self, args):
		status = self.v.status()
		client.log("Guestbook: %s | Messages: %s | Forum: %s | Friend requests: %s" % (status['guestbook'], status['messages'], status['forum'], status['friends']))
	
	def do_news(self, args):
		client.log("Fetching news")
		for news in self.v.all_news():
			client.log(news['title'])
			if news['body'] != "":
				client.log(news['body'])
			if news['attached']['url'] != "":
				client.log("Attached: %s | URL: %s" % (news['attached']['filename'], news['attached']['url']))
			print ""

	def do_lunch_menu(self, args):
		menu = self.v.food_menu()
		for day in self.days:
			client.log("%s: %s" % (day, menu[day]))
	
	def do_time_summary(self, args):
		summary = self.v.time_summary()
		client.log("Time summary for the past 30 days")
		client.log("Present: ")
		client.log("  * %i minutes" % summary['present']['minutes'])
		client.log("  * %i%%" % summary['present']['percentage'])

		client.log("Absent: ")
		client.log("  * %i minutes" % summary['absent']['minutes'])
		client.log("  * Approved   %i%% " % summary['absent']['approved_percentage'])
		client.log("  * Unapproved %i%% " % summary['absent']['unapproved_percentage'])
	
	def do_schedule(self, args):
		schedule = self.v.current_schedule()
		for day in self.days:
			client.log(day)
			for lesson in schedule[day]: 
				client.log("  * %s --> %s %s %s" % (lesson['from'], lesson['to'], lesson['room'], lesson['name']))
	
	def do_profile_visitors(self, args):
		client.log("Latest profile visitors:")
		for visitor in self.v.latest_profile_visitors():
			client.log("  * %s | %s" % (visitor['time'], visitor['name']))
	
	def do_courses(self, args):
		client.log("Courses:")
		for course in self.v.courses():
			client.log("  * %s" % course)
	
	def print_exam(self, exam):
		client.log("Name:    %s" % exam['name'])
		client.log("Course:  %s" % exam['course'])
		client.log("Type:    %s" % exam['type'])
		client.log("Date:    %s" % exam['date'])
		if exam['grades'] != None: # There's statistics available
			possible_grades = ""
			for possible_grade in exam['possible_grades']:
				possible_grades += possible_grade + "/"
			client.log("Achievable grades: %s" % possible_grades)
			client.log("Participants: %s/%s" % (exam['exam_participants'], exam['course_participants']))
			results = "Statistics: "
			for grade, amount in exam['grades'].items():
				results += "%s: %s | " % (grade, amount)
			client.log(results)
		else:
			client.log("No statistics available")


	def do_class_exams(self, args):
		client.log("Exams listed in the class calendar:")
		for exam in self.v.class_calendar_exams():
			self.print_exam(exam)
			print ""
	
	def do_class_events(self, args):
		client.log("Events listed in the class calendar:")
		for event in self.v.class_events():
			client.log("  > " + event['name'])
			client.log("  * " + event['description'])
			print ""
	
	def do_exam(self, exam_id):
		try:
			exam_id = int(exam_id)
		except:
			client.log("Please enter an exam id as an argument")
			return False
			
		self.print_exam(self.v.exam_statistics(exam_id))

	def print_message(self, message):
		client.log("|   %s   |   %s   |   %s   |" % (message['title'], message['creator']['name'], message['created']))
		client.log(message['body'])
		client.log("")
		if len(message['posts']) > 0:
			client.log("Posts:")
			for post in message['posts']:
				print "  |  %s  |  %s  |" % (post['date'], post['username'])
				print "  --> %s" % post['body']

	def do_fetch_messages(self, args):
		self.messages = self.v.first_messages()
		self.messages.reverse()

	def do_messages(self, args):
		if len(self.messages) == 0:
			self.do_fetch_messages("")
		
		for message_id in range(len(self.messages)):
			client.log("[%i] %s" % (message_id, self.messages[message_id]['title']))
			client.log("  * From: %s" % self.messages[message_id]['creator']['name'])
			client.log("  * Date: %s" % self.messages[message_id]['created'])
			print ""

		message_id = int(client.input("Message id: "))
		self.print_message(self.messages[message_id])
	
	def do_download(self, args):
		url, filename = args.split(" ")
		client.download(url, filename)
		
tui = Tui()
tui.cmdloop()

