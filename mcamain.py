import shproto.dispatcher
import shproto.alert
import time
import threading
import re
import argparse
import os
from datetime import datetime, timezone, timedelta
from commonFunctions import calculateFilename,calculateDir


shproto.dispatcher.start_timestamp = datetime.now(timezone.utc)


if __name__ == '__main__':

	
	parser = argparse.ArgumentParser(description='Description of your program')
	parser.add_argument("-t","--time",type=int,help="specify time")
	args=parser.parse_args()
	if args.time:
		collecttime = args.time
		if (collecttime<10):
			collecttime=10
		if (collecttime>1800):
			collecttime=1800
		print("Collection time {}".format(collecttime))
	else:
		print("Usage:  mcamain.py -t [x] where [x] is the data collection time")
		exit(0)

	spec_dir = calculateDir()
	spec_file = spec_dir+calculateFilename("GSPEC")
	shproto.dispatcher.csv_out = 1
	shproto.dispatcher.xml_out = 0
	shproto.dispatcher.interspec_csv = 1

	print("Found devices: {}".format(shproto.port.getallportsastext()))
	dispatcher = threading.Thread(target=shproto.dispatcher.start)
	dispatcher.start()
	time.sleep(1)
	spec = threading.Thread(target=shproto.dispatcher.process_01, args=(spec_file,))
	shproto.dispatcher.spec_stopflag = 1
	alert = threading.Thread(target=shproto.alert.alertmode, args=(spec_dir, 1.5,))
	shproto.alert.alert_stop = 1


	with shproto.dispatcher.hide_next_responce_lock:
		shproto.dispatcher.hide_next_responce = True
	shproto.dispatcher.process_03("-cal")
	time.sleep(2)
	shproto.dispatcher.process_03("-inf")
	time.sleep(1)
	shproto.dispatcher.process_03("-sto")
	time.sleep(1)
	shproto.dispatcher.process_03("-rst")
	time.sleep(1)
	shproto.dispatcher.process_03("-sta {} -r".format(collecttime))
	time.sleep(1)
	if shproto.dispatcher.spec_stopflag == 0:
		print("Collecting thread allready running")
	spec.start()

	while True:
		if (shproto.dispatcher.total_time > (collecttime-2)):  #total time starts at 0.  so sending -sta 1800 the time increments from 0 to 1799

			print("sending stop")
			shproto.dispatcher.spec_stop()
			time.sleep(1)
			print("Updating inf")
			shproto.dispatcher.process_03("-inf")
			time.sleep(1)
			print("collecting data and saving to file " + spec_file)
			spec = threading.Thread(target=shproto.dispatcher.process_01, args=(spec_file,))
			time.sleep(5)
			shproto.dispatcher.stop()
			print("done")
			exit(0)
		time.sleep(5)
