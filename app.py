#!/usr/bin/env python

"""app.py: does the dew"""

from flask import Flask, render_template, request, jsonify

import requests
import json
import opc, time, datetime, sched, sys, itertools, os.path, math, socket

from config import discogsUsername, sort, pageNumber, defaultFormats

__author__		= "Mike Smith"
__copyright__	= "Copyright 2017, Mike Smith"
__license__		= "MIT"
__maintainer__	= "Mike Smith"

totalPixels = 500
selectedNo = 0
box = [0]
boxes = box * 25
activeArea = box * 15
recordAreaOffset = 200
pixelsPerBox = 20
black = (0,0,0)
white = (255,255,255)
red = (255,0,0)
green = (0,255,0)
blue = (0,0,255)
blankFrame = [ black ] * totalPixels

#establish fadecandy connection
client = opc.Client('localhost:7890')

#provide your discogs.com username
userName = discogsUsername

#params = {
  #'api_key': '{API_KEY}',
#}


collection = []
filteredCollection = []
formats = 'null'

app = Flask(__name__, template_folder='.')
#startup is the first function called
def startup():
	print "startup started:"
	global num_pages
	#try to connect to Discogs to gather info about userName's collection
	try:
		r = requests.get('https://api.discogs.com/users/' + userName + '/collection/folders/0/releases?per_page=50&page=' + pageNumber + '&sort=' + sort)
		initData =  json.loads(r.text)
		initKeys = initData.keys()
		if initKeys[0] == 'message':
			print "Error connecting to discogs:"
			print initData['message']
		if initKeys[0] == 'pagination':
			num_pages = initData['pagination']['pages']
			print "Ready to download " + str(num_pages) + " pages of collection data from " + discogsUsername + "\'s Discogs collection."
	except Exception,e:
		print e

def internet_on():
	for timeout in [1]:
		try:
			print "checking internet connection.."
			socket.setdefaulttimeout(timeout)
			host = socket.gethostbyname("www.google.com")
			s = socket.create_connection((host, 80), 2)
			s.close()
			print 'internet on'
			return True
		except Exception,e:
			print e
	print "internet off"
	return False

def dataCheck():
	global defaultFormats
	global formats
	global newCollection
	print "dataCheck called"
	#check to see if collection.json exists
	if os.path.isfile('collection.json'):
		#open .json if it exists
		with open('collection.json') as data_file:
			#if collection.json exists, use it to fill 'collection'
			collection = json.load(data_file)
			return collection
			# formats = loadFormats(collection)
			# #filter
			# newCollection = []
			# for f in collection:
			# 	try:
			# 		if f.get("basic_information", {}).get("formats"):
			# 			#print f.get("basic_information", {}).get("formats")
			# 			types = f["basic_information"]["formats"][0]["descriptions"]
			# 			#make this user-definable
			# 			for w in defaultFormats:
			# 				#print "Checking for defaultFormat " + w;
			# 				if w in types:
			# 					newCollection.append(f)
			# 			#print f
			# 	except KeyError:
			# 		print ("Error on " + f["basic_information"]["title"])
			# return newCollection


# def loadFormats(data):
# 	global formats
# 	print "loadFormats called : "
# 	formats = []
# 	for release in data:
# 	  descriptions = release["basic_information"]["formats"][0].get("descriptions",{})
# 	  #check to see if desired format matches current record's format
# 	  for description in descriptions:
# 		  if description not in formats:
# 		  	formats.append(description)
# 	formats = sorted(formats)
# 	return formats
#
# def formatFilter(data, filters):
# 	print "formatFilter called : "
# 	#empty filteredCollection list each time it's called
# 	filteredCollection = []
# 	releases = data
# 	targets = filters
# 	for f in filters:
# 		print "Filter = " + f
# 	for r in releases:
# 		description = r["basic_information"]["formats"][0].get("descriptions",{})
# 		#check to see if desired format matches current record's format
# 		for t in targets:
# 			if t in description:
# 			  filteredCollection.append(r)
# 	#for f in filteredCollection:
# 		#fName = f["basic_information"]["artists"][0]["name"]
# 		#fTitle = f["basic_information"]["title"]
# 		#fFormat = f["basic_information"]["formats"][0]["descriptions"][0]
# 		#print (fFormat + " - " + fName + " - " + fTitle)
# 	filteredSize = len(filteredCollection)
# 	print ("Filter complete! " + str(filteredSize) + " records returned.")
# 	return filteredCollection

def index2led(index, indexes):
	print "index2led called"
	activePixels = pixelsPerBox * len(activeArea)
	indexesPerLED = float(indexes)/activePixels
	print ("Input : " + str(index))
	print ("Indexes : " + str(indexes) + " Active Pixels : " + str(activePixels) + " Indexes Per LED : " + str(indexesPerLED))
	result = math.ceil(index/indexesPerLED)
	led = int(result)
	print "rounded up (index/indexesPerLED) = " + str(led)
	print "Output : " + str(led)
	#0/1 indexing correction
	return led

def clearAllPixels():
	client.put_pixels(blankFrame)
	client.put_pixels(blankFrame)
	#time.sleep(0.01)

#################
## Lighting FX ##
#################

def mirrorWipe(led, timeout):
	print ('FX mirrorWipe -  LED : ' + str(led) + ' Timeout : ' + str(timeout))
	clearAllPixels()
	newFrame =[ black ]* totalPixels
	resetTime = time.time() + timeout*1   # 5 seconds from now
	effectWidth = 10
	animationSteps = 3
	while True:
		if time.time() > resetTime:
			clearAllPixels()
			break
		for j in range(animationSteps):
			#reverse range so effect sweeps inward
			for i in range(effectWidth,0,-1):
				ledUp = led + i
				ledDown = led - i
				#blink centerLED in red
				if led < totalPixels:
					if j % 2 == 0:
						newFrame[led] = red
					else:
						newFrame[led] = black
				if ledUp < totalPixels:
					newFrame[ledUp] = (255/animationSteps*j, 255/animationSteps*j, 255/animationSteps*j)
				if ledDown > 0:
					newFrame[ledDown] = (255/animationSteps*j, 255/animationSteps*j, 255/animationSteps*j)
				client.put_pixels(newFrame)
			#clearAllPixels


