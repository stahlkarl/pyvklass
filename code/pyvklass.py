# -*- coding: utf-8 -*-
import cookielib, urllib2, urllib, os, cre, json, client, sqlite3, os, time
from threading import *

class Vklass:
	dbc    = sqlite3.connect("vklass.db")
	cursor = dbc.cursor()
	profile_picture_dir = "profile_pictures"
	my_profile_info     = None
	base_url            = "https://www.vklass.se"
	configuration_file  = "pyvklass.conf"

	def __init__(self):
		self.login_from_file()
	
	def login_from_file(self):
		if os.path.exists(self.configuration_file):
			f = open(self.configuration_file, 'r')
			conf = json.loads(f.read())
			f.close()
			try:
				self.login(conf['account']['username'], conf['account']['password'])
			except:
				client.log("Could not log in to %s with the credentials in %s" % (self.base_url, self.configuration_file))

	def create_tables(self):
		client.log("Creating tables")
		try:
			self.cursor.execute("CREATE TABLE users (id integer primary key autoincrement, profile_id integer, profile_id2 text, name text, class text, age text, msn text, email text, cellphone_number text, school text, avatar_filename text)")
			self.cursor.execute("CREATE TABLE chat (id integer primary key autoincrement, from_id text, to_id text, message text, time integer)")
			self.dbc.commit()
		except:
			client.log("Failed. Do they already exist?")

	def login(self, username, password):
		client.log("Logging in to %s as %s" % (self.base_url, username))
		self.username     = username
		self.password     = password
		vklass_cj         = cookielib.CookieJar()
		vklass_opener     = urllib2.build_opener(urllib2.HTTPCookieProcessor(vklass_cj))
		vklass_opener.addheaders = [('User-agent', 'Mozilla/5.0 (X11; U; Linux x86_64; en-US; rv:1.9.2.10) Gecko/20100922 Ubuntu/10.10 (maverick) Firefox/3.6.11')]
		urllib2.install_opener(vklass_opener)

		index           = urllib2.urlopen(self.base_url).read()
		eventvalidation = cre.between('<input type="hidden" name="__EVENTVALIDATION" id="__EVENTVALIDATION" value="', '" />', index)
		viewstate       = cre.between('<input type="hidden" name="__VIEWSTATE" id="__VIEWSTATE" value="', '" />', index)
		login_data      = urllib.urlencode({'__EVENTTARGET' : 'Button1', '__EVENTARGUMENT' : '', '__VIEWSTATE' : viewstate, '__EVENTVALIDATION' : eventvalidation, 'tb_username' : username, 'tb_password' : password, 'ThemeSelect' : 'Vklass', 'RadWindow1_ClientState' : '', 'RadWindowManager1_ClientState' : ''})
		login = urllib2.urlopen(self.base_url + '/login.aspx?cookieCheck=true', login_data)
		if 'title="Logga ut' in urllib2.urlopen("%s/default.aspx" % self.base_url).read():
			client.log("Login successfull")
			return True
		client.log("Login failed")
		return False
	
	def stay_logged_in(self):
		if 'title="Logga ut' not in urllib2.urlopen("%s/default.aspx" % self.base_url).read():
			client.log("Got logged out")
			self.login(self.username, self.password)

	def profile_info(self, profile_id):
		info = None
		initial_profile_id = profile_id
		client.log("Looking up info for profile id %s" % str(profile_id))
		query        = "SELECT * FROM users WHERE profile_id = %i" % int(profile_id)
		self.cursor.execute(query)
		dbresult = self.cursor.fetchone()
		if dbresult:
			client.log("Returning info from db")
			profile_id       = dbresult[1]
			profile_id2      = dbresult[2]
			profile_name     = dbresult[3]
			profile_class    = dbresult[4]
			age              = dbresult[5]
			msn              = dbresult[6]
			email            = dbresult[7]
			cellphone_number = dbresult[8]
			school           = dbresult[9]
			avatar_filename  = dbresult[10]
		elif profile_id == 0 and self.my_profile_info != None:
			client.log("Already fetched info for this account")
			return self.my_profile_info
		else:
			lookup_url = "%s/User.aspx?id=%s" % (self.base_url, str(profile_id))
			client.log("No info in db. Fetching from %s" % lookup_url)
			try:
				profile_data     = urllib2.urlopen(lookup_url).read()
				profile_id       = int(cre.between('href="Guestbook.aspx\?id=', '"', profile_data))
				profile_id2      = cre.between('frameborder="0" src="https://user.vklass.se/presentation/', '"', profile_data)
				profile_name     = cre.between('<li><span id="ctl00_ContentPlaceHolder2_nameLabel">Namn: ', '</span></li>', profile_data)
				profile_class    = cre.between('<li><span id="ctl00_ContentPlaceHolder2_classLabel">Klass: ', '</span></li>', profile_data)
				age              = cre.between('<li><span id="ctl00_ContentPlaceHolder2_ageLabel">', '</span></li>', profile_data)
				msn              = cre.between('<li><span id="ctl00_ContentPlaceHolder2_msnLabel">MSN: ', '</span></li>', profile_data)
				email            = cre.between('<li><span id="ctl00_ContentPlaceHolder2_mailLabel">Email: ', '</span></li>', profile_data)
				cellphone_number = cre.between('<li><span id="ctl00_ContentPlaceHolder2_mobileLabel">Mobil: ', '</span></li>', profile_data)
				school           = cre.between('<li>Skola: ', '<', profile_data)
				avatar_filename  = cre.between('https://user.vklass.se/photo/large/', '" target="', profile_data)
		
				self.cursor.execute("INSERT INTO users (profile_id, profile_id2, name, class, age, msn, email, cellphone_number, school, avatar_filename) VALUES(%i, '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s')" % (profile_id, profile_id2, profile_name, profile_class, age, msn, email, cellphone_number, school, avatar_filename))
				self.dbc.commit()
				client.ensure_dir(self.profile_picture_dir)
				if avatar_filename:
					client.download('%s/photo/large/%s' % (self.base_url, avatar_filename, self.profile_picture_dir + "/" + avatar_filename))
				info = {"profile_id" : profile_id, "profile_id2": profile_id2, "name" : profile_name, "class" : profile_class, "age" : age, "msn" : msn, "email" : email, "cellphone_number" : cellphone_number, "school" : school, "avatar_filename" : avatar_filename}
			except:
				client.log("Could not fetch data from %s" % lookup_url)

		if self.my_profile_info == None and initial_profile_id == 0:
			self.my_profile_info = info
		return info

	def users_online(self):
		users_online = json.loads(urllib2.urlopen("%s/handler/usersOnline.ashx?action=friendsonline" % self.base_url).read())['users']
		return users_online
	
	def info_by_id2(self, id2):
		for user in self.users_online():
			if user['UserID'] == id2:
				return user
		return {'UserID': "", "UserName": ""}

	def send_chat(self, to, message):
		client.log("Sending message: %s, to: %s" % (message, self.info_by_id2(to)['UserName']))
		chat_url = "%s/Handler/chathandler.ashx?action=sendchat" % self.base_url
		request  = urllib.urlencode({'to': to, 'message': message})
		result   = urllib2.urlopen(chat_url, request).read()
		self.cursor.execute("INSERT INTO chat (from_id, to_id, message, time) VALUES('%s', '%s', '%s', %i)" % ('0', to, message.replace("'", "''"), int(time.time())))
		self.dbc.commit()
	
	def get_chat(self):
		chatheartbeat_url = "%s/Handler/chathandler.ashx?action=chatheartbeat" % self.base_url
		chat_messages_raw = urllib2.urlopen(chatheartbeat_url).read().replace("\n", "")
		chat_messages     = []
		for message in json.loads(chat_messages_raw)['items']:
			sender    = client.unescape(message['f'])
			message = client.unescape(message['m'])
			self.cursor.execute("INSERT INTO chat (from_id, to_id, message, time) VALUES('%s', '%s', '%s', %i)" % (sender.replace("'", "''"), '0', message.replace("'", "''"), int(time.time())))
			self.dbc.commit()
			chat_messages.append({"from": sender, "message": message})

		return chat_messages
	
	def news_listing(self):
		html     = urllib2.urlopen("%s/MySchool.aspx" % self.base_url).read()
		dirty_news_ids = cre.all_between('<a id="ctl00_ContentPlaceHolder2_newsRepeater_ctl', "&amp;", html)
		clean_news_ids = []
		for dirty_news_id in dirty_news_ids:
			clean_news_id = dirty_news_id.split("=")[2]
			if int(clean_news_id) not in clean_news_ids:
				clean_news_ids.append(int(clean_news_id))
	
		return clean_news_ids

	def news(self, news_id):
		news           = {"title": "", "body": "", "attached": {"url": "", "filename": ""}}
		html           = urllib2.urlopen("https://www.vklass.se/SchoolNews.aspx?id=%i" % news_id).read()
		news['body']   = cre.prettify(cre.between('<span id="ctl00_ContentPlaceHolder2_newsShortLabel">', '</span>', html))
		news['title']  = cre.prettify(cre.between('<span id="ctl00_ContentPlaceHolder2_nameLabel">', '</span>', html))
		attached_file_html_chunk = cre.between('<a id="ctl00_ContentPlaceHolder2_NewsAttachmentLink" href="', '</a>', html)
		if attached_file_html_chunk != "":
			news['attached']['url'] = attached_file_html_chunk.split('">')[0]
			news['attached']['filename'] = attached_file_html_chunk.split('">')[1]

		return news
	
	def all_news(self):
		all_news = []
		for news_id in self.news_listing():
			news = self.news(news_id)
			all_news.append(news)
		all_news.reverse()

		return all_news
	
	def latest_profile_visitors(self):
		visitors = []
		html     = urllib2.urlopen("%s/UserVisitors.aspx" % self.base_url).read()
		trash    = cre.all_between('<td class="logg-name">', '</span></td>', html)
		for trash in trash:
			visitor = {}
			visitor['name'] = trash.split('"')[3]
			if visitor['name'].endswith('_dateLabel'):
				visitor['name'] = "anonymous"
			visitor['time'] = trash.split(">")[-1]
			visitors.append(visitor)
		visitors.reverse()

		return visitors
	
	def exam_statistics(self, exam_id):
		# The exam_id seems to increment by one for every new exam and they start at 1 and is 2011-04-16 around 8000.

		html                        = urllib2.urlopen("%s/ExamStatistics.aspx?id=%i" % (self.base_url, exam_id)).read()
		critical_error_messages = ["existerar ej"]
		for error_message in critical_error_messages:
			if error_message in html:
				return None
		else:
			exam                        = {"possible_grades": None, "exam_participants": None, "course_participants": None, "grades": None}
			exam['name']                = cre.between('<span id="ctl00_ContentPlaceHolder2_nameLabel">', '</span>', html)
			exam['course']              = cre.between('<span id="ctl00_ContentPlaceHolder2_courseLabel">', '</span>', html)
			exam['type']                = cre.between('<span id="ctl00_ContentPlaceHolder2_typeLabel">', '</span>', html).replace("  ", "")
			exam['date']                = cre.between('<span id="ctl00_ContentPlaceHolder2_dateLabel">', '</span>', html)
			if "ej statistik" not in html:
				exam['possible_grades']     = cre.between('<span id="ctl00_ContentPlaceHolder2_gradingLabel">', '</span>', html).split("/")
				exam['exam_participants']   = cre.between('<span id="ctl00_ContentPlaceHolder2_numberLabel">', '</span>', html).split(" ")[0]
				exam['course_participants'] = cre.between('<span id="ctl00_ContentPlaceHolder2_numberLabel">', '</span>', html).split(" ")[2]
				exam['grades']              = {}
				for offset in range(len(exam['possible_grades'])):
					exam['grades'][exam['possible_grades'][offset]] = cre.between('<span id="ctl00_ContentPlaceHolder2_infoLabel">', '</span>', html).replace(" ", "").split(":")[1 + offset].split("<")[0]
	
			return exam
	
	def class_uid(self):
		html      = urllib2.urlopen("%s/classlist.aspx" % self.base_url).read()
		class_uid = cre.between("classUID=\" \+ '", "'\)", html)

		return class_uid

	def class_calendar_exam_ids(self):
		url  = "%s/ClassCalendar.aspx?id=%s" % (self.base_url, self.class_uid())
		html = urllib2.urlopen(url).read()
		client.dump(html)
		ids = [int(id) for id in cre.all_between('<a href="ExamStatistics\\.aspx\\?id=', '&', html)]

		return ids
	
	def class_calendar_exams(self):
		exams = []
		for exam_id in self.class_calendar_exam_ids():
			exam_data = self.exam_statistics(exam_id)
			exams.append(exam_data)
			
		return exams
	
	def class_events(self):
		events       = []
		html         = urllib2.urlopen("%s/ClassCalendar.aspx?id=%s" % (self.base_url, self.class_uid())).read()
		event_chunks = cre.all_between('<span id="ctl00_ContentPlaceHolder2_monthsRepeater_ctl.._eventsRepeater_ctl.._topicLabel">Klassh..ndelse: ', '</span></dd>', html)
		for trash in event_chunks:
			event = {"name": trash.split("</span>")[0], "description": trash.split('">Beskrivning: ')[-1]}
			events.append(event)

		return events	

	def time_summary(self):
		# Presence the latest 30 days
		html     = urllib2.urlopen("%s/Results/default.aspx" % self.base_url).read()
		trash    = cre.between('<span id="ctl00_ContentPlaceHolder2_attendanceMinutesLabel">', '</span>', html).split(" ")
		time = {"present": {}, "absent": {}}
		time['scheduled_minutes'] = int(trash[6])

		time['present']['percentage'] = int(trash[0])
		time['present']['minutes'] = int(trash[3])

		time['absent']['minutes'] = time['scheduled_minutes'] - time['present']['minutes']
		time['absent']['late_arrival_minutes'] = int(trash[10])
		time['absent']['approved_percentage'] = int(trash[14])
		time['absent']['unapproved_percentage'] = int(trash[18])
		
		return time

	def status(self):
		# This one is called scoreboard on vklass.se. Ugly and hackish, fix later..
		html = urllib2.urlopen("%s/Handler/scoreboard.ashx" % self.base_url).read()
		info = []
		for trash in cre.all_between("</span>", "</dd><dt><a href=", html):
			info.append(trash.split(">")[-1])

		status = {'guestbook': info[0], 'messages': info[1], 'forum': info[2], 'friends': info[3]}

		return status
	
	def current_schedule(self):
		# Will show the current schedule for this week. Ugly and hackish, fix later..
		html     = urllib2.urlopen("%s/schema.aspx" % self.base_url).read()
		lessons  = {"monday": [], "tuesday": [], "wednesday": [], "thursday": [], "friday": []}
		for chunk in cre.all_between('<div class="LessonInfoContainer"', '</td>', html):
			name = chunk.split("<br />")[-3].split("<span>")[-1]
			room = chunk.replace("</span></div>", "").split(">")[-1]
			for thingie in room.split(" "):
				try:
					room = int(thingie)
				except:
					pass
			time             = cre.between('px;">', "<br />", chunk)
			day              = time.split(" ")[0]
			from_hour        = time.split(" ")[1]
			to_hour          = time.split(" ")[3]
			day_replacements = [["M", "monday"], ["Ti", "tuesday"], ["Ons", "wednesday"], ["To", "thursday"], ["F", "friday"]] 
			for replacement in day_replacements:
				if day.startswith(replacement[0]):
					day = replacement[1]
			lesson = {"name": name, "room": room, "from": from_hour, "to": to_hour}
			lessons[day].append(lesson)
		return lessons
	
	def courses(self):
		html    = urllib2.urlopen("%s/courselist.aspx" % self.base_url).read()
		courses = cre.all_between('<td class="kurs"><a id="ctl00_ContentPlaceHolder2_StudentRepeater_ctl.._courseLink" href="Course.aspx\?id=.{5}">', '</a>', html)
		
		return courses
	
	def food_menu(self):
		menu             = {"monday": "", "tuesday": "", "wednesday": "", "thursday": "", "friday": ""}
		html             = urllib2.urlopen("https://www.vklass.se/MySchool.aspx").read()
		days             = cre.all_between('<strong><span id="ctl00_ContentPlaceHolder2_lunchRepeater_ctl.._dayLabel">', '</span></strong>', html)
		meals            = cre.all_between('<span id="ctl00_ContentPlaceHolder2_lunchRepeater_ctl.._dayMenuLabel">', '</span>', html.replace("<br />", "").replace("\n", "").replace("\r", ""))

		for id in range(len(days)):
			for day in [["M", "monday"], ["Ti", "tuesday"], ["Ons", "wednesday"], ["To", "thursday"], ["F", "friday"]]:
				if days[id].startswith(day[0]):
					menu[day[1]] = meals[id]

		return menu
	
	def message(self, message_id):
		html                           = urllib2.urlopen("%s/Messaging/MessageRead.aspx?id=%i" % (self.base_url, message_id)).read()
		message                        = {"attachments": [], "participants": [], "posts": []}
		message['owner']               = self.username
		message['body']                = cre.prettify(cre.all_between('<span id="ctl00_ContentPlaceHolder2_postRepeater_ctl.._textLabel">', '</span>', html)[-1])
		message['title']               = cre.prettify(cre.between('<span id="ctl00_ContentPlaceHolder2_topicLabel">', '</span>', html))
		message['created']             = cre.prettify(cre.between('<span id="ctl00_ContentPlaceHolder2_dateLabel">', '</span>', html))
		trash                          = cre.all_between('<span id="ctl00_ContentPlaceHolder2_postRepeater_ctl.._posterLabel">', '</p>', html)
		del trash[-1]
		for trash in trash:
			username                   = trash.split("</span>")[0]
			body                       = trash.split("</span>")[-2].split('_textLabel">')[-1]
			date                       = cre.between('<span id="ctl00_ContentPlaceHolder2_postRepeater_ctl.._Label1">', '</span>', trash)
			post = {"username": username, "date": date, "body": body}
			message['posts'].append(post)

		trash                          = cre.between('<a id="ctl00_ContentPlaceHolder2_creatorLink" href="/User.aspx\?id=', '</a></h3>', html).split('">')
		message['creator']             = {'user_id': int(trash[0]), "name": trash[1]}
		participants_dirty_html_chunks = cre.between('<h3>Deltagare: ', '</h3>', html).split(', ')
		for dirty_participant_chunk in participants_dirty_html_chunks:
			user_id                    = int(cre.between('<a href="/User.aspx\?id=', '">', dirty_participant_chunk))
			username                   = cre.between('">', '</a>', dirty_participant_chunk)
			participant                = {"user_id": user_id, "username": username}
			message['participants'].append(participant)
			for post_id in range(len(message['posts'])):
				if message['posts'][post_id]['username'] == username:
					message['posts'][post_id]['user_id'] = user_id
		
		dirty_attachment_html_chunks   = cre.all_between('_AttachmentLink" href="', '</a></li>', html)
		for chunk in dirty_attachment_html_chunks:
			attachment                 = {"url": chunk.split('"')[0], "filename": chunk.split('">')[-1]}
			message['attachments'].append(attachment)

		return message
	
	def first_message_ids(self):
		return [int(x) for x in cre.all_between('href="MessageRead.aspx\?id=', '&amp;', urllib2.urlopen(self.base_url + "/Messaging/Messages.aspx").read())]
	
	def first_messages(self):
		i           = 0
		messages    = []
		message_ids = self.first_message_ids()
		for message_id in self.first_message_ids():
			client.push("Fetching message: %i [%i/%i]" % (message_id, i + 1, len(message_ids)))
			message = self.message(message_id)
			messages.append(message)
			i += 1
		client.push("\n")

		return messages
