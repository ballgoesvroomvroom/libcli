import time
import json
import os
from os import path
import hashlib

from includes.database_engine import database_engine

# database collections
database_engine.create_reader("users.json")
database_engine.create_reader("isbn.json")

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

	def compare_str(a, b):
		# a, b: str
		# compares both string alphabetically to determine order
		# returns 1 if a > b (len(a) > len(b); 'Ab' > 'Aa')
		# returns 2 if a < b (len(a) < len(b); 'Aa' < 'Ab')
		# returns 3 if a == b

		# convert them to lower case first for fair comparison
		a, b = a.lower(), b.lower()

		# handle extreme cases (empty comparisons)
		if (a == ""):
			if (b == ""):
				# equal
				return 3
			else: return 2 # a is smaller than b
		elif (b == ""):
			# b is smaller than a
			return 1
		elif (a == b):
			# both the same
			return 3

		print("PREMATURE")

		lower_limit = min(len(a), len(b))
		for idx in range(lower_limit):
			x, y = ord(a[idx]), ord(b[idx])
			if (x == y):
				continue
			elif (x > y):
				# b is smaller
				return 1
			else:
				# a is smaller
				return 2

		# not yet determined
		# occurs when either one is an anchored substring of the other string
		# e.g. a = "he", b = "hello"
		if (len(a) < len(b)):
			# a is smaller
			return 2
		else:
			# a is bigger (should never be the same since equality check has been performed on a and b (proper string subsets))
			return 1

	def _quick_sort_partition(arr, comparison_fn, low, high):
		# partition function, returns partition index
		pivot_idx = high
		ge_ele_ptr = low -1

		for j in range(low, high):
			print("COMPARING")
			r = comparison_fn(arr[j], arr[pivot_idx])
			if r == 1:
				# element greater than pivot
				ge_ele_ptr += 1
				arr[ge_ele_ptr], arr[j] = arr[j], arr[ge_ele_ptr]

		# swap pivot element with greater element
		arr[ge_ele_ptr], arr[pivot_idx] = arr[pivot_idx], arr[ge_ele_ptr]

		# return partition index
		return ge_ele_ptr +1

	def quick_sort(arr, comparison_fn, low=0, high=-1):
		# sorts elements in arr
		# will call comparison_fn with TWO elements as arguments
		# comparison_fn to return 1 if a > b, or 2 if a <= b

		if (high == -1): high = len(arr) -1 # use length instead of negative indices

		if (low < high):
			partition_idx = UtilCLI._quick_sort_partition(arr, comparison_fn, low, high)

			UtilCLI.quick_sort(arr, comparison_fn, low, partition_idx -1)
			UtilCLI.quick_sort(arr, comparison_fn, partition_idx +1, high)
			print("RUNNNING")
			pivot_idx = len(arr) -1; # end of array
			ge_ele_ptr = -1

			for j in range(low, high):
				r = comparison_fn(arr[j], arr[pivot_idx])
				if r == 1:
					# element greater than pivot
					ge_ele_ptr += 1
					arr[ge_ele_ptr], arr[j] = arr[j], arr[ge_ele_ptr]

	def bubble_sort(arr, comparison_fn):
		print("INIT", arr)
		for i in range(len(arr) -1):
			for j in range(len(arr) -1 -i):
				r = comparison_fn(arr[i], arr[i +1])
				print(arr[i], arr[i +1], r)
				if (r == 1):
					# arr[i] > arr[i +1]
					arr[i], arr[i +1] = arr[i +1], arr[i]




class LibraryData:
	def __init__(self):
		self.data = database_engine.created_readers["isbn"]

		# will be populated when self.process_data() is called
		self.sorted_isbn = [];
		self.sorted_title = [];

	def process_data(self):
		# populate self.sorted_isbn and self.sorted_title in ascending order
		# implements quick sort
		alpha_data = []
		isbn_data = []

		for isbn in self.data["all"]:
			alpha_data.append([self.data["all"][isbn]["title"], isbn])
			isbn_data.append(isbn)

		print("BEFORE", alpha_data)
		UtilCLI.bubble_sort(alpha_data, lambda a, b: UtilCLI.compare_str(a[0], b[0])) # wrap in lambda since elements of alpha_data is [title, isbn]
		UtilCLI.bubble_sort(isbn_data, UtilCLI.compare_str) # no need to be wrapped

		print("AFTER", alpha_data)
		for x in alpha_data:
			print(x)

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

