from sites import Site
# import urllib
import requests
import datetime
from bs4 import BeautifulSoup
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

FROM_ADDR = "rbl-check@umbc.edu"

class SiteList(object):

	def __init__(self, list_url):
		self.list_url = list_url
		self.site_list = []
		self.html = ""
		self.email = ""
		self.listed = set()
		self.blacklist = set()
		self.no_delisting = set()
	
	def downloadList(self):
		# multirbl.valli.org blocked the user agent of this method
		# http = urllib.urlopen(self.list_url)
		# self.html = http.read()
		# http.close()

		header = {'User-Agent':'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.62 Safari/537.36'}
		
		req = requests.Session()
		req.headers.update(header)
		html = req.get(self.list_url)
		self.html = html.text

		
	# process the html
	def grind(self, ipList):
		soup = BeautifulSoup(self.html)
		
		'''
			Example temp list structure from the following for structure
		0	<td>292</td>
		1	<td><a href="http://www.zoneedit.com/">ZoneEdit deny DNS services domains</a></td>
		2	<td>ban.zebl.zoneedit.com</td>
		3	<td>-</td>
		4	<td>-</td>
		5	<td>dom</td>
		6	<td>b</td>
		7	<td>(<a href="/detail/ban.zebl.zoneedit.com.html">info</a>)</td>
		'''
		
# 		print "finding all table rows"

		for link in soup.table.find_all('tr'):
			for ip in ipList:
				temp = []
				for sibling in link.find_all('td'):
					temp.append(sibling)
				
				name = temp[1].text
				tempurl = temp[1]
				url = tempurl.a['href']
				dns_zone = temp[2].string
				
				if temp[3].text == "ipv4":
					zone_type = temp[3].text
				elif temp[4].text == "ipv6":
					zone_type = temp[4].text
				elif temp[5].text == "dom":
					zone_type = temp[5].text
				else:
					zone_type = None
				
				# if the rbl identifies as anything but a blacklist, trash it
				if temp[6].text == 'b':
					self.site_list.append(Site(name, url, dns_zone, zone_type, ip))

	def findBlacklistedFromFile(self, filename):
		savefile = open(filename,'r')
		for line in savefile:
			if line != "":
				lineList = line.encode('utf-8').strip().split("\t")
				# 	mail_ip			dns_zone				 name					 URL						type
				# ['130.85.25.77', 'dnsbl.anticaptcha.net', 'AntiCaptcha.NET IPv4', 'http://anticaptcha.net/', 'ipv4']
				self.blacklist.add(Site(lineList[2], lineList[3], lineList[1], lineList[4], lineList[0]))
	
	# formats the html section of the email
	def toHTML(self, ip_list):
		if self.site_list != None:
			html  = "<html>"
			html += "Source URL:%s <br>" % self.list_url
			html += "Mail Servers Checked: %s<br>" % str(ip_list)
		
			# listed table
			sorted_listed = sorted(self.listed, key=lambda x: x.mail_ip)
			if len(sorted_listed) != 0:
				html += "<h2>We're listed on these RBLs</h2>"
				html += "<table border=1>"
				html += "<tr><td><b>Our Mail IP</b></td><td><b>Dns Zone</b></td><td><b>Name/Link</b></td><td><b>Type</b></td></tr>"
				for site in sorted_listed:
					html += "<tr>"
					html += "	<td>%s</td>" % site.mail_ip
					html += "	<td>%s</td>" % site.dns_zone
					html += "	<td><a href=\"%s\">%s</a></td>" % (site.url, site.name)
					html += "	<td>%s</td>" % site.zone_type
					html += "</tr>"
				html += "</table>"
			else:
				html += "<br><b>We aren't listed on anything we can request delisting from!</b><br>"
		
			html += "<br>"
			html += "Listed on %s RBLs<br>" % len(self.listed)
			html += "RBLs checked: %s<br>" % len(self.site_list)
			html += "<br>"		
		
			# no delisting table
			sorted_no_delisting = sorted(self.no_delisting, key=lambda x: x.mail_ip)
			if len(sorted_no_delisting) != 0:
				html += "<br><h2>We cannot request delisting from these %s RBLs</h2><br>" % len(self.no_delisting)
				html += "<table border=1>"
				html += "<tr><td><b>Our Mail IP</b></td><td><b>Dns Zone</b></td><td><b>Name/Link</b></td><td><b>Type</b></td></tr>"
				for site in sorted_no_delisting:
					html += "<tr>"
					html += "	<td>%s</td>" % site.mail_ip
					html += "	<td>%s</td>" % site.dns_zone
					html += "	<td><a href=\"%s\">%s</a></td>" % (site.url, site.name)
					html += "	<td>%s</td>" % site.zone_type
					html += "</tr>"
				html += "</table>"
			
				html += "</html>"
			else:
				html += "<b>We can request delisting from everything!</b>"	
		else:
			html = "We tried to download the list of DNS Blacklist services from %s, but the site was down!" % self.list_url
		
		self.email = html
	
	def sendMail(self, toaddrs):
		recipients = ', '.join(toaddrs)
		
		msg = MIMEMultipart('alternative')
		msg['Subject'] = "Blacklist Check Results for %s" % datetime.datetime.now().strftime("%x %H:%M")
		
		msg.attach(MIMEText(self.email, 'plain', _charset='utf-8'))
		msg.attach(MIMEText(self.email, 'html', _charset='utf-8'))
		
		send = smtplib.SMTP('localhost')
		send.sendmail(FROM_ADDR, toaddrs, msg.as_string())
		send.quit()
	
	def __str__(self):
		for site in self.site_list:
			print site
