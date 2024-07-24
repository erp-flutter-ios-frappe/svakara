
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
from erpnext.globle import globleUserLogin
import json
import datetime
from frappe.utils import getdate,nowdate
from datetime import timedelta




@frappe.whitelist(allow_guest=True)
def create_user_in_erp(docname):


	response= {}

	query = "SELECT * FROM `tabSatvaras User` WHERE `name`='{}'".format(docname)
	previousentry = frappe.db.sql(query,as_dict=True)

	if len(previousentry)==0:
		return "Order is not there"

	firstName = previousentry[0]['first_name']
	lastName = previousentry[0]['last_name']
	city = previousentry[0]['city']
	pincode = previousentry[0]['pincode']
	phone = previousentry[0]['mobile_number']


	if firstName in ['',None,'None']:
		firstName = ""

	if lastName in ['',None,'None']:
		lastName = ""

	if city in ['',None,'None']:
		city = ""

	if pincode in ['',None,'None']:
		pincode = ""


	response['passfirst_validation']="true"
	try:
		user = frappe.db.get("User", {"name": phone})
		if user:
			response['user_found']="true"
			response["customer_found"]="Yes"
			frappe.db.sql("""UPDATE `tabUser` SET `last_name`='"""+lastName+"""',`location`='"""+city+"""',`bio`='"""+pincode+"""', `first_name`='"""+firstName+"""' WHERE `name`='"""+phone+"""'""")

			customerdetail = frappe.db.get("Customer", {"name": phone})
			if not customerdetail:
				response['customer_not_found']="true"
				frappe.db.sql("""INSERT INTO `tabCustomer` (`name`, `owner`, `docstatus`,  `idx`, `naming_series`, `disabled`, `customer_name`, `territory`, `customer_group`, `customer_type`, `is_frozen`, `custom_city`, `custom_pincode`,`creation`,`modified`) VALUES ('"""+phone+"""', '"""+phone+"""', '0',  '0', 'CUST-', '0', '"""+firstName+""" """+lastName+"""', 'India','Individual', 'Individual', '0', '"""+city+"""', '"""+pincode+"""', '"""+str(frappe.utils.now_datetime())+"""', '"""+str(frappe.utils.now_datetime())+"""')""")
				d = frappe.get_doc({
					"doctype": "DefaultValue",
					"parent": "" + phone,
					"parenttype": "User Permission",
					"parentfield": "system_defaults",
					"defkey": "Customer",
					"defvalue": "" + phone
				})
				d.insert(ignore_permissions=True)
				p = frappe.get_doc({"docstatus":0,"doctype":"User Permission","name":"New User Permission 1","__islocal":1,"__unsaved":1,"owner":"Administrator","apply_for_all_roles":0,"__run_link_triggers":0,"user":"" + phone,"allow":"Customer","for_value":"" + phone})
				p.insert(ignore_permissions=True)

			frappe.db.sql("""UPDATE `tabCustomer` SET `customer_name`='"""+firstName+"""' '"""+lastName+"""',`custom_city`='"""+city+"""',`custom_pincode`='"""+pincode+"""' WHERE `name`='"""+phone+"""'""")
			return AddressCheck(docname,phone)
		else:
			response["user_not_found"]="No"
			frappe.db.sql("""INSERT INTO `tabUser` (`name`, `owner`, `docstatus`, `idx`, `user_type`, `last_name`, `thread_notify`, `first_name`, `login_after`, `email`, `username`, `location`, `bio`,`creation`,`modified`) VALUES ('"""+phone+"""', 'Guest', '0', '0', 'System User', '"""+lastName+"""', '1', '"""+firstName+"""', '0', '"""+phone+"""@example.com', '"""+phone+"""', '"""+city+"""', '"""+pincode+"""', '"""+str(frappe.utils.now_datetime())+"""', '"""+str(frappe.utils.now_datetime())+"""')""")
			frappe.db.sql("""INSERT INTO `tabCustomer` (`name`, `owner`, `docstatus`,  `idx`, `naming_series`, `disabled`, `customer_name`, `territory`, `customer_group`, `customer_type`, `is_frozen`, `custom_city`, `custom_pincode`,`creation`,`modified`) VALUES ('"""+phone+"""', '"""+phone+"""', '0',  '0', 'CUST-', '0', '"""+firstName+""" """+lastName+"""', 'India','Individual', 'Individual', '0', '"""+city+"""', '"""+pincode+"""', '"""+str(frappe.utils.now_datetime())+"""', '"""+str(frappe.utils.now_datetime())+"""')""")

			d = frappe.get_doc({
				"doctype": "DefaultValue",
				"parent": "" + phone,
				"parenttype": "User Permission",
				"parentfield": "system_defaults",
				"defkey": "Customer",
				"defvalue": "" + phone
			})
			d.insert(ignore_permissions=True)
			
			p = frappe.get_doc({"docstatus":0,"doctype":"User Permission","name":"New User Permission 1","__islocal":1,"__unsaved":1,"owner":"Administrator","apply_for_all_roles":0,"__run_link_triggers":0,"user":"" + phone,"allow":"Customer","for_value":"" + phone})
			p.insert(ignore_permissions=True)
		
		frappe.db.commit()
		return AddressCheck(docname,phone)
		response["status"]=200
		response["message"]="customer created"
		return response
	except Exception as e:
		app_error_log("User signup error: {}".format(phone),str(e))
		app_error_log("User signup error traceable: {}".format(phone),str(traceback.format_exc()))
		response["status"]=500
		response["message"]=str(e)
		response["message_trackeable"]=traceback.format_exc()
		return response


