#!/usr/bin/python
# -*- coding: utf-8 -*-
#----------------------------------------------------------------------
#	Copyright (c) 2010  Giuseppe Attardi (attardi@di.unipi.it).
#----------------------------------------------------------------------

"""Cluster news.

Usage:
  cluster.py [options] outputFile

Options:
  -c category	print clusters for given category
  -d days	go back number of days [default 1]
  -f db		database file [default newsflow]
  -h, --help	display this help and exit
"""
import sys
import getopt
import codecs
import os
import time
from BeautifulSoup import BeautifulSoup
import re
import subprocess
import urlparse
import feedparser
from store import *

def show_help():
    print >> sys.stderr, __doc__
    sys.exit(1)

categories = [
    ('Cronaca', re.compile('cronac', re.IGNORECASE)),
    ('Esteri', re.compile('ester', re.IGNORECASE)),
    ('Economia e Finanza', re.compile('economia|finanz|sostenibilit', re.IGNORECASE)),
    ('Politica', re.compile('politica', re.IGNORECASE)),
    ('Scienza e Tecnologia', re.compile('scienz|tecnolog', re.IGNORECASE)),
    ('Sport', re.compile('sport', re.IGNORECASE)),
    ('Calcio', re.compile('calcio', re.IGNORECASE)),
    ('Arte e Spettacolo', re.compile('arte|spettacol', re.IGNORECASE)),
    ('Cinema e Teatro', re.compile('cinema|teatro|tv', re.IGNORECASE)),
    ('Musica e Concerti', re.compile('music|concert', re.IGNORECASE)),
    ('Cultura', re.compile('cultura', re.IGNORECASE)),
    ('Donna', re.compile('donna', re.IGNORECASE)),
    ('Salute', re.compile('salute|benessere', re.IGNORECASE)),

    ('Firenze', re.compile('firenze|toscana', re.IGNORECASE)),
    ('Milano', re.compile('milano|lombardia', re.IGNORECASE))
]

catParent = { 'Arte e Spettacolo' : 'Spettacoli e Cultura',
  'Cinema e Teatro' : 'Spettacoli e Cultura',
  'Musica e Concerti' : 'Spettacoli e Cultura',
  'Cultura' : 'Spettacoli e Cultura',
  'Firenze' : 'Locali',
  'Milano' : 'Locali',
  'Calcio' : 'Sport',
  'Donna' : 'Vivere',
  'Salute': 'Vivere'
}

MinScore = 1.5

header = '''<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01//EN"
	  "http://www.w3.org/TR/html4/strict.dtd">
<html lang="it">
  <head>
    <title>NewsFlow</title>
<meta http-equiv="Content-Type" content="text/html; charset=UTF-8">
<link rel="stylesheet" type="text/css" href="/newsflow/styles/newsflow.css" media="screen">
<link rel="stylesheet" type="text/css" href="/newsflow/styles/print.css" media="print">
<script type="text/javascript" src="/newsflow/scripts/jquery.js"></script>
<script type="text/javascript" src="/newsflow/scripts/jquery.quickflip.min.js"></script>
<script type="text/javascript" src="/newsflow/scripts/newsflow.js"></script>
<script type="text/javascript" src="/newsflow/scripts/labels.js"></script>
<link title="NewsFlow RSS Feed" rel="alternate" type=application/rss+xml 
      href="/newsflow/feed">
<link rel=pingback href="/newsflow/xmlrpc.php">
</head>
<body>

 <div id="header">
   <div class="heading">
     <div id="logo">
       <h1><a href="/newsflow/index.html">News Flow</a></h1>
       All the news that's fit to you
     </div>
   <ul class="menu">
     <li><form id="searchForm" class="searchForm" method="get" action="/newsflow/search">
	 <label class="input">
	   <span>Cerca articoli</span>
	   <input type="text" class="searchField" name="q" />
	 </label>
	 <input type="image" class="button" src="/newsflow/images/icons/searchButton.gif" />
     </form></li>
     <li><a href="">Log in</a></li>
   </ul>
   </div><!-- heading -->
'''

pageStart = '  <div id="page">'
pageEnd =   '  </div><!-- END PAGE -->'

contentStart = '   <div id="content">'
contentEnd =   '   </div><!-- content -->'

