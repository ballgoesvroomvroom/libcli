import time
import json
import os
from os import path
import hashlib

from includes.database_engine import database_engine

# database collections
database_engine.create_reader("users.json")

class HistoryManager:
	def __init__(self):
		self.cacheHistory = -1 ## value of -1 means not yet cached; will store the length of self.content here for cache validation
		self.history = ""

		self.reader = database_engine.create_reader("history.json")
		self.content = self.reader.content # reference to .content within reader object so any chances to self.content will affect reader.content too

	def logAction(self, userId, action, *args):
		self.content.append([time.time(), userId, action, *args])

	def display(self, limit = 20):
		# returns a repr string of the history action in verbose format
		# with default limit to 20 - i.e. returns up to 20 entries in the history
		if (self.cacheHistory == -1 or (self.cacheHistory != len(self.content))):
			# cache is invalidated, regenerate
			history = "{:<20} | {:<10} | {:<2} | {:<30}".format("timestamp", "userid", "actionid", "description")
			for data in range(limit):
				action_code = data[2]
				action_description = "";

				if (action_code == 2):
					# searched for a book with id
					action_description = "searched for book ({})".format(data[3])
				history = "{:<20} | {:<10} | {:<2} | {:<30}\n".format(data[0], data[1], data[2], action_description)

			self.history = history[:-1]; # slice away trailing new line character
			self.cacheHistory = len(self.content)
		
		return self.history # re-use cache

class AuthManager:
	def __init__(self):
		# load up local environment variables in .env
		with open(path.join(__file__, "../.env"), "r") as f:
			for line in f:
				line = line.strip() # remove leading & trailing whitespaces
				if line and not (line.startswith("#")):
					key, value = line.split("=", 1) # split by "=" ONCE only
					os.environ[key] = value

		self.salt = os.environ.get("BUTTER")
	
	def hash(self, msg):
		# msg: string
		# hashes msg into hex representation
		hash_object = hashlib.sha512()
		hash_object.update((msg +self.salt).encode("ASCII")) # accepts byte strings, encode in ASCII format
		return hash_object.hexdigest()

	def get_access_level(self, username, verbose=False):
		# returns the corresponding access level for a user
		# verbose (optional boolean parameter), if true will return string, else simply returns the access level code
		if (username in database_engine.created_readers["users"]):
			al = database_engine.created_readers["users"][username]["access_level"]
			if (verbose):
				return ["User", "Librarian", "Administrator", "Root"][al]
			else:
				return al
		else:
			return None

	def authenticate_creds(self, username, password):
		# returns 1 upon successful authentication
		# returns 2 upon unsuccessful authentication (invalid username)
		# returns 3 upon unsuccessful authentication (invalid password)
		if not (username in database_engine.created_readers["users"]):
			return 2
		if len(password) == 0:
			return 3

		password_hash = self.hash(password)
		eq = password_hash == database_engine.created_readers["users"][username]["password"]
		if (eq):
			return 1
		else: return 3

class UtilCLI:
	# CLI utility class for misc actions not related to library function
	def clear():
		# clear screen
		if (os.name == "nt"):
			# windows
			os.system("cls")
		else:
			# posix (mac, linux)
			os.system("clear")

	def white_lines(line):
		# line: int (number of empty lines to print out)
		# prints out empty lines depending on line
		print("\n" *line)


class LibCLI:
	def __init__(self):
		# objects
		self.authManager = AuthManager()

		# states
		self.active = True

		# session memory
		self.username = ""
		self.session_start = time.perf_counter();

	def set_user(self, username):
		self.username = username
		self.access_level = self.authManager.get_access_level(username)
		self.access_level_verbose = self.authManager.get_access_level(username, True)

		# clear screen, greet user
		UtilCLI.clear();
		print("{} | {}".format(self.username, self.access_level_verbose))
		UtilCLI.white_lines(5);

		print("Welcome to The Library\nWhere knowledge overflows.")

		UtilCLI.white_lines(5);

	def logout_handler(self):
		# log out handler, performs log out tasks
		"""
		tasks to do
		1. write to database
		2. output goodbye message
		"""

		print("")

	def login_handler(self):
		# login handler

		# get a valid username
		username = ""
		for u_retries in range(3):
			username_inp = input("Username: ")

			if len(username_inp) == 0:
				print("Empty username entered, please try again.")
				continue

			print(database_engine.created_readers["users"])
			if (username_inp in database_engine.created_readers["users"]):
				username = username_inp; # only assign upon successful (so post-loop control knows whether max_retries was hit)
				break
			else:
				print("No user found for username, {}, please enter a valid username.".format(username_inp))

		if (len(username) == 0 and u_retries == 2):
			return False


		# ask for password
		for p_retries in range(3):
			password = input("Password (entered as plaintext, not hidden): ")

			code = self.authManager.authenticate_creds(username, password)
			if (code == 1):
				# successful
				self.set_user(username)
				break
			elif (code == 2):
				# invalid username?
				# ask out username again
				return self.login();
			elif (code == 3):
				# invalid password

				if (p_retries == 2):
					# max retries
					print("Invalid password, maximum attempts reached, please attempt to log in again.")
				else:
					print("Invalid password, please try again ({} attempts left).".format(3 -p_retries -1))

if __name__ == "__main__":
	CLI = LibCLI();

	# log in
	success = CLI.login_handler();

	if not (success):
		# exit program
		print("Failed to authenticate, please try re-running the program again.")
		return

	# run commands (initiate main control loop)
	while CLI.active:

LibCLI().login_handler();