def blink(led, count, speed):
	print('Blink Called - Selected LED : ' + str(led)+' Count: '+str(count)+' Speed: '+str(speed) )
	clearAllPixels()
	#this many times (50)
	for _ in range(count):
		newFrame =[ black ]* totalPixels
		for n,i in enumerate(newFrame):
			if n==led:
				newFrame[n] = black
		client.put_pixels(newFrame)
		client.put_pixels(newFrame)
		time.sleep(speed/100)
		newFrame =[ black ]* totalPixels
		for n,i in enumerate(newFrame):
			if n==led:
				newFrame[n] = red
		client.put_pixels(newFrame)
		client.put_pixels(newFrame)
		time.sleep(speed/100)




#################
##   Routes    ##
#################

@app.route('/')
def homepage():

  #check if internet connection is active
  #if internet_on() == True:
  	#initialize
  #	startup();
  #else:
  #	print "No internet connection"
  startup()

  #check to see if collection.json exists
  collection = dataCheck()
  #check to see if collection.json has been downloaded already and route appropriately
  if os.path.isfile('collection.json'):
	#return error page with fixLink
	return render_template('static/releases.html', releases=collection, formats=formats, length=len(collection))
	#return str(len(collection))
  else:
	return render_template('static/error.html', errorMessage="It appers as if you haven't downloaded your collection data yet.", fixText="Click here to download " + str(num_pages) + " pages of collection data from "+ discogsUsername + "\'s Discogs collection.", fixLink="/load/")
	#return str(len(collection))

@app.route('/load/')
def loadpage():
  global collection
  #change the following 2 to num_pages after debugging
  for page in range(1, num_pages+1):
	  r = requests.get('https://api.discogs.com/users/' + userName + '/collection/folders/0/releases?page=' + str(page) + '&sort=' + sort)
	  data = json.loads(r.text)['releases']
	  collection.extend(data)
	  print ('Getting page '+str(page)+' of '+str(num_pages))
	  #unauthenticated discogs requests limited at 30/minute
	  time.sleep(2)
  #print collection
  with open('collection.json', 'w') as outfile:
	json.dump(collection, outfile)
  return render_template('static/success.html', message="Collection data updated!", linkUrl="../", linkText="Click to return home")

@app.route('/blink/<int:selectedLed>')
def locate(selectedLed):
	# Fade to white
	clearAllPixels()
	#blink, led, count, speed
	blink(selectedLed, 10,90)
	return 'selected : ' + str(selectedLed)

@app.route('/select/<int:selectedIndex>')
def selectPage(selectedIndex):
	collection = dataCheck()
	#clear
	clearAllPixels()

	#check to see if filteredCollection has been updated, if so, use it
	if len(filteredCollection) > 0:
		collection = filteredCollection
	#change record index to corresponding led
	led = index2led(selectedIndex, len(collection))

	#special offset for specific area of shelves that has items to be located
	offsetLed = led + recordAreaOffset

	#mirrorWipe(led, timeout in seconds)
	mirrorWipe(offsetLed, 5)
	print ("LED : "+str(led)+" Offset LED : "+str(offsetLed))
	return render_template('static/releases.html', releases=collection, formats=formats, length=len(collection))

@app.route('/format/<format>')
def formatpage(format):
  global filteredCollection
	#check to see if collection.json exists
  if os.path.isfile('collection.json'):
	  #open .json if it exists
	  with open('collection.json') as data_file:
		  #if collection.json exists, use it to fill 'collection'
		  collection = json.load(data_file)
		  formats = loadFormats(collection)
		  filteredCollection = formatFilter(collection,[format])
  else:
	  #otherwise return error page with fixLink
	  return render_template('static/error.html', errorMessage="No collection loaded!", fixText="Click here to load collection data", fixLink="/load/")
#render releases.html with saved collection data from collection.json
  return render_template('static/releases.html', releases=filteredCollection, formats=formats, length=len(filteredCollection))

@app.route('/test/', methods=['GET','POST'])
def test():
	clicked=None
	#print clicked
	if request.method == "POST":
		#print clicked
		json = request.get_json()
		clicked=json['data']
	#print clicked
	#change record index to corresponding led
	led = index2led(int(clicked), len(newCollection))

	#special offset for specific area of shelves that has items to be located
	offsetLed = led + recordAreaOffset

	#mirrorWipe(led, timeout in seconds)
	mirrorWipe(offsetLed, 5)
	print ("LED : "+str(led)+" Offset LED : "+str(offsetLed))
	return clicked

@app.route('/filters/', methods=['GET','POST'])
def filters():
	global defaultFormats
	global collection
	if request.method == "POST":
		json = request.get_json()
		selectedFormats=json['data']
	#change record index to corresponding led
	defaultFormats = selectedFormats
	collection = dataCheck()
	print collection[0]
	for w in defaultFormats:
		print ("defaultFormats array updated : " + w)
 	#print collection
	return render_template('static/releases.html', releases=collection, formats=formats, length=len(collection))

@app.route('/collectionData')
def collectionData():
	#open up a json file and return it as jsonified data? really? I need to do this?
	with open("collection.json") as file:
		data = json.load(file)
		return jsonify(data)


if __name__ == '__main__':
  app.run(host='0.0.0.0', debug=True)
