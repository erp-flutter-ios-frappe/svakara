
from __future__ import unicode_literals
import frappe
from frappe import throw, msgprint, _
import frappe.permissions
import traceback
import string
import random
from frappe.utils.password import update_password as _update_password
from frappe.utils import add_days,nowdate
from frappe.core.doctype.communication.email import make
from svakara.globle import appErrorLog


@frappe.whitelist()
def generateResponse(_type,status=None,message=None,data=None,error=None):
	response= {}
	if _type=="S":
		if status:
			response["status"]=status
		else:
			response["status"]="200"
		response["message"]=message
		response["data"]=data
	else:
		error_log=appErrorLog(frappe.session.user,str(error))
		frappe.local.response['http_status_code'] = 500

		if status:
			response["status"]=status
		else:
			response["status"]="500"	
		response["message"]=message
		response["data"]=None
	return response

@frappe.whitelist(allow_guest=True)
def getDefaultValue():
	response= {}
	response["dashboard"]=frappe.db.sql("""Select * from `tabDashboard images`""",as_dict=True)
	# response["offer"]=frappe.get_all('offer', filters=[["offer","end_date",">=",nowdate()],["offer","start_date","<=",nowdate()]], fields=['*'])
	response["settings"]=frappe.get_all('application setting', filters=[["application setting","title","=",'Satvaras']], fields=['*'])
	response["images"]=frappe.get_all('App Images', fields=['*'])
	response["productinformation"]=frappe.get_all('Product Information', fields=['*'])
	response["ERPDateTime"] = frappe.utils.data.get_datetime()
	currenttime=frappe.utils.data.nowtime()
	x = currenttime.split(":")
	days=0
	#server is 1 hour behind
	if int(x[0])>=14:
		days=1

	days=1

	response["ERPTime"] = x[0]
	response["ERPMinimum"] = add_days(frappe.utils.data.get_datetime(),days)
	response["ItemChangeDateTime"] = frappe.db.sql("""select max(modified) from tabItem where  item_group = 'Products'""")[0][0]
	response["deliveryTimeSlot"]=frappe.db.sql("""Select * from `tabTime` order by sort""",as_dict=True)

	return response



@frappe.whitelist(allow_guest=True)
def get_version_detail(allow_guest=True):
	try:
		data1=frappe.db.sql("""select * from `tabapplication setting` where title='Satvaras'""",as_dict=True)
		return data1[0]
	except Exception as e:
		return generateResponse("F",error=e)

@frappe.whitelist(allow_guest=True)
def save_usersetting(platform,osversion,appversion,device_name,token,phone):

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
		return generateResponse("F",error=e)


@frappe.whitelist()
def GetBalance():

	return GetBalanceNew(frappe.session.user)

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
def GetBalanceNew(phono):

	try:
		totalUsedAmount= frappe.db.sql("""SELECT SUM(total) FROM `tabSales Order` where customer = '"""+phono+"""' and `docstatus` not in ('2')""")
		
		totalSaleOrderAmount= frappe.db.sql("""SELECT SUM(total) FROM `tabSales Order` where customer = '"""+phono+"""' and `docstatus` not in ('2')""")
		
		# totalwalletamount=frappe.db.sql("""SELECT SUM(wallet_balance) FROM `tabWallet` where docstatus=1 and customer = '"""+phono+"""'""")
		totalwalletamount=frappe.db.sql("""SELECT SUM(wallet_balance) FROM `tabWallet` where customer = '"""+phono+"""' and `docstatus` not in ('0','2')""")


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
		error_log=appErrorLog("User Detail error:",str(e))
		response["status"]=500
		response["message"]="There is issue to fetch user detail"
		return response

@frappe.whitelist(allow_guest=True) 
def getProfile(phone):
	
	reply={}
	reply["status_code"]="200"
	reply["message"]=""
	reply["data"]=[]


	try:
		filters = [
			["Dynamic Link", "link_doctype", "=", "Customer"],
			["Dynamic Link", "link_name", "=", phone],
			#["Dynamic Link", "link_name", "=", frappe.session.user],
			["Address", "custom_hideaddress", "!=", 1]

		]
		address = frappe.get_all("Address", filters=filters, fields=['*'])
		reply["data"]=address
		return reply
			
	except Exception as e:
		reply["message"]=str(e)
		reply["status_code"]="500"
		return reply

