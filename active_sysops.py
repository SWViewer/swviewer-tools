import re
import json
import time
import toolforge
import requests

wikis_result, user_agent, delay = {}, {"User-Agent": "Iluvatar@toolforge; python; requests"}, 6
data = {"action": "query", "format": "json", "utf8": 1, "list": "wikisets", "wsfrom": "Opted-out of global sysop wikis",
        "wsprop": "wikisincluded"}
url = "https://meta.wikimedia.org/w/api.php"
sql = """-- active sysops
SELECT COUNT(actor_name) AS active FROM user_groups JOIN actor ON actor_user = ug_user AND ug_group = "sysop"
WHERE EXISTS (SELECT rev_id FROM revision_userindex WHERE actor_id = rev_actor
AND LEFT (rev_timestamp, 8) >= REPLACE (CURDATE() - interval 2 month, '-', '') LIMIT 1)
OR EXISTS (SELECT log_id FROM logging_userindex WHERE actor_id = log_actor
AND LEFT (log_timestamp, 8) >= REPLACE (CURDATE() - interval 2 month, '-', '') LIMIT 1)
-- total sysops
UNION ALL SELECT COUNT(ug_user) AS total FROM user_groups WHERE ug_group = "sysop"
-- actove sysop for w-detect
UNION ALL
SELECT COUNT(actor_name) AS active FROM user_groups JOIN actor ON actor_user = ug_user AND ug_group = "sysop"
WHERE (EXISTS (
SELECT rev_id FROM revision_userindex WHERE actor_id = rev_actor AND
LEFT (rev_timestamp, 8) >= REPLACE (CURDATE() - interval 1 week, '-', '') LIMIT 1) OR
EXISTS (
SELECT log_id FROM logging_userindex WHERE actor_id = log_actor AND
LEFT (log_timestamp, 8) >= REPLACE (CURDATE() - interval 1 week, '-', '') LIMIT 1))"""


def get_wiki_domain(wiki_name):
    wiki_name = wiki_name.replace("_", "-")
    wiki_name = re.sub(r"^(.*)?wikimedia$", r"\1.wikimedia.org", wiki_name)
    wiki_name = re.sub(r"^(.*)?wikibooks$", r"\1.wikibooks.org", wiki_name)
    wiki_name = re.sub(r"^(.*)?wikiquote$", r"\1.wikiquote.org", wiki_name)
    wiki_name = re.sub(r"^(.*)?wiktionary$", r"\1.wiktionary.org", wiki_name)
    wiki_name = re.sub(r"^(.*)?wikisource$", r"\1.wikisource.org", wiki_name)
    wiki_name = re.sub(r"^(.*)?wikivoyage$", r"\1.wikivoyage.org", wiki_name)
    wiki_name = re.sub(r"^(.*)?mediawikiwiki$", "mediawiki.org", wiki_name)
    wiki_name = re.sub(r"^(.*)?wikinews$", r"\1.wikinews.org", wiki_name)
    wiki_name = re.sub(r"^(.*)?wikiversity$", r"\1.wikiversity.org", wiki_name)
    wiki_name = re.sub(r"foundationwiki", "foundation.wikimedia.org", wiki_name)
    wiki_name = re.sub(r"^(.*)?wikimaniawiki$", "wikimania.wikimedia.org", wiki_name)
    wiki_name = re.sub(r"^(.*)?outreachwiki$", "outreach.wikimedia.org", wiki_name)
    wiki_name = re.sub(r"^(.*)?testcommonswiki$", "test-commons.wikimedia.org", wiki_name)
    wiki_name = re.sub(r"^(.*)?testwikidatawiki$", "test.wikidata.org", wiki_name)
    wiki_name = re.sub(r"^(.*)?testwiki$", "test.wikipedia.org", wiki_name)
    wiki_name = re.sub(r"^(.*)?incubatorwiki$", "incubator.wikimedia.org", wiki_name)
    wiki_name = re.sub(r"^apiportalwiki$", "api.wikimedia.org", wiki_name)
    wiki_name = re.sub(r"^(.*)?wiki$", r"\1.wikipedia.org", wiki_name)
    return wiki_name


def get_sql(project):
    try:
        conn = toolforge.connect("{0}_p".format(project))
        with conn.cursor() as cur:
            cur.execute(sql)
            result = cur.fetchall()
        conn.close()
        return [result[0][0], result[1][0], result[2][0]]
    except Exception as sql_error:
        print(sql_error)
        return False


try:
    r = requests.post(url=url, data=data, headers=user_agent).json()
    wikis = r["query"]["wikisets"][0]["wikisincluded"]
except Exception as api_error:
    print(api_error)
    pass
else:
    for wiki in wikis:
        count = get_sql(wikis[wiki])
        if count:
            active_sysops_count, total_sysops_count, week_sysops_count = count[0], count[1], count[2]
            if active_sysops_count == 0:
                status = 0
            elif active_sysops_count == 1 or active_sysops_count == 2:
                status = 1
            else:
                status = 3
            wikis_result[wikis[wiki]] = [get_wiki_domain(wikis[wiki]), status, total_sysops_count, active_sysops_count, week_sysops_count]
        time.sleep(delay)

    if len(wikis_result) > 100:
        with open("public_html/lists/active_sysops.json", "w") as outfile:
            json.dump(wikis_result, outfile)
            outfile.close()
