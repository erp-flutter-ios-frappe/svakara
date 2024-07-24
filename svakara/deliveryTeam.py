
from __future__ import unicode_literals
import frappe
from frappe import throw, msgprint, _
import frappe.permissions
import traceback
import string
import random
from frappe.utils.password import update_password as _update_password
from frappe.utils import nowdate,add_days
from frappe.core.doctype.communication.email import make
from erpnext.satvaras_cron import salesOrderSubmit




# Assign todays sales order to delivery boy. At mid night it will done auto.
@frappe.whitelist(allow_guest=True)
def assignTodaysOrders():

	try:
		allOrders=frappe.db.get_all("Sales Order", {"delivery_date": str(frappe.utils.data.nowdate())}, ["*"])
		for order in allOrders:
			customerDetail=frappe.db.get("Customer", {"name": order["customer"]})
			if customerDetail["custom_delivery_person_id"] not in ["",None]:
				if order["custom_delivery_person_id"] in ["","None",None]:
					query = "UPDATE `tabSales Order` SET `custom_delivery_person_id`='{}', `custom_delivery_person_name`='{}' WHERE `name`='{}'".format(customerDetail["custom_delivery_person_id"],customerDetail['custom_delivery_person_name'],order["name"])
					frappe.db.sql(query)

		frappe.db.commit()
		return True
	except Exception as e:
		# frappe.local.response['http_status_code'] = 404
		return False

@frappe.whitelist(allow_guest=True)
def unassignTodaysSalesOrder():

	assignTodaysOrders()

	response= {}
	response["status_code"]=200
	response["message"]=""
	response["data"]=[]
	
	try:	

		userobj = frappe.get_all(
			"Sales Order", 
			fields=["*"],
			filters={
				"custom_delivery_person_id": ["is", "not set"], ## IS NULL, 
				"delivery_date": str(frappe.utils.data.nowdate()),
				"docstatus": ["in", [0,1]]
			})

		# userobj=frappe.db.get_all("Sales Order", {"delivery_date": str(frappe.utils.data.nowdate()),"custom_delivery_person_id":""}, ["*"])
		
		# query = "SELECT * FROM `tabSales Order` WHERE `docstatus` IN (0,1) AND `delivery_date`='{}' AND `custom_delivery_person_id` IN ('','None') ORDER BY `transaction_date` desc".format(str(frappe.utils.data.nowdate()))
		# return query
		# userobj=frappe.db.sql(query,as_dict=1)
		
		
		if userobj:
			response["status_code"]=200
			response["message"]="data found"
			response["data"]=userobj
			return response 
		else:		
			response["status"]=200
			response["message"]="data not found"
			return response
	except Exception as e:
		# frappe.local.response['http_status_code'] = 404
		response["status_code"]=500
		response["message"]=str(e)
		return response


@frappe.whitelist(allow_guest=True)
def allTodaysSalesOrder():

	response= {}
	response["status_code"]=200
	response["message"]=""
	response["data"]=[]
	
	try:	

		userobj = frappe.get_all(
			"Sales Order", 
			fields=["*"],
			filters={
				"delivery_date": str(frappe.utils.data.nowdate()),
				"docstatus": ["in", [0,1]]
			})
		
		if userobj:
			response["status_code"]=200
			response["message"]="data found"
			response["data"]=userobj
			return response 
		else:		
			response["status"]=200
			response["message"]="data not found"
			return response
	except Exception as e:
		# frappe.local.response['http_status_code'] = 404
		response["status_code"]=500
		response["message"]=str(e)
		return response



@frappe.whitelist(allow_guest=True)
def getDeliveryTeamMembers():
	response= {}
	allOrders=frappe.db.get_all("Delivery Team", {"disable": 0, "delivery": 1}, ["*"])
	response["status_code"]=200
	response["message"]="data found"
	response["data"]=allOrders
	return response