@frappe.whitelist(allow_guest=True) 
def getCustomerDetail():
	
	try:
		filters = [
			["Customer", "name", "=", frappe.session.user]
		]
		customerDetail = frappe.get_all("Customer", filters=filters, fields=["*"])
		if len(customerDetail) > 0:
			return customerDetail[0]
		else:
			return []
	except Exception as e:
		return generateResponse("F",error=e)

@frappe.whitelist(allow_guest=True) 
def reduceSubscriptionDays():
	try:
		filters = [
			["Customer", "subscription_days", ">", 0]
		]
		customerDetail = frappe.get_all("Customer", filters=filters, fields=["*"])
		reply={}
		reply["count"] = str(len(customerDetail))
		changes = []
		for cust in customerDetail:
			reply[cust["name"]] = cust

			if int(cust["subscription_days"]) > 0:
				days = int(cust["subscription_days"])
				days = days - 1
				test = frappe.db.sql("""update tabCustomer SET subscription_days='""" + str(days) + """' WHERE name= '""" + cust["name"] +"""'  """)
				changes.append(test)

		reply["process"] = changes
		return reply
	except Exception as e:
		return generateResponse("F",error=e)

@frappe.whitelist(allow_guest=True)
def profileupdate(address1,address2,pincode,area,city,state,name,isprimary,phone):
	reply={}
	reply['status_code']="200"
	reply['message']=""
	try:
		
		if len(name) == 0 :
			d = frappe.get_doc({
					"doctype":"Address",
					"customer": phone,
					"address_line1":address1,
					"address_line2":address2,
					"custom_area":area,
					"city":city,
					"state":state,
					"pincode":pincode,
					"docstatus":0,
					"custom_is_primary_address": isprimary,
					"links": [{"link_doctype":"Customer","doctype":"Dynamic Link","idx":1,"parenttype":"Address","link_name":phone,"docstatus":0,"parentfield":"links"}]
					})
			d.insert(ignore_permissions=True)
			reply['message']="Address added sucessfully"
			reply['name']=d.name
			return reply
		else:
			query = "UPDATE `tabAddress` SET `address_line1`='{}', `address_line2`='{}', `custom_area`='{}', `city`='{}', `state`='{}', `pincode`='{}', `custom_is_primary_address`='{}' WHERE `name`='{}'".format(address1,address2,area,city,state,pincode,isprimary,name)
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
			# 		"custom_is_primary_address": isprimary,
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
		reply['message']=str(e)
		reply['message_traceable']=traceback.format_exc()
		return reply

@frappe.whitelist() 
def deleteAddress(name): 
	try:
		frappe.db.sql("""DELETE FROM tabAddress WHERE name= '""" + name +"""'  """)
		return True
	except Exception as e:
		return generateResponse("F",error=e)


@frappe.whitelist(allow_guest=True)
def hideAddress(addressid):
	response={}
	frappe.db.sql("""UPDATE `tabAddress` SET custom_hideaddress = 1 WHERE name= '""" + addressid +"""'  """)
	frappe.db.commit()
	frappe.local.response['http_status_code'] = 200
	response["status"]=str(200)
	response["status_message"]='DELETED'
	response["message"]="Delete Sucessfully"
	return response

