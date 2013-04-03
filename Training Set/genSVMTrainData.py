import detect
import random
from PIL import ImageOps, ImageFilter

def writeSVMTrain(labelFname="train.dat", svmFname="SVMDat.dat"):
	labels = detect.loadTrain(labelFname)
	f = open(svmFname, "w")
	with f:
		for image in labels.keys():
			im = detect.loadImage(image)
			inst = genSVMTrainInstance(im, labels[image])
			for example in inst:
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
	out = []
	#don't append label
	#out.append(features[0])
	for featType in features[1:]:
		for channel in featType:
			out.append(channel)
	return out
						
def genSVMTrainInstance(im, bounds, windowSize=50):
	data = []
	#greyImg = ImageOps.grayscale(image)
	sx,sy = im.size
	mean, mode, median, stddev, edge = statistics(im)
	data = []
	for x in range(sx/windowSize-1):
		x = x*windowSize
		for y in range(sy/windowSize-1):
			y = y*windowSize
			label = 0
			for bound in bounds:
				if inBounds(x,y,[int(wx) for wx in bound.split(" ")]):
					label = 1
					break;
				else:
					label = -1
			if label==-1 and random.random()<0.7:
				continue
			#print x,y
			window = im.crop((x,y,x+windowSize, y+windowSize))
			wMean, wMode, wMedian, wStddev, wEdge = statistics(window)
			meanDiff = [abs(a-b) for (a,b) in zip(wMean, mean)]
			modeDiff = [abs(a-b) for (a,b) in zip(wMode, mode)]
			medianDiff = [abs(a-b) for (a,b) in zip(wMedian, median)]
			stdDiff = [abs(a-b) for (a,b) in zip(wStddev, stddev)]
			#todo Edge diff
			data.append((label,meanDiff,modeDiff,medianDiff,stdDiff,wEdge))
	return data
	
def inBounds(x,y, bound):
	if (x>bound[0] and y>bound[1] and x<bound[2] and y<bound[3]):
		return True
	else:
		return False

#256 is white!!!
def statistics(im, binSize=1):
	sx, sy = im.size
	stat = ImageStat.Stat(im)
	numPixels = sx*sy
	mean = stat.mean
	mode = []
	median = stat.median
	stddev = stat.stddev
	edgeness = []
	for band in im.split(): #split into each color (r,g,b,etc)
		hist = im.histogram()
		
		"""avg = 0
		for color in range(len(hist)): #should be 256!
			avg+=hist[color]*color
		avg/=numPixels
		mean.append(avg)"""
		
		mostFreqColor = hist.index(max(hist))
		mode.append(mostFreqColor)
		
		im1 = band.filter(ImageFilter.FIND_EDGES)
		temp = ImageStat.Stat(im1)
		edgeness.append(temp.sum[0])
	return (mean,mode,median,stddev,edgeness)
	