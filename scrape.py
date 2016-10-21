from bs4 import BeautifulSoup
import random
import urllib.request
import csv
import datetime
import time
import re
import sys
import traceback

baseURL = 'http://www.funda.nl'
startURL = baseURL + '/koop/heel-nederland/'

csvfile = open('houses.csv', 'a')
csvwriter = csv.DictWriter(csvfile, fieldnames=['link', 'address', 'living_area', 'plot_size', 'nr_of_rooms', 'year', 'garden', 'garden_orientation', 'volume', 'price'])
csvwriter.writeheader()

def reduce_to_int(string):
	stripped = re.sub('[^0-9]','',string)
	if stripped == "":
		print("int is BLANK")
		return 0
	return int(stripped)

def house_details(h):
	print(baseURL+h['link'])
	req = urllib.request.Request(baseURL + h['link'])
	req.add_header('User-Agent', 'prive crawler (Python3, urllib), harm@mindshards.com')
	with urllib.request.urlopen(req) as response:
		html = response.read()
		soup = BeautifulSoup(html,'html.parser')
		soup = soup.find('div', class_='object-detail')

		try:
			if soup.find('dt',text="Bouwjaar") != None:
			    h['year'] = reduce_to_int(soup.find('dt',text="Bouwjaar").next_sibling.next_sibling.text)
			else:
			    h['year'] = reduce_to_int(re.sub('-[0-9]+', '', soup.find('dt',text="Bouwperiode").next_sibling.next_sibling.text))

			h['volume'] = reduce_to_int(soup.find('dt',text="Inhoud").next_sibling.next_sibling.text)

			h['garden'] = ""
			garden = soup.find('dt',text="Achtertuin")
			if garden != None:
			    h['garden'] = garden.next_sibling.next_sibling.text

			h['garden_orientation'] = ""
			garden_orientation = soup.find('dt',text="Ligging tuin")
			if garden_orientation != None:
			    h['garden_orientation'] = garden_orientation.next_sibling.next_sibling.text
			return h
		except:
			print("EXCEPTION DURING DETAILS PROCESSING")
			filename = random.randrange(10000)
			print("ID",filename)
			with open(str(filename)+".html", 'w') as f:
			    f.write(soup.prettify())
			traceback.print_exc()
			return {}

def extract_house_from_list(house):
	try:
		h = {}
		h['link'] = house.find('a', attrs={'class': None}).get('href')
		h['address'] = " ".join(house.find('h3').text.replace('\n', '').split())
		h['price'] = reduce_to_int(house.find('span', class_='search-result-price').text)
		h['nr_of_rooms'] = reduce_to_int(house.find_all('li')[1].text)
		h['living_area'] = reduce_to_int(house.find('span', title="Woonoppervlakte").text)

		h['plot_size'] = 0
		plot_size = house.find('span', title="Perceeloppervlakte")
		if plot_size != None:
			h['plot_size'] = reduce_to_int(plot_size.text)
		return h

	except Exception as e:
		print("EXCEPTION DURING LIST PROCESSING")
		filename = random.randrange(10000)
		print("ID",filename)
		with open(str(filename)+".html", 'w') as f:
		    f.write(house.prettify())
		traceback.print_exc()
		return {}

def fetch_search_result_page(req):
	req.add_header('User-Agent', 'prive crawler (Python3, urllib), harm@mindshards.com')
	with urllib.request.urlopen(req) as response:
		html = response.read()
		soup = BeautifulSoup(html,'html.parser')
		
		sublists = soup.find_all('ol', class_='search-results')
		houses_soup = []
		for sublist in sublists:
			houses_soup.extend(sublist.find_all('div', class_="search-result-content"))

		houses = []
		for house_soup in houses_soup:
			houses.append(extract_house_from_list(house_soup))

		return soup.find('a', class_='pagination-next').get('href'), houses

next_page_link = open('last','r').read()
retries = 0

while True:
	req = urllib.request.Request(baseURL + next_page_link)
	print("\n")
	print(req.full_url)
	try:
		time.sleep(1+random.random())
		next_page_link, houses = fetch_search_result_page(req)
		retries = 0
	except urllib.error.URLError:
		if retries > 3:
			raise
		retries += 1
		continue

	for house in houses:
		if house == {}:
			continue
		while True:
			try:
				time.sleep(1+random.random())
				h = house_details(house)
				retries = 0
				if h == {}:
					break
				csvwriter.writerow(h)
			except urllib.error.URLError:
				if retries > 3:
					raise
				retries += 1
				continue
			break
