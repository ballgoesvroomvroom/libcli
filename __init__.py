import time
import json
import os
from os import path
from Crypto.Hash import SHA512

from includes.database_engine import database_engine

# database collections
database_engine.create_reader("users.json")
database_engine.create_reader("session.json")

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
		hash_object = SHA512.new(data=(msg +self.salt).encode("ASCII")) # accepts byte strings, encode in ASCII format
		return hash_object.hexdigest()


class LibCLI:
	def __init__(self):
		self.user = -1

	def login(self):
		# try to use cookies
		if ('token' in database_engine.created_readers["session"]):
			# validate token
			
		
		# ask for a username
		username = input("Username: ")

		if not (username in database_engine.created_readers["users"]):
			# check for validity of user
			return False

		password = input("Password (entered as plaintext, not hidden): ")
		# valid, compare password hashes

		
		
print(AuthManager().hash("0000"))