pageContent = '''
  <!-- START TABBED SECTION -->
   <div class="ui-tabs">
     <ul id="flip-navigation" class="ui-tabs-nav">
       <li class="ui-tab selected"><a id=tab-0 href="#">Fronte</a></li>
       <li class="ui-tab"><a id="tab-1" href="#">Retro</a></li>
       <li class="ui-tab"><a id="tab-2" href="#">Opinioni</a></li>
     </ul>
     <div id="flip-container" class="ui-tabs-container">
     <!-- TAB 1: LEAD ARTICLE -->
     <div class="ui-tabs-panel">
       <a class=alignleft rel=bookmark
	  title="Articolo Principale" href="today/AccuseFini">
	 <img class=lead alt="Articolo Principale" src="/newsflow/images/photo/FiniTulliani.jpg"></a> 
       <h3><a title="Leggi gli articoli in Notizie" 
	      href="category/Notizie/index.html">Notizie</a></h3>
       <a class=title rel=bookmark
	  title="Articolo Principale" href="today/AccuseFini">
	  Accuse a Fini</a>
       <p class=author><a href="authors/author-1">L. Autore</a></p>
       <p class=catenaccio>Questa è la storia di apertura. È la prima
	 cosa che coglie l'attenzione dei visitatori. Normalmente si
	 tratta della notizia del giorno, scelta in base alle
	 segnalazioni redazionali.</p>
       <p>Di solito è accompagnata da un'immagine significativa. 
	 Segue un estratto della notizia per illustrare l'argomento
	 e il testo iniziale dell'articolo.</p>
     </div><!-- END TAB 1 -->
     <!-- TAB 2 -->
     <div class="ui-tabs-panel bullets">
       <h3 class=title>Storia</h3>
       <p>In questa parte si presentano gli antefatti della notizia.
       Fatti precedenti che hanno portato alla notizia o riferimenti
       ad approfondimenti.</p>
       <ul>
	 <li><a title="Antefatto #1" href="today/antefatto-1">Antefatto 
	     con commenti</a></li>
	 <li><a title="Antefatto #2" href="today/antefatto-2">Antefatto #2</a></li>
	 <li><a title="Antefatto #3" href="today/antefatto-3">Antefatto #3</a></li>
	 <li><a title="Antefatto with a video" href="today/antefatto-4">Antefatto con video</a></li>
	 <li><a title="Antefatto #5" 
		href="today/antefatto-5">Antefatto #5</a></li>
	 <li><a title="Antefatto 4" 
		href="today/antefatto4">Antefatto 4</a></li>
       </ul>
     </div><!-- END TAB 2 -->
     <!-- TAB 3 -->
     <div class="ui-tabs-panel">
       <h3 class=title>Opinioni</h3>
       <p>In questa scheda si riportano opinioni di vari autori
	 collegati all'articolo principale.</p>
       <p>Il lettore troverà qui riferimenti a scritti di
       autori di cui si fida o che ha dimostrato di apprezzare
       o direttamente o tramite altri del suo gruppo.</p>
     </div><!-- END TAB 3 -->
   </div><!-- END flip-container -->
   </div><!-- END TABBED SECTION -->
'''

