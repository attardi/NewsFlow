from storm.locals import *

class Channel(object):
    "Feed channel"
    __storm_table__ = "Channel"
    id = Int(primary=True)
    title = Unicode()
    link = Unicode()
    description = Unicode()
    # lang
    # copyright
    # date
    # ttl
    # image

    def __init__(self, link, title, description):
        self.title = title
        self.link = link
        self.description = description

class Item(object):
    "Feed item"
    __storm_table__ = "Item"
    guid = Unicode(primary=True)
    title = Unicode()
    link = Unicode()
    description = Unicode()
    date = Int()
    enclosure = Unicode()
    category = Unicode()
    author = Unicode()
    channelId = Int()
    channel = Reference(channelId, Channel.id)

    def __init__(self, channel, guid, title, link, description, date,
                 enclosure, category, author):
        self.channel = channel
        self.guid = guid
        self.title = title
        self.link = link
        self.description = description
        self.date = date
        self.enclosure = enclosure
        self.category = category
        self.author = author

    def __str__(self):
        return '<Item><g>%s</g>\n  <t>%s</t>\n  <l>%s</l>\n  <d>%s</>\n  <c>%s</c>\n  <a>%s</a>\n</Item>' % (self.guid, self.title, self.link, self.description, self.category, self.author)

def StoreCreate(file):
    db = create_database("sqlite:"+file)
#    db = create_database("mysql://root:posso@localhost/newsflow")
    store = Store(db)
    store.execute("""CREATE TABLE IF NOT EXISTS Channel(
                  id INTEGER PRIMARY KEY,
                  link VARCHAR UNIQUE ON CONFLICT REPLACE,
		  title VARCHAR,
		  description VARCHAR
		  )""")
    store.execute("""CREATE TABLE IF NOT EXISTS Item(
                   guid VARCHAR PRIMARY KEY,
 		   title VARCHAR,
		   link VARCHAR,
		   description VARCHAR,
		   date INTEGER,
		   enclosure VARCHAR,
		   category VARCHAR,
		   author VARCHAR,
		   channelId INTEGER
		   )""")
    store.execute("""CREATE INDEX IF NOT EXISTS date_idx ON Item(date)""")
    return store
