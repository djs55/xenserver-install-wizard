#!/usr/bin/env python

import sys

import tui

IPTABLES="/etc/sysconfig/iptables"

def accept_port_of(line):
	line = line.strip()
	bits = line.split()
	if bits[-1] == "ACCEPT":
		for i in range(0, len(bits)):
			if bits[i] == "--dport":
				return int(bits[i + 1])

def all_accepted_ports_of(lines):
	result = []
	for line in lines:
		port = accept_port_of(line)
		if port <> None:
			result.append(port)
	return result

def analyse(filename = IPTABLES):
	f = open(filename, "r")
	lines = f.readlines()
	f.close()

	ports = all_accepted_ports_of(lines)
	needed_ports = [80, 443]
	ports_to_add = []
	for p in needed_ports:
		if p in ports:
			print >>sys.stderr, "OK: there appears to be a firewall hole for port %d" % p
		else:
			if tui.yesno("Would you like me to add a firewall hole for port %d?" % p):
				ports_to_add.append(p)
			else:
				print >>sys.stderr, "WARNING: the firewall might be blocking port %d" % p

	if ports_to_add == []:
		return None
	new_lines = []
	done = False
	for line in lines:
		tmp = line.strip()
		if tmp.startswith("-A INPUT") and not done:
			for p in ports_to_add:
				new_lines.append("-A INPUT -p tcp -m tcp --dport %d -j ACCEPT" % p)
			done = True
		new_lines.append(tmp)
	return (filename, new_lines)

if __name__ == "__main__":
	filename = IPTABLES
	if len(sys.argv) == 2:
		filename = sys.argv[1]
	result = analyse(filename = filename)
	if result:
		print "I propose the file %s is changed to read:" % result[0]
		for line in result[1]:
			print line
