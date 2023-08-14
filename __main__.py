import time
import math
import random
import json
import hashlib
import os
from os import path

from includes.database_engine import database_engine
from includes import help_messages

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

	def levenshtein_distance(a, b):
		# returns the levenshtein distance between two strings
		la, lb = len(a) +1, len(b) +1 # represents m and n (distance being an m * n matrix)
		distance = [[0 for x in range(la)] for y in range(lb)] # initiate array

		# first row, first column
		for x in range(la):
			distance[0][x] = x

		for y in range(lb):
			distance[y][0] = y

		for y in range(1, lb):
			for x in range(1, la):
				sc = 1 if a[x -1] != b[y -1] else 0 # substitution cost

				distance[y][x] = min(
					distance[y -1][x] +1,
					distance[y][x -1] +1,
					distance[y -1][x -1] +sc
				)

		return distance[lb -1][la -1]

	def get_command(command_inpt, command_list):
		# returns an index within command_list, if no commands found, suggest close proximity commands
		# returns if exact match: [True, idx_of_element: int]
		# returns if no exact found: [False, suggestion: str?]; suggestion may be None if threshold not met
		try:
			idx = command_list.index(command_inpt.lower())
			return [True, idx]
		except ValueError:
			min_distance = 10 # acting threshold (stores minimum value)
			min_ele = None # store contents of minimal element
			for x in command_list:
				d = UtilCLI.levenshtein_distance(command_inpt, x)
				if (d) < min_distance:
					min_distance = d
					min_ele = x

					if (d <= 1):
						# closest you'll get
						return [False, min_ele]

			return [False, min_ele]

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
		pivot_idx = random.randint(low, high)
		ge_ele_ptr = low -1

		for j in range(low, high):
			r = comparison_fn(arr[j], arr[pivot_idx])
			if r == 2:
				# element greater than pivot
				ge_ele_ptr += 1
				arr[ge_ele_ptr], arr[j] = arr[j], arr[ge_ele_ptr]

		# swap pivot element with greater element
		arr[ge_ele_ptr +1], arr[pivot_idx] = arr[pivot_idx], arr[ge_ele_ptr +1]

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

	def bubble_sort(arr, comparison_fn):
		# comparison function
		# returns 1 if a > b (len(a) > len(b); 'Ab' > 'Aa')
		# returns 2 if a < b (len(a) < len(b); 'Aa' < 'Ab')
		# returns 3 if a == b

		for i in range(len(arr) -1):
			for j in range(len(arr) -1 -i):
				r = comparison_fn(arr[j], arr[j +1])
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

		# parse self.BOOK_TYPE
		self.BOOK_TYPE_MAPPED = []
		for type_idx in range(3):
			for key in self.BOOK_TYPE.keys():
				if type_idx +1 == self.BOOK_TYPE[key]:
					self.BOOK_TYPE_MAPPED.append(key)
					break

		# will be populated when self.process_data() is called
		self.sorted_isbn = []
		self.sorted_title = []

		self.total_entries = -1 # will be initialised

	def validate_isbn(isbn_code):
		# returns true if isbn is validated, accepts both 10 mod and 11 mod versions
		# compares the check digit
		if (isbn_code.find("-") == -1):
			# no hyphen, 10 digit isbn
			if len(isbn_code) != 10:
				return False
			else:
				# exactly 10 chars, compute check digit
				if not (isbn_code[:-1].isdigit()):
					# can only contain digits (portion until check digit, exclusive)
					return False
				else:
					checksum = 0
					for idx in range(9):
						factor = 10 -idx
						checksum += int(isbn_code[idx]) *factor

					# compute check digit (last digit of isbn)
					checkdigit = 11 -(checksum %11)
					print(checksum, checkdigit)
					if checkdigit == 1:
						checkdigit = "X"
					else:
						checkdigit = str(checkdigit)
					return isbn_code[-1] == checkdigit
		else:
			s = isbn_code.split("-")
			if (len(s) != 2 or len(s[0]) != 3 or len(s[1]) != 10):
				# invalid length
				return False

			if (not s[0].isdigit() or not (s[1][:-1].isdigit())): # don't pass 'X' check digit into .isdigit()
				# not valid digits
				return False

			# compute checkdigit
			alternate = True
			digits = s[0] +s[1] # string concatenation
			checksum = 10
			for idx in range(12):
				factor = 1 if alternate else 3
				checksum += int(digits[idx]) *factor

				alternate = not alternate # toggle

			# compute check digit
			checkdigit = 10 -(checksum %10)
			return int(isbn_code[-1]) == checkdigit

	def duplicate_isbn(self, isbn):
		# returns true if unique isbn
		return isbn in self.data

	def process_data(self):
		# populate self.sorted_isbn and self.sorted_title in ascending order
		# implements quick sort
		alpha_data = []
		isbn_data = []

		self.total_entries = 0 # reset counter first
		for isbn in self.data:
			alpha_data.append([self.data[isbn]["title"], isbn])
			isbn_data.append(isbn)

			# increment total entries
			self.total_entries += 1

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
		return True

	def delete_book(self, isbn):
		# removes isbn from database, and from all user's loan references
		del self.data[isbn]

		# update references
		self.process_data()

		for username in database_engine.created_readers["users"]:
			user_data = database_engine.created_readers["users"][username]
			loan_idx = 0
			for loan_entry in user_data["loaning"]:
				if (loan_entry[0] == isbn):
					# pop entry (should only have one unique entry in "loaning")
					user_data["loaning"].pop(loan_idx)
					break
				loan_idx += 1

			n = len(user_data["loaned_books"])
			for loan_idx in range(n):
				loan_entry = user_data["loaned_books"][n -loan_idx -1] # start from the last element
				if (loan_entry[0] == isbn):
					user_data["loaned_books"].pop(n -loan_idx -1) # minimal shifting

		return True
					

	def update_book(self, isbn, payload):
		# payload: {title: str?, quantity: int?, type: int?}
		# return boolean (success state)
		if (self.data.get(isbn)):
			book_data = self.data[isbn]

			title = book_data["title"]
			if ("title" in payload):
				# validate title
				if type(payload["title"]) != str or payload["title"] == "":
					# not a string or an empty string
					return False
				else:
					# valid title
					title = payload["title"]

			quantity = book_data["quantity"]
			if ("quantity" in payload):
				# validate quantity
				if type(payload["quantity"]) != int or payload["quantity"] < 0:
					# not an int, OR value is a zero/negative number
					return False
				else:
					# valid quantity
					quantity = payload["quantity"]

			book_type = book_data["type"]
			if ("type" in payload):
				# validate type
				if type(payload["type"]) != int or payload["type"] <= 0 or payload["type"] >= 4:
					# not an int, OR value <= 0, OR value >= 0
					return False
				else:
					# valid type
					book_type = payload["type"]

			# assign attributes
			book_data["title"] = title
			book_data["quantity"] = quantity
			book_data["type"] = book_type

			# success
			return True

	def search_book(self, search_params):
		# search_params: {query: str?, type: integer?, size: integer?, search_by_isbn: boolean?}
		# returns sorted array based on search_params (sorted based on relevance) of size n (defined in search_params.size or by default 10)
		# defaults search to by title of books
		interested = []; # build a list of interested search candidates to search

		# search parameters
		queryStr = search_params.get("query")
		typeFilter = search_params.get("type")
		searchISBN = search_params.get("search_by_isbn", False)

		ld_threshold = 100 # levenshtein threshold (i.e. any distance greater than this value is not a candidate of interest)
		search_target = self.sorted_isbn if searchISBN else self.sorted_title # this matters since we want items to appear in alphabetical order
		for isbn_code in search_target:
			# compare levenshtein distances with white spaces removed
			if (queryStr != None):
				# has query string (title to query)
				ld = UtilCLI.levenshtein_distance(isbn_code if searchISBN else self.data[isbn_code]["title"], queryStr)
				if (ld < ld_threshold):
					# interest candidate (title match)

					# filter out candidates
					if ((typeFilter != None and self.data[isbn_code]["type"] == typeFilter) or (typeFilter == None)):
						# passes filter OR no filter at all
						interested.append([isbn_code, ld])

		# sort interested candidates based on their relevance factor (levenshtein distance)
		UtilCLI.bubble_sort(interested, lambda a, b: 1 if a[1] > b[1] else (3 if a[1] == b[1] else 2))

		# returns (iterators not ideal here since it can not traverse backwards)
		page_container = []
		entries_per_page = search_params.get("size", 10)
		candidate_n = len(interested)
		for page_no in range(candidate_n //entries_per_page +1):
			page_container.append(interested[(page_no) *entries_per_page: min((page_no +1) *entries_per_page +1, candidate_n)])

		return page_container

class AuthManager:
	USER_ACCESS_LEVEL = ["User", "Librarian", "Administrator", "Root"]
	def __init__(self):
		# load up local environment variables in .env
		with open(path.join(__file__, "../.env"), "r") as f:
			for line in f:
				line = line.strip() # remove leading & trailing whitespaces
				if line and not (line.startswith("#")):
					key, value = line.split("=", 1) # split by "=" ONCE only
					os.environ[key] = value

		# attach database reader
		self.data = database_engine.created_readers["users"]

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
		if (username in self.data):
			al = self.data[username]["access_level"]
			if (verbose):
				return self.USER_ACCESS_LEVEL[al]
			else:
				return al
		else:
			return

	def authenticate_creds(self, username, password):
		# returns 1 upon successful authentication
		# returns 2 upon unsuccessful authentication (invalid username)
		# returns 3 upon unsuccessful authentication (invalid password)
		if not (username in self.data):
			return 2
		if len(password) == 0:
			return 3

		password_hash = self.hash(password)
		eq = password_hash == self.data[username]["password"]
		if (eq):
			return 1
		else: return 3

	def create_user(self, username, password, access_level):
		# creates a new user, returns boolean as success value
		if (username in self.data):
			# account with the same username exists
			return False

		self.data[username] = {
			"password": self.hash(password),
			"access_level": access_level,
			"loaning": [],
			"loaned_books": []
		}

		return True

	def change_password(self, username, old_password, password):
		if (self.hash(old_password) == self.data[username]["password"]):
			# matches password
			self.data[username]["password"] = self.hash(password)
			return True
		else:
			# not match
			return False

class Screen:
	def __init__(self, header):
		self.content = header # content will be built here

	def build(self, content):
		# append content to self.content
		self.content += str(content)

	def out(self, reuse=False):
		# clear screen first
		# reuse: boolean (if false, will throw away reference to self.content)
		UtilCLI.clear();
		print(self.content);

		if not reuse:
			# remove reference from self.content
			self.content = None # await GC to clean up object


class LibCLI:
	def __init__(self):
		# objects
		self.authManager = AuthManager()
		self.libraryManager = LibraryData() # initiated class

		# states
		self.active = True

		# session memory
		self.username = "" # to be set
		self.access_level = 0 # to be set
		self.access_level_verbose = "" # to be set
		self.session_start = time.perf_counter(); # seconds

		# user data
		self.overdue_loans = [] # stores isbn of books overdue

		# do some preprocessing on the book database (isbn.json)
		self.libraryManager.process_data();

	def create_new_screen(self):
		return Screen("{} | {}\n".format(self.username, self.access_level_verbose))

	def getBookTypeOptionsRepr(self):
		# returns a selection representation in the format of "1. book_type_1\n2. book_type_2\n3. book_type_3\n"
		# to accommodate a flexible book type listing
		# TO IMPROVE: cache computed string (minimal savings)
		representation = ""
		idx = 0
		for book_type in self.libraryManager.BOOK_TYPE_MAPPED:
			idx += 1
			representation += "{}. {}\n".format(idx, book_type)

		return representation

	def create_book_details_banner_diff(self, book_data_arr):
		# book_data_arr: book_data[] stores book_data in a list (book_data contains 'isbn' key)
		# unlike create_book_details_banner(), does not accept isbn (this method mainly for building visual difference diagrams)

		# build width array (max_width data)
		max_width_arr = []
		for book_data in book_data_arr:
			max_width = 0 # initialise
			for key in book_data.keys():
				r_width = len(key) + len(str(book_data[key]))
				if (r_width > max_width):
					max_width = r_width
			max_width_arr.append(max_width +2) # colon, space after colon

		# build line by line
		representation = ""
		gutter_seq = " " *8 # 4 space characters
		total_book = len(book_data_arr)
		for idx in range(total_book):
			suffix = gutter_seq if idx +1 < total_book else "\n"
			representation += "+-{}-+{}".format("-" *max_width_arr[idx], suffix)

		for idx in range(total_book):
			suffix = gutter_seq if idx +1 < total_book else "\n"
			representation += "| {:<{}} |{}".format("ISBN: {}".format(book_data_arr[idx]["isbn"]), max_width_arr[idx], suffix)

		for idx in range(total_book):
			suffix = "  {}>  ".format("-" *(len(gutter_seq) -5)) if idx +1 < total_book else "\n"
			representation += "| {:<{}} |{}".format("Title: {}".format(book_data_arr[idx]["title"]), max_width_arr[idx], suffix)

		for idx in range(total_book):
			suffix = gutter_seq if idx +1 < total_book else "\n"
			representation += "| {:<{}} |{}".format("Type: {}".format(book_data_arr[idx]["type"]), max_width_arr[idx], suffix)

		for idx in range(total_book):
			suffix = gutter_seq if idx +1 < total_book else "\n"
			representation += "| {:<{}} |{}".format("Quantity: {}".format(book_data_arr[idx]["quantity"]), max_width_arr[idx], suffix)

		for idx in range(total_book):
			suffix = gutter_seq if idx +1 < total_book else "\n"
			representation += "+-{}-+{}".format("-" *max_width_arr[idx], suffix)

		representation += "\n\n" # vertical padding
		return representation

	def create_book_details_banner(self, isbn):
		# creates a table view of book details
		# returns a string representation to be build into a screen object
		book_data = self.libraryManager.data.get(isbn)
		if (book_data == None):
			return ""

		max_width = len("ISBN") +len(isbn)
		for key in book_data.keys():
			r_width = len(key) + len(str(book_data[key])) # row width
			if (r_width) > max_width:
				max_width = r_width
		max_width += 2 # colon, space after colon

		representation = "+-{}-+\n".format("-" *max_width)
		representation += "| {:<{}} |\n".format("ISBN: {}".format(isbn), max_width)
		representation += "| {:<{}} |\n".format("Title: {}".format(book_data["title"]), max_width)
		representation += "| {:<{}} |\n".format("Type: {}".format(book_data["type"]), max_width)
		representation += "| {:<{}} |\n".format("Quantity: {}".format(book_data["quantity"]), max_width)
		representation += "+-{}-+\n\n\n".format("-" *max_width)
		return representation

	def set_user(self, username):
		self.username = username
		self.access_level = self.authManager.get_access_level(username)
		self.access_level_verbose = self.authManager.get_access_level(username, True)

		# greet user with new screen
		screen = self.create_new_screen()
		screen.build("\n\n\n\nWelcome to The Library\nWhere knowledge overflows.\n\nType 'help' for help message.")

		# check for loan book status
		user_data = database_engine.created_readers["users"][username]
		overdue_loans_n = 0
		now = time.time() # seconds (unix epoch) in UTC
		for loan_data in user_data["loaning"]:
			if (loan_data[1] +loan_data[2]) <= now:
				# overdued book
				overdue_loans_n += 1
				self.overdue_loans.append(loan_data[0])

		if (overdue_loans_n > 0):
			screen.build("You have \033[31m{}\033[0m loans overdue, please return them promptly by calling 'return'.\n".format(overdue_loans_n))
			loan_idx = 0
			for isbn_code in self.overdue_loans:
				loan_idx += 1
				screen.build(" {}. {}\n".format(loan_idx, self.libraryManager.data[isbn_code]["title"]))

		# vertical padding
		screen.build("\n")

		# out the screen
		screen.out();

	def logout_handler(self):
		# log out handler, performs log out tasks
		"""
		tasks to do
		1. write to database (push all database_readers)
		2. output goodbye message
		"""

		# push all saves
		database_engine.created_readers["isbn"].push()
		database_engine.created_readers["users"].push()

		# time out
		self.session_end = time.perf_counter()
		session_dur = self.session_end -self.session_start

		# logout screen
		logout_screen = self.create_new_screen()
		logout_screen.build("\n\nTransferring knowledge..\nCleaning up..\nLogging out..")
		logout_screen.build("\n\n\nLogged out.\nSession lasted: {}min{} {:.4f}s".format(int(session_dur //60), "s" if session_dur >= 120 else "", session_dur %60))

		# out screen
		logout_screen.out()

		exit(1) # exit program

	def login_handler(self):
		# login handler

		# clear screen
		UtilCLI.clear();

		# get a valid username
		username = ""
		for u_retries in range(3):
			username_inp = input("Username: ").lower() # case-insensitive usernames

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
				return self.login_handler();
			elif (code == 3):
				# invalid password

				if (p_retries == 2):
					# max retries
					print("Invalid password, maximum attempts reached, please attempt to log in again.")
					return False # return an exit code of False so main control flow knows login was unsuccessful
				else:
					print("Invalid password, please try again ({} attempts left).".format(3 -p_retries -1))

		return True # returns true so main control flow knows login was successful

	def create_user(self):
		if (self.access_level < 2):
			print("[ERROR]: Permissions denied.")
			return False

		# create user screen
		create_user_screen = self.create_new_screen()
		create_user_screen.build("\n\nCreate a new user.\n")

		# out screen
		create_user_screen.out()

		# user set up parameters
		username, password, al_val = "", "", 0

		# encapsulate in try block to capture keyboard interrupt
		try:
			# enter a valid username
			username_duplicate = True
			while username_duplicate:
				username = input("Username: ").strip()
				username_duplicate = username == "" or username in self.authManager.data # don't allow empty passwords

				if (username_duplicate):
					print("[WARN]: Username cannot be empty or username already exists, please try again.\n")

			# enter a valid password
			invalid_password = True
			while invalid_password:
				password = input("Password: ")
				invalid_password = password == ""

				if not invalid_password:
					# ask for a second confirmation
					password_confirmation = input("Re-enter password: ")
					invalid_password = password != password_confirmation

					if invalid_password:
						print("[WARN]: Please enter the same passwords.\n")
				else:
					# empty password
					print("[WARN]: Password cannot be empty\n")

			# get an access level
			invalid_al = True
			while invalid_al:
				al = input("Grant access level\n{}\n: ".format("\n".join(["{} - {}".format(idx, self.authManager.USER_ACCESS_LEVEL[idx]) for idx in range(len(self.authManager.USER_ACCESS_LEVEL))])))
				invalid_al = not al.isdigit()

				al_val = int(al) # typecast
				al_n = len(self.authManager.USER_ACCESS_LEVEL) # get length

				invalid_al = True # assume invalid first
				if (al_val < 0 or al_val >= al_n):
					# out of range
					print("[WARN]: Input out of range, please enter within 0-{} (inclusive).\n".format(al_n))
				elif (al_val >= al_n -1):
					# cannot grant root perms
					print("[WARN]: Cannot grant root level permissions.\n")
				else:
					# valid
					invalid_al = False

			success = self.authManager.create_user(username, password, al_val)
			if (success):
				print("\033[32m[SUCCESS]: User created successfully for {}.\033[0m".format(username))
			else:
				print("[UNSUCCESSFUL]: Failed to create user {}.".format(username))
		except KeyboardInterrupt:
			print("\n\n[ERROR]: Exited create user interface. (；′⌒`)")

	def change_password(self):
		# ask for current password, validate it
		try:
			retry = True
			curr_password = ""
			while retry:
				curr_password = input("Current password (plaintext, not hidden): ")
				status = self.authManager.authenticate_creds(self.username, curr_password)
				retry = status != 1

				if (status == 2):
					print("[WARN]: Unable to process your request, username not attached to a live database, please contact an administrator.")
					return False

			# enter a valid password
			invalid_password = True
			password = ""
			while invalid_password:
				password = input("Password: ")
				invalid_password = password == ""

				if not invalid_password:
					# ask for a second confirmation
					password_confirmation = input("Re-enter password: ")
					invalid_password = password != password_confirmation

					if invalid_password:
						print("[WARN]: Please enter the same passwords.\n")
				else:
					# empty password
					print("[WARN]: Password cannot be empty\n")

			success = self.authManager.change_password(self.username, curr_password, password)
			if (success):
				print("\033[32m[SUCCESS]: Password changed.\033[0m")
			else:
				print("[UNSUCCESSFUL]: Password failed to change for user {}, please contact an administrator.".format(self.username))

			return success
		except KeyboardInterrupt:
			# exit
			print("\n\n[ERROR]: Exited change password interface.")
			return False


		

	def delete_book_interface(self, isbn, args={}, flags=[]):
		# new screen
		del_screen = self.create_new_screen()
		del_screen.build("\n\nDeleting entry for [{}]:\n{}Processing entry..\n[Ctrl + C] to exit.\n".format(isbn, self.create_book_details_banner(isbn)))

		# out screen (out screen first to warn users about potential waiting time)
		del_screen.out()

		if not ("f" in flags):
			# show consequences (people loaning books etc)
			# global search (may take some time)
			red_flag = False # will be set to True if exists in loan entries
			for username in database_engine.created_readers["users"]:
				user_data = database_engine.created_readers["users"][username]
				for loan_entry in user_data["loaning"]:
					if (loan_entry[0] == isbn):
						red_flag = True
						break

				if not red_flag:
					for loan_entry in user_data["loaned_books"]:
						if (loan_entry[0] == isbn):
							red_flag = True
							break

				if red_flag:
					break

			if red_flag: print("\033[33m[WARN]: There are users with books loaned tied to the ISBN value, removing it will remove it from their loan entries and history.\033[0m")

		confirmation = input("Delete (y/n): ").lower()
		if (confirmation == "y"):
			success = self.libraryManager.delete_book(isbn)
			if (success):
				print("\033[32m[SUCCESS]: Book removed successfully.\033[0m\n\n")
			else:
				print("\033[31m[ERROR]: Book removed unsuccessfully, please contact an administrator.\033[0m\n\n")
		else:
			print("[UNSUCCESSFUL]: Book entry was not removed.\n\n")

	def update_book_interface(self, isbn):
		# new screen
		edit_screen = self.create_new_screen()
		edit_screen.build("\n\nModifying entry for [{}]:\n{}[Ctrl + C] to exit, 'help' for help.\n".format(isbn, self.create_book_details_banner(isbn)))

		# out screen
		edit_screen.out(reuse=True)

		# construct the change payload (to be sent to self.libraryManager.update_book())
		payload = {}

		# action list
		action_list = ["help", "title", "quantity", "type", "save"]

		# construct history to rebuild screen afterwards
		action_hist = [] # elements: [action_code, trigger, input, output_msg]

		supplying_changes = True
		while supplying_changes:
			# ask for input
			action = ""
			try:
				action = input("Action: ")
			except KeyboardInterrupt:
				# out home screen
				screen = self.create_new_screen();
				screen.build("\n\n\n\nExited book details update, no changes saved (´。＿。｀)\n\n")
				screen.out()

				# exit
				return

			mapped_action = UtilCLI.get_command(action, action_list)
			if mapped_action[0]:
				# switch statement :(
				input_value = "" # for history management
				output_msg = ""
				if mapped_action[1] == 0:
					# help statement
					output_msg = help_messages.update_book
					pass
				elif mapped_action[1] == 1:
					# change title
					title = input("New title: ")
					if (title == ""):
						# title cannot be empty
						output_msg = "[WARN]: Title cannot be empty"
					else:
						input_value = title
						output_msg = "[SUCCESS]: Title changed to '{}'.".format(title)
						payload["title"] = title
				elif mapped_action[1] == 2:
					# change quantity
					qty = input("Quantity: ")
					if not (qty.isdigit()):
						# input is not a zero/positive integer
						output_msg = "[WARN]: Quantity must be a valid positive (or zero) integer."
					else:
						input_value = qty
						output_msg = "[SUCCESS]: Quantity changed to {}.".format(qty)
						payload["quantity"] = int(qty)
				elif mapped_action[1] == 3:
					# change type (idx of 3)
					book_type = input("Type\n{}: ".format(self.getBookTypeOptionsRepr()))
					if not (book_type.isdigit()) or int(book_type) <= 0 or int(book_type) >= 4:
						# input is not an integer within the range 1 <= x <= 3
						output_msg = "[WARN]: Book type must be an integer within the range 1 and 3 (inclusive)."
					else:
						input_value = book_type
						output_msg = "[SUCCESS]: Book type changed to {}.".format(book_type)
						payload["type"] = int(book_type)
				elif mapped_action[1] == 4:
					# save changes

					# confirmation
					# view changes, construct the new book_data from payload
					payload["isbn"] = isbn # important when constructing diff diagrams
					storage = {
						# populate exisiting values here (for comparison to feed into .create_book_details_banner_diff())
						"isbn": isbn
					}
					for key in self.libraryManager.data[isbn].keys():
						if not (key in payload):
							# re-use current values
							payload[key] = self.libraryManager.data[isbn][key]

						# build storage (original data structure and values)
						storage[key] = self.libraryManager.data[isbn][key]

					# visual diff diagram
					confirmation_screen = self.create_new_screen();
					confirmation_screen.build("\n\nPlease confirm the changes modified.\n")
					confirmation_screen.build(self.create_book_details_banner_diff([storage, payload]))
					confirmation_screen.build("\n\n")

					# out screen
					confirmation_screen.out()

					# ask for confirmation
					confirmation_inpt = input("Confirm (y/n): ").lower()
					if confirmation_inpt == "y":
						# confirmed
						success = self.libraryManager.update_book(isbn, payload)
						if (success):
							print("\033[32m[SUCCESS]: Changes modified.\033[0m")
							supplying_changes = False # changes made
						else:
							# should not happen since inputs have been validated
							print("\033[31m[ERROR]: Failed to modify, please try again.[0m")
					else:
						# no confirmation, go back to continuing modifying
						# build history to screen (to be out again if needed)
						for hist_data in action_hist:
							edit_screen.build("Action: {}\n".format(hist_data[1]))
							follow_up_inpt = "{}"
							if (hist_data[0] == 0):
								# help, do nothing
								pass
							elif (hist_data[0] == 1):
								# change title
								follow_up_inpt = "New title: {}\n"
							elif (hist_data[0] == 2):
								# change quantity
								follow_up_inpt = "Quantity: {}\n"
							elif (hist_data[0] == 3):
								# change type
								follow_up_inpt = "Type\n{}: {{}}\n".format(self.getBookTypeOptionsRepr())
							edit_screen.build(follow_up_inpt.format(hist_data[2]))
							edit_screen.build("{}\n".format(hist_data[3]))

						edit_screen.out(reuse=True)

				# show output
				print(output_msg)

				# build history
				action_hist.append([mapped_action[1], action, input_value, output_msg])
			else:
				# failed to map input to a known command
				if (mapped_action[1]):
					# suggestion given
					print("[WARN]: No command found for '{}', did you mean '{}'.".format(action, mapped_action[1]))
				else:
					# no suggestion given
					print("[WARN]: No command found for '{}'.".format(action))

	def browse_interface(self, args={}, flags=[]):
		# browse through all the books

		# params
		page_size = args.get("n", 10)
		is_detailed = "d" in flags

		# parse params
		if (type(page_size) == str and (not page_size.isdigit() or page_size[0] == "0")):
			# page_size[0] is fine since .isdigit() will return False on empty strings
			print("[ERROR]: n field must be a positive non-zero integer")
			return False
		page_size = int(page_size)

		# target data
		data = []
		if "i" in flags:
			# browse through by isbn
			data = self.libraryManager.sorted_isbn
		else:
			# browse through by titles
			data = self.libraryManager.sorted_title
		data_n = len(data) # size of data
		page_total = math.ceil(data_n /page_size) # round up

		# error message, will be set at the end of the control loop
		error_msg = "\n"

		# page view
		page_idx = 1
		while True:
			# focus indices
			start = (page_idx -1) *page_size
			end = min(page_idx *page_size +1, data_n)

			# focus data
			focus = data[start: end]
			focus_n = end -start -1

			# new screen
			browse_screen = self.create_new_screen()
			browse_screen.build("\n{}\n\nBrowsing [{}-{} out of {} books]\n".format(error_msg, start +1, end -1, data_n)) # convert to one index base counting

			# build results
			for idx in range(page_size):
				if (idx < focus_n):
					# entry exists
					browse_screen.build("{:<4} [{}] {}\n".format(" {}.".format(idx +1), focus[idx], self.libraryManager.data[focus[idx]]["title"]))

					if is_detailed:
						# detailed view, show type and quantity
						# \t character has too wide of a space here
						browse_screen.build("    - Type: {} | Quantity: {}\n".format(self.libraryManager.data[focus[idx]]["type"], self.libraryManager.data[focus[idx]]["quantity"]))
				else:
					browse_screen.build("\n") # empty white space

			# out screen
			browse_screen.build("\n\n[Ctrl + C] to exit.")
			browse_screen.out()

			# formulate navigation guide
			page_inpt_prompt = ""
			if (page_idx > 1):
				# has back page
				if (page_idx < page_total):
					# has both navigs
					page_inpt_prompt = "[-1 for prev page; -2 for next page]"
				else:
					# has back page
					page_inpt_prompt = "[-1 for prev page]"
			elif (page_idx < page_total):
				# has next page
				page_inpt_prompt = "[-2 for next page]"

			# ask for navigation input
			selection = ""
			try:
				selection = input("Navigation {}: ".format(page_inpt_prompt))
			except KeyboardInterrupt:
				# exit, out home screen
				screen = self.create_new_screen();
				screen.build("\n\n\n\nExited browsing ╯︿╰\n\n")
				screen.out()

				return # exit

			if (selection == "-2"):
				# next page
				if (page_idx < page_total):
					# go next page
					error_msg = "\n" # reset error message
					page_idx += 1
				else:
					# cannot go next page
					error_msg = "[WARN]: No next page to proceed!\n"
			elif (selection == "-1"):
				# prev page
				if (page_idx > 1):
					# go prev page
					error_msg = "\n" # reset error message
					page_idx -= 1
				else:
					# cannot go prev page
					error_msg = "[WARN]: No previous page to proceed!\n"



	def search_interface(self, args={}, flags=[]):
		# get user input search query
		# returns a valid isbn after searching (returns None on exit)

		# -d flag for detailed view
		is_detailed = "d" in flags # detailed view
		search_by_isbn = "p" in flags # precision search

		# search target (representation)
		search_field_target = "ISBN" if search_by_isbn else "title"

		# show 10 entries of search results
		entries_limit = args.get("entries_limit", 10) # default value of 10

		# reserved vertical screen space for search results
		# initial whitespace value
		search_results_repr = "\n" *(entries_limit *(2 if is_detailed else 1) +1) # +1 for "searched for" header

		# control loop
		while True:
			# display result, new screen
			screen = self.create_new_screen()
			screen.build("\n\n\n\n{}".format(search_results_repr))
			screen.build("\n\n")

			# out screen
			screen.out()

			# get search query
			search_query = ""
			try:
				search_query = input("[Ctrl + C] to exit.\nSearch ({}): ".format(search_field_target))
			except KeyboardInterrupt:
				# exit
				# out home screen
				screen = self.create_new_screen();
				screen.build("\n\n\n\nExited search （；´д｀）ゞ\n\n")
				screen.out()

				return # exit

			# get search results
			search_results_pages = self.libraryManager.search_book({"query": search_query, "size": entries_limit, "search_by_isbn": search_by_isbn})

			# pageinated view
			page_view = True # status
			current_page_idx = 1;
			page_n = len(search_results_pages) # total pages
			prev_error = "\n" # placeholder for now
			while page_view:
				search_results = search_results_pages[current_page_idx -1]

				# build header
				search_results_repr = "Searching for '\033[35m{}\033[0m' ({}) [page {} - {}; out of {} entries]\n".format(search_query, search_field_target, current_page_idx, page_n, self.libraryManager.total_entries)

				# build search results (in row view)
				search_results_n = len(search_results)
				for idx in range(entries_limit):
					# search_entry: str[]; [0] = isbn, [1] = relevance factor (levenshtein distance)
					if (idx < search_results_n):
						search_entry = search_results[idx]
						if (search_entry[1] == 0):
							# exact match
							search_results_repr += "{:<4} [\033[35m{}\033[0m] {}\n".format(" {}.".format(idx +1), search_entry[0], self.libraryManager.data[search_entry[0]]["title"])
						else:
							search_results_repr += "{:<4} [{}] {}\n".format(" {}.".format(idx +1), search_entry[0], self.libraryManager.data[search_entry[0]]["title"])

						if is_detailed:
							# detailed view, show type and quantity
							# \t character has too wide of a space here
							search_results_repr += "    - Type: {} | Quantity: {}\n".format(self.libraryManager.data[search_entry[0]]["type"], self.libraryManager.data[search_entry[0]]["quantity"])
					else:
						search_results_repr += "\n" # empty white space

				# new screen
				screen = self.create_new_screen()
				screen.build("\n{}\n\n{}".format(prev_error, search_results_repr))
				screen.build("\n\n")

				# out screen
				screen.out()

				# build input prompt (with navigation aid)
				page_inpt_prompt = ""
				if (current_page_idx > 1 and current_page_idx < page_n):
					page_inpt_prompt = "Enter an entry (index) [-1 for prev page; -2 for next page; Ctrl + C to exit]: "
				elif (current_page_idx > 1):
					# can only go previous page (i.e. page_n = 2)
					page_inpt_prompt = "Enter an entry (index) [-1 for prev page; Ctrl + C to exit]: "
				elif (current_page_idx < page_n):
					# can go next page
					page_inpt_prompt = "Enter an entry (index) [-2 for next page; Ctrl + C to exit]: "
				else:
					# no page navigation
					page_inpt_prompt = "Enter an entry (index) [Ctrl + C to exit]: "

				try:
					selection = input(page_inpt_prompt).strip()

					if (selection == "-2"):
						# next page
						if (current_page_idx < page_n):
							# go next page
							prev_error = "\n" # reset error message
							current_page_idx += 1
						else:
							# cannot go next page
							prev_error = "[WARN]: No next page to proceed!\n"
					elif (selection == "-1"):
						# prev page
						if (current_page_idx > 1):
							# go prev page
							prev_error = "\n" # reset error message
							current_page_idx -= 1
						else:
							# cannot go prev page
							prev_error = "[WARN]: No previous page to proceed!\n"
					elif (selection.isdigit()):
						# can only be a positive integer
						selection_idx = int(selection) -1
						if (selection_idx < 0 or selection_idx >= entries_limit):
							# out of range error
							prev_error = "[WARN]: Selection out of range, please select between 1-{} (inclusive).\n".format(entries_limit)
						else:
							# valid selection, return isbn
							return search_results[selection_idx][0] # return the isbn
					else:
						# invalid selection
						prev_error = "[WARN]: Malformed input received, please input a valid integer between 1-{} (inclusive).\n".format(entries_limit)
				except KeyboardInterrupt:
					# exit, to ask for new query again
					break

	def loan_return_interface(self):
		# return loaned book
		user_data = database_engine.created_readers["users"][self.username]
		loans_n = len(user_data["loaning"])			

		timestamp_now = time.time() # seconds, unix epoch UTC

		# return screen
		ret_screen = self.create_new_screen()
		ret_screen.build("\n\nReturn books interface.\n\nYou currently have {} books in loan.\n".format(loans_n))

		if (loans_n <= 0):
			# no books to return
			ret_screen.build("\n\nNothing to return :).\n\n\n")
			ret_screen.out()
			return

		# show list of books to return
		loan_idx = 0
		for loan_entry in user_data["loaning"]:
			# mark over due with red
			# mark near due date (<= 1 day left) with orange
			loan_idx += 1

			# calculate loan return date
			loan_return_timestamp = loan_entry[1] +loan_entry[2]
			loan_return_timestamp_repr = time.strftime("%d %b %Y %H:%M", time.localtime(loan_return_timestamp))

			if (loan_return_timestamp -timestamp_now) <= 0:
				# overdue
				ret_screen.build(" {}. \033[31m{} [{}] '{}'\033[0m\n".format(loan_idx, loan_return_timestamp_repr, loan_entry[0], self.libraryManager.data[loan_entry[0]]["title"]))
			elif (loan_return_timestamp -timestamp_now) <= 86400:
				ret_screen.build(" {}. \033[33m{} [{}] '{}'\033[0m\n".format(loan_idx, loan_return_timestamp_repr, loan_entry[0], self.libraryManager.data[loan_entry[0]]["title"]))
			else:
				ret_screen.build(" {}. {} [{}] '{}'\n".format(loan_idx, loan_return_timestamp_repr, loan_entry[0], self.libraryManager.data[loan_entry[0]]["title"]))

		# out screen
		ret_screen.build("\n[Ctrl + C to exit]\n")
		ret_screen.out()

		# get selection
		while True:
			selection = ""
			try:
				selection = input("Selection (index): ")
			except KeyboardInterrupt:
				# exit, out home screen
				screen = self.create_new_screen();
				screen.build("\n\n\n\nExited return interface ┌( ´_ゝ` )┐\n\n")
				screen.out()

				return # exit

			if (selection.isdigit()):
				selection_value = int(selection)
				if (selection_value <= 0 or selection_value >= loans_n +1):
					# equality comparisons better than selection_value > loans_n
					print("[ERROR]: Please input a valid selection between 1-{} (inclusive).".format(loans_n))
				else:
					# valid selection, process loan
					selection_value -= 1 # revert to zero-based indexing

					# move data entry to user_data["loaned_books"]
					loan_entry = user_data["loaning"].pop(selection_value)
					user_data["loaned_books"].append(loan_entry +[time.time()]) # append an extra element (return timestamp)

					# update database
					self.libraryManager.data[loan_entry[0]]["quantity"] += 1

					# if overdue, remove it
					for overdue_idx in len(self.overdue_loans):
						if (self.overdue_loans[overdue_idx] == loan_entry[0]):
							self.overdue_loans.pop(overdue_idx)

					# output message
					print("[SUCCESS]: Returned book '{}'".format(self.libraryManager.data[loan_entry[0]]["title"]))

					time.sleep(2) # give 2 seconds wait
					return self.loan_return_interface() # check for loans again
			else:
				# invalid input
				print("")


		# move data entry to user_data["loaned_books"]
		loan_entry = user_data["loaning"].pop(loan_entry_idx)
		user_data["loaned_books"].append(loan_entry +[return_timestamp])

	def loan_interface(self, isbn):
		# loans book

		# loaning screen
		loan_screen = self.create_new_screen()
		loan_screen.build("\n\nLoaning [{}] '{}' ♪(^∇^*)\n\n".format(isbn, self.libraryManager.data[isbn]["title"]))

		# dont grant loan if there are overdue books
		user_data = database_engine.created_readers["users"][self.username]
		if (len(self.overdue_loans) > 0):
			# cannot loan
			loan_screen.build("[ERROR]: Unable to loan books, please return your overdue loans by calling 'return'.")

			# out screen
			loan_screen.out()
			return

		# maximum loan a user can have is 5 books
		if (len(user_data["loaning"]) >= 5):
			# cannot loan
			loan_screen.build("[ERROR]: Unable to loan books as you have reached the maximum capacity of 5 loans, please return some of the loaned books by calling 'return'.")

			# out screen
			loan_screen.out()
			return

		# check if there are any existing entries in user's currently loaned book
		for loan_data in user_data["loaning"]:
			if (loan_data[0] == isbn):
				# cannot loan
				loan_screen.build("[ERROR]: Unable to loan books as you have already loaned this book.")

				# out screen
				loan_screen.out()
				return

		# check if there are copies left in the library
		book_data = self.libraryManager.data[isbn]
		if (book_data["quantity"] <= 0):
			# no quantities left, cannot loan
			loan_screen.build("[ERROR]: Unable to loan books as the library currently have no more copies available, sorry!")

			# out screen
			loan_screen.out();
			return
		else:
			# decrement stock count
			book_data["quantity"] -= 1

		loan_dur_day = 2 # loan it for exactly 48 hours
		loan_dur_sec = loan_dur_day *86400

		loan_timestamp = time.time() # seconds, unix epoch (UTC)
		loan_return_timestamp = time.time() +loan_dur_sec # seconds
		loan_return_local_timestamp = time.localtime(loan_return_timestamp)

		# loan logic
		user_data["loaning"].append([isbn, loan_timestamp, loan_dur_sec])

		# build screen
		loan_screen.build("\n\n\nLoaned '{}'.\nDuration: {}day(s)\n".format(book_data["title"], loan_dur_day))
		loan_screen.build("Return on: {}\n\n".format(time.strftime("%d %b %Y %H:%M", loan_return_local_timestamp)))

		# out screen
		loan_screen.out();

	def kernel(self, command, args={}, flags=[]):
		# executes the actual command
		if (command == "help"):
			output_help_msg = help_messages.user_home
			if (self.access_level >= 1):
				output_help_msg += help_messages.librarian_home
			if (self.access_level >= 2):
				output_help_msg += help_messages.administrator_home
			if (self.access_level >= 3):
				output_help_msg += help_messages.root_home

			# output
			print(output_help_msg)

			return

		if (self.access_level >= 0):
			# open up command space for regular users
			if (command == "loan"):
				isbn = self.search_interface(args, flags)
				if isbn == None:
					# exit (home screen already out)
					print("Update failed [no search performed].")
					return

				return self.loan_interface(isbn);
			elif (command == "return"):
				return self.loan_return_interface()
			elif (command == "browse"):
				return self.browse_interface(args, flags)
			elif (command == "search"):
				isbn = self.search_interface(args, flags)
				return isbn
			elif (command == "cpw"):
				return self.change_password()
			elif (command == "logout" or command == "exit"):
				self.logout_handler(); # will call exit()
		if (self.access_level >= 1):
			# librarians, administrators and root users
			if (command == "update"):
				isbn = self.search_interface(args, flags)
				if isbn == None:
					# exit (home screen already out)
					print("Update failed [no search performed].")
					return

				return self.update_book_interface(isbn)
			elif (command == "add"):
				book_data = {
					"isbn": args.get("isbn"),
					"title": args.get("title"),
					"quantity": args.get("quantity"),
					"type": args.get("type")
				}

				try:
					# ask for all the book details in sequence, use data provided in args as default
					print("Data required for book entry.")

					# isbn code
					if (book_data["isbn"] != None and LibraryData.validate_isbn(book_data["isbn"]) and not self.libraryManager.duplicate_isbn(book_data["isbn"])):
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
							print("[WARN]: ISBN code may be a duplicate or may have been provided in the wrong format, please ensure the checkdigit is correct.")

						isbn_inpt = "";
						while True:
							# input required
							isbn_inpt = input("ISBN (-1 to exit): ")
							if (isbn_inpt == "-1"):
								break
							elif not LibraryData.validate_isbn(isbn_inpt):
								print("[WARN]: {} is not a valid isbn, please ensure the checkdigit is correct.".format(isbn_inpt))
							elif self.libraryManager.duplicate_isbn(isbn_inpt):
								print("[WARN]: {} entry already exists with book title: '{}', please enter the correct ISBN.".format(isbn_inpt, self.libraryManager.data[isbn_inpt]["title"]))
							else:
								break # valid isbn


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
						while True:
							# input required
							title_inpt = input("Title (-1 to exit): ")
							if (title_inpt == "-1"):
								break
							elif title_inpt == "":
								print("[WARN]: Title input cannot be empty, please enter at least one character.")
							else:
								break # valid title

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
							print("[WARN]: Quantity provided in wrong format, please enter a positive non-zero integer without zero padding.")

						qty_inpt = "";
						while True:
							# input required
							qty_inpt = input("Quantity (-1 to exit): ")
							if (qty_inpt == "-1"):
								break
							elif (not qty_inpt.isdigit() or qty_inpt[0] == "0"):
								print("[WARN]: Please enter a valid positive non-zero integer without any zero-padding.")
							else:
								break # valid qty input

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
						while True:
							# input required
							type_inpt = input("Type\n\t1. Hard cover\n\t2. Paper back\n\t3. EBook\n(-1 to exit): ")
							if (type_inpt == "-1"):
								break
							elif not type_inpt.isdigit() or not(1 <= int(type_inpt) <= 3):
								print("[WARN]: Please enter within the valid range 1-3 (inclusive).")
							else:
								break # valid type selection

						if (type_inpt == "-1"):
							# cancel command
							return
						else:
							# validated type input
							book_data["type"] = int(type_inpt) # typecast it to an integer first
				except KeyboardInterrupt:
					# exit
					print()
					return

				success = self.libraryManager.add_book(book_data)

				# change book_data["type"] to enum representative
				for enum_repr in LibraryData.BOOK_TYPE:
					if (book_data["type"] == LibraryData.BOOK_TYPE[enum_repr]):
						book_data["type"] = enum_repr
						break

				# out new screen
				screen = self.create_new_screen();
				screen.build("\n\n\n\nUpdate book success!\nEntry details:\n")

				max_width = 0
				for key in book_data:
					r_width = len(key) + len(str(book_data[key])) # row width
					if (r_width) > max_width:
						max_width = r_width
				max_width += 2 # colon, space after colon

				screen.build("+-{}-+\n".format("-" *max_width))
				screen.build("| {:<{}} |\n".format("ISBN: {}".format(book_data["isbn"]), max_width))
				screen.build("| {:<{}} |\n".format("Title: {}".format(book_data["title"]), max_width))
				screen.build("| {:<{}} |\n".format("Type: {}".format(book_data["type"]), max_width))
				screen.build("| {:<{}} |\n".format("Quantity: {}".format(book_data["quantity"]), max_width))
				screen.build("+-{}-+\n\n\n".format("-" *max_width))
				screen.out();

		if (self.access_level >= 2):
			# administrators, root users
			if (command == "create"):
				return self.create_user()

		if (self.access_level >= 3):
			# root users ONLY (highest)
			if (command == "delete"):
				isbn = self.search_interface(args, flags)
				if isbn == None:
					# exit (home screen already out)
					print("Delete failed [no search performed].")
					return

				return self.delete_book_interface(isbn, args, flags)



	def interface(self):
		# responsible for retrieving ONE single command
		try:
			inpt = input("System: ")
		except KeyboardInterrupt:
			# exit
			self.logout_handler()

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