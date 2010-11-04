#!/usr/bin/python
#----------------------------------------------------------------------
#	Copyright (c) 2010  Giuseppe Attardi (attardi@di.unipi.it).
#----------------------------------------------------------------------

"""Feed Fetcher:
  Fetches RSS feeds from given set of URLs.

Usage:
  fetcher.py [options] file

Options:
  -d, --db		database file
  -h, --help		display this help and exit
"""

import sys
import getopt
import time
import feedparser
import re
from store import *

def show_help():
    print >> sys.stderr, __doc__
    sys.exit(1)

def capitalize(x):
    if len(x) > 2 and x[1] == "'":
        return x[0:2] + x[2:].capitalize()
    else:
        return x.capitalize()

def getAuthor(e, description):
    "heuristic to extract real author"
    author = e.get('author', u'')
    if author.startswith('repubblicawww@repubblica.it'):
        m = re.compile('<br />di (.+?)<br').search(description)
        if m:
            author = m.group(1)
            author = ' '.join([capitalize(x) for x in author.split()])
    return author

def main():

    try:
        opts, args = getopt.gnu_getopt(sys.argv[1:], 'd:h', ['db', 'help'])
    except getopt.GetoptError:
        show_help()
    
    db = 'newsflow'
    for opt, arg in opts:
        if opt in ('-h', '--help'):
            show_help()
        elif opt in ('-d', '--db'):
            db = arg

    if len(args) != 1:
        show_help()

    try:
        list = open(args[0])
    except IOError:
        print "Can't open file", args[0]
        sys.exit(2)

    store = StoreCreate(db)

    count = 0
    for url in list:
        if url[0] == '#':       # skip comments
            continue
        d = feedparser.parse(url)
        feedTitle = d.feed.get('title', u'')
        print feedTitle
        feedDescription = d.feed.get('description', u'')
        feedLink = d.feed.get('link', u'')
        ch = Channel(feedTitle, feedLink, feedDescription)
        # FIXME: should be
#        ch = Channel(feedLink, feedTitle, feedDescription)
        for e in d.entries:
            if not 'id' in e:
                if not e.link:
                    continue
                e.id = e.link
            if store.get(Item, e.id):
                continue
            count += 1
            title = e.get('title', u'')
            link = e.get('link', u'')
            description = e.get('description', u'')
            if 'date_parsed' in e:
                t = int(time.mktime(e.date_parsed))
            else:
                t = time.time()
            enclosure = u''
            if 'enclosures' in e:
                enclosure = unicode(e.enclosures[0])
            category = e.get('category', u'')
            author = getAuthor(e, description)
            item = Item(ch, e.id, title, link, description, t,
                        enclosure, category, author)
            store.add(item)
    store.commit()
    print "Collected", count, "articles."

if __name__ == '__main__':
    main()
