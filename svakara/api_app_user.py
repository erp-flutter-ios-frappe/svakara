
from __future__ import unicode_literals
import frappe
from frappe import throw, msgprint, _
import frappe.permissions
import string
import random
from frappe.utils.password import update_password as _update_password
from frappe.utils import add_days,nowdate
from frappe.core.doctype.communication.email import make
from svakara.globle import appErrorLog,defaultResponseBody,defaultResponseErrorBody
import traceback
from svakara.cron import customerDetailUpdate


#Use in app
@frappe.whitelist(allow_guest=True)
def getDefaultValue():

	response= {}
	response["dashboard"]=frappe.db.sql("""Select * from `tabDashboard images`""",as_dict=True)
	# response["offer"]=frappe.get_all('offer', filters=[["offer","end_date",">=",nowdate()],["offer","start_date","<=",nowdate()]], fields=['*'])
	response["offer"]=[]
	response["filters"]=frappe.db.sql("""SELECT * from `tabItem Category`""",as_dict=True)
	response["settings"]=frappe.get_all('application setting', filters=[["application setting","title","=",'Svakara']], fields=['*'])
	response["images"]=frappe.get_all('App Images', fields=['*'])
	response["productinformation"]=frappe.get_all('Product Information', fields=['*'])
	response["ERPDateTime"] = frappe.utils.data.get_datetime()
	currenttime=frappe.utils.data.nowtime()
	x = currenttime.split(":")
	days=0
	#server is 1 hour behind
	if int(x[0])>=23:
		days=1

	days=1

	response["ERPTime"] = x[0]
	response["ERPMinimum"] = add_days(frappe.utils.data.get_datetime(),days)
	response["ItemChangeDateTime"] = frappe.db.sql("""select max(modified) from tabItem where  item_group = 'Products'""")[0][0]
	response["deliveryTimeSlot"]=frappe.db.sql("""Select * from `tabTime` order by sort""",as_dict=True)

	return response

#Use in app
@frappe.whitelist(allow_guest=True)
def get_version_detail(allow_guest=True):

	reply=defaultResponseBody()
	reply['data']={}

	try:
		data1=frappe.db.sql("""select * from `tabapplication setting` where title='Svakara'""",as_dict=True)
		if len(data1)!=0:
			reply['data']= data1[0]
	except Exception as e:
		frappe.local.response['http_status_code'] = 500
		reply = defaultResponseErrorBody(reply,str(e),str(traceback.format_exc()),'api_app_user','get_version_detail')

	return reply

#Use in app
@frappe.whitelist(allow_guest=True)
def save_user_setting(platform,osversion,appversion,device_name,token,phone):

	reply=defaultResponseBody()
	reply['data']={}

	try:
		query2="SELECT name FROM `tabUser Settings` WHERE `name`='{}' OR `customer`='{}'".format(str(phone),str(phone))
		user_setting = frappe.db.sql(query2,as_dict=1)

		if len(user_setting)!=0:
			query = "UPDATE `tabUser Settings` SET `platform`='{}', `os_version`='{}', `app_version`='{}', `device_name`='{}', `token`='{}' WHERE `name`='{}'".format(str(platform),str(osversion),str(appversion),str(device_name),token,user_setting[0]['name'])
			test = frappe.db.sql(query)
			return get_version_detail()
		else:
			d2 = frappe.get_doc({
						"docstatus": 0,
						"doctype": "User Settings",	
						"name": "New User Setting 1",
						"__islocal": 1,
						"__unsaved": 1,
						"owner":str(phone),
						"user": str(phone),
						"customer":str(phone),
						"platform": str(platform),
						"os_version": str(osversion),
						"app_version": str(appversion),
						"device_name": str(device_name),
						"token":str(token)
					   })
			result=d2.insert(ignore_permissions=True)
			if result:
				return get_version_detail()

	except Exception as e:
		frappe.local.response['http_status_code'] = 500
		reply = defaultResponseErrorBody(reply,str(e),str(traceback.format_exc()),'api_app_user','save_user_setting')

	return reply