sideBar = '''  <!-- SIDEBAR -->
  <div id=sidebar>
   <div class="listPanel">
     <div class=list>
       <h3><a title="Leggi articoli del tema Attualità" 
	      href="/newsflow/today/Notizie/index.html">Attualità</a>
	 <span class=opener>&#9660;</span></h3>
       <ul class=bullets>
	 <li><a rel=bookmark
		href="/newsflow/today/notizia-1">Notizia 1</a></li>
	 <li><a rel=bookmark
		href="/newsflow/today/notizia-2">Notizia 1</a></li>
	 <li><a rel=bookmark
		href="/newsflow/today/notizia-3">Notizia 3</a></li>
	 <li><a rel=bookmark
		href="/newsflow/today/notizia-4">Notizia 4</a></li>
       </ul>
     </div>
     <div class=list>
       <h3>Temi Preferiti<span class=opener>&#9660;</span></h3>
       <ul class=topics>
	 <li class="topic">
	   <a title="Leggi articoli del tema Energia" 
	      href="/newsflow/topic/energia/index.html">Energia (7)</a>
	 </li>
	 <li class="topic">
	   <a title="Leggi articoli del tema Internet" 
	      href="/newsflow/topic/internet/index.html">Internet (16)</a> 
	 </li>
	 <li class="topic">
	   <a title="Leggi articoli del tema Elezioni" 
	      href="/newsflow/topic/elezioni/index.html">Elezioni Anticipate (8)</a> 
	 </li>
	 <li class="topic">
	   <a title="Leggi articoli del tema Gadget"
	      href="/newsflow/topic/gadget/index.html">Gadget (21)</a>
	 </li>
	 <li class="topic">
	   <div>
	   <a title="Leggi articoli del tema Tecnologia"
	      style="display: inline"
	      href="/newsflow/topic/tecnologia">Tecnologia</a>
	   <span class=opener>&#9660;</span></div>
	   <ul class="children">
	     <li class="topic">
	       <a title="Leggi articoli del tema Google" 
		  href="/newsflow/topic/google">Google (3)</a></li>
	     <li class="topic">
	       <a title="Leggi articoli del tema Cloud Computing" 
		  href="/newsflow/topic/cloud-computing">Cloud Computing (15)</a> </li>
	     <li class="topic">
	       <a title="Leggi articoli del tema Software" 
		  href="/newsflow/topic/software">Software (6)</a></li>
	 </ul></li>
	 <li class="topic click">
	   <a title="Crea un nuovo tema" href="/newsflow/topics/creaTema.htm">
	     <img alt="" class=icon src="/newsflow/images/icons/create_profile.png">Crea un nuovo tema</a> 
	 </li>
       </ul>
     </div>
     <div class=list>
       <h3>Autori Preferiti<span class=opener>&#9660;</span></h3>
       <ul class=people>
	 <li class="person">
	   <a title="Autore preferito" 
	      href="http://scobleizer.com/"><img alt="" src="/newsflow/author/Scoble.jpg"/>R. Scoble</a> 
	 </li>
	 <li class="person">
	   <a title="Autore preferito" 
	      href="guides/scalfari"><img alt="" src="/newsflow/author/Scalfari.jpg"/>E. Scalfari</a> 
	 </li>
       </ul>
     </div><!-- list -->
     <div class=list>
       <h3>Guide<span class=opener>&#9660;</span></h3>
       <ul class=people>
	 <li class="person">
	   <a title="Persona che segui" href="/newsflow/guides/gfp.htm">
	     <img alt="" src="/newsflow/guides/gfpSmall.jpg"/>G.F. Prini</a> 
	 </li>
	 <li class="person">
	   <a title="Guida che segui" href="http://repubblica.it/">
	     <img alt="" src="/newsflow/guides/laRepubblica.png"/>La Repubblica</a>
	 </li>
	 <li class="person">
	   <a title="Guida che segui" href="http://corriere.it/">
	     <img alt="" src="/newsflow/guides/ilCorriere.png"/>Il Corriere della Sera</a>
	 </li>
	 <li class="person">
	   <a title="Persona che segui" href="http://ilsole24ore.it/">
	     <img alt="" src="/newsflow/guides/ilSole24ore.png"/>Il Sole 24 Ore</a>
	 </li>
	 <li class="person">
	   <a title="Guida che segui" href="http://unita.it/">
	     <img alt="" src="/newsflow/guides/lUnita.png"/>l'Unit&agrave;</a>
	 </li>
	 <li class="person">
	   <a title="Persona che segui" href="/newsflow/guides/sja">
	     <img alt="" src="/newsflow/guides/sjaSmall.jpg"/>S.J. Attardi</a>
	 </li>
	 <li class="topic click">
	   <a title="Cerca persone" href="/newsflow/guides/search.htm">
	     <img alt="" class=icon src="/newsflow/images/icons/findPeople.png">Altri da seguire</a> 
	 </li>
	 <li class="topic click">
	   <a title="Invita" href="/newsflow/guides/invite.htm">
	     <img alt="" class=icon src="/newsflow/images/icons/share.png">Invita</a> 
	 </li>
       </ul>
     </div><!-- list -->
     <div>
       <h3>Annunci</h3>
     </div>
     <div>
       <h3>Archivio</h3>
       <select
	  onchange="document.location.href=this.options[this.selectedIndex].value;"
	  name=archive-choice>
	 <option selected value="">Mese</option>
	 <option value=archives/2010/05>Maggio 2010</option>
	 <option value=archives/2010/06>Giugno 2010</option>
	 <option value=archives/2010/07>Luglio 2010</option>
       </select>
     </div>
     <div>
       <h3>Segui</h3>
       <ul>
	 <li><a href="/newsflow/feed">
	     <img style="border: 0" title="RSS" src="/newsflow/images/icons/feed.png" />&nbsp;</a></li>
       </ul>
     </div>
   </div><!--END SIDELIST-->
  </div><!--END SIDEBAR-->'''

