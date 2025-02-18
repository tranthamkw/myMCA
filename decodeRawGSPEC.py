#mcamain.py
import sys
import time
import re
import logging
import os
from datetime import datetime
import csv


max_bins            = 8192
histogram           = [0] * max_bins
max_blocks = 129 # the end of the stream is counted.
offset=[0]*max_blocks  #offset. there should be 128 of them.  The offset is used to calculate channel number
exes=[0]*max_blocks # x position in the raw data buffere where the block starts
block=0 # ranges from 0 to 128
blocksize=[0]*max_blocks #each block should be 264
myInfo="test"
returnmessage=""
rawData=[]
replacements=[]

def is253(a):
	value = True
	value = (rawData[a]==253)|(rawData[a+1]==253)|(rawData[a+2]==253)
	return value

def calculateValue(a):
	global rawData
	value = (rawData[a]&0xFF)|((rawData[a+1]&0xFF) << 8)|((rawData[a+2]&0xFF) << 16)|((rawData[a+3]&0xFF) << 24)
	return (value & 0x7FFFFFF)

def writeHistogram2CSV(filename):
	global histogram
	global max_bins
	global myInfo
	global total_time
	with open(filename,mode='w') as f:
		f.write(myInfo)
		f.write(filename)
		f.write("\ntotal time,{}\n".format(total_time))
		f.write("Channel,Count\n")
		for x in range(max_bins):
			f.write("{},{}\n".format(x,histogram[x]))



filename=sys.argv[1]

with open(filename, mode='r') as f:
	myInfo=f.readline()
	line = f.readline()
	while line:
		try:
			rawData.append(int(line))
		except ValueError:
			rawData.append(0)
			print("value error")
			os_exit(-1)
		line=f.readline()

outfilename=re.sub("Raw","X",filename)
print(outfilename)
print(myInfo)

# Data structure
#	[x-6] = CRC
#	[x-5] = CRC for previous data block
#	[x-4] = 0xA5 ; end of previous data block
#	[x-3] = 0xFF ;												]
#	[x-2] = 0xFE ; start of data block							]
#	[x-1] = command. 1 expected for histogram data; 4 for stats	] - - - 3 bytes for start of block
#	[x] = offset (LSB)		]
#	[x+1] = offset << (MSB)	]---- 2 bytes for offset. Channel number = offset plus the ith "index" 
#	[x+2] counts LSB		]
#	[x+3] counts <<8		]
#	[x+4] counts <<16		]---- 4 bytes per channel, for index=1  there are 64 channels in one block. 64 * 4 = 256
#	[x+5] counts <24 MSB	]
#	[x+258] = CRC for block	]
#	[x+259] = CRC for block	] - - - 2 bytes
#	[x+260] = 0xA5; end		] - - - 1 byte

#					3 + 2  + 256 + 2 + 1 =  264 bytes
#											x 128 blocks  = 33792 bytes
#		+ 19 bytes at the begining (0xFF,0xFE,0x03,- ok stopped /n/r,CRC,CRC,0xA5)
#		+ 24 at the end (stats, cmd =4)
#		= 33835 bytes in total


print("Length of data {}".format(len(rawData)))
print("Number of excess bytes {}".format(len(rawData)-33835))

block=0
if len(rawData)>33834:
	print("processing histogram data")
	div_idx=[]
	idx=[]
	# find the x positions of the starting blocks
	for x in range(16,len(rawData)):
		if ((rawData[x-1]==1)or(rawData[x-1]==4))and(rawData[x-2]==254)and(rawData[x-3]==255)and(rawData[x-4]==165):
			if(block<=max_blocks):
				exes[block]=x  #position in raw data for the ith block
				offset[block]=(rawData[x] & 0xFF) | ((rawData[x+1]&0xFF)<<8)
				block+=1

	if (block!=max_blocks):
		print("unexpected number of blocks")
		print("found blocks {}, length exes {}".format(block,len(exes)))
		os_.exit(-1)

	#find the blocksizes the difference from 264
	for i in range(max_blocks-1):  # the last one starts the stats portion of the stream
		blocksize[i] = (exes[i+1]-exes[i])-264
#		print("Block {}\tExes {}\tOffset {}\tSize {}".format(i,exes[i],offset[i],blocksize[i]))

	for i in range(max_blocks-1):
		if blocksize[i]==0: # then expected number of bytes in the block process as normal
			for j in range(0,64):
				index = offset[i]+j
				value=calculateValue(exes[i]+2+4*j) # plus 2 for offset bytes
				histogram[index] = value & 0x7FFFFFF
		if blocksize[i]>0:  #excess number of bytes. 
			num253=0
			for x in range(exes[i]+2,exes[i+1]-3-blocksize[i]):
 # +2 for offset bytes, -3 for CRC&end -excess bytes -1 some'253's' occur just before the CRC. we can ignore these
				if rawData[x]==253:
					num253+=1
			if (blocksize[i]==num253):
				dj=0
				for j in range(0,64):
					index = offset[i]+j

					if(is253(exes[i]+2+4*j+dj)): #this number always
# shows when there is an excess byte. 
						dj+=1
						replacements.append(index)
						histogram[index]=histogram[index-1]
# this is the un-nerving part
#what do we use for a value? what was it meant to be? 
					else:		# calculate value normally
						value=calculateValue(exes[i]+2+4*j+dj) # plus 2 for offset bytes
						histogram[index] = value & 0x7FFFFFF
			else:
				print("In block {}, excessbytes {} does not equal number of 253s: {}".format(i,blocksize[i],num253))

	if(exes[max_blocks-1]+9<len(rawData)):
		x=exes[max_blocks-1]
		total_time = (rawData[x]&0xFF) | ((rawData[x+1]&0xFF)<<8) | ((rawData[x+2]&0xFF)<<16) | ((rawData[x+3]&0xFF)<<24)
		cps = (rawData[x+6]&0xFF) | ((rawData[x+7]&0xFF)<<8) | ((rawData[x+8]&0xFF)<<16) | ((rawData[x+9]&0xFF)<<24)
		print("total time {}\tcps {}".format(total_time,cps))

	print("corrected channels : ")
	for i in range(len(replacements)):
		sys.stdout.write("{}, ".format(replacements[i]))
	print("\n")


	writeHistogram2CSV(outfilename)

else:
	print("file too short??")


print("Done")
os._exit(0)