#Use in app
@frappe.whitelist(allow_guest=True) 
def getProfile(phone):
	
	reply=reply=defaultResponseBody()
	reply["data"]=[]
	reply["addresses"]=[]
	reply['customer']={}
	reply['user']={}
	reply['distributor']={}
	reply['delivery']={}
	reply['employee']={}
	reply['subscription'] = []
	reply['pages'] = []

	try:

		is_distributor = False
		dil_query = "SELECT * from `tabDelivery Team` WHERE `mobile`='{}' AND `disable`=0".format(phone)
		dil_list =frappe.db.sql(dil_query,as_dict=True)
		if len(dil_list)!=0:
			reply['delivery'] = dil_list[0]
			if dil_list[0]['employee'] not in ['',None,'null']:
				emp_query = "SELECT * from `tabEmployee` WHERE `name`='{}' AND `status`='Active'".format(dil_list[0]['employee'])
				emp_list =frappe.db.sql(emp_query,as_dict=True)
				if len(emp_list)!=0:
					reply['employee'] = emp_list[0]


			dis_query = "SELECT * from `tabDistributor` WHERE `mobile`='{}' AND `disable`=0".format(phone)
			dis_list =frappe.db.sql(dis_query,as_dict=True)
			if len(dis_list)!=0:
				reply['distributor'] = dis_list[0]
				is_distributor = True

		CustomerName = ""

		if is_distributor:
			customer_query = "SELECT * from `tabCustomer` WHERE `name`='{}'".format(dis_list[0]['customer'])
			customer_list =frappe.db.sql(customer_query,as_dict=True)
			if len(customer_list)!=0:
				reply['customer'] = customer_list[0]
				CustomerName = customer_list[0]['name']

			user_query = "SELECT * from `tabUser` WHERE `name`='{}'".format(dis_list[0]['user'])
			user_list =frappe.db.sql(user_query,as_dict=True)
			if len(user_list)!=0:
				reply['user'] = user_list[0]

		else:
			customer_query = "SELECT * from `tabCustomer` WHERE `name`='{}'".format(phone)
			customer_list =frappe.db.sql(customer_query,as_dict=True)
			if len(customer_list)!=0:
				reply['customer'] = customer_list[0]
				CustomerName = customer_list[0]['name']

			user_query = "SELECT * from `tabUser` WHERE `name`='{}'".format(phone)
			user_list =frappe.db.sql(user_query,as_dict=True)
			if len(user_list)!=0:
				reply['user'] = user_list[0]

		filters = [
			["Dynamic Link", "link_doctype", "=", "Customer"],
			["Dynamic Link", "link_name", "=", phone],
			["Address", "custom_hideaddress", "!=", 1]
		]
		address_list = frappe.get_all("Address", filters=filters, fields=['*'])
		reply["data"]=address_list
		reply["addresses"]=address_list
		
		query_subscription = "SELECT * from `tabSubscription Item` WHERE `customer`='{}' AND `disable`='0'".format(phone)
		reply['subscription'] = frappe.db.sql(query_subscription,as_dict=True)

		pages_query = "SELECT * FROM `tabStaff Page Permission Child` WHERE `parent`='{}'".format(CustomerName)
		reply['pages'] =frappe.db.sql(pages_query,as_dict=True)

		return reply

	except Exception as e:
		frappe.local.response['http_status_code'] = 500
		reply = defaultResponseErrorBody(reply,str(e),str(traceback.format_exc()),'api_app_user','getProfile')

	return reply

#Use in app
@frappe.whitelist(allow_guest=True)
def userDetail(name):

	reply=defaultResponseBody()

	try:	
		userobj=frappe.db.get("User", {"name": name})	
		if userobj:
			reply["status_code"]=200
			reply["message"]="data found"
			reply["data"]=userobj
			return reply 
		else:
			reply["status_code"]=200
			reply["message"]="data not found"

	except Exception as e:
		frappe.local.response['http_status_code'] = 500
		reply = defaultResponseErrorBody(reply,str(e),str(traceback.format_exc()),'api_app_user','userDetail')

	return reply

