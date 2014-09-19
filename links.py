from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import NoSuchElementException
from bs4 import BeautifulSoup
from bs4.element import Tag
import time, re, pymysql, html5lib, random, smtplib, socket, sys
i=1


def scrape_links(driver):
	global i
	profile_urls = []
	time.sleep(1+random.random()*2)

	soup = BeautifulSoup(driver.page_source, 'html5lib')
	for li in soup.find_all("li", 'organic-result'):
		anchor = li.find('a', 'pull-left')
		#print('found '+anchor['href'])
		profile_urls.append(anchor['href'])
	
	
	a = soup.find("a", {'rel': 'next'})
	if (a):
		i += 1	
		element = driver.find_element_by_link_text(str(i))
		element.click()
		profile_urls += scrape_links(driver)
	else:
		print 'stopped on page ', i
		check_bot(driver)

		
	return profile_urls

def check_bot(driver):
	print driver.title
	if 'Suspicious' in driver.title:
		try:
			print 'bot page'
			driver.delete_all_cookies()
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
		except Exception:
			print 'not that bot page'



def get_to(driver, i):
	try:
		base_url = "http://www.manta.com"
		driver.get(base_url)
		
		time.sleep(5+random.random()*5)
		
		driver.set_window_size(400+random.randint(1, 100),600)
		time.sleep(1)
		driver.find_element_by_link_text("Printing & Publishing").click()
		time.sleep(3+random.random()*12)
	
		#get to the state
		driver.find_element_by_link_text(i).click()
		#driver.find_element_by_xpath("//html[@id='ng-app']/body/div[4]/div[2]/div[2]/div/div[4]/div/div/ul/li["+str(i)+"]/a/span/strong").click()
		time.sleep(2)
	except Exception:
			print 'getting there didnt work'
			pass
		

def finalize(urls, abbr):
	global i
	#print urls
		
	conn = pymysql.connect(host="waleup.com", user="emails", passwd="emails123", db="emails")
	cursor = conn.cursor()
	for url in urls:
		query = "INSERT INTO link (link, state, category) VALUES (%s, '"+abbr+"', 'Publishing')"
		cursor.execute(query, (url))
	conn.commit()
	cursor.close()
	conn.close()
	i = 1
	print 'inserted ', len(urls), ' links in the database'

def start():
	global i
	
	states3 = [{'id': 1, 'code': 'OK'}, {'id': 2, 'code': 'OR' }, {'id': 3, 'code': 'PA'}, {'id': 4, 'code': 'PR'}, {'id': 5, 'code': 'RI'}, {'id': 6, 'code': 'SC'}, {'id': 7, 'code': 'SD'},
	{'id': 8, 'code': 'TN'}, {'id': 9, 'code': 'TX'}, {'id': 10, 'code': 'UT'}, {'id': 11, 'code': 'VT'},
	{'id': 12, 'code': 'VI'}, {'id': 13, 'code': 'VA'}, {'id': 14, 'code': 'WA'}, {'id': 15, 'code': 'WV'},
	{'id': 16, 'code': 'WI'}, {'id': 17, 'code': 'WI'}]
	states1 = [{'id': 4, 'code': 'AR'}, {'id': 5, 'code': 'CA'}, {'id': 6, 'code': 'CO'}, {'id': 7, 'code': 'CT'}, {'id': 8, 'code': 'DE'}, {'id': 9, 'code': 'DC'}, {'id': 10, 'code': 'FL'},
	{'id': 11, 'code': 'GA'}, {'id': 12, 'code': 'HI'}, {'id': 13, 'code': 'ID'}, {'id': 14, 'code': 'IL'}, {'id': 15, 'code': 'IN'}, {'id': 16, 'code': 'IA'}, {'id': 17, 'code': 'KS'}, {'id': 18, 'code': 'KY'}]
	
	states = [{'id': 'Texas', 'code': 'TX'}]

	
	for state in states:
		driver = webdriver.Chrome('/Users/waleup/Downloads/chromedriver')
		driver.implicitly_wait(1000)
		
		
		i = 1
		stateId = state['id']
		stateCd = state['code']
		print 'state ', stateId, ' ', stateCd
		get_to(driver, stateId)
		soup = BeautifulSoup(driver.page_source, 'html5lib')
		a = soup.find("a", {'rel': 'next'})
		if(a):
			urls = scrape_links(driver)
			finalize(urls, stateCd)
		else:
			lst = []
			lst += soup.find("ul","geo-list-left").children
			lst += soup.find("ul","geo-list-center").children
			lst += soup.find("ul","geo-list-right").children
			for item in reversed(lst):
				if(isinstance(item, Tag)):
					href = item.a.get('href')
					if(href):
						try:
							href = 'http://www.manta.com'+href
							driver.get(href)
							urls = scrape_links(driver)
							finalize(urls, stateCd)
							get_to(driver, stateId)
						except Exception:
							print 'exception'
							check_bot(driver)
							pass						
			
		driver.quit()
		
	
	
if __name__ == "__main__":
    start()
