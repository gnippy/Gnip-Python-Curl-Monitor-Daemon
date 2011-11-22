#!/usr/bin/env python
#
# Gnip Inc
#   2011-11-13
#     Scott Hendrickson
#
# Requires daemon module.  
#   See http://www.jejik.com/articles/2007/02/a_simple_unix_linux_daemon_in_python/
#
# This code licensed GPL
#
# scott(@)drskippy(.)net

import sys
import time
import subprocess
import random
from daemon import Daemon
import ConfigParser
import datetime
import sha

sleep_seconds = 10

def isRunning ( proc_name ):
    	# pgrep not statard install on osx
	ps = subprocess.Popen("pgrep -f %s"%proc_name, shell=True, stdout=subprocess.PIPE)
	pid = ps.communicate()[0].strip()
	if pid == '':
		return False, 0
	else:
		return True, pid

def killRunning( pid ):
	if 1 == subprocess.call("kill -9 %s"%pid, shell=True):
		sys.stderr.write("Kill process pid %s unsuccessful.\n"%pid)
	return

class Observe( Daemon ):
  
    process_name = "youwillnotfindthis"
 
    def run(self):
        while True:
	    t, pid = isRunning(self.process_name)
            if not t:
		ds = datetime.datetime.strftime(datetime.datetime.now(),'%Y%m%d_%H%M')
		# Don't remove the custom cache file names -- id's the process
		# If you change cmd, change it belwo in the testURL function!
		cmd = [ 	
			"/usr/bin/curl","--compressed","-v",
        		"-u%s"%auth_string,
			"-c%s/cache_%s"%(working_dir_name, self.process_name),
        		"-b%s/cache_%s"%(working_dir_name, self.process_name),
        		url, 
			"-o", "%s/%s.json"%(data_dir_name, '_'.join([output_file_base_name,ds])) 
			]
		sys.stderr.write("%s not running, restarting.\n"%self.process_name)
		subprocess.Popen(cmd)
                time.sleep(sleep_seconds)
	    elif self.timeInterval > 0 and time.time() >= self.timeLast + self.timeInterval:
		killRunning( pid )
		self.timeLast = time.time()
		# Restarted on next pass through loop, so no sleep here 
            else:
                time.sleep(sleep_seconds)

    def customInit(self, u, i):
	self.process_name = u
	self.timeInterval = i
	# set this to zero for no restart
	self.timeLast = time.time() 
   
    def testURL(self):
	ds = datetime.datetime.strftime(datetime.datetime.now(),'%Y%m%d_%H%M')
	# don't type here, cut and paste from run function if you change it
	cmd = [
                        "/usr/bin/curl","--compressed","-v",
                        "-u%s"%auth_string,
                        "-c%s/cache_%s"%(working_dir_name, self.process_name),
                        "-b%s/cache_%s"%(working_dir_name, self.process_name),
                        url,
                        "-o", "%s/%s.json"%(data_dir_name, '_'.join([output_file_base_name,ds]))
                        ]
	return str(' '.join(cmd))   

if __name__ == "__main__":
	
	config = ConfigParser.ConfigParser()
	config.read('./watcher.cfg')
	working_dir_name = config.get('config', 'working_dir_name')
	data_dir_name = config.get('config', 'data_dir_name')
	output_file_base_name = config.get('config', 'output_file_base_name')
	auth_string = config.get('collector', 'auth_string')
	url = config.get('collector','url')
	lock_file_dir = config.get('sys','lock_file_dir')
	new_file_interval = int(config.get('sys','new_file_interval'))

	# UNIQ must be unique to the processes this watcher watches, but evaluate to
	# the same result each time this watcher is run. So base it on the working
	# directory.
	hash = sha.new(working_dir_name + data_dir_name)
	UNIQ = hash.hexdigest()[0:20]
	
	lockfile = lock_file_dir+'/observe%s.pid'%UNIQ
	daemon = Observe(lockfile)
	daemon.customInit(UNIQ, new_file_interval)

	if len(sys.argv) == 2:
        	if 'start' == sys.argv[1]:
            		daemon.start()
        	elif 'stop' == sys.argv[1]:
			t, pid = isRunning(daemon.process_name)
			sys.stderr.write("Killing process pid %s.\n"%pid)
            		daemon.stop()
			if t:
				killRunning(pid)
        	elif 'restart' == sys.argv[1]:
			t, pid = isRunning(daemon.process_name)
			sys.stderr.write("Killing process pid %s and starting new process.\n"%pid)
            		#daemon.restart()  # use this if the watcher isn't controlling the watched process as well
			daemon.stop()
			if t:
				killRunning(pid)
			daemon.start()
		elif 'test' == sys.argv[1]:
			print daemon.testURL()
        	else:
            		print "Unknown command"
            		sys.exit(2)
       	 	sys.exit(0)
    	else:
        	print "usage: %s start|stop|restart|test" % sys.argv[0]
        	sys.exit(2)