#Use in app
@frappe.whitelist(allow_guest=True)
def profileupdate(address1,address2,pincode,area,city,state,name,isprimary,phone):
	
	reply=defaultResponseBody()
	try:
		if len(name) == 0 :
			d = frappe.get_doc({
					"doctype":"Address",
					"customer": phone,
					"address_line1":address1,
					"address_line2":'{}'.format(address2),
					"custom_area":area,
					"city":city,
					"state":state,
					"pincode":pincode,
					"docstatus":0,
					"custom_last_use_address": isprimary,
					"links": [{"link_doctype":"Customer","doctype":"Dynamic Link","idx":1,"parenttype":"Address","link_name":phone,"docstatus":0,"parentfield":"links"}]
					})
			d.insert(ignore_permissions=True)
			reply['message']="Address added sucessfully"
			reply['name']=d.name
			return reply
		else:
			query = "UPDATE `tabAddress` SET `address_line1`='{}', `address_line2`='{}', `custom_area`='{}', `city`='{}', `state`='{}', `pincode`='{}', `custom_last_use_address`='{}' WHERE `name`='{}'".format(address1,address2,area,city,state,pincode,isprimary,name)
			test = frappe.db.sql(query)

			# doc=frappe.get_doc("Address",name)
			# d = frappe.get_doc({
			# 		"doctype":"Address",
			# 		"name":name,
			# 		"customer": ""+frappe.session.user,
			# 		"address_line1":address1,
			# 		"address_line2":address2,
			# 		"area":area,
			# 		"city":city,
			# 		"state":state,
			# 		"pincode":pincode,
			# 		"docstatus":0,
			# 		"customer_name": ""+fname+" "+lname+"",
			# 		"custom_last_use_address": isprimary,
			# 		"links": [{"link_doctype":"Customer","doctype":"Dynamic Link","idx":1,"parenttype":"Address","link_name":""+frappe.session.user,"docstatus":0,"parentfield":"links"}],
			# 		"modified":doc.modified,
			# 		"country":doc.country,
			# 		"address_type":doc.address_type
			# 		})
			# d.save(ignore_permissions=True)
			# return d
			reply['message']="Address update sucessfully"
			reply['name']=name
			return reply
	except Exception as e:
		frappe.local.response['http_status_code'] = 500
		reply = defaultResponseErrorBody(reply,str(e),str(traceback.format_exc()),'api_app_user','profileupdate')

	return reply

@frappe.whitelist() 
def deleteAddress(name):
	
	reply=defaultResponseBody()
	try:
		frappe.db.sql("""DELETE FROM tabAddress WHERE name= '""" + name +"""'  """)
		return True
	except Exception as e:
		frappe.local.response['http_status_code'] = 500
		reply = defaultResponseErrorBody(reply,str(e),str(traceback.format_exc()),'api_app_user','deleteAddress')

	return reply

@frappe.whitelist(allow_guest=True)
def hideAddress(addressID):

	response={}
	frappe.db.sql("""UPDATE `tabAddress` SET `custom_hideaddress` = 1, `disabled`=1 WHERE `name`='"""+addressID+"""'  """)
	frappe.db.commit()
	frappe.local.response['http_status_code'] = 200
	response["status"]=str(200)
	response["status_message"]='DELETED'
	response["message"]="Delete Sucessfully"
	return response

@frappe.whitelist(allow_guest=True)
def setPrimaryAddress(name,phone): 

	reply=defaultResponseBody()

	try:
		filters = [
			["Dynamic Link", "link_doctype", "=", "Customer"],
			["Dynamic Link", "link_name", "=", phone]
		]
		address = frappe.get_all("Address", filters=filters, fields=['*'])

		for addressname in address:
			if addressname["name"] == name:
				frappe.db.sql("""UPDATE `tabAddress` SET `custom_last_use_address`=1, `is_primary_address`=1 WHERE `name`='"""+addressname["name"]+"""' """)
			else:
				frappe.db.sql("""UPDATE `tabAddress` SET `custom_last_use_address`=0, `is_primary_address`=0 WHERE `name`='"""+addressname["name"]+"""' """)



		frappe.enqueue(customerDetailUpdate,queue='long',job_name="Customer detail update: {}".format(customer),timeout=100000,customer=customer)
		# addressreturn = frappe.get_all("Address", filters=filters, fields=['*'])
		reply['data']=[]

	except Exception as e:
		frappe.local.response['http_status_code'] = 500
		reply["status_code"]="500"
		reply["message"]=str(e)
		reply["message_traceback"]=traceback.format_exc()
	
	return reply