@frappe.whitelist(allow_guest=True)
def AddressCheck(docname,customer):


	try:
		reply = {}
		reply['message']=''
		reply['status_code']='200'
		reply['data']=[]

		if not frappe.db.exists('Address', "{}-Billing".format(customer)):
			query = "SELECT * FROM `tabSatvaras User` WHERE `name`='{}'".format(docname)
			previousentry = frappe.db.sql(query,as_dict=True)

			add2 = previousentry[0]['address_line2']

			if len(previousentry)!=0:
				d1=frappe.get_doc({
					"docstatus": 0,
					"doctype": "Address",
					"name": "New Address 1",
					"__islocal": 1,
					"__unsaved": 1,
					"pincode": previousentry[0]['pincode'],
					"address_line1": previousentry[0]['address_line1'],
					"address_line2": add2,
					"city": previousentry[0]['city'],
					"address_title": customer,
					"custom_area": previousentry[0]['area'],
					"state": previousentry[0]['state'],
					"address_type": "Billing",
					"is_primary_address":1,
					"country": "India",
					"is_shipping_address": 1,
					"custom_hideaddress": 0,
				})
				reply['Createddata']=d1
				d2=d1.insert(ignore_permissions=True)
				reply['message']='Address insert'

				d = frappe.get_doc({
					"doctype": "Dynamic Link",
					"link_doctype": "Customer",
					"parent": d2.name,
					"parenttype": "Address",
					"link_name": customer,
					"parentfield": "links",
				})
				d.insert(ignore_permissions=True)
				reply['message']='Address created and link with customer'
		else:
			reply['message']='customer not found'
	
	except Exception as e:
		app_error_log("User signup error: {}".format(customer),str(e))
		app_error_log("User signup error traceable: {}".format(customer),str(traceback.format_exc()))
		reply["status"]=500
		reply["message"]=str(e)
		reply["message_trackeable"]=traceback.format_exc()
		return reply

	return reply


@frappe.whitelist(allow_guest=True)
def findKeys(keysName,keysList,orderDetails):

	if keysName in keysList:
		return orderDetails[keysName]

	return ""


@frappe.whitelist()
def app_error_log(title,error):
	d = frappe.get_doc({
			"doctype": "App Error Log",
			"title":title,
			"error":error
		})
	d = d.insert(ignore_permissions=True)
	return d