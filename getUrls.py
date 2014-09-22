from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import NoSuchElementException, WebDriverException, TimeoutException
from bs4 import BeautifulSoup
import time, re, pymysql, html5lib, random, sys, urlparse, urllib, ConfigParser

add_urls = [ 'yellowpages.com', 'facebook.com' ]
ignore_urls = [ 'manta.com', 'angieslist.com', 'bbb.org', 'yelp.com', 'google.com', 'whitepages.com', 'superpages.com', 'citysearch.com', 'mojopages.com', 'usplaces.com', 'mapquest.com', 'yellowbook.com', 'merchantcircle.com', 'credibility.com', 'findthebest.com', 'amfibi.com', 'citypages.com', 'indeed.com', 'craigslist.org', 'corporationwiki.com', 'opendi.us', 'dandb.com', 'fastsigns.com', 'printchomp.com', 'usbizplace.com']

config = ConfigParser.ConfigParser()
config.read('config.ini')
chrome_path = config.get('chromedriver', 'path')
conn = pymysql.connect(host=config.get('database', 'host'), user=config.get('database', 'user'), passwd=config.get('database', 'passwd'), db=config.get('database', 'db'))


def prepare_source(source):
	source = re.sub('>\W+<', '><', source)
	return source.replace("\n", "")
	
def scrape(id, name, city, state):
	driver = webdriver.Chrome(chrome_path)
	driver.implicitly_wait(3)
	base_url = "http://google.com/#q="
	final_url = base_url+urllib.quote(name+", "+city+", "+state)
	print final_url

	driver.get(final_url)
	time.sleep(1+random.random()*3)
	soup = BeautifulSoup(driver.page_source, 'html5lib')
	divv = soup.find_all("div", "srg")
	#print 'div', divv
	lname = name.split()
	i = 0
	added_link_types = []
	found =''
	for li in divv:
		if(len(li['class']) != 1):
			continue
			
		i +=1
		
		if i>4 and not li.a:
			break;
		
		title = ''.join([n.string for n in li.a.contents])
		url = li.a['href']
		
		ignore = False
		for url1 in ignore_urls:
			if url1 in url:
				ignore = True
		
		if(ignore):
			continue
		
		link_type_id = 2;
		
		for url2 in add_urls:
			if url2 in url:
				ignore = True
				if(('/mip/' in url) | link_type_id==3) and (link_type_id not in added_link_types):
					added_link_types.append(link_type_id)
					print 'ADDING LINK', link_type_id, url
					add_link(url, id, link_type_id)
			link_type_id += 1
		
		if(ignore):
			continue
		
		tcount = 0
		ucount = 0
		host = urlparse.urlparse(url)
		host = host.netloc
		
		for word in lname:
			if word in title:
				tcount += 1
			if word.lower() in host:
				ucount += 1
				
		print 'title matches', title, tcount
		print 'url matches', host, ucount
		if(tcount > (len(lname)//2)) & (ucount > (len(lname)//2)):
			i = 10
			print 'FOUND WEB host', host
			found = host
			
			
	driver.quit()
	
	update_email(id, found)
	
def update_email(id, host):
	global conn
	try:
		cursor = conn.cursor()
		
		query = 'UPDATE email SET web=%s, status_id=-1 WHERE id=%s'
		cursor.execute(query, (host, id))
		
		conn.commit()
		cursor.close()
	except Exception:
		print 'MySQL error'
		pass
		
def add_link(url, id, link_type_id):
	global conn
	try:
		cursor = conn.cursor()
		
		query = "INSERT INTO link (link, biz_id, link_type_id, is_scraped) VALUES (%s, %s, %s, 0)"
		cursor.execute(query, (url, id, link_type_id))
			
		conn.commit()
		cursor.close()
		
	except Exception:
		print 'MySQL error'
		pass
		
def get_bus(idd):
	global offset
	i = 0
	print 'offset: ', offset
	
	
	max = 10000 if idd == 0 else 1
	while(i < max):
		
		cursor = conn.cursor()
		
		where = "WHERE status_id=0 and web =''" if idd == 0 else "WHERE email.id = "+idd
		
		sql = "SELECT id, name, city, region, zip FROM email "+where+" LIMIT 100 OFFSET "+ str(offset)
		cursor.execute(sql)
		
		for link in cursor.fetchall():
			print ' ------------------------------------------------- '
			print 'scraping', link[0], '"', link[1], '"', link[2], link[3], link[4]
			scrape(link[0], link[1], link[2], link[3])
			#time.sleep(1+random.random()*3)
		
		i+=100
		print 'i is at ', i
			
		conn.commit()
		cursor.close()
		
	conn.close()

if __name__ == '__main__':
	global offset
	offset = 0  if len(sys.argv) <= 1 else sys.argv[1]
	idd = 0
	get_bus(idd)
