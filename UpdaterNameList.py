#!/usr/bin/env python
# -- coding: utf-8 --

import json
import time
from urllib.request import urlopen
import toolforge

conn = toolforge.connect('metawiki_p')
with conn.cursor() as cur:
    cur.execute("SELECT site_global_key AS wiki, trim(trailing '.org' from trim(leading '.' from reverse(site_domain))) AS domain FROM sites")
    res = cur.fetchall()
    cur.close()

closed_wikis = urlopen("https://noc.wikimedia.org/conf/dblists/closed.dblist").readlines()
closed_wikis = [x.decode('UTF-8').rstrip('\n') for x in closed_wikis[1:]]
deleted_wikis = urlopen("https://noc.wikimedia.org/conf/dblists/deleted.dblist").readlines()
deleted_wikis = [x.decode('UTF-8').rstrip('\n') for x in deleted_wikis[1:]]
private_wikis = urlopen("https://noc.wikimedia.org/conf/dblists/private.dblist").readlines()
private_wikis = [x.decode('UTF-8').rstrip('\n') for x in private_wikis[1:]]
test_wikis = urlopen("https://noc.wikimedia.org/conf/dblists/testwikis.dblist").readlines()
test_wikis = [x.decode('UTF-8').rstrip('\n') for x in test_wikis[1:]]
fishbowl_wikis = urlopen("https://noc.wikimedia.org/conf/dblists/fishbowl.dblist").readlines()
fishbowl_wikis = [x.decode('UTF-8').rstrip('\n') for x in fishbowl_wikis[1:]]
additional_wikis = ["apiportalwiki", "testcommonswiki", "loginwiki", "test2wiki"]

all_wikis = []

for wiki in res:
    name = str(wiki[0], "utf-8")
    domain = str(wiki[1], "utf-8")
    if name not in closed_wikis and name not in deleted_wikis \
            and name not in private_wikis and name not in test_wikis \
            and name not in fishbowl_wikis and name not in additional_wikis:
        all_wikis.append([name, domain])

if len(all_wikis) >= 500:
    with open('public_html/lists/names.txt', 'w') as names:
        for w in all_wikis:
            names.write(w[0] + "," + w[1] + '\n')
        names.close()

    ex = []
    for w in all_wikis:
        url = "https://" + w[1] + ".org/w/api.php?action=query&uselang=en&meta=siteinfo&format=json&siprop=general&utf8=1"
        a = w[0].replace("wikimedia", "").replace("wikiquote", "").replace("wiktionary", "").replace("wikivoyage", "").replace("wikisource", "").replace("wikiversity", "").replace("wikibooks", "").replace("wikinews", "").replace("wiki", "")
        res = urlopen(url).read()
        res = json.loads(res.decode("utf-8"))
        if a.replace("_", "-") != res["query"]["general"]["lang"]:
            print(res["query"]["general"]["lang"], w[0])
            ex.append([res["query"]["general"]["lang"], w[0]])
        time.sleep(1)

    
    if len(ex) > 5:
        with open('public_html/lists/exLangs.txt', 'w') as exl:
            for e in ex:
                exl.write(e[0] + "," + e[1] + '\n')
            exl.close()

langs = []
for a in all_wikis:
        a = a[0].replace("wikimedia", "").replace("wikiquote", "").replace("wiktionary", "").replace("wikivoyage", "").replace("wikisource", "").replace("wikiversity", "").replace("wikibooks", "").replace("wikinews", "").replace("wiki", "")
        if a not in langs:
            langs.append(a)

all_langs = []
if len(langs) > 10:
    X = [langs[i:i+49] for i in range(0, len(langs), 49)]
    for m in X:
        raw = ""
        for z in m:
            raw += z.replace("_", "-") + "|"
        req = urlopen("https://www.mediawiki.org/w/api.php?action=query&licode=" + raw + "&format=json&utf8=1&meta=languageinfo&liprop=bcp47%7Cautonym%7Cname%7Ccode%7Cname&uselang=en").read()
        req = json.loads(req.decode("utf-8"))
        for z in m:
            try:
                all_langs.append([z, z + " - " + req["query"]["languageinfo"][z.replace("_", "-")]["name"]])
            except:
                pass
        time.sleep(5)

if len(all_langs) > 50:
    with open('public_html/lists/namesLangs.txt', 'w') as fl:
        for l in all_langs:
            fl.write(l[0] + "," + l[1] + '\n')
        fl.close()
