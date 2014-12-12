#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
rbl.rbl -- mail blacklist check

rbl.rbl is a tool to check ip's on a blacklist servers

It defines classes_and_methods

@author:	Nick Miller 

@copyright:  2014 UMBC Unix Infrastructure. All rights reserved.

@license:	 Apache License 2.0

@contact:	 nmiller3@umbc.edu
@deffield	 updated: Updated
'''

import socket
import re
import Queue
import threading
from list_gatherer import SiteList
import sys
import os
from argparse import ArgumentParser
from argparse import RawDescriptionHelpFormatter
import syslog

__all__ = []
__version__ = 0.1
__date__ = '2014-07-17'
__updated__ = '2014-11-24'

DEBUG = False
TESTRUN = 0
PROFILE = 0

#
# OPTIONS
#
NUM_WORKER_THREADS = 120
WORKER_THREAD_CHECK_FREQUENCY = .5

#
# DEFAULT COMMAND LINE OPTIONS
#
MAIL = ""
LIST_URL = ""
ADDRESSES = ""
BLACKLIST = ""

class CLIError(Exception):
	'''Generic exception to raise and log different fatal errors.'''
	def __init__(self, msg):
		super(CLIError).__init__(type(self))
		self.msg = "E: %s" % msg
	def __str__(self):
		return self.msg
	def __unicode__(self):
		return self.msg

ipList = []
job_queue = Queue.Queue()
listed_queue = Queue.Queue()
jobs_done = threading.Event()
def worker():
	while not jobs_done.isSet():
		try:
			site = job_queue.get(True,WORKER_THREAD_CHECK_FREQUENCY)
			if site.blacklistCheck():
				site.listed = True
				listed_queue.put(site)
			job_queue.task_done()
		except Queue.Empty:
			pass

def main(argv=None): # IGNORE:C0111
	
	#stdout = False
	def output(text):
		if args.stdout:
			syslog.syslog("rblcheck: %s" % text)
		else:
			syslog.syslog("rblcheck: %s" % text)
			print("rblcheck: %s" % text)


	'''Command line options.'''
	if argv is None:
		argv = sys.argv
	else:
		sys.argv.extend(argv)
	program_name = os.path.basename(sys.argv[0])
	program_version = "v%s" % __version__
	program_build_date = str(__updated__)
	program_version_message = '%%(prog)s %s (%s)' % (program_version, program_build_date)
	program_shortdesc = __import__('__main__').__doc__.split("\n")[1]
	program_license = '''%s

	Created by nmiller3 on %s.
	Copyright 2014 UMBC Unix Infrastructure. All rights reserved.

	Licensed under the Apache License 2.0
	http://www.apache.org/licenses/LICENSE-2.0

	Distributed on an "AS IS" basis without warranties
	or conditions of any kind, either express or implied.

USAGE
''' % (program_shortdesc, str(__date__))
	try:
		# Setup argument parser
		parser = ArgumentParser(description=program_license, formatter_class=RawDescriptionHelpFormatter)
		parser.add_argument('-a', '--addresses', nargs='+', action='append', default=ADDRESSES, help="one or more IPs to blacklist check")
		parser.add_argument('-l', '--list_url', action='store', default=LIST_URL, help="the source url of the list to check the IPs against. default:")
		parser.add_argument('-m', '--mail', nargs='+', action='store', default=MAIL, help="address to receive the email summary after completion. default:")
		parser.add_argument('-b', '--blacklist', action='store', default=BLACKLIST, help="file where blacklisted Sites are stored, tab delimited default %s" % BLACKLIST)
		parser.add_argument('-V', '--version', action='version', version=program_version_message)
		parser.add_argument('-s', '--stdout', action='store_true', help='optionally turn off printing to stdout')
		# Process arguments
		args = parser.parse_args()
		output(args)
	
		# validate IP addresses
		ipList = args.addresses[0]
		for ip in ipList:
			try:
				socket.inet_aton(ip)
			except socket.error:
				output(ip + " is not a valid IP address")
				sys.exit(1)
		
		# validate email address
		send_to_addresses = args.mail
		for email in send_to_addresses:
			if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
				output(email + " is not a valid email address")
				sys.exit(1)
		
		# create the SiteList object with the provided url
		sites = SiteList(args.list_url)
		
		output("trying to download the list... ",)
		try:
			sites.downloadList()
			output("successful")
		except:
			output("this list is down or does not exist")
			sites.site_list = None
			sites.toHTML(ipList)
			output("sending mail to %s" % send_to_addresses)
			sites.sendMail(send_to_addresses)
			sys.exit(1)
		
		# process the list of sites
		output("parsing website... ")
		sites.grind(ipList)
		output("successful")
		
		# reads the blacklisted file from the provided name
		output("reading blacklisted file... ",)
		try:
			output("successful")
			sites.findBlacklistedFromFile(args.blacklist)
		except IOError:
			output("file does not exist")
			s.exit(1)
		
# 		for site in sites.blacklist:
#			print site
		
		# loop to spawn the worker threads
		output("spawning workers... ",)
		for i in range(NUM_WORKER_THREADS):
			t = threading.Thread(target=worker)
			t.start()
		output("successful")
		
		# populate the queue
		output("populating the job_queue... ",)
		for site in sites.site_list:
			job_queue.put(site)
		output("successful")
		
		output("processing the queue... ",)	
		job_queue.join()
		# sets jobs_done to true so that worker threads die
		jobs_done.set()
		# reads the listed_queue
		while not listed_queue.empty():
			site = listed_queue.get()
			if site in sites.blacklist:
# 				output("%s %s is on the blacklist!" % (site.mail_ip, site.dns_zone))
				sites.no_delisting.add(site)
			else:
				sites.listed.add(site)
		
		if len(sites.listed) != 0:
			output("successful")
			for site in sites.listed:
				output(site)
		else:
			output("nothing that isn't blacklisted is listed")
		
		# generates the HTML message and mails it
		sites.toHTML(ipList)
		output("sending mail to %s" % send_to_addresses)
		sites.sendMail(send_to_addresses)
				
		output("DONE")
		return 0
	
	except KeyboardInterrupt:
		### handle keyboard interrupt ###
		return 0
	except Exception, e:
		if DEBUG or TESTRUN:
			raise(e)
		indent = len(program_name) * " "
		sys.stderr.write(program_name + ": " + repr(e) + "\n")
		sys.stderr.write(indent + "  for help use --help")
		return 2

if __name__ == "__main__":
	sys.exit(main())
