import time
import random
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

		for isbn in self.data:
			alpha_data.append([self.data[isbn]["title"], isbn])
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
		return True

	def search_book(self, search_params):
		# search_params: {query: str?, type: integer?, size: integer?}
		# returns sorted array based on search_params (sorted based on relevance) of size n (defined in search_params.size or by default 10)
		# also yields the remaining pages left to go
		interested = []; # build a list of interested search candidates to search

		# search parameters
		queryStr = search_params.get("query")
		typeFilter = search_params.get("type")

		ld_threshold = 100 # levenshtein threshold (i.e. any distance greater than this value is not a candidate of interest)
		for isbn_code in self.sorted_title:
			# compare levenshtein distances with white spaces removed
			if (queryStr != None):
				# has query string (title to query)
				ld = UtilCLI.levenshtein_distance(self.data[isbn_code]["title"], queryStr)
				if (ld < ld_threshold):
					# interest candidate (title match)

					# filter out candidates
					if ((typeFilter != None and self.data[isbn_code]["type"] == typeFilter) or (typeFilter == None)):
						# passes filter OR no filter at all
						interested.append([isbn_code, ld])

		# sort interested candidates based on their relevance factor (levenshtein distance)
		UtilCLI.bubble_sort(interested, lambda a, b: 1 if a[1] > b[1] else (3 if a[1] == b[1] else 2))

		print("SORTED", interested)

		# returns (iterators not ideal here since it can not traverse backwards)
		page_container = []
		entries_per_page = search_params.get("size", 10)
		candidate_n = len(interested)
		for page_no in range(candidate_n //entries_per_page +1):
			page_container.append(interested[(page_no) *entries_per_page: min((page_no +1) *entries_per_page +1, candidate_n)])

		return page_container

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
		self.libraryManager = LibraryData() # initiated class

		# states
		self.active = True

		# session memory
		self.username = ""
		self.session_start = time.perf_counter();

		# do some preprocessing on the book database (isbn.json)
		self.libraryManager.process_data();

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

	def search_interface(self):
		# get user input search query
		# returns a valid isbn after searching

		# show 10 entries of search results
		entries_limit = 10

		# reserved vertical screen space for search results
		# initial whitespace value
		search_results_repr = "\n" *(entries_limit +1) # +1 for "searched for" header

		# control loop
		searching = True # state
		while searching:
			# display result, new screen
			screen = self.create_new_screen()
			screen.build("\n\n\n{}".format(search_results_repr))
			screen.build("\n\n")

			# out screen
			screen.out()

			# get search query
			search_query = input("Search (title): ")

			# get search results
			search_results_pages = self.libraryManager.search_book({"query": search_query, "size": entries_limit})

			# pageinated view
			page_view = True # status
			current_page_idx = 1;
			page_n = len(search_results_pages) # total pages
			prev_error = "\n" # placeholder for now
			while page_view:
				search_results = search_results_pages[current_page_idx -1]

				# build header
				search_results_repr = "Searching for '{}' [page {} - {}]\n".format(search_query, current_page_idx, page_n)

				# build search results (in row view)
				search_results_n = len(search_results)
				for idx in range(entries_limit):
					# search_entry: str[]; [0] = isbn, [1] = relevance factor (levenshtein distance)
					if (idx < search_results_n):
						search_entry = search_results[idx]
						search_results_repr += " {}. [{}] {}\n".format(idx +1, search_entry[0], self.libraryManager.data[search_entry[0]]["title"])
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
					page_inpt_prompt = "Enter an entry (index) [-2 for prev page; -1 for next page; 0 to exit]: "
				elif (current_page_idx > 1):
					# can only go previous page (i.e. page_n = 2)
					page_inpt_prompt = "Enter an entry (index) [-2 for prev page; 0 to exit]: "
				elif (current_page_idx < page_n):
					# can go next page
					page_inpt_prompt = "Enter an entry (index) [-1 for next page; 0 to exit]: "
				else:
					# no page navigation
					page_inpt_prompt = "Enter an entry (index) [0 to exit]: "

				selection = input(page_inpt_prompt).strip()
				if (selection == "0"):
					# exit
					break
				elif (selection == "-1"):
					# next page
					if (current_page_idx < page_n):
						# go next page
						prev_error = "" # reset error message
						current_page_idx += 1
					else:
						# cannot go next page
						prev_error = "[WARN]: No next page to proceed!"
				elif (selection == "-2"):
					# prev page
					if (current_page_idx > 1):
						# go prev page
						prev_error = "" # reset error message
						current_page_idx -= 1
					else:
						# cannot go prev page
						prev_error = "[WARN]: No previous page to proceed!"
				elif (selection.isdigit()):
					# can only be a positive integer
					selection_idx = int(selection) -1
					if (selection_idx >= entries_limit):
						# out of range error
						prev_error = "[WARN]: Selection out of range, please select between 1-{} (inclusive).".format(entries_limit)
					else:
						# valid selection, return isbn
						return search_results[selection_idx][0] # return the isbn
				else:
					# invalid selection
					prev_error = "[WARN]: Malformed input received, please input a valid integer between 1-{} (inclusive).".format(entries_limit)





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
		elif (command == "search"):
			isbn = self.search_interface()
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
				while True:
					# input required
					isbn_inpt = input("ISBN (-1 to exit): ")
					if (isbn_inpt == "-1"):
						break
					elif not LibraryData.validate_isbn(isbn_inpt):
						print("[WARN]: {} is not a valid isbn, please conform to the xxx-yyyyyyyyyyyyy (3x-13y) format.".format(isbn_inpt))
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

			print(book_data)
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