@frappe.whitelist(allow_guest=True) 
def setprimaryaddress(name,phone): 

	try:
		filters = [
			["Dynamic Link", "link_doctype", "=", "Customer"],
			["Dynamic Link", "link_name", "=", phone]
		]
		address = frappe.get_all("Address", filters=filters, fields=['*']) or {}
		for addressname in address:
			if addressname["name"] == name:
				frappe.db.sql("""update tabAddress SET  custom_is_primary_address = 1 WHERE name= '""" +addressname["name"] +"""'  """)
			else:
				frappe.db.sql("""update tabAddress SET  custom_is_primary_address = 0 WHERE name= '""" +addressname["name"] +"""'  """)


		addressreturn = frappe.get_all("Address", filters=filters, fields=['*']) or [{"name":"", "address_line1":"", "address_line2":"", "area":"", "city":"", "state":"", "country":"","pincode":"","custom_is_primary_address":""}]

		return addressreturn
	except Exception as e:
		return generateResponse("F",error=e)

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
			frappe.db.sql("""UPDATE `tabCustomer` SET `customer_name`='"""+firstName+"""' '"""+lastName+"""',`custom_city`='"""+city+"""',`custom_pincode`='"""+pincode+"""' WHERE `name`='"""+phoneNo+"""'""")
		else:		
			frappe.db.sql("""INSERT INTO `tabUser` (`name`, `owner`, `docstatus`, `idx`, `user_type`, `last_name`, `thread_notify`, `first_name`, `login_after`, `email`, `username`, `location`, `bio`) VALUES ('"""+phoneNo+"""', 'Guest', '0', '0', 'System User', '"""+lastName+"""', '1', '"""+firstName+"""', '0', '"""+phoneNo+"""@example.com', '"""+phoneNo+"""', '"""+city+"""', '"""+pincode+"""')""")
			
			#frappe.db.sql("""INSERT INTO `tabUserRole` (`name`, `creation`, `modified`, `modified_by`, `owner`, `docstatus`, `parent`, `parentfield`, `parenttype`, `idx`, `role`) VALUES ('"""+id_generator(10)+"""', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, '"""+phoneNo+"""', '"""+phoneNo+"""', '0', '"""+phoneNo+"""', 'user_roles', 'User', '1', 'Customer')""")
			#frappe.db.sql("""INSERT INTO `tabHas Role` (`name`, `creation`, `modified`, `modified_by`, `owner`, `docstatus`, `parent`, `parentfield`, `parenttype`, `idx`, `role`) VALUES ('"""+id_generator(10)+"""', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, '"""+phoneNo+"""', '"""+phoneNo+"""', '0', '"""+phoneNo+"""', 'roles', 'User', '1', 'Customer')""")
			frappe.db.sql("""INSERT INTO `tabCustomer` (`name`, `owner`, `docstatus`,  `idx`, `naming_series`, `disabled`, `customer_name`, `territory`, `customer_group`, `customer_type`, `is_frozen`, `custom_city`, `custom_pincode`) VALUES ('"""+phoneNo+"""', '"""+phoneNo+"""', '0',  '0', 'CUST-', '0', '"""+firstName+""" """+lastName+"""', 'India','Individual', 'Individual', '0', '"""+city+"""', '"""+pincode+"""')""")
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
			recipients = ['meetbarot154@gmail.com','rsp4388@gmail.com','support@satvaras.com','jitendersinhd@gmail.com'],
			sender = "satvaras2020@gmail.com",
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
					"raised_by":"support@satvaras.com",
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

@frappe.whitelist(allow_guest=True)
def leadDisable(firstname,lastname,email,phone,dob,gender,country,state,city):

	alreadyAdded=frappe.db.sql("""select * from `tabMarketingList` where email=%s""",email)
	#return alreadyAdded
	if len(alreadyAdded) > 0:
		frappe.db.set_value("MarketingList",alreadyAdded[0][0],"inactive",1)
		frappe.db.commit()
		return True

	d1=frappe.get_doc({
				"docstatus": 0,
				"doctype": "MarketingList",
				"name": "MarketingList 1",
				"__islocal": 1,
				"__unsaved": 1,
				"first_name": firstname,
				"last_name": lastname,
				"email":email,
				"phone":phone,
				"dob":dob,
				"gender":gender,
				"country":country,
				"state":state,
				"city":city,
			})
	d2=d1.insert(ignore_permissions=True)
	alreadyAdded=frappe.db.sql("""select email from `tabMarketingList` where email=%s""",email)
	if len(alreadyAdded) > 0:
		frappe.db.set_value("MarketingList",alreadyAdded['name'],"inactive",1)
		frappe.db.commit()

	return True



@frappe.whitelist(allow_guest=True)
def leadCreated(firstname,lastname,email,phone,dob,gender,country,state,city):

	try:

		alreadyAdded=frappe.db.sql("""select email from `tabMarketingList` where email=%s""",email)

		if len(alreadyAdded) > 0:
			frappe.local.response['http_status_code'] = 200
			return True


		d1=frappe.get_doc({
					"docstatus": 0,
					"doctype": "MarketingList",
					"name": "MarketingList 1",
					"__islocal": 1,
					"__unsaved": 1,
					"first_name": firstname,
					"last_name": lastname,
					"email":email,
					"phone":phone,
					"dob":dob,
					"gender":gender,
					"country":country,
					"state":state,
					"city":city,
				})
		d2=d1.insert(ignore_permissions=True)
		frappe.local.response['http_status_code'] = 200
		return True

	except Exception as e:
		response={}
		error_log=appErrorLog(frappe.session.user,e)
		frappe.local.response['http_status_code'] = 500
		response["status"]="500"
		response["message"]=str(e)
		return False