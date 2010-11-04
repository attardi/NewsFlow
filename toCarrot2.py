#!/usr/bin/python
#----------------------------------------------------------------------
#	Copyright (c) 2010  Giuseppe Attardi (attardi@di.unipi.it).
#----------------------------------------------------------------------

"""Dump DB from store to Carrot2 format.

Usage:
  toCarrot2.py [options] outputFile

Options:
  -c category	select articles from given category
  -d days	go back number of days [default 1]
  -h, --help	display this help and exit
"""
import sys
import getopt
import codecs
import time
from BeautifulSoup import BeautifulSoup
import re
import feedparser
from store import *

def show_help():
    print >> sys.stderr, __doc__
    sys.exit(1)

cleanRE = re.compile(r'<[^<]*?/?>|\([0-9:/ ]+\)')
ampRE = re.compile(r'&([^#])')
def cleanup(s):
    p = BeautifulSoup(s)
    for rel in p.findAll('div', 'mf-related'): # Repubblica: Articoli correlati
        rel.extract()
    # remove all tags
    r = cleanRE.sub(' ', str(p))
    return ampRE.sub(r'&amp;\1', r).replace('&amp;amp;', '&amp;')

secPerDay = 24 * 60 * 60

def CatMatch(pat, cat):
    return pat and pat.search(cat)

def main():

    try:
        opts, args = getopt.gnu_getopt(sys.argv[1:], 'c:d:h', ['help'])
    except getopt.GetoptError:
        show_help()

    cat = None
    days = 1
    for opt, arg in opts:
        if opt in ('-h', '--help'):
            show_help()
        elif opt in ('-c'):
            cat = re.compile(arg, re.IGNORECASE)
        elif opt in ('-d'):
            days = int(arg)

    if len(args) != 1:
        show_help()

    output = codecs.open(args[0], 'wb', 'utf-8')

    store = StoreCreate()

    start = int(time.time()) - days * secPerDay
    print >> output, '<?xml version="1.0" encoding="UTF-8"?>'
    print >> output, '<searchresult>'
    for d in store.find(Item, Item.date > start):
        if not CatMatch(cat, d.category): # skip those not in requested category
            continue
        print d.category
        print >> output, ' <document>'
        print >> output, '  <title>%s</title>' % cleanup(d.title)
        print >> output, '  <snippet>%s</snippet>' % cleanup(d.description)
        print >> output, '  <url>%s</url>' % d.link
        if d.enclosure:
            print >> output, '  <field key="thumbnail-url"><value type="java.lang.String" value="%s"/></field>' % d.enclosure
        print >> output, ' </document>'
    print >> output, '</searchresult>'

if __name__ == '__main__':
    main()
