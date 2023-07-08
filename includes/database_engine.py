class DatabaseEngine:
	def __init__(self):
		# scheduler loop, to trigger attached readers every minute (depending on rate)
		self.running = False # running state
		self.update_rate = 30 # pushes updates every 30 seconds

		# created readers go here
		self.created_readers = {}

		# internal clock (seconds)
		self._lastupdate = -1
	
	def create_reader(filename):
		# creates a new reader and queues it in the scheduler for constant updates (writes)
		# returns a reader_uid which is a string to uniquely identify the reader
		new_reader = DatabaseReader(filename)

		self.created_readers[new_reader.hash] = new_reader

		return new_reader

	def del_reader(reader_uid):
		# reader_uid: string to uniquely identify the reader object
		# to delete the created reader instance
		if (self.created_readers.get(reader_uid)):
			del created_readers[reader_uid] # remove entry for existing key
	
	def run(self):
		if self.running:
			return # already running
		else:
			self.running = True


		self._lastupdate = time.process_time() # cpu clock time
		while self.running:
			# single thread so no de-sync worries :)
			if (time.process_time() - self._lastupdate > self._lastupdate):
				for reader in self.created_readers.values():
					reader.push() # call .push() method on readers
				
				self._lastupdate = time.process_time(); # update timer
			time.sleep() # called on every few cycles if possible

class DatabaseReader:
	# reader for database files (instances of the big engine)
	def __init__(self, filename):
		self.filename = filename
        self.filepath = path.join(__file__, "/database", filename) # build filepath once
		self.content = []

        # load content
		with open(self.filepath, "r") as f:
			self.content = json.load(f)
		
        # use self.filename as hash without the .json extension
        self.hash = "".join(self.filename.split(".")[:-1])
		
        return self.content
	
	def push(self):
		# save to file
		with open(self.filepath, "w") as f:
            f.write(json.dumps(self.content))

database_engine = DatabaseEngine();