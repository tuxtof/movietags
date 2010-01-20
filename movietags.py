#!/usr/bin/env python
#encoding:utf-8
#author:tuxtof
#project:movietags
#license:Creative Commons GNU GPL v2
# (http://creativecommons.org/licenses/GPL/2.0/)

"""
movietags
Automatic Movie tagger.
Uses data from www.themoviedb.org

thanks goes to:
the MP4v2 team (http://code.google.com/p/mp4v2/) for their excellent mp4 container editing library
the Subler team (http://code.google.com/p/subler/), their project was used as a template for MP4Tagger (source code soon to be released)
dbr - http://github.com/dbr/themoviedb - for the API wrapper to TMDb
ccjensen - for the source code
"""

__author__ = "tuxtof"
__version__ = "0.5"

import os
import sys
import re
import glob
from optparse import OptionParser
import tmdb_api
import tempfile

def whichBin(execName):
	for path in os.environ["PATH"].split(":"):
		if os.path.exists(os.path.join(path,execName)):
			return 1

def openurl(urls):
    for url in urls:
        if len(url) > 0:
            os.popen("open \"%s\"" % url)
        #end if len
    #end for url
    return
#end openurl

def getDataFromTMDb(opts, movieName):
    """docstring for getDataFromTMDb"""
    if opts.verbose == 2:
        print "!!Looking up data for: %s" % (movieName)
    #end if debug
    movieResults = tmdb_api.search(movieName.decode("utf-8"))
    movies = []
    
    if opts.verbose == 2:
        print "!!Search returned %s hits" % len(movieResults)
    #end if debug
    
    #we got zero hits, try replacing some commonly used replacement-characters due to filename illegality
    if len(movieResults) < 1:
        if movieName.count(';'):
            tempMovieName = movieName.replace(';', ':')
            return getDataFromTMDb(opts, tempMovieName)
        elif movieName.count('_'):
            tempMovieName = movieName.replace('_', ' ')
            return getDataFromTMDb(opts, tempMovieName)
        else:
            #last ditch attempt, search for movies by longest word in movie name as long as more then one word
            if len(movieName.split()) < 2:
                return movies
            #end if len
            movieNameLongestWord = max(movieName.split(), key=len)
            longestWordMovies = getDataFromTMDb(opts, movieNameLongestWord)
            if opts.interactive or len(longestWordMovies) == 1:
                if opts.verbose == 2:
                    print "!!Using search result(s) based upon longest word search"
                #end if debug
                return longestWordMovies
            #end if interactive
            return movies
        #end if count
    #end if len
    
    
    for movieResult in movieResults:
		#check that the year tag in the file name matches with the release date, otherwise not the movie we are looking for
		if opts.verbose == 2:
			print "!!Potential hit: %s" % movieResult['name']
		movie = tmdb_api.getMovieInfo(movieResult['id'])
		movies.append(movie)
	#end for movie
    
    return movies
#end getDataFromTMDb


def tagFile(opts, movie):
    """docstring for tagFile"""
    if opts.verbose > 0:
        print "  Tagging file..."
    #end if verbose
    
    #setup tags for the MP4Tagger function
    addArtwork = " --artwork \"%s\"" % movie['artworkFileName'] #the file we downloaded earlier
    addMediaKind = " --media_kind \"Movie\"" #set type to Movie
    addName =  " --name \"%s\"" % movie['name']
    addDescription = " --description \"%s\"" % movie['overview']
    addLongDescription = " --long_description \"%s\"" % movie['overview']
    addContentRating = "" # --content_rating \"%s\"" % "Inoffensive"
    addRating = " --rating \"%s\"" % "Unrated"
    addComments = " --comments \"tagged by movietags\""
    additionalParameters = ""
    
    if (movie['released'] == ""):
        addYear = ""
    else:
        addYear = " --release_date \"%sT07:00:00Z\"" % movie['released']
    #end if (movie['released'] == "")
    
    genres = movie['categories']['genre'].keys()
    if (len(genres) > 0):
        addGenre = " --genre \"%s\"" % genres[len(genres)-1]
    else:
        addGenre = ""
    #end if (len(genres)
    
    artist = ""
    for personID in movie['cast']['Director']:
        artist = movie['cast']['Director'][personID]['name']
        break #we only need one of the director's (if multiple)
    #end for personID
    
    addArtist = " --artist \"%s\"" % artist
    
    #create rDNSatom
    addCast = ""
    addDirectors = ""
    addCodirectors = ""
    addProducers = ""
    addScreenwriters = ""
    if len(movie['cast']['Actor']) > 0:
        actors = createCommaSeperatedStringFromJobSpecificCastDict(movie['cast']['Actor'])
        addCast = " --cast \"%s\"" % actors
    #end if len
    if len(movie['cast']['Director']) > 0:
        directors = createCommaSeperatedStringFromJobSpecificCastDict(movie['cast']['Director'])
        addDirectors = " --director \"%s\"" % directors
    #end if len
    if len(movie['cast']['Codirector']) > 0:
        codirectors = createCommaSeperatedStringFromJobSpecificCastDict(movie['cast']['Codirector'])
        addCodirectors = " --codirector \"%s\"" % codirectors
    #end if len
    if len(movie['cast']['Producer']) > 0:
        producers = createCommaSeperatedStringFromJobSpecificCastDict(movie['cast']['Producer'])
        addProducers = " --producers \"%s\"" % producers
    #end if len
    if len(movie['cast']['Author']) > 0:
        authors = createCommaSeperatedStringFromJobSpecificCastDict(movie['cast']['Author'])
        addScreenwriters = " --screenwriters \"%s\"" % authors
    #end if len
    
    #Create the command line string
    tagCmd = "MP4Tagger -i \"" + movie['fileName'] + "\"" \
    + addName + addArtwork + addMediaKind + addArtist + addGenre + addDescription \
    + addRating + addContentRating + addYear + addComments + addLongDescription \
    + addCast + addDirectors + addCodirectors + addProducers + addScreenwriters \
    + additionalParameters
    
    tagCmd = tagCmd.replace('`', "'")
    
    if opts.verbose == 2:
        print "!!Tag command: %s" % tagCmd
    #end if debug
    
    #run MP4Tagger using the arguments we have created
    result = os.popen(tagCmd).read()
    if result.count("Program aborted") or result.count("Error"):
        print "** ERROR: %s" % result
        return