class Screen:
	def __init__(self, header):
		self.content = header # content will be built here

	def build(self, content):
		# append content to self.content
		self.content += str(content)

	def out(self):
		# clear screen first
		UtilCLI.clear();
		print(self.content);

		# remove reference from self.content
		self.content = None # await GC to clean up object


class LibCLI:
	def __init__(self):
		# objects
		self.authManager = AuthManager()

		# states
		self.active = True

		# session memory
		self.username = ""
		self.session_start = time.perf_counter();

	def create_new_screen(self):
		return Screen("{} | {}\n".format(self.username, self.access_level_verbose))

	def set_user(self, username):
		self.username = username
		self.access_level = self.authManager.get_access_level(username)
		self.access_level_verbose = self.authManager.get_access_level(username, True)

		# greet user with new screen
		screen = self.create_new_screen()
		screen.build("\n\n\n\nWelcome to The Library\nWhere knowledge overflows.\n\n\n\n")

		# out the screen
		screen.out();

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

		# clear screen
		UtilCLI.clear();

		# get a valid username
		username = ""
		for u_retries in range(3):
			username_inp = input("Username: ")

			if len(username_inp) == 0:
				print("Empty username entered, please try again.")
				continue

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
					return False # return an exit code of False so main control flow knows login was unsuccessful
				else:
					print("Invalid password, please try again ({} attempts left).".format(3 -p_retries -1))

		return True # returns true so main control flow knows login was successful

	def displayBooks(n=10):
		# displays the interface to select books (a list is visually available)
		# sorted by isbn no (s flag) or by title name (a flag)
		# n being page size
		screen = self.create_new_screen()
		screen.build("Search for books\n\n")

		data = database_engine.created_readers["isbn"]


	def kernel(self, command, args={}, flags=[]):
		# executes the actual command
		if (command == "help"):
			pass

		if (command == "show"):
			if (name in args):
				# name present
				self.showBookDetails(args.name)
			else:
				self.showAllBooks(n=10)


	def interface(self):
		# responsible for retrieving ONE single command
		inpt = input("System: ")

		# parse input (extract command, space-separated)
		data = inpt.split(" ")
		command = data[0]

		# differentiate args from flags
		args, flags = {}, []
		for value in data[1:]:
			if (value.find("=") != -1):
				# argument found, can only contains two parts (key=value)
				split = value.split("=")
				if (len(split) != 2):
					print("[ERROR]: malformed input, there can only contain one '=' for every key value pair argument.")
					return

				key, value = split # tuple unpacking (with list)
				args[key] = value
			elif (value[0] == "-"):
				# should exist as the first element
				# e.g. '-i' for i flag
				if (value.count("-") != 1):
					# there can only exist one flag demarker
					print("[ERROR]: malformed input, there can only exist one '-' (flag marker) per flag.")
					return
				else:
					flags.append(value[1:]) # append without the hyphen
			else:
				# unrecognised input
				print("[ERROR]: malformed input, unknown character sequence in command, '{}'.".format(value))
				return

		self.kernel(command, args=args, flags=flags)


if __name__ == "__main__":
	# do some preprocessing on the book database (isbn.json)
	LibraryData().process_data();
	exit(1)

	# call login handler to perform login
	CLI = LibCLI();

	# log in
	success = CLI.login_handler();

	if not (success):
		# exit program
		print("Failed to authenticate, please try re-running the program again.")
		exit(1); # exit program with status code of 1

	# run commands (initiate main control loop)
	while CLI.active:
		CLI.interface()

LibCLI().login_handler();