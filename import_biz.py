from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import NoSuchElementException, WebDriverException, TimeoutException
from bs4 import BeautifulSoup
import time, re, pymysql, html5lib, random, sys, urlparse, urllib, ConfigParser, traceback

add_urls = [ 'manta.com', 'yellowpages.com', 'facebook.com' ]
ignore_urls = [ 'angieslist.com', 'bbb.org', 'yelp.com', 'google.com', 'whitepages.com', 'superpages.com', 'citysearch.com', 'mojopages.com', 'usplaces.com', 'mapquest.com', 'yellowbook.com', 'merchantcircle.com', 'credibility.com', 'findthebest.com', 'amfibi.com', 'citypages.com', 'indeed.com', 'craigslist.org', 'corporationwiki.com', 'opendi.us', 'dandb.com', 'fastsigns.com', 'printchomp.com', 'usbizplace.com', 'linkedin.com', 'wikipedia.org', 'ibegin.com','intelius.com']

config = ConfigParser.ConfigParser()
config.read('config.ini')
chrome_path = config.get('chromedriver', 'path')
conn = pymysql.connect(host=config.get('database', 'host'), user=config.get('database', 'user'), passwd=config.get('database', 'passwd'), db=config.get('database', 'db'))
commit = True

def prepare_source(source):
	source = re.sub('>\W+<', '><', source)
	return source.replace("\n", "")
	
def scrape(id, name, city, state, webb, cat_id):
		
	try:
		driver = webdriver.Chrome(chrome_path)
		driver.implicitly_wait(3)
		base_url = "http://google.com/#q="
		final_url = base_url+urllib.quote(name+", "+city+", "+state)
		print final_url
		links_to_add = []
		found = ''

		driver.get(final_url)
		time.sleep(1+random.random()*3)
		soup = BeautifulSoup(driver.page_source, 'html5lib')
		divv = soup.find_all("div", "srg")
		#print 'div', divv
		lname = name.split()
		i = 0
		added_link_types = []
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
		
			link_type_id = 1;
		
			for url2 in add_urls:
				if url2 in url:
					ignore = True
					if(('/mip/' in url) | link_type_id<>2) and (link_type_id not in added_link_types):
						added_link_types.append(link_type_id)
						print 'FOUND LINK', link_type_id, url
						links_to_add.append((url, link_type_id))
					#add_link(url, id, link_type_id)
				link_type_id += 1
		
			if(ignore):
				continue
			
			tcount = 0
			ucount = 0
			host = urlparse.urlparse(url)
			host = host.netloc
		
			for word in lname:
				if word.lower() in title.lower():
					tcount += 1
				if word.lower() in host.lower():
					ucount += 1
				
			print 'title matches', title, tcount
			print 'url matches', host, ucount
			if(tcount > (len(lname)//2)) & (ucount > (len(lname)//2)):
				i = 10
				print 'FOUND WEB host', host
				found = host
	except Exception, err:
		print traceback.format_exc()
		pass

	finally:
		driver.quit()


	found = webb if webb<>'' else found
	found = found.replace('www.', '')

	if (found <> '') | (len(links_to_add) > 0):
		try:

			biz_id = create_biz(id, found, cat_id)
			for link in links_to_add:
				add_link(link[0], biz_id, link[1])
		except Exception, err:
			print traceback.format_exc()
			pass
			
		
	#update_email(id, found)
	
def update_email(id, host):
	try:
		cursor = conn.cursor()
		
		query = 'UPDATE email SET web=%s, status_id=-1 WHERE id=%s'
		cursor.execute(query, (host, id))
		
		if commit: conn.commit()
		cursor.close()
	except Exception:
		print 'MySQL error'
		pass
		
def add_link(url, id, link_type_id):
	#try:
	cursor = conn.cursor()
		
	query = "INSERT INTO link (link, biz_id, link_type_id, is_scraped) VALUES (%s, %s, %s, 0)"
	cursor.execute(query, (url, id, link_type_id))
			
	if commit: conn.commit()
	cursor.close()
	print 'added link', url, id, link_type_id
		
	#except Exception:
	#	print 'MySQL error'
	#	pass

def check_dup(name, zipp):
	try:
		cursor = conn.cursor()
		sql = "SELECT * FROM biz WHERE name=%s AND zip=%s"
		cursor.execute(sql, (name, zipp))

		if cursor.fetchone():
			cursor.close()
			return True
		else:
			cursor.close()
			return False
	except Exception:
		print 'MySQL Error'
		pass

def update_biz(idd, found):
	#try:
	cursor = conn.cursor()
	sql = "UPDATE biz SET status_id=-3, web=%s WHERE id=%s"
	cursor.execute(sql, (found, idd))

	if commit: cursor.commit()

	cursor.close()
	#except Exception:
	#	print 'MySQL Error'
	#	pass


def create_biz(idd, found, cat_id):
	#try:
	cursor = conn.cursor()
	found = found if found <> '' else None
	sql = "INSERT INTO biz (exec_name, name, address, city, region, zip, sic, sic_description, phone, lat, `long`, sales_volume, employee_size, credit_rating, timezone, status_id, web, category_id)" + \
	"SELECT exec_name, name, address, city, region, zip, sic, sic_description, phone, lat, `long`, sales_volume, employee_size, credit_rating, timezone, -3, %s, %s FROM import WHERE id=%s"
	cursor.execute(sql, (found, cat_id, idd))
	
	if commit: conn.commit()
	biz_id = cursor.lastrowid
	print 'biz created with id', biz_id, found
	cursor.close()
	
	return biz_id
	#except Exception:
	#	print 'MySQL Error'
	#	pass


def set_imported(idd):
	try:
		cursor = conn.cursor()
		sql = "UPDATE import SET is_imported=1 WHERE id=%s"
		cursor.execute(sql, (idd))

		if commit: conn.commit()
		print "set as imported", idd
		cursor.close()
	except Exception:
		print 'MySQL error'
		pass


def get_bus(idd, table, cat_id):
	global offset
	i = 0
	print 'offset: ', offset, 'table', table, 'category', cat_id
	
	
	max = 10000 if idd == 0 else 1
	while(i < max):
		
		cursor = conn.cursor()
		
		where = "WHERE sic IN (SELECT sic FROM "+table+") AND is_imported = 0" if idd == 0 else "WHERE import.id = "+idd
		
		sql = "SELECT id, name, city, region, zip, web FROM import "+where+" LIMIT 100 OFFSET "+ str(offset)
		cursor.execute(sql)
		
		for link in cursor.fetchall():
			print ' ------------------------------------------------- '
			print 'scraping', link[0], '"', link[1], '"', link[2], link[3], link[5]
			
			if check_dup(link[1], link[4]):
				print 'duplicate to existing biz record'
			else:
				scrape(link[0], link[1], link[2], link[3], link[5].strip(), cat_id)
			#time.sleep(1+random.random()*3)

			set_imported(link[0])
		
		i+=100
		print 'i is at ', i
			
		cursor.close()
		
	conn.close()

if __name__ == '__main__':
	global offset
	offset = 0
	idd = 0 
	table = sys.argv[1]
	cat_id = sys.argv[2]

	get_bus(idd, table, cat_id)

