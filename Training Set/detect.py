#!/usr/bin/env python
from PIL import Image, ImageMath, ImageOps, ImageFilter, ImageDraw
import sys
import numpy as np
import cv2, cv
import genSVMTrainData as gen
import svm2weight
def loadImage(fname):
    return Image.open(fname)

def loadTrain(fname="train.dat"):
    dat = dict()
    f=open(fname,'r')
    with f:
        for line in f:
            #print line
            chunks = line.split(":")
            imgName = chunks[0].strip()
            boxes = [x.strip() for x in chunks[1].split(";")]
            dat[imgName] = boxes
    return dat

def test(dat, windowSize, thresh, modelFname = "model2"):
    stat_array = []

    for image in dat.keys():
        #print image
        im = loadImage(image)
        #segment(image)
        sx,sy = im.size
        detected = detectStains(fixSize(im),None, windowSize, thresh, modelFname)
        #segment(image)
        #Draw rectangles on original iamge
        draw = ImageDraw.Draw(im)
        for box in dat[image]:
            break
            coordinates = box.split(" ")
            #print [int(x) for x in coordinates]
            draw.rectangle([int(x) for x in coordinates], outline="red")
        im = fixSize(im)
        

        #Draw boxes around where we detected stains
        draw = ImageDraw.Draw(im)
        temp = detected.load()
        for x in range(detected.size[0]):
            for y in range(detected.size[1]):
                if temp[x,y]==255:
                    draw.rectangle(getBoxFromPoint(windowSize,x,y))
        stats(dat,detected,windowSize,image,sx,sy,stat_array)                    
        im.show()
        #im.save(image+"marked-SVM.jpg", "JPEG")
    writestats(stat_array)
    
def fixSize(im):
    sx,sy = im.size
    if sy>sx:
        im = im.rotate(90)
        sx,sy = im.size
    if sx>1000:
        im = im.resize((600, sy*600/sx), Image.ANTIALIAS)
    return im

def detectStains(im, mask = None, windowSize=10, thresh=150, modelFname = "model1"):
    #im = ImageOps.equalize(im)
    #im = im.filter(ImageFilter.BLUR)
#    im = im.filter(ImageFilter.SMOOTH_MORE)
    #for band in im.split(): #split into each color (r,g,b,etc)
    #    detectStainsMono(band, windowSize)
    #im = fixSize(im)
    #segment(fname)
    #return detectStainsMono(im,windowSize, thresh, mask)
    weights = svm2weight.getWeights(svm2weight.load_file(modelFname))
    return detectStainsSVM(im,windowSize, weights, mask)

def detectStainsSVM(im, windowSize, weights, mask=None):
    #print weights
    sx, sy = im.size
    #mask.show()
    res = []
    vis = Image.new("L", (sx/windowSize, sy/windowSize), None)
    temp = gen.genSVMTrainInstance(im, [], windowSize, True, mask)
    b = weights[1]
    weights = weights[0]
    for pt in temp[2]:
   		feature = gen.getVector(pt)
   		#print feature
   		classification = sum([a*b for (a,b) in zip(weights,feature)])
   		if classification>0:
	   		print "c", classification
   		res.append((classification>0) * 255)
    vis.putdata(res)
    vis.show()
    return vis
    
def detectStainsMono(im, windowSize, thresh, mask=None):
    sx, sy = im.size
    #first find average of all windows
    count = 0.0
    temp = None
    winMask = None
    for x in range(sx / windowSize):
        for y in range(sy / windowSize):
            count+=1
            xp = x*windowSize
            yp = y*windowSize
            window = im.crop((xp,yp,xp+windowSize, yp+windowSize))
            if mask!=None:
            	winMask = mask.crop((xp,yp,xp+windowSize, yp+windowSize))
            if temp==None:
                window.load()
                temp = window
            else:
                temp = ImageMath.eval("float(a)+float(b)", a=temp, b=window)
    temp2 = temp.load()
    for x in range(windowSize):
        for y in range(windowSize):
            temp2[x,y]/=count
    #temp.show()
    avg = temp
    #raw_input("")
    
    """Basic difference method: subtract out each window with average window, then
    filter by average difference"""
    res = []
    for y in range(sy / windowSize):
        #res.append([])
        for x in range(sx / windowSize):
            xp = x*windowSize
            yp = y*windowSize
            window = im.crop((xp,yp,xp+windowSize, yp+windowSize))
            #window.show()
            #raw_input("")
            temp = ImageMath.eval("float(a)-float(b)",a=window, b=avg)
            temp2 = temp.load()
            diff = 0
            for c in range(windowSize):
                for r in range(windowSize):
                    diff+=pow(temp2[r,c],2.0)
            #res[x].append(diff)
            res.append(diff)
    #find average difference
    accum = 0
    accum = sum(res)
    """for r in res:
        for i in r:
            accum+=i"""
    accum/=count
    
    #subtract out average
    dmax = -1.0
    dmin = 1000000000.0
    for x in range(sx/windowSize):
        for y in range(sy/windowSize):
            res[x+y*(sx/windowSize)]-=accum
            res[x+y*(sx/windowSize)] = abs(res[x+y*(sx/windowSize)])
    #print res
    dmax = max(res)
    dmin = min(res)
    vis = Image.new("L", (sx/windowSize, sy/windowSize), None)
    temp = dmax-dmin
    if temp==0:
        temprange =0
    else:
        temprange = 255/temp
    #print res
    #print "dmin",dmin
    #print "dmax",dmax
    #print "max",temprange
    #print len(res)
    vis.putdata(res, temprange, -dmin*(255/(-dmin+dmax)))
    
    #Draw rectangles on original iamge
    draw = ImageDraw.Draw(im)
    
    temp = vis.load()
    
    #Threshold
    for y in range(sy/windowSize):
        for x in range(sx/windowSize):
            #print sys.stdout.write(str(temp[x,y])+" ")
            if temp[x,y]<thresh:
                temp[x,y] = 0
            else:
                temp[x,y] = 255
        #print ' '
    #im.show()
    #visEnlarged = vis.resize(im.size)
    #visEnlarged.show()
    #raw_input("")
    return vis