@frappe.whitelist(allow_guest=True)
def setPrimaryAddressNew(addressName,customer): 

	reply=defaultResponseBody()

	try:
		filters = [
			["Dynamic Link", "link_doctype", "=", "Customer"],
			["Dynamic Link", "link_name", "=", customer]
		]
		address = frappe.get_all("Address", filters=filters, fields=['*'])

		for addressname in address:
			if addressname["name"] == addressName:
				frappe.db.sql("""UPDATE `tabAddress` SET `custom_last_use_address`=1, `is_primary_address`=1 WHERE `name`='"""+addressname["name"]+"""' """)
			else:
				frappe.db.sql("""UPDATE `tabAddress` SET `custom_last_use_address`=0, `is_primary_address`=0 WHERE `name`='"""+addressname["name"]+"""' """)



		frappe.enqueue(customerDetailUpdate,queue='long',job_name="Customer detail update: {}".format(customer),timeout=100000,customer=customer)
		# addressreturn = frappe.get_all("Address", filters=filters, fields=['*'])
		reply['data']=[]

	except Exception as e:
		frappe.local.response['http_status_code'] = 500
		reply["status_code"]="500"
		reply["message"]=str(e)
		reply["message_traceback"]=traceback.format_exc()
	
	return reply



@frappe.whitelist(allow_guest=True)
def setPrimaryContact(phone,customer): 

	reply=defaultResponseBody()

	try:
		filters = [
			["Dynamic Link", "link_doctype", "=", "Customer"],
			["Dynamic Link", "link_name", "=", customer]
		]
		address = frappe.get_all("Contact", filters=filters, fields=['*'])
		for addressParent in address:

			addressInner = frappe.get_all("Contact Phone", filters=[["Contact Phone", "parent", "=", addressParent["name"]]], fields=['*'])

			for addressChild in addressInner:

				if addressChild["phone"] == phone:
					frappe.db.sql("""UPDATE `tabContact Phone` SET `is_primary_phone`=1, `is_primary_mobile_no`=1 WHERE `name`='"""+addressChild["name"]+"""' AND `phone`='"""+addressChild["phone"]+"""' """)
				else:
					frappe.db.sql("""UPDATE `tabContact Phone` SET `is_primary_phone`=0, `is_primary_mobile_no`=0 WHERE `name`='"""+addressChild["name"]+"""' AND `phone`='"""+addressChild["phone"]+"""' """)

		customerDetailUpdate(customer=customer)

	except Exception as e:
		frappe.local.response['http_status_code'] = 500
		reply["status_code"]="500"
		reply["message"]=str(e)
		reply["message_traceback"]=traceback.format_exc()
	
	return reply


@frappe.whitelist(allow_guest=True)
def ContactDelete(phone,customer):

	reply=defaultResponseBody()
	filters = [
		["Dynamic Link", "link_doctype", "=", "Customer"],
		["Dynamic Link", "link_name", "=", customer]
	]
	address = frappe.get_all("Contact", filters=filters, fields=['*'])

	for addressParent in address:
		addressInner = frappe.get_all("Contact Phone", filters=[["Contact Phone", "parent", "=", addressParent["name"]]], fields=['*'])
		for addressChild in addressInner:
			if addressChild["phone"] == phone:
				frappe.db.sql("""DELETE FROM `tabContact Phone` WHERE `phone`='"""+addressChild["phone"]+"""' AND `parent`='"""+addressChild["parent"]+"""' """)

	reply['message']="Delete contact"
	return reply


