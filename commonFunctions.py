#mcamain.py
import sys
import time
import os
import re
from datetime import datetime


def calculateDir():
	filename=""
	file=""
	data_directory  = "/home/pi/data/"
	if not os.path.exists(data_directory):
		print("path does not exist")
		os._exit(-1)
	t1=time.time()
	end_time = datetime.fromtimestamp(t1)
	dir_ext = "{}/".format(end_time.strftime("%Y-%m-%d"))
	data_directory = data_directory+dir_ext
	if not os.path.exists(data_directory):
		os.makedirs(data_directory)
	return data_directory

def calculateFilename(prefix):
	t1=time.time()
	end_time = datetime.fromtimestamp(t1)
	file="{}{}.csv".format(prefix,end_time.strftime("%Y-%m-%d_%H%M%S"))
	return file
