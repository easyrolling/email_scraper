from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import NoSuchElementException, WebDriverException, TimeoutException
from bs4 import BeautifulSoup
import time, re, pymysql, html5lib, random, sys, urlparse, urllib, ConfigParser

config = ConfigParser.ConfigParser()
config.read('config.ini')
chrome_path = config.get('chromedriver', 'path')
conn = pymysql.connect(host=config.get('database', 'host'), user=config.get('database', 'user'), passwd=config.get('database', 'passwd'), db=config.get('database', 'db'))
offset = 0
commit = True

def scrape(id, url, biz_id):
	driver = webdriver.Chrome(chrome_path)
	driver.implicitly_wait(3)
	driver.get(url)
	time.sleep(1+random.random()*3)
	
	try:	
		element = driver.find_element_by_link_text('About')

		if(element):
			if(element.get_attribute('href') !='https://www.facebook.com/facebook'):
				#print element.get_attribute('href')
				element.click()
	except Exception:
		print 'Exception while looking for About page'
		pass

	time.sleep(1+random.random()*3)
	
	prog = re.compile('(mailto:|>|\W)([\w.]+@[\w.]+)', re.I)				
	email = prog.search(driver.page_source)
	email_val = ''
	web_val = ''
	if(email):
		email_val = email.group(2)
		print 'email:', email_val

	prog = re.compile('>https?:\/\/([\w\.]+)<', re.I)
	web = prog.search(driver.page_source)
	
	if(web):
		web_val = web.group(1)
		print 'web:', web_val

	update_biz(biz_id, email_val, web_val)
	update_link(id)

	driver.quit()

def update_link(id):
	cursor = conn.cursor()
	sql = 'UPDATE link SET is_scraped=1 WHERE id=%s'
	cursor.execute(sql, (id))

	if(commit): conn.commit()
	cursor.close()

def update_biz(id, email, web):
	if(email == '') and (web == ''):
		return
	cursor = conn.cursor()
	if(email != '') and (web != ''):
		sql = 'UPDATE email SET email=%s, web=%s, status_id=2 WHERE id=%s'
		cursor.execute(sql, (email, web, id))
	
	if(email != '') and (web == ''):
		sql = 'UPDATE email SET email=%s, status_id=2 WHERE id=%s'
		cursor.execute(sql, (email, id))

	if(email == '') and (web != ''):
		sql = 'UPDATE email SET web=%s, status_id=1 WHERE id=%s'
		cursor.execute(sql, (web, id))

	if(commit): conn.commit()
	cursor.close()

def get_links():
	i = 0
	print 'offset:', offset
	
	max = 10000
	while i < max:
	
		query = 'SELECT link.id, link.link, link.biz_id FROM link, email WHERE link.is_scraped=0 AND link_type_id=3 AND link.biz_id=email.id AND email.status_id=-1 AND email.web = "" LIMIT 100'
		cursor = conn.cursor()
		
		cursor.execute(query)
		
		for link in cursor.fetchall():
			print 'scraping', link[0], link[1]
			scrape(link[0], link[1], link[2])
		i += 100
get_links()