footer = '''
<div id=footer>
© 2010 NewsFlow | Powered by <a href="http://comprendo.it/">Comprendo</a> | <a href="/newsflow/about.htm">About</a>
</div>

</body>
</html>
'''
menuBarStart = '''   <!-- CATEGORIES -->
  <ul id="categories" class="ie-shadow">'''
menuBarEnd = '''  </ul><!-- END CATEGORIES -->

 </div><!-- END HEADER -->'''

menuItems = ['<li class="category"><a href="/newsflow/index.html">Home</a></li>']

cleanRE = re.compile(r'<[^<]*?/?>|\([0-9:/ ]+\)')
ampRE = re.compile(r'&([^#])')
def cleanup(s):
    p = BeautifulSoup(s)
    for rel in p.findAll('div', 'mf-related'): # Repubblica: Articoli correlati
        rel.extract()
    # remove all tags
    r = cleanRE.sub(' ', str(p))
    return unicode(ampRE.sub(r'&amp;\1', r).replace('&amp;amp;', '&amp;'))

secPerDay = 24 * 60 * 60

def CatMatch(pat, cat):
    return cat and pat and pat.search(cat)

javaCommand = 'java -Xms64m -Xmx256m -Djava.ext.dirs=lib org.carrot2.cli.batch.BatchApp -o '

def freshness(t):
    delta = int(time.time()) - t
    days = delta / secPerDay
    if days:
        return str(days) + ' giorni fa'
    hours = delta / 3600
    if hours:
        return str(hours) + ' ore fa'
    return str(delta / 60) + ' minuti fa'

def source(url):
    host = urlparse.urlparse(url).hostname 
    s = host.split('.')[-2]     # get second level domain name
    if s == 'feedsportal':
        s = re.compile('0L.*?0.(.+?)0').search(url).group(1)
    return s

catRE = re.compile(r'>([^>]+?)</a')

def hierarchy(menuItems):
    "menuItems is a list of category items (<LI>)."
    m = []                   # [ '<li>...</li>' ] top categories
    h = {}                   # { topCat: [ '<li>...</li>' ] } child categories
    for item in menuItems:
        cat = catRE.search(item).group(1) # get the name of the category
        if cat in catParent:              # eg Calcio
            top = catParent[cat]          # eg Sport
            if not top in h:
                h[top] = []
            h[top].append(item) # Sport goes into h, with child Calcio
        else:
            m.append(item)      # Sport goes into m
    r = ''
    for li in m:
        cat = catRE.search(li).group(1) # get the name of the category
        if cat in h:
            r += li[0:li.rfind('</li>')]
            r += '<ul class="children">' + '\n'.join(h[cat]) + '</ul></li>\n'
            del h[cat]
        else:
            r += li + '\n'
    for top in h:               # create category titles for leftover
        r += '<li class="category"><a href=#>' + top + '</a>\n<ul class="children">\n'
        r += '\n'.join(h[top])
        r += '\n</ul></li>\n'
    return r

def printItem(output, img, docs):
                print >> output, '<dt>'
                if img:
                    print >> output, '<img alt="" src="'+img['href']+'"/>'
                print >> output, '</dt>'
                print >> output, '<dd class="Item">',
                print >> output, '<a class="FirstItem" href="%s">%s</a><br/>' % (docs[0].link, docs[0].title)
                print >> output, '<div class="Occhiello">%s</div>' % cleanup(docs[0].description)
                print >> output, '<span class="source">%s</span> -' % source(docs[0].link),
                print >> output, '<span class="fresh">%s</span><br/>' % freshness(docs[0].date)
                print >> output, '<ul>'
                for i in range(1, len(docs)):
                    print >> output, '<li><a class="Item" href="%s">%s</a> <span class="source">%s</span></li>' % (docs[i].link, docs[i].title, source(docs[i].link))
                print >> output, '</ul>'
                print >> output, '</dd>'

