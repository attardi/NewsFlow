#!/usr/bin/python
#----------------------------------------------------------------------
#       Copyright (c) 2010  Giuseppe Attardi (attardi@di.unipi.it).
#----------------------------------------------------------------------

"""Feed Fetcher:
  Fetches RSS feeds from given set of URLs.

Usage:
  fetcher.py [options] file

Options:
  -d, --db              database file
  -h, --help            display this help and exit
"""

import sys
import getopt
import time
import feedparser
import re
from couchdbkit import Server, ResourceConflict, BulkSaveError

store = Server('http://attardi:beppe@attardi.cloudant.com')['semawiki']

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

    count = 0
    for url in list:
        if url[0] == '#':       # skip comments
            continue
        d = feedparser.parse(url)
        feedTitle = d.feed.get('title', u'')
        print feedTitle
        feedDescription = d.feed.get('description', u'')
        feedLink = d.feed.get('link', u'')
        #print 'Storing channel...'
        try:
            ch = store.save_doc({
                'type': 'channel',
                'title': feedTitle,
                '_id': feedLink,
                'description': feedDescription
            })
        except (ResourceConflict, PreconditionFailed):
            pass
        #print 'Storing channel done.'
        # FIXME: should be
        #        ch = Channel(feedLink, feedTitle, feedDescription)
        docs = []
        for e in d.entries:
            count += 1
            description = e.get('description', u'')
            if 'date_parsed' in e:
                t = int(time.mktime(e.date_parsed))
            else:
                t = time.time()
            docs.append({
                '_id': e.id,
                'type': 'item',
                'channel': feedLink,
                'title': e.get('title'),
                'link': e.get('link'),
                'description': description,
                'time': t,
                'enclosure': e.get('enclosures', [''])[0],
                'category': e.get('category'),
                'author': getAuthor(e, description)
            })
        #print 'Storing items...'
        try:
            store.bulk_save(docs)
        except BulkSaveError, e:
            print e
        #print 'Storing item done.'
>>>>>>> Switched store to CouchDB/Cloudant.
    print "Collected", count, "articles."

if __name__ == '__main__':
    main()


