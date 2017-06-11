import requests
import json
import datetime
import re
import csv
from bs4 import BeautifulSoup

# Get data for a specific show
# Accepts a string in the format xxxx-xx-xx
# Returns the setlist data portion of JSON as dict
def get_show(date):

	api_key = '' # enter your Phish.net API key
	url = 'https://api.phish.net/v3/setlists/get?apikey=' + api_key + '&showdate=%s' % date

	response = requests.request("GET", url)
	my_dict = json.loads(response.text)
	
	return my_dict['response']['data'][0]


# Accepts a string representing a phish.net username
# Returns a list of strings representing show dates
def get_show_list(username):
	# Grab URL for seedfile
	r = requests.get('http://phish.net/seedfile/user/%s' % username)

	# Parse contents that match as a list
	myMatch = re.findall("^[0-9]{1,2}\\/[0-9]{1,2}\\/[0-9]{1,2}", r.text, re.M)

	# Populate a new list with properly-formatted strings
	formatted = []
	for i in range(len(myMatch)):
		formatted.insert(i, datetime.datetime.strptime(myMatch[i], '%m/%d/%y').strftime('%Y-%m-%d'))
	return formatted

########################################################

# Set phish.net username
username = raw_input("Enter Phish.NET username: ")

# Get list of shows for user
print 'Getting show list for %s' % username
show_dates = get_show_list(username)
print 'Found %d shows.' % len(show_dates)

# Iterate over shows in the list
for date in show_dates:
	show_data = get_show(date)
	
	# Capture show details as variables for populating CSV
	show_date = show_data['short_date'].encode('utf-8')
	show_venue =  BeautifulSoup(show_data['venue'], 'html.parser').find('a').get_text().encode('utf-8')
	show_location = show_data['location'].encode('utf-8')
	show_url = show_data['url'].encode('utf-8')
	show_rating = show_data['rating'].encode('utf-8')
	play_url = 'http://www.phish.in/' + date

	# Extract `setlistdata` HTML from JSON response
	html = show_data['setlistdata'].encode('utf-8')
	# Replace problematic '->' characters to 'segue'
	html = html.replace('->', 'segue')
	html = html.replace(' > ', 'to')
	html = html.replace('Encore ', 'Set ')

	# Load into a BeautifulSoup object
	soup = BeautifulSoup(html, 'html.parser')
	sets = list(soup.children)

	print'Processing %s' % show_date, 

	# Iterate over sets
	for i in range(len(sets)):
		# Get the set title
		set_title = sets[i].find('span').get_text().encode('utf-8')

		# Search for 'a' tags containing class 'setlist-song'
		songs = sets[i].find_all('a', class_='setlist-song')
		song_order = 0
		
		# Iterate over songs in set
		for j in range(len(songs)):
			
			song_order = song_order + 1
			song_title = songs[j].get_text().encode('utf-8')
			song_url = songs[j]['href'].encode('utf-8')
			
			previous_song = 'not set yet'
			next_song = 'not set yet'
			
			# set previous and next song names
			if (j == 0): # first song of set
				previous_song = '(set opener)'
				if (j != (len(songs)-1)):
					next_song = songs[j+1].get_text().encode('utf-8')
				else: # first (and only) song of set
					next_song = '(set closer)'
			elif (j == (len(songs)-1)): # last song of set
				previous_song = songs[j-1].get_text().encode('utf-8')
				next_song = '(set closer)'
			else: # songs in the middle
				previous_song = songs[j-1].get_text().encode('utf-8')
				next_song = songs[j+1].get_text().encode('utf-8')
		
			# Write each song with corresponding show data in a line of a new CSV file
			with open(username + '-shows.csv', 'ab') as csvfile:
				 show_writer = csv.writer(csvfile, delimiter=',',
												 quotechar='\"', quoting=csv.QUOTE_ALL)
				 show_writer.writerow([show_date, show_location, show_venue, show_url, set_title, song_title, song_url, song_order, show_rating , play_url, previous_song, next_song])
				 
	print '...Done!'