@frappe.whitelist(allow_guest=True)
def ContactAddNew(phone,customer): 

	reply=defaultResponseBody()

	try:
		filters = [
			["Dynamic Link", "link_doctype", "=", "Customer"],
			["Dynamic Link", "link_name", "=", customer]
		]
		address = frappe.get_all("Contact", filters=filters, fields=['*'])

		#Is there is no contact create for customer then create it first
		if len(address)==0:
			customer = frappe.get_doc("Customer", customer)
			first_name = ""
			last_name = ""
			full_name = str(customer.customer_name).split(' ')

			first_name = full_name[0]
			if len(full_name)>=2:
				last_name = full_name[1]


			d = frappe.get_doc({
					"doctype":"Contact",
					"customer": phone,
					"first_name":first_name,
					"last_name":last_name,
					"docstatus":0,
					"links": [{"link_doctype":"Customer","doctype":"Dynamic Link","idx":1,"parenttype":"Contact","link_name":customer.name,"docstatus":0,"parentfield":"links"}]
				})
			contactDocument = d.insert(ignore_permissions=True)
			frappe.db.commit()


		#Get all contact for the customer
		contactLst = frappe.get_all("Contact", filters=filters, fields=['*'])

		if len(contactLst)==0:
			reply['message']="No contact forund for the customer"
			frappe.local.response['http_status_code'] = 500
			reply["status_code"]="500"
			return reply

		foundNumber = False
		for addressParent in contactLst:
			addressInner = frappe.get_all("Contact Phone", filters=[["Contact Phone", "parent", "=", addressParent["name"]]], fields=['*'])
			for addressChild in addressInner:
				if addressChild["phone"] == phone:
					foundNumber = True
					frappe.db.sql("""UPDATE `tabContact Phone` SET `is_primary_phone`=1, `is_primary_mobile_no`=1 WHERE `name`='"""+addressChild["name"]+"""' AND `phone`='"""+addressChild["phone"]+"""' """)
				else:
					frappe.db.sql("""UPDATE `tabContact Phone` SET `is_primary_phone`=0, `is_primary_mobile_no`=0 WHERE `name`='"""+addressChild["name"]+"""' AND `phone`='"""+addressChild["phone"]+"""' """)


		if not foundNumber:
			contact = frappe.get_doc("Contact",contactLst[0]['name'])

			child = frappe.new_doc("Contact Phone")
			child.update({'phone': phone,
			'is_primary_phone': 1,
			'is_primary_mobile_no': 1,
			'parent': contact.name,
			'parenttype': 'Contact',
			'parentfield': 'phone_nos'})
			contact.phone_nos.append(child)
			contact.save(ignore_permissions=True)
			frappe.db.commit()


		frappe.enqueue(customerDetailUpdate,queue='long',job_name="Customer detail update: {}".format(customer),timeout=100000,customer=customer)
		reply["message"]='Contact add sucessfully'

	except Exception as e:
		frappe.local.response['http_status_code'] = 500
		reply["status_code"]="500"
		reply["message"]=str(e)
		reply["message_traceback"]=traceback.format_exc()
	
	return reply


@frappe.whitelist(allow_guest=True) 
def set_vacation_mode(**kwargs): 

	parameters=frappe._dict(kwargs)
	allParamKeys = parameters.keys()

	reply=defaultResponseBody()

	try:
		query = "UPDATE `tabCustomer` SET `custom_vacation_mode`={} WHERE `name`='{}'".format(parameters['vacation_mode'],parameters['customer'])
		op=frappe.db.sql(query)
	except Exception as e:
		frappe.local.response['http_status_code'] = 500
		reply = defaultResponseErrorBody(reply,str(e),str(traceback.format_exc()),'api_app_user','set_vacation_mode')

	return reply


def id_generator(size):
   return ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(size))

@frappe.whitelist(allow_guest=True)
def UserSignUpUpdate(phoneNo,firstName,lastName,city,pincode):
	response= {}
	try:
		otpobj=frappe.db.get("UserOTP", {"mobile": phoneNo})
		user = frappe.db.get("User", {"name": phoneNo})
 
		if user:			
			frappe.db.sql("""UPDATE `tabUser` SET `last_name`='"""+lastName+"""',`location`='"""+city+"""',`bio`='"""+pincode+"""', `first_name`='"""+firstName+"""' WHERE `name`='"""+phoneNo+"""'""")
			customerName = "{} {}".format(firstName,lastName)
			frappe.db.sql("""UPDATE `tabCustomer` SET `customer_name`='"""+customerName+"""',`custom_city`='"""+city+"""',`custom_pincode`='"""+pincode+"""' WHERE `name`='"""+phoneNo+"""'""")
		else:		
			frappe.db.sql("""INSERT INTO `tabUser` (`name`, `owner`, `docstatus`, `idx`, `user_type`, `last_name`, `thread_notify`, `first_name`, `login_after`, `email`, `username`, `location`, `bio`) VALUES ('"""+phoneNo+"""', 'Guest', '0', '0', 'Website User', '"""+lastName+"""', '1', '"""+firstName+"""', '0', '"""+phoneNo+"""@example.com', '"""+phoneNo+"""', '"""+city+"""', '"""+pincode+"""')""")
			
			#frappe.db.sql("""INSERT INTO `tabUserRole` (`name`, `creation`, `modified`, `modified_by`, `owner`, `docstatus`, `parent`, `parentfield`, `parenttype`, `idx`, `role`) VALUES ('"""+id_generator(10)+"""', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, '"""+phoneNo+"""', '"""+phoneNo+"""', '0', '"""+phoneNo+"""', 'user_roles', 'User', '1', 'Customer')""")
			#frappe.db.sql("""INSERT INTO `tabHas Role` (`name`, `creation`, `modified`, `modified_by`, `owner`, `docstatus`, `parent`, `parentfield`, `parenttype`, `idx`, `role`) VALUES ('"""+id_generator(10)+"""', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, '"""+phoneNo+"""', '"""+phoneNo+"""', '0', '"""+phoneNo+"""', 'roles', 'User', '1', 'Customer')""")
			customerName = "{} {}".format(firstName,lastName)
			frappe.db.sql("""INSERT INTO `tabCustomer` (`name`, `owner`, `docstatus`,  `idx`, `naming_series`, `disabled`, `customer_name`, `territory`, `customer_group`, `customer_type`, `is_frozen`, `custom_city`, `custom_pincode`) VALUES ('"""+phoneNo+"""', '"""+phoneNo+"""', '0',  '0', 'CUST-', '0', '"""+customerName+"""', 'India','Individual', 'Individual', '0', '"""+city+"""', '"""+pincode+"""')""")
			d = frappe.get_doc({
				"doctype": "DefaultValue",
				"parent": "" + phoneNo,
				"parenttype": "User Permission",
				"parentfield": "system_defaults",
				"defkey": "Customer",
				"defvalue": "" + phoneNo
			})
			d.insert(ignore_permissions=True)
			
			p = frappe.get_doc({"docstatus":0,"doctype":"User Permission","name":"New User Permission 1","__islocal":1,"__unsaved":1,"owner":"Administrator","apply_for_all_roles":0,"__run_link_triggers":0,"user":"" + phoneNo,"allow":"Customer","for_value":"" + phoneNo})
			p.insert(ignore_permissions=True)
			
		_update_password(phoneNo, otpobj.otp)
		
		response["status"]=200
		response["message"]="customer created"
		return response
	except Exception as e:
		error_log=appErrorLog(phoneNo,str(e))
		response["status"]=500
		response["message"]=str(e)
		response["message_trackeable"]=traceback.format_exc()
		return response