def main():

    try:
        opts, args = getopt.gnu_getopt(sys.argv[1:], 'c:d:f:h', ['help'])
    except getopt.GetoptError:
        show_help()

    showClusters = False
    days = 1
    db = 'newsflow'
    global categories
    for opt, arg in opts:
        if opt in ('-h', '--help'):
            show_help()
        elif opt in ('-c'):
            categories = [(arg, re.compile(arg, re.IGNORECASE))]
            showClusters = True
        elif opt in ('-d'):
            days = int(arg)
        elif opt in ('-f'):
            db = arg

    if len(args) != 1:
        show_help()

    index = args[0]
    dir = os.path.dirname(index) + '/'
    main = codecs.open(index, 'wb', 'utf-8')
    print >> main, header
    for cat in categories:
        catPage = 'category/'+cat[0]+'.html'
        menuItems.append('<li class="category"><a href="/newsflow/%s">%s</a></li>' % (catPage, cat[0]))

    menuBar = hierarchy(menuItems)
    print >> main, menuBarStart
    print >> main, menuBar
    print >> main, menuBarEnd

    print >> main, pageStart

    print >> main, contentStart
    print >> main, pageContent

    store = StoreCreate(db)

    start = int(time.time()) - days * secPerDay
        
    for cat in categories:
        temp = codecs.open('temp.xml', 'wb', 'utf-8')
        print >> temp, '<?xml version="1.0" encoding="UTF-8"?>'
        print >> temp, '<searchresult>'
        items = []
        for d in store.find(Item, Item.date > start):
            title = d.category
            if not title:
                ch = d.channel
                if ch:
                    title = ch.link         # FIXME: should be title
#                    title = ch.title
            if not CatMatch(cat[1], title): # skip those not in requested category
                continue
            d.title = cleanup(d.title)
            d.description = cleanup(d.description)
            items.append(d)
            print >> temp, ' <document>'
            print >> temp, '  <title>%s</title>' % d.title
            print >> temp, '  <snippet>%s</snippet>' % d.description
            print >> temp, '  <url>%s</url>' % d.link
            if d.enclosure:
                print >> temp, '  <field key="thumbnail-url"><value type="java.lang.String" value="%s"/></field>' % d.enclosure
            print >> temp, ' </document>'
        print >> temp, '</searchresult>'
        temp.close()

        # build clusters
        try:
            subprocess.check_call(javaCommand + 'clusters temp.xml', shell=True)
        except subprocess.CalledProcessError:
            continue

        temp = codecs.open('clusters/temp.xml', 'rb', 'utf-8')
        clusters = BeautifulSoup(temp)
        groups = clusters.findAll('group')
        # Sort by ranking:
        groups = sorted(groups, key = lambda x: len(x.findAll('document')), reverse=True)
        if showClusters:
            for group in groups:
                print group.find('phrase').string
                docs = [items[int(doc['refid'])] for doc in group.findAll('document')]
                print '\t', docs[0].title
            continue

        catPage = 'category/'+cat[0]+'.html'
        output = codecs.open(dir + catPage, 'wb', 'utf-8')

        # create page
        print >> output, header
        print >> output, menuBarStart
        print >> output, menuBar
        print >> output, menuBarEnd

        print >> output, pageStart
        print >> output, contentStart
        print >> output, '<dl class="Items">'
        first = True
        for group in groups:
            # select high enough score
            label = group.find('phrase').string
            if float(group['score']) > MinScore and len(label.split()) > 1:
                docs = [items[int(doc['refid'])] for doc in group.findAll('document')]
                # find picture
                img = None
                for d in docs:
                    if d.enclosure:
                        img = eval(d.enclosure)
                        break
                printItem(output, img, docs)
                if first:
                    print >> main, '<h3 class="item"><a href="/newsflow/%s">%s</a></h3>' % (catPage, cat[0])
                    print >> main, '<dl class="Items">'
                    printItem(main, img, docs)
                    print >> main, '</dl>'
                    first = False

        print >> output, '</dl>'
        print >> output, contentEnd
        print >> output, sideBar
        print >> output, pageEnd
        print >> output, footer

        output.close()
        temp.close()

    print >> main, contentEnd

    print >> main, sideBar
    print >> main, pageEnd
    print >> main, footer
    main.close()

if __name__ == '__main__':
    main()
