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
			pivot_idx = len(arr) -1; # end of array
			ge_ele_ptr = -1

			for j in range(low, high):
				r = comparison_fn(arr[j], arr[pivot_idx])
				if r == 1:
					# element greater than pivot
					ge_ele_ptr += 1
					arr[ge_ele_ptr], arr[j] = arr[j], arr[ge_ele_ptr]

	def bubble_sort(arr, comparison_fn):
		for i in range(len(arr) -1):
			for j in range(len(arr) -1 -i):
				r = comparison_fn(arr[j], arr[j +1])
				print(j, arr[j], arr[j +1], r)
				if (r == 1):
					# arr[j] > arr[j +1]
					arr[j], arr[j +1] = arr[j +1], arr[j]




class LibraryData:
	BOOK_TYPE = {
		"Hard Cover": 1,
		"Paper Back": 2,
		"EBook": 3
	}

	def __init__(self):
		self.data = database_engine.created_readers["isbn"]

		# will be populated when self.process_data() is called
		self.sorted_isbn = [];
		self.sorted_title = [];

	def validate_isbn(isbn_code):
		# returns true if isbn is validated, follows 3x-13y format
		if (isbn_code.find("-") == -1):
			# no hyphen
			return False

		s = isbn_code.split("-")
		if (len(s) != 2 or len(s[0]) != 3 or len(s[1]) != 13):
			# invalid length
			return False

		if (not s[0].isdigit() or not (s[1].isdigit())):
			# not valid digits
			return False

		# passed all checks
		return True

	def process_data(self):
		# populate self.sorted_isbn and self.sorted_title in ascending order
		# implements quick sort
		alpha_data = []
		isbn_data = []

		for isbn in self.data["all"]:
			alpha_data.append([self.data["all"][isbn]["title"], isbn])
			isbn_data.append(isbn)

		UtilCLI.bubble_sort(alpha_data, lambda a, b: UtilCLI.compare_str(a[0], b[0])) # wrap in lambda since elements of alpha_data is [title, isbn]
		UtilCLI.bubble_sort(isbn_data, UtilCLI.compare_str) # no need to be wrapped

		# transform alpha_data to primitive elements instead of an array
		primitive_alpha_data = []; # stores alpha_data but without the title reference, simply stores the isbn reference (since alpha_data is already sorted)
		total_length = len(alpha_data)
		for i in range(total_length):
			primitive_alpha_data.append(alpha_data[i][1]) # push only the isbn reference (of string type - primitive)

		self.sorted_isbn = isbn_data # elements already in primitive data type
		self.sorted_title = primitive_alpha_data


	def add_book(self, book_data):
		# book_data: {isbn: str, title: str, quantity: integer, type: integer}
		# adds a book to self.data, returns boolean indicating result of operation (true for success)
		self.data[book_data["isbn"]] = {
			"title": book_data["title"],
			"type": book_data["type"],
			"quantity": book_data["quantity"]
		}

		# update references
		self.process_data()

		# return status true
		return true

	def search_book(self, search_params):
		# search_params: {query: str?, type: integer?}
		# returns a sorted array based on search_params
		interested = []; # build a list of interested search candidates to search

		# search parameters
		queryStr = search_params["query"]
		typeFilter = search_params["type"]

		for isbn_code in self.sorted_title:
			if (queryStr != None and self.data[isbn_code]["title"].find(queryStr) != -1):
				# interested candidate (name match)
				if (typeFilter != None and self.data[isbn_code]["type"] == typeFilter):
					# interested candidate (matches type)
					pass
				elif (typeFilter == None):
					# interested candidate (no type match performed)
					pass

			# if (self.data[isbn_code]["title"].find(search_params))
		pass

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
		1. write to database (push all database_readers)
		2. output goodbye message
		"""

		database_engine.created_readers["isbn"].push()
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
		elif (command == "add"):
			book_data = {
				"isbn": args.get("isbn"),
				"title": args.get("title"),
				"quantity": args.get("quantity"),
				"type": args.get("type")
			}

			# ask for all the book details in sequence, use data provided in args as default
			print("Data required for book entry.")

			# isbn code
			if (book_data["isbn"] != None and LibraryData.validate_isbn(book_data["isbn"])):
				# has default data (valid isbn)
				isbn_inpt = input("ISBN ({}): ".format(book_data["isbn"]))

				if (isbn_inpt == ""):
					# empty input, use default
					pass
				else:
					# value keyed in, overwrite arguments
					book_data["isbn"] = isbn_inpt
			else:
				# no default data can be used
				if (book_data["isbn"] != None):
					# invalid isbn, warn user
					print("[WARN]: ISBN code provided in the wrong format, please conform to xxx-yyyyyyyyyyyyy (3x-13y).")

				isbn_inpt = "";
				while not LibraryData.validate_isbn(isbn_inpt):
					# input required
					isbn_inpt = input("ISBN (-1 to exit): ")
					if (isbn_inpt == "-1"):
						break

				if (isbn_inpt == "-1"):
					# cancel command
					return
				else:
					# validated isbn_inpt
					book_data["isbn"] = isbn_inpt

			# title input
			if (book_data["title"] != None and len(book_data["title"]) >= 1):
				# has default data (valid title)
				title_inpt = input("Title ({}): ".format(book_data["title"]))

				if (title_inpt == ""):
					# empty input, use default
					pass
				else:
					# value keyed in, overwrite arguments
					book_data["title"] = title_inpt
			else:
				# no default data can be used
				if (book_data["title"] != None):
					# invalid isbn, warn user
					print("[WARN]: Title provided in wrong format, please conform to the restriction of at least 1 character.")

				title_inpt = "";
				while title_inpt == "":
					# input required
					title_inpt = input("Title (-1 to exit): ")
					if (title_inpt == "-1"):
						break

				if (title_inpt == "-1"):
					# cancel command
					return
				else:
					# validated title input
					book_data["title"] = title_inpt

			# quantity input
			if (book_data["quantity"] != None and book_data["quantity"].isdigit() and book_data["quantity"][0] != "0"):
				# has default data (valid qty, positive integer with no leading zeroes as to suggest non-zero values)
				qty_inpt = input("Quantity ({}): ".format(book_data["quantity"]))

				if (qty_inpt == ""):
					# empty input, use default
					# typecast default to int too (since parsed from command line)
					book_data["quantity"] = int(book_data["quantity"])
				else:
					# value keyed in, overwrite arguments
					book_data["quantity"] = int(qty_inpt)
			else:
				# no default data can be used
				if (book_data["quantity"] != None):
					# invalid isbn, warn user
					print("[WARN]: Quantity provided in wrong format, please enter a positive non-negative integer without zero padding.")

				qty_inpt = "";
				while not qty_inpt.isdigit() or qty_inpt[0] == "0":
					# input required
					qty_inpt = input("Quantity (-1 to exit): ")
					if (qty_inpt == "-1"):
						break

				if (qty_inpt == "-1"):
					# cancel command
					return
				else:
					# validated quantity input
					book_data["quantity"] = int(qty_inpt) # typecast it to an integer first

			# type input
			if (book_data["type"] != None and book_data["type"].isdigit() and 1 <= int(book_data["type"][0]) <= 3):
				# has default data (valid qty, positive integer with no leading zeroes as to suggest non-zero values)
				type_inpt = input("Type\n\t1. Hard cover\n\t2. Paper back\n\t3. EBook\n({}): ".format(book_data["type"]))

				if (type_inpt == ""):
					# empty input, use default
					# typecast default to int too (since parsed from command line)
					book_data["type"] = int(book_data["type"])
				else:
					# value keyed in, overwrite arguments
					book_data["type"] = int(type_inpt)
			else:
				# no default data can be used
				if (book_data["type"] != None):
					# invalid type, warn user
					print("[WARN]: Type value provided in wrong format, please enter a selection of book types from 1-3 (inclusive).")

				type_inpt = "";
				while not type_inpt.isdigit() or not(1 <= int(type_inpt) <= 3):
					# input required
					type_inpt = input("Type\n\t1. Hard cover\n\t2. Paper back\n\t3. EBook\n(-1 to exit): ")
					if (type_inpt == "-1"):
						break

				if (type_inpt == "-1"):
					# cancel command
					return
				else:
					# validated type input
					book_data["type"] = int(type_inpt) # typecast it to an integer first


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