#end tagFile

def alreadyTagged(opts, fileName):
	"""docstring for checkIfAlreadyTagged"""
	if opts.verbose > 1:
		print "check if file has already been tagged"
	cmd = "MP4Tagger -i \"" + fileName + "\" -t"
	existingTagsUnsplit = os.popen(cmd).read()
	existingTags = existingTagsUnsplit.split('\r')
	for line in existingTags:
	    if line.count("Comments: tagged by movietags"):
	        if opts.verbose > 0:
	            print "  Already tagged. Skipping..."
	        #end if verbose
	        return True
	    #end if line.count
	#end for line
	if opts.verbose == 2:
	    print "!!Not previously tagged"
	return False
#end checkIfAlreadyTagged

def correctFileName(opts, filePath, fileName, movie):
	
	#Correct file name if incorrect
	if fileName != "%s.m4v" % (movie['name'].replace('/', "-")):
		newFileName = "%s.m4v" % (movie['name'].replace('/', "-"))
		renameCmd = "mv -n \"%s/%s\" \"%s/%s\"" % (filePath, fileName, filePath, newFileName)
		os.popen(renameCmd)
		if opts.verbose > 0 :
			print "Filename corrected from \"%s\" to \"%s\"" % (fileName, newFileName)
		#end if verbose
		movie['fileName'] = newFileName
	else:
		if opts.verbose > 0:
			print "Filename \"%s\" already correct" % fileName
		#end if verbose
	#end if fileName
#end correctFileName

def createCommaSeperatedStringFromJobSpecificCastDict(dict):
    """docstring for createNameArrayFromJobSpecificCastDict"""
    result = ""
    for personID in dict:
        if result == "":
            result = dict[personID]['name']
        else:
            result = "%s, %s" % (result, dict[personID]['name'])
    return result
#end createNameArrayFromJobSpecificCastDict

