from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import NoSuchElementException, WebDriverException, TimeoutException
from bs4 import BeautifulSoup
import time, re, pymysql, html5lib, random, sys, urlparse, mechanize
offset=0

def prepare_source(source):
	source = re.sub('>\W+<', '><', source)
	return source.replace("\n", "")
	
def scrape(email_id, email_val, url):
	driver = webdriver.Chrome('/Users/waleup/Downloads/chromedriver')
	driver.implicitly_wait(3)
	base_url = "http://"
	final_url = base_url+url
	print final_url
	try:
		driver.get(final_url)
		print 'title', driver.title
		if ('is not available' in driver.title) | ('Verizon' in driver.title):
			print 'wrong url', url
			url = ''
			status_id = 4
		else:
			status_id = 3
			time.sleep(1+random.random()*3)
			
			url = urlparse.urlparse(driver.current_url)
			url = url.netloc
			current_url = url.replace('www.', '')
			print 'url: ', url
			
			source = prepare_source(driver.page_source)
			soup = BeautifulSoup(source, 'html5lib')
			anchor = soup.find('a', text=re.compile("contact", re.I))
			
			if(anchor):
				print 'found anchor', anchor.text, anchor.get('href')
				href = anchor.get('href')
				if(href):
					status_id = 2
					if href.startswith('http'):
						driver.get(href)
					else:
						if href.startswith('/') | href.startswith('#'):
							driver.get('http://'+url+href)
						else:
							driver.get('http://'+url+'/'+href)
					
					time.sleep(1+random.random()*3)
					
					source = prepare_source(driver.page_source)
					
					prog = re.compile('(mailto:|>|\W)([\w.]+@'+current_url+')', re.I)
					
					email = prog.search(source)
					
					print 'results', email
					if(email):
						if(len(email.groups()) > 1):
							print 'Email:', email.group(2)
							status_id = 1
							email_val = email.group(2)
					else:
						prog = re.compile('(mailto:|>|\W)([\w.]+@[\w.]+)', re.I)
						email = prog.search(source)
						print 'results', email
						if(email):
							if(len(email.groups()) > 1):
								print 'Email:', email.group(2)
								status_id = 1
								email_val = email.group(2)
		
		
		update_contact(email_id, email_val, url, status_id)
		driver.quit()
	except Exception:
		print 'Exception on', url
		pass

def update_contact(email_id, email, web, status_id):

	try:
		conn = pymysql.connect(host="waleup.com", user="emails", passwd="emails123", db="emails")
		cursor = conn.cursor()
		
		query = "UPDATE email SET email=%s, web=%s, status_id=%s WHERE id=%s"
		
		print 'updating email', email_id, 'with values (', email, ',', web,',', status_id,')'
		
		cursor.execute(query, (email, web, status_id, email_id))
			
		conn.commit()
		
		
		cursor.close()
		conn.close()
	except Exception:
		print 'MySQL error'
		pass
		
def get_links(idd):
	global offset
	i = 0
	print 'offset: ', offset
	
	
	max = 5000 if idd == 0 else 1
	while(i < max):
		conn = pymysql.connect(host="waleup.com", user="emails", passwd="emails123", db="emails")
		cursor = conn.cursor()
		
		where = "WHERE email.status_id = 0 AND email.web <> '' AND email.email = ''" if idd == 0 else "WHERE email.id = "+idd
		
		sql = "SELECT email.id, email.email, email.web FROM email "+where+" LIMIT 100 OFFSET "+ str(offset)
		cursor.execute(sql)
		
		for link in cursor.fetchall():
			print 'scraping ', link[0], 'url ', link[1]
			scrape(link[0], link[1], link[2])
		
		i+=100
		print 'i is at ', i
			
		conn.commit()
		cursor.close()
		conn.close()


if __name__ == '__main__':
	global offset
	offset = 0 if len(sys.argv) <= 1 else sys.argv[1]
	idd = 0

	get_links(idd)
