# GetPa0s.py v 1.0 by Grop
# 0.1 - initial version (strat: 7 + 8)
# 1.0 - improved strat  (strat: 2 + 5 + 8)

# Special thanks to Roadrunner for his nsmbulib

from nsmbulib.Yaz0 import decompress
from nsmbulib.Sarc import load
import os
import sys

# Explanation of the chosen file combination:

# Here are a few tables with the smallest file containing a certain set
# of Pa0 files, represented by a 4-bit integer. The lowest bit represents
# Pa0_jyotyu, the second one _chika, the third one _yougan, and the highest
# bit represents _yougan2.
# The goal is to get to 15 (0b1111) with the smallest filesize.

###############################			################################		#####################################
# 		Just NSMBU 			  #			#          Just NSLU 		   #		# 			NSLU + NSMBU 		    #
# ----------------------------#			# -----------------------------#		# ----------------------------------#
# 0b0000: 13-2.szs  (166875B) #			# 0b0001: 1-39.szs  (2558969B) #		# 0b0000: NSMBU/13-2.szs  (166875B) #
# 0b0001: 1-39.szs (2569173B) #			# 0b0010: 9-5.szs   (4463849B) #		# 0b0001: NSLU/1-39.szs  (2558969B) #
# 0b0010: 16-6.szs (3306306B) #			# 0b0011: 9-3.szs   (7650491B) #		# 0b0010: NSMBU/16-6.szs (3306306B) #
# 0b0011: 5-1.szs  (8432005B) #			# 0b0100: 8-3.szs   (5744345B) #		# 0b0011: NSLU/9-3.szs   (7650491B) #
# 0b0100: 15-1.szs (4675994B) #			# 0b0101: 2-23.szs (10865505B) #		# 0b0100: NSMBU/15-1.szs (4675994B) #
# 0b0101: 13-3.szs (6444139B) #			################################		# 0b0101: NSMBU/13-3.szs (6444139B) #
# 0b0111: 9-6.szs (12570672B) #													# 0b0111: NSMBU/9-6.szs (12570672B) #
# 0b1000: 17-1.szs (3698139B) #													# 0b1000: NSMBU/17-1.szs (3698139B) #
###############################													#####################################

# Possible ways to get to 15:
# We need 8, since that's the only file in the list containing _yougan2.

# The obvious way is 7 + 8, but we might be able to substitute 7 for a 
# smaller combination (with smaller total filesize)

#   7   ->                     12570672 B (12.6 MB) 
# 1 + 6 -> 2558969 + ??????? = ???????? B
# 2 + 5 -> 3306306 + 6444139 =  9750445 B ( 9.8 MB)
# 3 + 4 -> 7650491 + 4675994 = 12326485 B (12.3 MB)

# So, 2 + 5 + 8 is a better strat, as it saves 2.8 MB! But maybe we can 
# substitute 5 again, since that isn't a power of 2.

#   5   ->                      6444139 B ( 6.4 MB) 
# 1 + 4 -> 2558969 + 4675994 =  7234963 B ( 7.2 MB)
# 2 + 3 -> 3306306 + 7650491 = 10956797 B (11.0 MB)

# So, no, we cannot substitute 5, so the optimal combination is: 
# 2 + 5 + 8 => NSMBU/16-6.szs + NSMBU/13-3.szs + NSMBU/17-1.szs

def main():
	if len(sys.argv) != 3:
		print("GetPa0s 1.0 - requires nsmbulib - by Grop")
		print("Usage: python getPa0s.py <courseresdir> <savedir>")
		print("       - courseresdir:   The course-res folder of")
		print("                          NSMBU")
		print("       - savedir:        The folder in which the" )
		print("                          Pa0's are to be placed" )
		print("=================================================")
		print("This script takes the NSMBU folder and extracts"  )
		print("all retail Pa0 tilesets for use with Satoru."     )
		return
	basepath = sys.argv[1]
	savepath = sys.argv[2]
	files = ["16-6.szs", "13-3.szs", "17-1.szs"]
	for i in range(3):
		file = os.path.join(basepath, files[i])
		with open(file, 'rb') as f:
			data = f.read()
		decompressed = decompress(data)
		del data
		sarcdata = load(decompressed)
		del decompressed

		if i == 0:
			file = os.path.join(savepath, "Pa0_jyotyu_chika.sarc")
			with open(file, 'wb') as f:
				f.write(sarcdata["Pa0_jyotyu_chika"])
		elif i == 1:
			file = os.path.join(savepath, "Pa0_jyotyu.sarc")
			with open(file, 'wb') as f:
				f.write(sarcdata["Pa0_jyotyu"])

			file = os.path.join(savepath, "Pa0_jyotyu_yougan.sarc")
			with open(file, 'wb') as f:
				f.write(sarcdata["Pa0_jyotyu_yougan"])
		else:
			file = os.path.join(savepath, "Pa0_jyotyu_yougan2.sarc")
			with open(file, 'wb') as f:
				f.write(sarcdata["Pa0_jyotyu_yougan2"])
		del sarcdata
	print("Done")

if __name__ == "__main__":
	main()