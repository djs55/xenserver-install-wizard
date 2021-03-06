#!/usr/bin/env python

import time, sys, os, os.path
import traceback
import XenAPI
from subprocess import call

def is_service_running(name):
	x = call(["service", name, "status"])
	if x == 0:
		return True
	return False

def start_service(service):
	x = call(["service", service, "start"])
	if x <> 0:
		print >>sys.stderr, "ERROR: failed to start %s" % service
	time.sleep(1)

def stop_service(service):
	x = call(["service", service, "stop"])
	if x <> 0:
		print >>sys.stderr, "ERROR: failed to stop %s" % service

services = [
	"message-switch",
	"forkexecd",
	"xcp-networkd",
	"xcp-rrdd",
        "xenopsd-xc",
	"xenopsd-xenlight",
	"ffs",
	"xapi-storage-script",
	"squeezed",
	"xapi",
]

already_started = []
for service in services:
	if is_service_running(service):
		already_started.append(service)

def pre_start_check():
        try:
                with open("/proc/xen/capabilities", "r") as capabilities:
                        if capabilities.read().strip() != 'control_d':
                                print >>sys.stderr, "\nCannot start XAPI unless we are running in dom0 (nested Xen?)\n"
                                return False
        except:
                traceback.print_exc()
                print >>sys.stderr, "Not running under Xen - but will attempt to start XAPI anyway"

        return True

def connect():
	return XenAPI.xapi_local()

def start():
        if pre_start_check() == False:
                raise Exception("XAPI pre-start checks failed, you may need to reboot")

	for service in services:
		if service not in already_started:
			start_service(service)

	# Wait for XAPI to start - up to 30 seconds (5*6)
	attempts = 6
	login_works = False
	while (attempts > 0):
		try:
			x = connect()
			# on success, we leak precisely 1 session
			x.login_with_password("root", "")
			login_works = True
			break
		except Exception, e:
                        traceback.print_exc()
			print >>sys.stderr, "Caught %s, retrying in 5s" % (str(e))
			time.sleep(5)
			attempts = attempts - 1
	if login_works == False:
		raise Exception("Could not log in to XAPI")

def sync():
	try:
		x = connect()
		x.login_with_password("root", "") # let this leak
		if x.xenapi.pool.sync_database() == "":
			print >>sys.stderr, "xapi database flushed to disk"
		else:
			print >>sys.stderr, "FAILED: to flush xapi database (pool.sync_database)"
	except:
		print >>sys.stderr, "WARNING: failed to sync xapi database"
