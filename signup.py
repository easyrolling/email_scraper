# -*- coding: utf-8 -*-
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import NoAlertPresentException
from email.mime.text import MIMEText
import unittest, time, re, pymysql, ConfigParser, os, smtplib, socket


class Signup(unittest.TestCase):
    conn = None
    config = None
    commit = True
    def setUp(self):
        self.driver = webdriver.Firefox()
        self.driver.implicitly_wait(30)
        self.base_url = "http://appredy.com/"
        self.verificationErrors = []
        self.accept_next_alert = True

	dirname = os.path.dirname(os.path.realpath(__file__))
	self.config = ConfigParser.ConfigParser()
	self.config.read(dirname+'/config.ini')
	self.conn = pymysql.connect(host=self.config.get('prod_db', 'host'), user=self.config.get('prod_db', 'user'), passwd=self.config.get('prod_db', 'passwd'), db=self.config.get('prod_db', 'db'))

    
    def notify(self, message):
	fromaddr = 'AppRedy Support <support@appredy.com>'
	toaddr = 'pasha@waleup.com'
	msg = """From: AppRedy Support <support@appredy.com>
To: pasha@waleup.com
Subject: Signup Test Failed

Signup Test Failed, please test manually
"""
	
	server = smtplib.SMTP('smtp.gmail.com:587')
	#server.set_debuglevel(1)
	server.starttls()
	server.login('support@waleup.com', 'nickelpen622')	
	server.sendmail(fromaddr, toaddr, msg)
	server.quit()

    def test_signup(self):
        driver = self.driver
        driver.get(self.base_url)
        driver.find_element_by_id("sf_guard_user_company_name").clear()
        driver.find_element_by_id("sf_guard_user_company_name").send_keys("TestApp01")
        driver.find_element_by_id("sf_guard_user_username").clear()
        driver.find_element_by_id("sf_guard_user_username").send_keys("TestApp01@yopmail.com")
        driver.find_element_by_id("sf_guard_user_password").clear()
        driver.find_element_by_id("sf_guard_user_password").send_keys("nickel6")
        driver.find_element_by_id("sf_guard_user_password2").clear()
        driver.find_element_by_id("sf_guard_user_password2").send_keys("nickel6")
        driver.find_element_by_id("sf_guard_user_company_phone").clear()
        driver.find_element_by_id("sf_guard_user_company_phone").send_keys("2125146728")
        driver.find_element_by_name("sf_guard_user[terms]").click()
        driver.find_element_by_name("submit").click()

	if(self.is_element_present(By.CLASS_NAME, 'used')):
		print 'Test Succeeded'
	else:
		print 'Test Failed'
		self.notify('Signup Test Failed')

    
    def is_element_present(self, how, what):
        try: self.driver.find_element(by=how, value=what)
        except NoSuchElementException, e: return False
        return True
    
    def is_alert_present(self):
        try: self.driver.switch_to_alert()
        except NoAlertPresentException, e: return False
        return True
    
    def close_alert_and_get_its_text(self):
        try:
            alert = self.driver.switch_to_alert()
            alert_text = alert.text
            if self.accept_next_alert:
                alert.accept()
            else:
                alert.dismiss()
            return alert_text
        finally: self.accept_next_alert = True
    
    def tearDown(self):
		#print self.driver.find_element_by_class_name('used')
        self.driver.quit()
        self.assertEqual([], self.verificationErrors)
	self.removeapp()
    
    def removeapp(self):
	cursor = self.conn.cursor()
	query = 'SELECT id, sf_guard_user_id FROM app WHERE name=%s'
	cursor.execute(query, ('testapp01'))

	app = cursor.fetchone()
	if(app):
		app_id = app[0]
		user_id = app[1]
		print app_id, user_id
		query = 'DELETE FROM about WHERE app_id=%s'
		#print query
		cursor.execute(query, (app_id))

		query = 'DELETE FROM app WHERE id=%s'
		#print query
		cursor.execute(query, (app_id))

		query = 'DELETE FROM sf_guard_user WHERE id=%s'
		#print query
		cursor.execute(query, (user_id))

		query = 'DELETE FROM lead WHERE email=%s'
		cursor.execute(query, ('TestApp01@yopmail.com'))

		if (self.commit): self.conn.commit()
		cursor.close()


if __name__ == "__main__":
    unittest.main()