@frappe.whitelist(allow_guest=True)
def assignDPtoSO(**kwargs):

	parameters=frappe._dict(kwargs)

	reply={}
	reply['status_code']=200
	reply['message']=''
	reply['data']={}

	parametersKeys = parameters.keys()
	if 'so_no' not in parametersKeys:
		reply['status_code']=500
		reply['message']='Sales order number parameter is not found.'
		return reply

	if 'employee_id' not in parametersKeys:
		reply['status_code']=500
		reply['message']='Employee parameter is not found.'
		return reply

	query = "UPDATE `tabSales Order` SET `custom_delivery_person_id`='{}', `custom_delivery_person_name`='{}' WHERE `name`='{}'".format(parameters['employee_id'],parameters['employee_name'],parameters['so_no'])
	frappe.db.sql(query)

	# frappe.db.set_value("Sales Order", parameters['so_no'], "custom_delivery_person_id", parameters['employee_id'])
	# frappe.db.set_value("Sales Order", parameters['so_no'], "custom_delivery_person_name", parameters['employee_name'])
	frappe.db.commit()
	return reply


@frappe.whitelist(allow_guest=True)
def assignDeliveryPartner(**kwargs):

	parameters=frappe._dict(kwargs)

	reply={}
	reply['status_code']=200
	reply['message']=''
	reply['data']={}

	parametersKeys = parameters.keys()
	if 'so_no' not in parametersKeys:
		reply['status_code']=500
		reply['message']='Sales order number parameter is not found.'
		return reply

	if 'employee_id' not in parametersKeys:
		reply['status_code']=500
		reply['message']='Employee parameter is not found.'
		return reply

	try:	
		deliveryPerson=frappe.db.get("Delivery Team", {"employee_id": parameters['employee_id']})
		salesOrder=frappe.db.get("Sales Order", {"name": parameters['so_no']})
		customer=frappe.db.get("Customer", {"name": salesOrder['customer']})

		query = "UPDATE `tabCustomer` SET `custom_delivery_person_id`='{}', `custom_delivery_person_name`='{}' WHERE `name`='{}'".format(deliveryPerson['employee_id'],deliveryPerson['employee_name'],customer['name'])
		frappe.db.sql(query)

		query = "UPDATE `tabSales Order` SET `custom_delivery_person_id`='{}', `custom_delivery_person_name`='{}' WHERE `name`='{}'".format(deliveryPerson['employee_id'],deliveryPerson['employee_name'],parameters['so_no'])
		frappe.db.sql(query)


		# frappe.db.set_value("Sales Order", parameters['so_no'], "custom_delivery_person_id", deliveryPerson['employee_id'])
		# frappe.db.set_value("Sales Order", parameters['so_no'], "custom_delivery_person_name", deliveryPerson['employee_name'])

		frappe.db.commit()
		return reply

	except Exception as e:
		reply["status"]=500
		reply["message"]="There is issue to fetch user detail"
		return reply












@frappe.whitelist(allow_guest=True)
def getEmployeeDetail(phonenumber):

	response= {}
	try:	
		userobj=frappe.db.get("Delivery Team", {"mobile_number": phonenumber})	
		if userobj:
			response["status"]=200
			response["message"]="data found"
			response["data"]=userobj
			return response 
		else:		
			response["status"]=200
			response["message"]="data not found"
			return response
	except Exception as e:
		frappe.local.response['http_status_code'] = 404
		#error_log=app_error_log(phoneNo,str(e))
		response["status"]=500
		response["message"]="There is issue to fetch user detail"
		return response



@frappe.whitelist(allow_guest=True)
def getTodaysSalesOrder():
	assignTodaysOrders()

	response= {}
	try:	
		userobj=frappe.db.get_all("Sales Order", {"delivery_date": str(frappe.utils.data.nowdate())}, ["*"])
		if userobj:
			response["status"]=200
			response["message"]="data found"
			response["data"]=userobj
			return response 
		else:		
			response["status"]=200
			response["message"]="data not found"
			return response
	except Exception as e:
		frappe.local.response['http_status_code'] = 404
		#error_log=app_error_log("Error",str(e))
		response["status"]=500
		response["message"]=str(e)
		return response