@frappe.whitelist(allow_guest=True)
def sendOTPInEmail(email,otp):
	response= {}
	try:
		msg="<br>Your Satvaras OTP is "+otp
		make(subject = "Stavaras OTP", content=msg, recipients=str(email),send_email=True, sender="erp@brillarescience.com")
		msg = """Email send successfully to Employee"""
		frappe.local.response['http_status_code'] = 200			
		response["status"]=200
		response["message"]="customer created"
		return response
	except Exception as e:
		frappe.local.response['http_status_code'] = 500
		error_log=appErrorLog(email,str(e))
		response["status"]=500
		response["message"]=str(e)
		return response


@frappe.whitelist(allow_guest=True)
def getOTPInEmail(phoneNo,email):
	response= {}
	try:
		frappe.db.set_value("Customer",phoneNo,"email_id",str(email))
		frappe.db.commit()
		otpobj=frappe.db.get("UserOTP", {"mobile": phoneNo}) 
		if otpobj:
			sendOTPInEmail(email,otpobj.otp)
			frappe.local.response['http_status_code'] = 200			
			response["status"]=200
			response["message"]="customer created"
			return response
		else:		
			frappe.local.response['http_status_code'] = 500
			response["status"]=500
			response["message"]="Issue to get OTP"
			return response
	except Exception as e:
		frappe.local.response['http_status_code'] = 500
		error_log=appErrorLog(phoneNo,str(e))
		response["status"]=500
		response["message"]="There is some issue please try again."
		return response


@frappe.whitelist(allow_guest=True)
def issueCreate(subject,raised_by,description):

	response={}

	try:
		frappe.sendmail(
			recipients = ['contact@svakara.com'],
			sender = "contact@svakara.com",
			subject = "Customer issue : {}".format(str(subject)),
			content = "Raise by:<br>{}<br>Description:<br>{}".format(raised_by,description),
			now = True
		)

		d1=frappe.get_doc({
					"docstatus": 0,
					"doctype": "Issue",
					"name": "Issue 1",
					"__islocal": 1,
					"__unsaved": 1,
					"status": "Open",
					"subject": subject,
					"raised_by":"contact@svakara.com",
					"description":"Raise by:<br>{}<br>Description:<br>{}".format(raised_by,description),
				})
		d2=d1.insert(ignore_permissions=True)
		frappe.local.response['http_status_code'] = 200
		
		response["status"]="200"
		response["message"]="Meessage send"
		return response
	except Exception as e:
		error_log=appErrorLog(frappe.session.user,e)
		frappe.local.response['http_status_code'] = 500
		response["status"]="500"
		response["message"]=str(e)
		return response