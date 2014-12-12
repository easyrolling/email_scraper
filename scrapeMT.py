from selenium import webdriver
from selenium.webdriver.firefox.firefox_profile import FirefoxProfile
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import NoSuchElementException, WebDriverException, TimeoutException
from bs4 import BeautifulSoup
import time, re, pymysql, html5lib, random, sys, urlparse, urllib, ConfigParser, subprocess, signal, os, traceback

config = ConfigParser.ConfigParser()
config.read('config.ini')
tor_path = config.get('tor', 'binary')
chrome_path = config.get('chromedriver', 'path')
conn = pymysql.connect(host=config.get('database', 'host'), user=config.get('database', 'user'), passwd=config.get('database', 'passwd'), db=config.get('database', 'db'))
offset = 0
commit = True


def scrape(id, url, biz_id):

	try:
		driver = webdriver.Chrome(chrome_path)

	#driver = webdriver.Chrome(chrome_path)
		driver.implicitly_wait(3)
		driver.set_window_size(300+random.randint(1, 100),400)
		driver.get(url)
		time.sleep(1+random.random()*3)
	

	#print 'url', driver.current_url
		
		if ('403 Forbidden' in driver.title) | ('Problem loading page' in driver.title) | ('Suspicious Activity' in driver.title) | ('Access to Website Blocked' in driver.page_source):
			print 'we are busted, get a new IP'
			driver.quit()
			return


		if(not '/c/' in driver.current_url):
			print 'forward'
			driver.quit()
			update_link(id)
			return


		soup = BeautifulSoup(driver.page_source, 'html5lib')

		region = soup.find('span', {'itemprop': 'addressRegion'})

		if(region):
			email = soup.find('div', {'itemprop': 'email'})
			web = soup.find('a', href=re.compile('/api/v1/urlverify/'))
			email_val = email.text.replace('Email: ', '') if email else ''
			web_val = web.text.replace('Web: ', '') if web else ''
			web_val = web_val.replace('www.','')
			print 'found', web_val, email_val
			update_biz(biz_id, email_val, web_val)
			update_link(id)
		else:
			print soup.title.string
			if soup.title.string == 'Manta - Error':
				print 'error page'
				insert_contact(link_id, 'error', '', '', '', '', '', '', '')
				print 'blank record inserted'	
			else:
				print 'bot page'
				driver.find_element_by_id("first_name").clear()
				driver.find_element_by_id("first_name").send_keys("robert")
				time.sleep(1)
				driver.find_element_by_id("last_name").clear()
				driver.find_element_by_id("last_name").send_keys("greene")
				time.sleep(1)
				driver.find_element_by_id("email").clear()
				driver.find_element_by_id("email").send_keys("rgreene@yopmail.com")
				time.sleep(1)
				driver.find_element_by_xpath("//button[@type='submit']").click()
				time.sleep(4+random.random()*4)
				scrape(url)
		driver.quit()
	except Exception, err:
		print traceback.format_exc()
		pass

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
	status_id = -3
	
	try:
		if(email != ''):
			status_id = 2
			sql = 'INSERT INTO email (email, biz_id) VALUES (%s, %s)'
			cursor.execute(sql, (email, id))

	
		if(web != ''):
			status_id = 1 if status_id < 1 else status_id
			sql = 'UPDATE biz SET web=%s, status_id=%s WHERE id=%s'
			cursor.execute(sql, (web, status_id, id))
		else:
			sql = 'UPDATE biz SET status_id=%s WHERE id=%s'
			cursor.execute(sql, (status_id, id))

	except Exception, err:
		print traceback.format_exc()
		pass

	print 'updated with status_id', status_id

	if(commit): conn.commit()
	cursor.close()

def get_links():
	i = 0
	print 'offset:', offset
	
	max = 10000
	while i < max:
	
		query = 'SELECT link.id, link.link, link.biz_id FROM link, biz WHERE link.is_scraped=0 AND link_type_id=1 AND link.biz_id=biz.id AND biz.status_id=-3 AND biz.web is NULL LIMIT 100 OFFSET %s'
		cursor = conn.cursor()
		
		cursor.execute(query, (offset))
		
		for link in cursor.fetchall():
			print 'scraping', link[0], link[1]
			scrape(link[0], link[1], link[2])
		i += 100

if(len(sys.argv) > 1):
    	offset = int(sys.argv[1])
get_links()