@frappe.whitelist(allow_guest=True)
def getTodaysSalesOrderOfEmployee(employeeID):
	assignTodaysOrders()

	response= {}
	response["status"]=200
	response["message"]="data not found"
	response["data"]=[]
	response["total"]=0
	response["item_count"]={}


	try:	
		orderList=frappe.db.get_all("Sales Order", {"delivery_date": str(frappe.utils.data.nowdate()),"custom_delivery_person_id":employeeID}, ["*"], order_by="name desc")
		
		order_number = []
		for ord in orderList:
			order_number.append(str(ord['name']))

		order_String = ','.join(order_number)
		x = order_String.replace(",", "','")
		order_String = "'{}'".format(x)



		# query = "SELECT item_code,SUM(qty) FROM `tabSales Order Item` WHERE `parent` IN ({}) GROUP BY `item_code`".format(order_String)
		query = "SELECT * FROM `tabSales Order Item` WHERE `parent` IN ({}) GROUP BY `item_code`".format(order_String)

		itemList=frappe.db.sql(query,as_dict=1)

		# response["total"]=query
		# response["item_count"]=item_detail

		# return response


		previousItems = {}
		total = 0
		for itm in itemList:
			previousKeys = previousItems.keys()
			total = total + itm['qty']

			if itm['item_code'] in previousKeys:
				previousItems[itm['item_code']] = float(previousItems[itm['item_code']])+itm['qty']
			else:
				previousItems[itm['item_code']] = itm['qty']

		response["total"]=total
		response["item_count"]=previousItems

		if orderList:
			response["status"]=200
			response["message"]="data found"
			response["data"]=orderList
			
		return response
	except Exception as e:
		frappe.local.response['http_status_code'] = 404
		response["status"]=500
		response["message"]=str(e)
		return response





@frappe.whitelist(allow_guest=True)
def unassignDeliveryPatner(customer):

	response= {}
	try:	
		userobj2=frappe.db.get("Customer", {"name": customer})

		if userobj2:
			frappe.db.sql("""UPDATE tabCustomer set delivery_patner="" where name=%s""",(customer))
			frappe.db.sql("""UPDATE tabCustomer set delivery_person_name="" where name=%s""",(customer))

			allOrders=frappe.get_all('Sales Order', filters=[["Sales Order","delivery_date","<=",nowdate()],["Sales Order","customer","=",customer]], fields=['*'])
			for order in allOrders:
				frappe.db.set_value("Sales Order", order["name"], "delivery_person_id", "")

			frappe.db.commit()
			response["status"]=200
			response["message"]="data found"
			response["data"]=userobj2
			return response
		else:
			response["status"]=200
			response["message"]="data not found"
			return response
	except Exception as e:
		frappe.local.response['http_status_code'] = 404
		#error_log=app_error_log(customer,str(e))
		response["status"]=500
		response["message"]="There is issue to fetch user detail"
		return response



@frappe.whitelist(allow_guest=True)
def getDefaultValue():
	response= {}
	response["dashboard"]=frappe.db.sql("""Select * from `tabdashboard`""",as_dict=True)
	response["offer"]=frappe.get_all('offer', filters=[["offer","end_date",">=",nowdate()],["offer","start_date","<=",nowdate()]], fields=['*'])
	response["settings"]=frappe.get_all('application setting', filters=[["application setting","title","=",'Satvaras']], fields=['*'])
	response["images"]=frappe.get_all('satvaras app images', fields=['*'])
	response["productinformation"]=frappe.get_all('satvaras product information', fields=['*'])
	response["ERPDateTime"] = frappe.utils.data.get_datetime()
	currenttime=frappe.utils.data.nowtime()
	x = currenttime.split(":")
	days=0
	#server is 1 hour behind
	if int(x[0])>=14:
		days=1

	response["ERPTime"] = x[0]
	response["ERPMinimum"] = add_days(frappe.utils.data.get_datetime(),days)
	response["ItemChangeDateTime"] = frappe.db.sql("""select max(modified) from tabItem where  item_group = 'Products'""")[0][0]
	response["deliveryTimeSlot"]=frappe.db.sql("""Select * from `tabtime` order by sort""",as_dict=True)

	return response



def get_version_detail():
	try:
		data1=frappe.db.sql("""select * from `tabapplication setting` where title='Satvaras'""",as_dict=True)
		return data1[0]
	except Exception as e:
		return str(e)

