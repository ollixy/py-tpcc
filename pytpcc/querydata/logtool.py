import os
import json
import sys

from operator import itemgetter
from pprint import pprint

def prepare(fname):
	with open(fname,'r') as log:
		logstr = log.read()
		logstr = logstr[:-2] + ']'
		for delstr in [r'\n',r'/*Int*/',r'/*Str*/']:
			logstr = logstr.replace(delstr,'')
		try:
			res = json.loads(logstr)
		except:
			print logstr
			raise
		return res

def interpret(log_json):
	queries = sorted(log_json, key=itemgetter('time'), reverse=True)
	lst = queries[0]
	
	import pdb; pdb.set_trace()

def ops(response_dict):
	return sorted(response_dict['performancedata'], key=itemgetter('duration'), reverse=True)
	
if __name__ == "__main__":	
	fname = None
	if len(sys.argv) == 1:
		fname = max(os.listdir('.'))
		print "Using file: %s" % fname
	elif len(sys.argv) != 2:
		print 'Usage: python logtool.py [FILE]'
		sys.exit(-1)
	else:
		fname = sys.argv[1]
	log_json = prepare(fname)
	interpret(log_json)
