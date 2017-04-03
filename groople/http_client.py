import logging
import urllib.request
import re
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


class HttpClient:

    def __init__(self, username, password, event):
        self.username = username
        self.password = password
        self.event = event
        self.opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor())
        self.osid = None

    def login(self):
        logger.debug("Login")
        auth = {'username': self.username, 'password': self.password}
        logger.debug("Auth: {0}".format(auth))

        res = self.opener.open("https://app.groople.me/admin/login.htm", urllib.parse.urlencode(auth).encode('ascii'))
        logger.debug("Redirected URL: {0}".format(res.geturl()))
        q = urllib.parse.parse_qs(urllib.parse.urlparse(res.geturl()).query)

        if q['p'][0] != "loginok":
            raise Exception("Bad Login")

        self.osid = q['osid'][0]

    def userInfo(self, userid):
        logger.debug("Fetching user info for {0}".format(userid))
        url = "https://app.groople.me/admin/user.htm?" \
              "event={event}&user={user}&osid={osid}&rp=users.htm%3Fevent%3D{event}%26p%3Drestore"
        res = self.opener.open(url.format(event=self.event, user=userid, osid=self.osid))
        soup = BeautifulSoup(res.read().decode("utf-8"), 'html.parser')
        res = dict()
        res['userid'] = userid
        res['username'] = soup.find("input", id=re.compile("_4$"))['value']
        res['password'] = soup.find("input", id=re.compile("_5$"))['value']
        return res

    def initialChoices(self, userid):
        logger.debug("Fetching choices for {0}".format(userid))
        url = "https://app.groople.me/admin/user.htm?" \
              "event={event}&user={user}&osid={osid}&rp=users.htm%3Fevent%3D{event}%26p%3Drestore"
        res = self.opener.open(url.format(event=self.event, user=userid, osid=self.osid))
        soup = BeautifulSoup(res.read().decode("utf-8"), 'html.parser')

        table = soup.find("table", class_=re.compile("splitable"))
        rows = table.find_all("tr")
        r0 = [i.find("div").string for i in rows[0].find_all("td")]
        r1a = [i.string for i in rows[1].find_all("td")]
        r1b = [re.match(r'.*free', i["class"][0]) is None for i in rows[1].find_all("td")]
        r2a = [i.string for i in rows[2].find_all("td")]
        r2b = [re.match(r'.*free', i["class"][0]) is None for i in rows[2].find_all("td")]

        availability = ([i for i in zip(r0,r1a,r1b,r2a,r2b)])
        initialChoice = [
            (re.sub(r'.*activity=(\d+).*', r'\1', i['href']), i.string)
            for i in soup.find_all("a", href=re.compile('activity\.htm.*activity='))
        ]

        return (availability, initialChoice)