@frappe.whitelist()
def save_usersetting(platform,osversion,appversion,device_name,token):
	#user_setting=frappe.db.get("User Setting",{"user":frappe.session.user}).name
	try:
		user_setting=frappe.db.sql("""select name from `tabUser Settings` where name=%s""",frappe.session.user)
		if user_setting:
			setting_data=frappe.get_doc("User Settings",frappe.session.user)
			d1 = frappe.get_doc({
				"docstatus": 0,
				"doctype": "User Settings",
				"name": setting_data.name,
				"modified":setting_data.modified,
				"platform": str(platform),
				"os_version": str(osversion),
				"app_version": str(appversion),
				"device_name": str(device_name),
				"token":token
				})
			result=d1.save(ignore_permissions=True)
			if result:
				return get_version_detail()
		else:
			d2 = frappe.get_doc({
						"docstatus": 0,
						"doctype": "User Settings",	
						"name": "New User Setting 1",
						"__islocal": 1,
						"__unsaved": 1,
						"owner":str(frappe.session.user),
						"user": str(frappe.session.user),
						"platform": str(platform),
						"os_version": str(osversion),
						"app_version": str(appversion),
						"device_name": str(device_name),
						"token":str(token)
					   })
			result=d2.insert()
			if result:
				return get_version_detail()
	except Exception as e:
		return str(e)


@frappe.whitelist()
def GetBalance():	

	try:
		totalUsedAmount= frappe.db.sql("""SELECT SUM(total) FROM `tabSales Order` where customer = '"""+frappe.session.user+"""' and `status`='Completed' """)
		
		totalSaleOrderAmount= frappe.db.sql("""SELECT SUM(total) FROM `tabSales Order` where customer = '"""+frappe.session.user+"""' and `status`<>'Cancelled'""")
		
		totalwalletamount=frappe.db.sql("""SELECT SUM(wallet_balance) FROM `tabWallet` where docstatus=1 and customer = '"""+frappe.session.user+"""'""")
		
		data={}
		if totalUsedAmount[0][0] != None and totalSaleOrderAmount[0][0] !=None and totalwalletamount[0][0] != None :
			data["WalletBalance"]=totalwalletamount[0][0] - totalUsedAmount[0][0]
			data["AvailableBalance"]=totalwalletamount[0][0] - totalSaleOrderAmount[0][0]
			return data
		
		elif totalSaleOrderAmount[0][0] !=None and totalwalletamount[0][0] != None:
			data["WalletBalance"]=totalwalletamount[0][0]
			data["AvailableBalance"]=totalwalletamount[0][0] - totalSaleOrderAmount[0][0]
			return data

		elif totalwalletamount[0][0] != None:
			data["WalletBalance"]=totalwalletamount[0][0]
			data["AvailableBalance"]=totalwalletamount[0][0]
			return data
		
		else:
			data["WalletBalance"]=0
			data["AvailableBalance"]=0
			return data
		
	except frappe.DoesNotExistError:
		data={}
		data["WalletBalance"]=0
		data["AvailableBalance"]=0
		return data

@frappe.whitelist(allow_guest=True)
def userDetail(name):

	response= {}
	try:	
		userobj=frappe.db.get("User", {"name": name})	
		if userobj:
			response["status"]=200
			response["message"]="data found"
			response["data"]=userobj
			return response 
		else:		
			response["status"]=200
			response["message"]="data not found"
			return response
	except Exception as e:
		#error_log=app_error_log(phoneNo,str(e))
		response["status"]=500
		response["message"]="There is issue to fetch user detail"
		return response

@frappe.whitelist(allow_guest=True) 
def getProfile():
	
	try:
		filters = [
			["Dynamic Link", "link_doctype", "=", "Customer"],
			["Dynamic Link", "link_name", "=", frappe.session.user],
			["Address", "hideaddress", "!=", 1]

		]
		fields = ["name", "address_line1", "address_line2", "city", "area",  "state", "country","pincode","is_primary_address","link_code"]
		address = frappe.get_all("Address", filters=filters, fields=fields) or [{"name":"", "address_line1":"", "address_line2":"", "area":"", "city":"", "state":"", "country":"","pincode":"","is_primary_address":""}]

		return address
			
	except Exception as e:
		return str(e)		 

