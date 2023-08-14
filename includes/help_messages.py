# Author: Chong Cheng Hock
# Admin No / Grp: 230643M / AA2301
user_home = """
help   | displays this message :)

loan   | interface to loan book via search interface
\t [-d] detailed view on search interface
\t [-p] precision search (search interface will use isbn to search)

return | interface to return books

browse | browse books in the library in alphabetically order (titles)
\t [-i] browse by sorted ISBN numbers
\t [-d] detailed view on browsing interface
\t [n=10] page size (default 10 items per page)

search | interface to search for books
\t [-d] detailed view on search interface
\t [-p] precision search (search interface will use isbn to search)

cpw    | interface to change password

logout | logouts of the library management system
\t [@exit] alias for this command
"""

librarian_home = """
update | interface to update book details
\t [-d] detailed view on search interface
\t [-p] precision search (search interface will use isbn to search)

add    | interface to add a new book
\t [isbn] supply isbn value (no default value)
\t [title] supply title value (no default value)
\t [quantity] supply quantity value (no default value)
\t [type] supply book type value (no default value)
"""
administrator_home = """
create | interface to create a new user
"""

root_home = """
delete | interface to delete a book
\t [-d] detailed view on search interface
\t [-p] precision search (search interface will use isbn to search)
\t [-f] forces delete without performing checks on whether users have loaned it or are loaning it (increased speed)
"""

update_book = "{:<9} | changes title of the book\n{:<9} | changes quantity of the book\n{:<9} | changes type of the book\n{:<9} | save changes, will prompt for confirmation\n".format("title", "quantity", "type", "save")