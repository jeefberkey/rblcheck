import socket
import string

class Site(object):
	
	def __init__(self, name, url, dns_zone, zone_type, mail_ip):
		self.name = name
		self.url = url
		self.dns_zone = dns_zone
		self.zone_type = zone_type
		self.mail_ip = mail_ip
	
	def blacklistCheck(self):
		if self.zone_type == "ipv4":
		# reverse ip address and add on the dns zone
			rev = self.mail_ip.split(".")[::-1]
			rev.append(self.dns_zone)
			revdns = string.join(rev,".")
			try:
				socket.gethostbyname(revdns)
				return True
			except socket.gaierror:
				return False
		elif self.zone_type == "ipv6":
# 			print "we don't support ipv6, so this %s fails" % self.name
			return False
		elif self.zone_type == "dom":
			try:
				domain = socket.gethostbyaddr(self.mail_ip)[0]
				rev = domain.split(".")[::-1]
				rev.append(self.dns_zone)
				revdns = string.join(rev,".")
				socket.gethostbyname(revdns)
				return True
			except socket.gaierror:
				return False
	
	def isListed(self):
		return self.listed
	
	# pretty printing
	def __repr__(self):
		return "%s(name=%r, url=%r, dns_zone=%r, zone_type=%r, mail_ip=%r)" % (
			self.__class__.__name__, self.name, self.url, self.dns_zone, self.zone_type, self.mail_ip)
	
	# for comparing site objects
	def __eq__(self, other):
		if self.dns_zone == other.dns_zone and self.mail_ip == other.mail_ip:
			return True
		else:
			return False
	
	# also for comparing site objects, but this is called before __eq__
	def __hash__(self):
		return hash((self.dns_zone, self.mail_ip))
	
# 	def __str__(self):
# # 		out = "Name:\t%s\n" % self.name
# # 		out += "URL:\t%s\n" % self.url
# # 		out += "DNS:\t%s\n" % self.dns_zone
# # 		out += "Type:\t%s\n" % self.zone_type
# # 		out += "MailIP:\t%s\n" % self.mail_ip
# # 		out += "Listed:\t%s" % self.listed
# 		
# 		out  = "SITE: "
# 		out += "%s " % self.mail_ip
# 		out += "%s " % self.name
# 		out += "%s " % self.url
# 		out += "%s " % self.dns_zone
# 		out += "%s " % self.zone_type
# 		out += "%s " % self.listed
# 		return out.encode('utf-8')
# 		