@frappe.whitelist() 
def profileupdate(fname,lname,address1,address2,pincode,area,city,state,name,isprimary): 
	try:
		
		if len(name) == 0 :
			d = frappe.get_doc({
					"doctype":"Address",
					"customer": ""+frappe.session.user,
					"address_line1":address1,
					"address_line2":address2,
					"area":area,
					"city":city,
					"state":state,
					"pincode":pincode,
					"docstatus":0,
					"customer_name": ""+fname+" "+lname+"",
					"is_primary_address": isprimary,
					"links": [{"link_doctype":"Customer","doctype":"Dynamic Link","idx":1,"parenttype":"Address","link_name":""+frappe.session.user,"docstatus":0,"parentfield":"links"}]

					})
			d.insert(ignore_permissions=True)
			return d
		else:
			doc=frappe.get_doc("Address",name)
			d = frappe.get_doc({
					"doctype":"Address",
					"name":name,
					"customer": ""+frappe.session.user,
					"address_line1":address1,
					"address_line2":address2,
					"area":area,
					"city":city,
					"state":state,
					"pincode":pincode,
					"docstatus":0,
					"customer_name": ""+fname+" "+lname+"",
					"is_primary_address": isprimary,
					"links": [{"link_doctype":"Customer","doctype":"Dynamic Link","idx":1,"parenttype":"Address","link_name":""+frappe.session.user,"docstatus":0,"parentfield":"links"}],
					"modified":doc.modified,
					"country":doc.country,
					"address_type":doc.address_type
					})
			d.save(ignore_permissions=True)
			return d
		return "Profile Updated SuccessFully"
	except Exception as e:
		return str(e)

@frappe.whitelist() 
def deleteAddress(name): 
	try:
		frappe.db.sql("""DELETE FROM tabAddress WHERE name= '""" + name +"""'  """)
		return True
	except Exception as e:
		return str(e)


@frappe.whitelist(allow_guest=True)
def hideAddress(addressid):
	response={}
	frappe.db.sql("""UPDATE `tabAddress` SET hideaddress = 1 WHERE name= '""" + addressid +"""'  """)
	frappe.db.commit()
	frappe.local.response['http_status_code'] = 200
	response["status"]=str(200)
	response["status_message"]='DELETED'
	response["message"]="Delete Sucessfully"
	return response

@frappe.whitelist() 
def setprimaryaddress(name): 
	try:
		filters = [
			["Dynamic Link", "link_doctype", "=", "Customer"],
			["Dynamic Link", "link_name", "=", frappe.session.user]
		]
		fields = ["name", "address_line1", "address_line2", "city", "area",  "state", "country","pincode","is_primary_address","link_code"]
		address = frappe.get_all("Address", filters=filters, fields=fields) or {}
		for addressname in address:
			if addressname["name"] == name:
				frappe.db.sql("""update tabAddress SET  is_primary_address = 1 WHERE name= '""" +addressname["name"] +"""'  """)
			else:
				frappe.db.sql("""update tabAddress SET  is_primary_address = 0 WHERE name= '""" +addressname["name"] +"""'  """)


		addressreturn = frappe.get_all("Address", filters=filters, fields=fields) or [{"name":"", "address_line1":"", "address_line2":"", "area":"", "city":"", "state":"", "country":"","pincode":"","is_primary_address":""}]

		return addressreturn
	except Exception as e:
		return str(e)

def id_generator(size):
   return ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(size))