def movietags(opts,fullPath):
	
	if not whichBin("MP4Tagger"):
		print "MP4Tagger tools not found"
		sys.exit(0)
	
	if not os.path.isfile(fullPath):
		sys.stderr.write(fullPath + " is not a valid file\n")
		sys.exit(1)
	#end if not os.path.isfile
	
	
	
	(filePath, fileName) = os.path.split(fullPath)
	
	if len(filePath) == 0:
		filePath = "."
	
	if opts.verbose > 0:
		processingString = "Processing: %s" % fileName
		print processingString
	#end if opts.verbose > 0
	
	(movieFileName, extension) = os.path.splitext(fileName)
	if not extension.count("mp4") and not extension.count("m4v"):
		sys.stderr.write("%s is of incorrect file type. Convert to h264 with extension mp4 or m4v\n" % fileName)
		sys.exit(2)
	#end if not extension
	
	if alreadyTagged(opts, fullPath):
		sys.stderr.write(fullPath + " is a already tagged file\n")
		if not opts.forcetagging:
			sys.exit(1)
	#end if alreadyTagged
	
	#download information from TMDb
	if opts.verbose > 0:
		print "  Retrieving data from TheMovieDB"
	#end if verbose
	movies = getDataFromTMDb(opts, movieFileName)
	if len(movies) == 0:
		sys.stderr.write("  No matches found for \"" + movieFileName + "\"\n")
		return 4
	
	if opts.interactive and len(movies) > 1:
		print "  Potential Title Matches"
		movieCounter = 0
		for movie in movies:
			print "   %s. %s (ID: %s)" % (movieCounter, movie['name'], movie['id'])
			movieCounter = movieCounter + 1
		#end for movie in movies
		
		#ask user what movie he wants to use
		movieChoice = int(raw_input("  Select correct title: "))
	else:
		if opts.verbose > 0:
			print "  Autoselecting only movie option"
		movieChoice = 0
	#end if interactive
	
	movie = movies[movieChoice]
	
	#============ ARTWORK ============
	artworksPreview = []
	artworksLarge = []
	artworksCache = os.path.join(tempfile.gettempdir(), "movietags")
	
	if not os.path.isdir(artworksCache):
		os.mkdir(artworksCache)
	
	for ids in movie['images']['poster']:
		artworksPreview.append(movie['images']['poster'][ids]['mid'])
		artworksLarge.append(movie['images']['poster'][ids]['original'])
	#end for ids
	
	if opts.interactive and len(artworksLarge) > 1:
		artworkCounter = 0
		print "\n  List of available artwork"
		for artwork in artworksPreview:
			print "   %s. %s" % (artworkCounter, artwork)
			artworkCounter += 1
		#end for artwork
		
		#allow user to preview images
		print "  Example of listing: 0 2 4"
		artworkPreviewRequestNumbers = raw_input("  List Images to Preview: ")
		artworkPreviewRequests = artworkPreviewRequestNumbers.split()
		
		artworkPreviewUrls = []
		for artworkPreviewRequest in artworkPreviewRequests:
			artworkPreviewUrls.append(artworksPreview[int(artworkPreviewRequest)])
		#end for artworkPreviewRequest
		openurl(artworkPreviewUrls)
		
		#ask user what artwork he wants to use
		artworkChoice = int(raw_input("  Artwork to use: "))
	else:
		if opts.verbose > 0:
			print "  Autoselecting only artwork option"
		artworkChoice = 0
	#end if interactive
	
	artworkUrl = artworksLarge[artworkChoice]
	
	#download artwork to use
	(artworkUrl_base, artworkUrl_fileName) = os.path.split(artworkUrl)
	(artworkUrl_baseFileName, artworkUrl_fileNameExtension)=os.path.splitext(artworkUrl_fileName)
	
	artworkFileName = movieFileName + artworkUrl_fileNameExtension
	artworkFullFileName = os.path.join(artworksCache, artworkFileName)
	
	if opts.verbose == 0:
		curlVerbosity ="-s"
	elif opts.verbose == 1:
		print "Downloaded Artwork: " + artworkFileName
		curlVerbosity ="-#"
	elif opts.verbose == 2:
		curlVerbosity ="-v"
	
	os.popen("curl %s -o \"%s\" \"%s\"" % (curlVerbosity, artworkFullFileName, artworkUrl))
	
	if opts.verbose > 0:
		print "  Downloaded Artwork: " + artworkFileName
	#end if verbose
	
		#update movie dict with filenames
	movie['fileName'] = fileName
	movie['artworkFileName'] = artworkFullFileName
	
	if opts.rename:
		#fix the filename
		correctFileName(opts, filePath, fileName, movie)
	#end if opts.rename
	
	tagFile(opts, movie)
	
	if opts.verbose > 0:
		print "  Deleted temporary artwork file created by movietags"
	#end if opts.verbose
	os.remove(artworkFullFileName)
	return 0

#end movietags

def main():
	parser = OptionParser(usage="%prog [options] <path to moviefile(s)>\n%prog -h for full list of options")
	
	parser.add_option(  "-b", "--batch", action="store_false", dest="interactive", help="Selects first search result, requires no human intervention once launched")
	parser.add_option(  "-i", "--interactive", action="store_true", dest="interactive",  help="Interactively select correct movie from search results [default]")
	parser.add_option(  "-d", "--debug", action="store_const", const=2, dest="verbose", help="Shows all debugging info")
	parser.add_option(  "-v", "--verbose", action="store_const", const=1, dest="verbose", help="Will provide some feedback [default]")
	parser.add_option(  "-q", "--quiet", action="store_const", const=0, dest="verbose", help="For ninja-like processing")
	parser.add_option(  "-n", "--renaming", action="store_true", dest="rename", help="Enable cleaning name")
	parser.add_option(  "-f", "--force-tagging", action="store_true", dest="forcetagging", help="Tags previously tagged files")
	parser.add_option(  "-r", "--remove-tags", action="store_true", dest="removetags", help="Removes all tags")
	parser.set_defaults( interactive=True, verbose=1, forcetagging=False, removetags=False, rename=False )
	
	opts, args = parser.parse_args()
	
	if len(args) == 0:
		parser.error("No movie file supplied")
	#end if len(args)
	
	for fullPath in args:
		movietags(opts,fullPath)




if __name__ == "__main__":
    sys.exit(main())

