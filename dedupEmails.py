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
commit = True
public_emails = [ 'gmail.com', 'yahoo.com', 'googlemail.com', 'live.com', 'aim.com', 'hotmail.com', 'aol.com', 'fastmail.com' ]

def dedup(cnt, email):
	web = email.split('@')[1]
	print 'web', web
	cursor = conn.cursor();
	sql = 'SELECT * FROM email WHERE email=%s'
	cursor.execute(sql, (email))
	
	winning_count = 0
	winning_email_id = 0
	winning_status_id = 0
	winning_biz_id = 0
	for eml in cursor.fetchall():
		id = eml[0]
		name = eml[2]
		status_id = eml[3]
		biz_id = eml[8]
		
		print id, name, status_id, biz_id
		
		count = 0
		words = name.split(' ')
		for word in words:
			if word in web:
				count +=1
				
				
		if status_id > winning_status_id:
			winning_status_id = status_id
			winning_email_id = id
			winning_count = count
			winning_biz_id = biz_id
			continue
		
		
				
		if (count > winning_count) & (status_id >= winning_status_id):
			winning_count = count
			winning_email_id = id
			winning_status_id = status_id
			winning_biz_id = biz_id
	
	print winning_count, winning_status_id, winning_email_id
	
	try:
		cursor.execute('DELETE FROM email WHERE email=%s AND id<>%s', (email, winning_email_id))
		cursor.execute('DELETE FROM uniq_email WHERE email=%s', (email))
		
		if web not in public_emails:
			cursor.execute('UPDATE biz SET web=%s WHERE id=%s', (web, winning_biz_id))
		
		if commit: conn.commit()
	except Exception as e:
		print 'MySQL error', e
		pass
	
	cursor.close()

def get_emails():
	cursor = conn.cursor()
	sql = 'SELECT * FROM uniq_email'
	cursor.execute(sql)
	
	for link in cursor.fetchall():
		print ' ------------------------------------------------- '
		print 'deduping', link[0], link[1]
		dedup(link[0], link[1])

	cursor.close()
	conn.close()

get_emails()