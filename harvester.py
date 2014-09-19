from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import NoSuchElementException
from bs4 import BeautifulSoup
import time, re, pymysql, html5lib, random, sys, smtplib, socket
offset=0

def scrape(url, link_id):
	driver = webdriver.Firefox()
	driver.set_window_size(300,500)
	driver.implicitly_wait(1000)
	base_url = "http://www.manta.com"
	final_url = base_url+url
	print final_url
	driver.get(final_url)
	time.sleep(3+random.random()*3)
	#print driver.page_source
	try:
		soup = BeautifulSoup(driver.page_source, 'html5lib')
		region = soup.find('span', {'itemprop': 'addressRegion'})
		if(region):
			name = soup.find('h1', {"itemprop" :"name"})
			address = soup.find('span', {'itemprop': 'streetAddress'})
			city = soup.find('span', {'itemprop': 'addressLocality'})
			zip = soup.find('span', {'itemprop': 'postalCode'})
			phone = soup.find('div', {'itemprop': 'telephone'})
			email = soup.find('div', {'itemprop': 'email'})
			web = soup.find('a', href=re.compile('/urlutils/verify/'))
			
			name = name.a.text
			address = address.text if address else ''
			city = city.text if city else ''
			region = region.text if region else ''
			zip = zip.text if zip else ''
			phone = phone.text.replace('Phone: ', '') if phone else ''
			email = email.text.replace('Email: ', '') if email else ''
			web = web.text.replace('Web: ', '') if web else ''
			
			insert_contact(link_id, name, address, city, region, zip, phone, email, web)
			print 'inserted (',name,',',address,',',city,',',region,',',zip,',',phone,',',email,',',web,')'
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
	except Exception:
		print 'exception'
		#notify('Exception on '+url)
		pass
		
	driver.quit()
	
def insert_contact(link_id, name, address, city, region, zip, phone, email, web):

	try:
		conn = pymysql.connect(host="waleup.com", user="emails", passwd="emails123", db="emails")
		cursor = conn.cursor()
		
		query = "INSERT INTO email (link_id, name, address, city, region, zip, phone, email, web) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)"
		cursor.execute(query, (link_id, name, address, city, region, zip, phone, email, web))
		
		query = "UPDATE link SET is_scraped=1 WHERE id=%s"
		cursor.execute(query, (link_id))
			
		conn.commit()
		
		
		cursor.close()
		conn.close()
	except Exception:
		print 'mysql error'
		#notify('MySQL error')
		pass

def get_links():
	global offset
	i = 0
	print 'offset: ', offset
	while(i < 5000):
		conn = pymysql.connect(host="waleup.com", user="emails", passwd="emails123", db="emails")
		cursor = conn.cursor()
		sql = 'SELECT * FROM link WHERE is_scraped=0 LIMIT 100 OFFSET '+str(offset)
		cursor.execute(sql)
		
		for link in cursor.fetchall():
			print 'scraping ', link[0], 'url ', link[1]
			scrape(link[1], int(link[0]))
		
		i+=100
		print 'i is at ', i
			
		conn.commit()
		cursor.close()
		conn.close()
	
if __name__ == "__main__":
    global offset
    if(len(sys.argv) > 1):
    	offset = int(sys.argv[1])
    	
    get_links()
    
