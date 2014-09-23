from selenium import webdriver
from selenium.webdriver.firefox.firefox_profile import FirefoxProfile
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import NoSuchElementException, WebDriverException, TimeoutException
from bs4 import BeautifulSoup
import time, re, pymysql, html5lib, random, sys, urlparse, urllib, ConfigParser, subprocess, signal, os

config = ConfigParser.ConfigParser()
config.read('config.ini')
tor_path = config.get('tor', 'binary')
chrome_path = config.get('chromedriver', 'path')
conn = pymysql.connect(host=config.get('database', 'host'), user=config.get('database', 'user'), passwd=config.get('database', 'passwd'), db=config.get('database', 'db'))
offset = 0
commit = True


def tor_start():
	subprocess.call([tor_path])
	time.sleep(7)

def tor_quit():
	p = subprocess.Popen(['ps', '-A'], stdout=subprocess.PIPE)
	out, err = p.communicate()
	
	for line in out.splitlines():
		if 'TorBrowser' in line:
			pid = int(line.split(None, 1)[0])
			print 'quit pid', pid
			os.kill(pid, signal.SIGKILL)

	time.sleep(7)


def scrape(id, url, biz_id):
	fprofile = FirefoxProfile()
	fprofile.set_preference('network.proxy.type', 1)
	fprofile.set_preference('network.proxy.socks', "127.0.0.1")
	fprofile.set_preference('network.proxy.socks_port', 9150)

	driver = webdriver.Firefox(firefox_profile=fprofile)

	#driver = webdriver.Chrome(chrome_path)
	driver.implicitly_wait(3)
	driver.set_window_size(300+random.randint(1, 100),400)
	driver.get(url)
	time.sleep(1+random.random()*3)
	

	#print 'url', driver.current_url
	
	if ('403 Forbidden' in driver.title) | ('Problem loading page' in driver.title):
		print 'we are busted, get a new IP'
		driver.quit()
		tor_quit()
		tor_start()
		return


	if(not '/mip/' in driver.current_url):
		print 'forward'
		driver.quit()
		update_link(id)
		return


	
	prog = re.compile('(mailto:)([\w.]+@[\w]+\.+[\w.]+)', re.I)				
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
	tor_start()
	while i < max:
	
		query = 'SELECT link.id, link.link, link.biz_id FROM link, email WHERE link.is_scraped=0 AND link_type_id=2 AND link.biz_id=email.id AND email.status_id=-1 AND email.web = "" LIMIT 100'
		cursor = conn.cursor()
		
		cursor.execute(query)
		
		for link in cursor.fetchall():
			print 'scraping', link[0], link[1]
			scrape(link[0], link[1], link[2])
		i += 100
get_links()