@frappe.whitelist(allow_guest=True)
def UserSignUpUpdate(phoneNo,firstName,lastName,city,pincode):
	response= {}
	try:
		otpobj=frappe.db.get("UserOTP", {"mobile": phoneNo})
		user = frappe.db.get("User", {"name": phoneNo})
 
		if user:			
			frappe.db.sql("""UPDATE `tabUser` SET `last_name`='"""+lastName+"""',`city`='"""+city+"""',`pincode`='"""+pincode+"""', `first_name`='"""+firstName+"""' WHERE `name`='"""+phoneNo+"""'""")
			frappe.db.sql("""UPDATE `tabCustomer` SET `customer_name`='"""+firstName+"""' '"""+lastName+"""',`city`='"""+city+"""',`pincode`='"""+pincode+"""' WHERE `name`='"""+phoneNo+"""'""")
		else:		
			frappe.db.sql("""INSERT INTO `tabUser` (`name`, `creation`, `modified`, `modified_by`, `owner`, `docstatus`, `parent`, `parentfield`, `parenttype`, `idx`, `last_active`, `last_ip`, `user_type`, `github_username`, `reset_password_key`, `last_name`, `google_userid`, `last_known_versions`, `user_image`, `thread_notify`, `first_name`, `middle_name`, `new_password`, `last_login`, `location`, `github_userid`, `login_after`, `email`, `restrict_ip`, `username`, `send_welcome_email`, `fb_userid`, `background_style`, `background_image`, `send_password_update_notification`, `email_signature`, `language`, `mute_sounds`, `gender`, `login_before`, `enabled`, `time_zone`, `fb_username`, `birth_date`, `unsubscribed`, `bio`, `city`, `pincode`) VALUES ('"""+phoneNo+"""', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'Guest', 'Guest', '0', '', '', '', '0', '', '', 'System User', '', '', '"""+lastName+"""', '', '', 'https://secure.gravatar.com/avatar/adb831a7fdd83dd1e2a309ce7591dff8?d=retro', '1', '"""+firstName+"""', '', '', '', '', '', '0', '"""+phoneNo+"""@example.com', '', '"""+phoneNo+"""', '1', '', 'Fill Screen', '', '0', '', '', '0', '', '0', '1', '', '', '', '0', '', '"""+city+"""', '"""+pincode+"""')""")
			
			frappe.db.sql("""INSERT INTO `tabUserRole` (`name`, `creation`, `modified`, `modified_by`, `owner`, `docstatus`, `parent`, `parentfield`, `parenttype`, `idx`, `role`) VALUES ('"""+id_generator(10)+"""', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, '"""+phoneNo+"""', '"""+phoneNo+"""', '0', '"""+phoneNo+"""', 'user_roles', 'User', '1', 'Customer')""")
			frappe.db.sql("""INSERT INTO `tabHas Role` (`name`, `creation`, `modified`, `modified_by`, `owner`, `docstatus`, `parent`, `parentfield`, `parenttype`, `idx`, `role`) VALUES ('"""+id_generator(10)+"""', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, '"""+phoneNo+"""', '"""+phoneNo+"""', '0', '"""+phoneNo+"""', 'roles', 'User', '1', 'Customer')""")
			frappe.db.sql("""INSERT INTO `tabCustomer` (`name`, `creation`, `modified`, `modified_by`, `owner`, `docstatus`,  `idx`, `naming_series`, `disabled`, `customer_name`, `credit_days`, `territory`, `default_commission_rate`, `credit_days_based_on`,  `credit_limit`, `customer_group`, `customer_type`, `is_frozen`, `city`, `pincode`) VALUES ('"""+phoneNo+"""', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, '"""+phoneNo+"""', '"""+phoneNo+"""', '0',  '0', 'CUST-', '0', '"""+firstName+""" """+lastName+"""', '0', 'India', '0.000000', '', '0.000000', 'Individual', 'Individual', '0', '"""+city+"""', '"""+pincode+"""')""")
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
		#error_log=app_error_log(phoneNo,str(e))
		response["status"]=500
		response["message"]="There is some issue please try again."
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
		#error_log=app_error_log(email,str(e))
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
		#error_log=app_error_log(phoneNo,str(e))
		response["status"]=500
		response["message"]="There is some issue please try again."
		return response


@frappe.whitelist(allow_guest=True)
def issueCreate(subject,raised_by,description):

	try:
		d1=frappe.get_doc({
					"docstatus": 0,
					"doctype": "Issue",
					"name": "Issue 1",
					"__islocal": 1,
					"__unsaved": 1,
					"status": "Open",
					"subject": subject,
					"raised_by": raised_by,
					"description":description,
					"customer":raised_by,
				})
		d2=d1.insert(ignore_permissions=True)
		frappe.local.response['http_status_code'] = 200
		return d2

	except Exception as e:
		response={}
		#error_log=appErrorLog(frappe.session.user,e)
		frappe.local.response['http_status_code'] = 500
		response["status"]="500"
		response["message"]=str(e)
		return response




@frappe.whitelist(allow_guest=True)
def deliverSalesOrder(so_no):
	
	response={}
	response["status"]=str(500)
	response["status_message"]='SUBMITTED'
	response["message"]="Submit Sucessfully"
	response["data"]={}

	query = "UPDATE `tabSales Order` SET `custom_delivery_status_by_person`='Delivered' WHERE `name`='{}'".format(so_no)
	test = frappe.db.sql(query)

	query = "UPDATE `tabSales Order` SET `custom_delivery_time`='Morning 5 to 7' WHERE `custom_delivery_time` like '2023%'"
	test = frappe.db.sql(query)


	frappe.enqueue(salesOrderSubmit,queue='long',job_name="SO to DL".format(so_no),timeout=100000,name=str(so_no))

	return response