import detect
import random
from PIL import Image, ImageOps, ImageFilter, ImageStat

def writeSVMTrain(labelFname="train.dat", svmFname="SVMDat.dat"):
	labels = detect.loadTrain(labelFname)
	f = open(svmFname, "w")
	with f:
		for image in labels.keys():
			im = detect.loadImage(image)
			print image
			(pos,neg,combined) = genSVMTrainInstance(im, labels[image])
			#print len(pos), len(neg)
			for example in pos + random.sample(neg, min(len(neg),len(pos))):
				#write label
				f.write(str(example[0])+ " ")
				featureNum = 1
				for item in getVector(example):
					f.write(str(featureNum)+":"+str(item)+" ")
					featureNum+=1
			
				"""featureNum = 1
				#write diffs
				for featType in example[1:]:
					for channel in featType:
						f.write(str(featureNum)+":"+str(channel)+" ")
						featureNum+=1"""
				f.write("\n")
def getVector(features):
	#print "getVec", features
	out = []
	#don't append label
	#out.append(features[0])
	for featType in features[1:]:
		for channel in featType:
			out.append(channel)
	return out
						
def genSVMTrainInstance(im, bounds, windowSize=10, returnAll = False, mask = None):
	data = []
	#greyImg = ImageOps.grayscale(image)
	sx,sy = im.size
	mean, mode, median, stddev, edge = statistics(im, mask)
	#mask.show()
	dataPos = []
	dataNeg = []
	combined = []
	#print sx,sy,windowSize
	for y in range(sy/windowSize):
		y = y*windowSize		
		for x in range(sx/windowSize):
			x = x*windowSize
			label = 0
			#print "bla"
			for bound in bounds:
				if inBounds(x,y,[int(wx) for wx in bound.split(" ")]):
					label = 1
					break;
				else:
					label = -1
			#if not returnAll and (label==-1 and random.random()<0.7):
			#	continue
			#print x,y
			window = im.crop((x,y,x+windowSize, y+windowSize))
			wMask = None
			if mask!=None:
				wMask = mask.crop((x,y,x+windowSize, y+windowSize))
			#window.show()
			#try:
			wMean, wMode, wMedian, wStddev, wEdge = statistics(window, wMask)
			#print wMean
			meanDiff = [abs(a-b) for (a,b) in zip(wMean, mean)]
			modeDiff = [abs(a-b) for (a,b) in zip(wMode, mode)]
			medianDiff = [abs(a-b) for (a,b) in zip(wMedian, median)]
			stdDiff = [abs(a-b) for (a,b) in zip(wStddev, stddev)]
			"""except:
				meanDiff = [0]*3
				modeDiff = [0]*3
				medianDiff = [0]*3
				stdDiff = [0]*3
				wEdge = [0]*3"""
			#todo Edge diff
			if label==1:		
				dataPos.append((label,meanDiff,modeDiff,medianDiff,stdDiff,wEdge))
			else:
				dataNeg.append((label,meanDiff,modeDiff,medianDiff,stdDiff,wEdge))
			combined.append((label,meanDiff,modeDiff,medianDiff,stdDiff,wEdge))
	return (dataPos, dataNeg, combined)
	
def inBounds(x,y, bound):
	if (x>bound[0] and y>bound[1] and x<bound[2] and y<bound[3]):
		return True
	else:
		return False

def createMask(img):
	pass
	
#256 is white!!!
def statistics(im, mask=None):
	stat = ImageStat.Stat(im, mask)
	if sum(stat.count)==0:
		return ([0]*3,[0]*3,[0]*3,[0]*3,[0]*3)
	mean = stat.mean
	mode = []
	median = stat.median
	stddev = stat.stddev
	edgeness = []
	for band in im.split(): #split into each color (r,g,b,etc)
		hist = im.histogram(mask)
		
		"""avg = 0
		for color in range(len(hist)): #should be 256!
			avg+=hist[color]*color
		avg/=numPixels
		mean.append(avg)"""
		
		mostFreqColor = hist.index(max(hist))
		mode.append(mostFreqColor)
		
		im1 = band.filter(ImageFilter.FIND_EDGES)
		temp = ImageStat.Stat(im1, mask)
		edgeness.append(temp.sum[0])
	return (mean,mode,median,stddev,edgeness)
	