def getBoxFromPoint(windowSize, x,y):
    halfWidth = windowSize/2.0
    return (x*windowSize - halfWidth, y*windowSize - halfWidth, x*windowSize + halfWidth, y*windowSize + halfWidth)

def boxWithinAreas(x,y,windowSize,regions,sx,sy):
    # x and y are post all transformations
    ratio = 1.0
    rotate = False

    if sx < sy:
        # Flip 90deg CCW
        rotate = True
        temp = sx
        sx = sy
        sy = temp

    if sx > 1000:
        ratio = 600.0/sx
    for region in regions:
        coordinates = region.split(" ")
        if rotate:
            # print `int(coordinates[1])*ratio` + "," + `(sy-int(coordinates[0]))*ratio` + "," + `int(coordinates[3])*ratio` + "," + `(sy-int(coordinates[2]))*ratio`
            if ((x >= int(coordinates[1])*ratio and y >= (sy-int(coordinates[2]))*ratio and x <= int(coordinates[3])*ratio and y <= (sy-int(coordinates[0]))*ratio) or (x+windowSize >= int(coordinates[1])*ratio and y+windowSize >= (sy-int(coordinates[2]))*ratio) and x+windowSize <= int(coordinates[3])*ratio and y+windowSize <= (sy-int(coordinates[0]))*ratio):
                return True
        else:
            if ((x >= int(coordinates[0])*ratio and y >= int(coordinates[1])*ratio and x <= int(coordinates[2])*ratio and y <= int(coordinates[3])*ratio) or (x+windowSize >= int(coordinates[0])*ratio and y+windowSize >= int(coordinates[1])*ratio) and x+windowSize <= int(coordinates[2])*ratio and y+windowSize <= int(coordinates[3])*ratio):
                return True
    return False
    
def segment(fname):
    #Now with segmentation!
    cv_image = cv2.imread(fname)
    gray = cv2.cvtColor(cv_image, cv2.COLOR_BGR2GRAY)
    ret,thresh = cv2.threshold(gray,0,255,cv2.THRESH_BINARY+cv2.THRESH_OTSU)
    
    fg = cv2.erode(thresh,None,iterations = 2)
    bgt = cv2.dilate(thresh,None,iterations = 3)
    ret,bg = cv2.threshold(bgt,1,128,1)
    
    marker = cv2.add(fg,bg)
    #cv2.imshow("temp", marker)
    marker32 = np.int32(marker)
    
    cv2.watershed(cv_image,marker32)
    m = cv2.convertScaleAbs(marker32)
    cv2.namedWindow("Image window", flags=cv2.CV_WINDOW_AUTOSIZE)
    cv2.imshow("Image window", m)
    cv2.waitKey(300)
    raw_input("")
    #pImage = Image.fromstring("L", cv.GetSize(m), m.tostring())
    #pImage.show()

def stats(dat, detected, windowSize, image, sx, sy, output):
    foo = detected.load()

    true_positives = 0.0
    false_positives = 0.0
    false_negatives = 0.0

    stat_row = []

    for x in range(detected.size[0]):
            for y in range(detected.size[1]):
                box = getBoxFromPoint(windowSize,x,y)
                within = boxWithinAreas(box[0],box[1],windowSize,dat[image],sx,sy)
                # print `box[0]` + "," + `box[1]` + "," + `within`

                if (foo[x,y]==255 and within):
                    true_positives += 1
                elif (foo[x,y]==255 and not within):
                    false_positives += 1
                elif (foo[x,y]!=255 and within):
                    false_negatives += 1

    stat_row.append(image)
    stat_row.append(true_positives)
    stat_row.append(false_positives)
    stat_row.append(false_negatives)
    stat_row.append(true_positives/((true_positives + false_positives) or 1))
    if true_positives + false_negatives == 0:
        stat_row.append(0)
    else:
        stat_row.append(true_positives/(true_positives + false_negatives))

    output.append(stat_row)

def writestats(stat_array):
    f = open('stats.csv', 'w+')
    f2 = open('overall_stats.csv','w+')

    f.write("File,True positives,False positives,False negatives,Precision,Recall\n")

    for row in stat_array:
        f.write(`row[0]`+","+`row[1]`+","+`row[2]`+","+`row[3]`+","+`row[4]`+","+`row[5]`+"\n")

    prec = [row[4] for row in stat_array]
    rec = [row[5] for row in stat_array]
    f2.write("Average precision: " + `sum(prec)/float(len(prec))` + "\n")
    f2.write("Average recall: " + `sum(rec)/float(len(rec))` + "\n")

    f.close()
    f2.close()

if __name__=="__main__":
	test(loadTrain("trainAll.dat"),10, 100, "model2(0.0001)")
#detectStains("how-to-get-blood-out-of-the-carpet.WidePlayer.jpg", 50)
#detectStains("red-wine.jpg",25)
#detectStains("stains.jpg",10)
#detectStains("2013-03-12 16.42.30.jpg",50)
#detectStains("cherry stain.JPG")
#for w in range(1,3):
#    detectStains("2013-03-12 16.42.30.jpg",w*10)
    #segment("2013-03-12 16.42.30.jpg")
    #raw_input("")
