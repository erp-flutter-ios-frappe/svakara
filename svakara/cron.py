from __future__ import unicode_literals
import frappe
from frappe import throw, msgprint, _
import frappe.permissions
import traceback
import string
import random
from frappe.utils.password import update_password as _update_password
from frappe.core.doctype.communication.email import make
import requests
from frappe.auth import LoginManager, CookieManager
from svakara.globle import defaultResponseBody,globleLoginUser,appErrorLog
import json
import datetime
from frappe.utils import getdate,nowdate
from datetime import timedelta
from svakara.account_utils import GetBalance
from frappe.contacts.doctype.address.address import get_address_display




@frappe.whitelist(allow_guest=True)
def customer_detail_cron():
	query_so = "SELECT name FROM `tabCustomer` WHERE `disabled`='0'"
	customerList = frappe.db.sql(query_so,as_dict=1)
	for cust in customerList:
		frappe.enqueue(customerDetailUpdate,queue='long',job_name="Customer detail update: {}".format(cust['name']),timeout=100000,customer=cust['name'])

	frappe.enqueue(commitDatabase,queue='long',job_name="Commit database",timeout=100000)
	return 'Cron start'


@frappe.whitelist(allow_guest=True)
def commitDatabase():
	frappe.db.commit()
	return True

@frappe.whitelist(allow_guest=True)
def customerDetailUpdate(customer):
	
	reply=defaultResponseBody()
	reply["data"]={}

	sessionuser = frappe.session.user
	frappe.set_user(globleLoginUser())

	try:

		query_so = "SELECT * FROM `tabCustomer` WHERE `name`='{}'".format(customer)
		customerList = frappe.db.sql(query_so,as_dict=1)

		if len(customerList)==0:
			return

		customerDetail = customerList[0]

		# customerObject = frappe.get_doc("Customer",customerDetail['name'])


		balance=GetBalance(customerDetail['name'])
		update_query = "UPDATE `tabCustomer` SET `custom_balance`= '{}' WHERE `name`='{}'".format(balance,customerDetail['name'])
		test = frappe.db.sql(update_query)
		# frappe.db.commit()
		# appErrorLog('b',update_query)
		reply["balance"]=balance
		# frappe.db.set_value("Customer", customerDetail['name'], "custom_balance", balance)

		# customerObject.custom_balance = balance

		# address_list=frappe.db.sql("""SELECT `tabAddress`.name FROM `tabAddress` inner join `tabDynamic Link` on `tabAddress`.name=`tabDynamic Link`.parent WHERE `tabDynamic Link`.link_name=%s AND `tabDynamic Link`.link_doctype='Customer' AND `tabDynamic Link`.parenttype='Address' AND `tabAddress`.disabled=0""",customerDetail['name'])
		
		query = "SELECT addr.name,addr.is_primary_address FROM `tabAddress` AS addr INNER JOIN `tabDynamic Link` AS dnl ON addr.name=dnl.parent WHERE dnl.link_name='{}' AND dnl.link_doctype='Customer' AND dnl.parenttype='Address' AND addr.disabled=0".format(customerDetail['name'])		
		address_list = frappe.db.sql(query,as_dict=1)
		
		last_user_address = ""
		for add in address_list:
			if last_user_address=="":
				last_user_address = add['name']

			if str(add['is_primary_address'])=="1":
				last_user_address = add['name']

		reply["is_primary_address"]=last_user_address

		if last_user_address != customerDetail['customer_primary_address']:

			address_display = get_address_display(address_dict=last_user_address)
			reply["address_display"]=address_display
			primayAddress = address_display.replace("<br>\n<br>\n", "<br>")
			primayAddress = primayAddress.replace("<br>\n", "<br>")
			primayAddress = primayAddress.replace("\n\n", "\n")
			primayAddress = primayAddress.replace("<br><br>", "<br>")
			update_query = "UPDATE `tabCustomer` SET `primary_address`='{}', `customer_primary_address`='{}' WHERE `name`='{}'".format(primayAddress,last_user_address,customerDetail['name'])
			test = frappe.db.sql(update_query)

			# customerObject.primary_address = primayAddress
			# customerObject.customer_primary_address = last_user_address
			# frappe.db.set_value("Customer", customerDetail['name'], "primary_address", primayAddress)
			# frappe.db.set_value("Customer", customerDetail['name'], "customer_primary_address", last_user_address)


			frappe.db.sql("""UPDATE `tabAddress` SET `custom_last_use_address`=1, `is_primary_address`=1 WHERE `name`='"""+last_user_address+"""' """)
			# frappe.db.commit()


		#Contact
		query = "SELECT addr.name FROM `tabContact` AS addr INNER JOIN `tabDynamic Link` AS dnl ON addr.name=dnl.parent WHERE dnl.link_name='{}' AND dnl.link_doctype='Customer' AND dnl.parenttype='Contact'".format(customerDetail['name'])		
		address_list = frappe.db.sql(query,as_dict=1)
		
		last_user_contact = ""
		last_user_phone = ""
		for add in address_list:
			query = "SELECT * FROM `tabContact Phone` WHERE `parent`='{}'".format(add['name'])
			contactlist_list = frappe.db.sql(query,as_dict=1)
			for contect in contactlist_list:
				if last_user_contact=="":
					last_user_contact = contect['parent']
					last_user_phone = contect['phone']

				if str(contect['is_primary_phone'])=="1":
					last_user_contact = contect['parent']
					last_user_phone = contect['phone']

		reply["customer_primary_contact"]=last_user_contact

		if last_user_contact != customerDetail['customer_primary_contact']:
			
			update_query = "UPDATE `tabCustomer` SET `mobile_no`='{}', `customer_primary_contact`='{}' WHERE `name`='{}'".format(last_user_phone,last_user_contact,customerDetail['name'])
			test = frappe.db.sql(update_query)
			# customerObject.mobile_no = last_user_phone
			# customerObject.customer_primary_contact = last_user_contact
			# frappe.db.set_value("Customer", customerDetail['name'], "mobile_no", last_user_phone)
			# frappe.db.set_value("Customer", customerDetail['name'], "customer_primary_contact", last_user_contact)

			

		# customerObject.save()
		# customerObject.save(ignore_permissions=True)
		reply["status_code"]="200"
		reply["message"]="Customer detail updated."

	except Exception as e:
		frappe.local.response['http_status_code'] = 500
		reply["status_code"]="500"
		reply["message"]=str(e)
		reply["message_error"]=str(e)
		reply["message_traceable"] = str(traceback.format_exc())
		reply["data"]={}
		

	frappe.set_user(sessionuser)
	# frappe.db.commit()
	return reply



# 