
from __future__ import unicode_literals
import frappe
from frappe import throw, msgprint, _
import frappe.permissions
import traceback
import requests
from frappe.auth import LoginManager, CookieManager
from erpnext.globle import globleUserLogin
import datetime
from frappe.utils import getdate,nowdate



@frappe.whitelist(allow_guest=True)
def GetBalance(phono):
		
	totalSaleOrderAmount= frappe.db.sql("""SELECT SUM(total) FROM `tabSales Order` where customer = '"""+phono+"""' and `docstatus` not in ('2')""")		
	totalwalletamount=frappe.db.sql("""SELECT SUM(wallet_balance) FROM `tabWallet` where customer = '"""+phono+"""' and `docstatus` not in ('0','2')""")
	
	data={}
	data["wallet_balance"]=0
	data["totalSaleOrderAmount"]=totalSaleOrderAmount
	data["totalwalletamount"]=totalwalletamount
	if totalSaleOrderAmount[0][0] != None and totalwalletamount[0][0] != None :
		data["wallet_balance"]=str(float(totalwalletamount[0][0]) - float(totalSaleOrderAmount[0][0]))
	
	return data

@frappe.whitelist(allow_guest=True)
def processAllWallets(total_records):
	
	query = "SELECT name FROM `tabWallet` WHERE `docstatus` not in ('1','2') limit {}".format(total_records)
	banames = frappe.db.sql(query,as_dict=1)

	frappe.local.form_dict = globleUserLogin()
	frappe.local.cookie_manager = CookieManager()
	frappe.local.login_manager = LoginManager()

	for index, old_order in enumerate(banames):	
		frappe.enqueue(walletSubmit,queue='long',job_name="Wallet Submit: {}".format(old_order['name']),timeout=100000,name=old_order['name'])


	# if len(old_order)!=0:
	# 	frappe.enqueue(processAllWallets,queue='long',job_name="Next batch wallet",timeout=100000)
	return banames


@frappe.whitelist(allow_guest=True)
def walletSubmit(name):

	doc1so=frappe.get_doc("Wallet",name)
	doc1so.submit()
	# frappe.enqueue(doc1so.submit,queue='long',job_name="Wallet submit",timeout=100000)

	return True
		




@frappe.whitelist(allow_guest=True)
def processAllSalesOrderSubmit(total_records):
	
	query = "SELECT name FROM `tabSales Order` WHERE `delivery_date`<'{}' AND `docstatus` not in ('1','2') limit {}".format(nowdate(),total_records)
	banames = frappe.db.sql(query,as_dict=1)
	
	frappe.local.form_dict = globleUserLogin()
	frappe.local.cookie_manager = CookieManager()
	frappe.local.login_manager = LoginManager()

	for index, old_order in enumerate(banames):	
		frappe.enqueue(salesOrderSubmit,queue='long',job_name="Sales Order Submit: {}".format(old_order['name']),timeout=100000,name=old_order['name'])


	# if len(old_order)!=0:
	# 	frappe.enqueue(processAllWallets,queue='long',job_name="Next batch wallet",timeout=100000)
	return banames

@frappe.whitelist(allow_guest=True)
def salesOrderSubmit(name):

	doc1so=frappe.get_doc("Sales Order",name)
	doc1so.submit()
	# frappe.enqueue(doc1so.submit,queue='long',job_name="Wallet submit",timeout=100000)

	return True




@frappe.whitelist(allow_guest=True)
def dateReconsilation(phone):

	reply = {}
	reply['message']='Start reconsilation'
	reply['status_code']='200'
	reply['data']=[]

	url="http://130.211.193.136/api/method/erpnext.flutter_wallet.dataForCustomers?phone={}".format(phone)
	smilyResponse = requests.post(url)
	inventoryUpdated=smilyResponse.json()
	fullData = inventoryUpdated['message']

	open_order_old = fullData['open_orders']
	cancel_order_old = fullData['cancelled_orders']
	wallet_transaction_old = fullData['wallet_transaction']

	for index, old_order in enumerate(open_order_old):
		# if index <= 10:
		frappe.enqueue(update_transaction_delivery_date,queue='long',job_name="Update Delivery Date: {}".format(old_order['name']),timeout=100000,po_no=old_order['name'],transaction_date=old_order['transaction_date'],delivery_date=old_order['delivery_date'])

	return len(open_order_old)



@frappe.whitelist(allow_guest=True)
def update_transaction_delivery_date(po_no,transaction_date,delivery_date):
	query = "UPDATE `tabSales Order` SET `delivery_date`='{}',`transaction_date`='{}' WHERE `docstatus`!=2 AND `po_no`='{}'".format(delivery_date,transaction_date,po_no)
	open_order_new=frappe.db.sql(query,as_dict=1)
	return True



@frappe.whitelist(allow_guest=True)
def getTodaysOrders(allow_guest=True):
	return getOrderListForDate(nowdate(),0)

@frappe.whitelist(allow_guest=True)
def getTodaysOrders1AM(allow_guest=True):
	return getOrderListForDate(nowdate(),0)

@frappe.whitelist(allow_guest=True)
def getTodaysOrders2AM(allow_guest=True):
	return getOrderListForDate(nowdate(),0)

@frappe.whitelist(allow_guest=True)
def getTodaysOrders3AM(allow_guest=True):
	return getOrderListForDate(nowdate(),0)


@frappe.whitelist(allow_guest=True)
def getTodaysOrdersMail(allow_guest=True):
	return getOrderListForDate(nowdate(),1)

# @frappe.whitelist(allow_guest=True)
# def getTodaysDeliveryDateOrders(date):
# 	query = "SELECT * FROM `tabSales Order` WHERE `docstatus`!=2 AND `delivery_date`='{}'".format(date)
# 	newERPOrder=frappe.db.sql(query,as_dict=1)
# 	for index, old_order in enumerate(newERPOrder):
# 		frappe.enqueue(updateDDOrderDetail,queue='long',job_name="Update Delivery Date",timeout=100000,po_no=old_order['po_no'])

# 	return "Order is processing"


@frappe.whitelist(allow_guest=True)
def updateDDOrderDetail(po_no):

	query = "SELECT name FROM `tabSales Order` WHERE `po_no`='{}'".format(po_no)
	previousentry = frappe.db.sql(query,as_dict=True)

	if len(previousentry)==0:
		return "Order is not there"

	reply = {}
	reply['message']='Sales Order detail'
	reply['status_code']='200'
	reply['data']={}

	url="http://130.211.193.136/api/method/erpnext.flutter_wallet.orderDetail?so_no={}".format(po_no)
	smilyResponse = requests.post(url)
	inventoryUpdated=smilyResponse.json()
	orderDetails = inventoryUpdated["message"]
	reply['data']=orderDetails


	allKeysInOrder = orderDetails.keys()
	if len(allKeysInOrder)!=0:
		frappe.enqueue(updateDeliveryDate,queue='long',job_name="Update Delivery Date",timeout=100000,so_no=orderDetails['name'],delivery_date=orderDetails['delivery_date'])

	return "Going for update"



@frappe.whitelist(allow_guest=True)
def getOrderListForDate(date,mailsend):

	reply = {}
	reply['message']='Sales orders list'
	reply['status_code']='200'
	reply['data']=[]

	# frappe.enqueue(getTodaysDeliveryDateOrders,queue='long',job_name="Check Todays Orders",timeout=100000,date=date)

	url="http://130.211.193.136/api/method/erpnext.flutter_wallet.getSalesOrderForDate?date={}".format(date)
	smilyResponse = requests.post(url)
	inventoryUpdated=smilyResponse.json()
	oldERPOrder=inventoryUpdated['message']
	reply['old_records']=inventoryUpdated['message']
	reply['old_records_total']=len(inventoryUpdated['message'])

	#Update Delivery Date
	for index, old_order in enumerate(oldERPOrder):
		frappe.enqueue(updateDeliveryDate,queue='long',job_name="Update Delivery Date",timeout=100000,so_no=old_order['name'],delivery_date=old_order['delivery_date'])


	query = "SELECT * FROM `tabSales Order` WHERE `docstatus`!=2 AND `delivery_date`='{}'".format(nowdate())
	newERPOrder=frappe.db.sql(query,as_dict=1)
	
	if len(oldERPOrder)!=len(newERPOrder):
		mismatch_orders=[]
		for index, old_order in enumerate(oldERPOrder):
			orderfound= False
			for index, new_order in enumerate(newERPOrder):
				if old_order['name']==new_order['po_no']:
					orderfound = True
					break

			if not orderfound:
				mismatch_orders.append(old_order)

		reply['mismatch_records']=mismatch_orders
		reply['mismatch_records_total']=len(mismatch_orders)
		orderNumbers = []
		for index, order in enumerate(mismatch_orders):
			orderNumbers.append(order['name'])
			if mailsend==0:
				frappe.enqueue(getSalesOrderDetail,queue='long',job_name="Createing Order",timeout=100000,so_no=order['name'])
				# frappe.enqueue(getUserDetails,queue='long',job_name="Createing todays Order",timeout=100000,phone=order['customer'])

		reply['mismatch_records_numbers']=orderNumbers

		if len(orderNumbers)!=0:
			if mailsend==1:
				frappe.sendmail(
					recipients = ['meetbarot154@gmail.com','rsp4388@gmail.com','support@satvaras.com','jitendersinhd@gmail.com'],
					sender = "satvaras2020@gmail.com",
					subject = "Mismatch order : {}".format(str(date)),
					content = ",".join(orderNumbers),
					now = True
				)


	# for index, order in enumerate(inventoryUpdated['message']):
		# frappe.enqueue(getUserDetails,queue='long',job_name="Createing todays Order",timeout=100000,phone=order['customer'])

	return reply


@frappe.whitelist(allow_guest=True)
def updateDeliveryDate(so_no,delivery_date):
	
	query = "UPDATE `tabSales Order` SET `delivery_date`='{}' WHERE `docstatus`!=2 AND `po_no`='{}'".format(delivery_date,so_no)
	open_order_new=frappe.db.sql(query,as_dict=1)

	return True


































@frappe.whitelist(allow_guest=True)
def getReconsilationData(phone):

	reply = {}
	reply['message']='Start reconsilation'
	reply['status_code']='200'
	reply['data']=[]

	url="http://130.211.193.136/api/method/erpnext.flutter_wallet.dataForCustomers?phone={}".format(phone)
	smilyResponse = requests.post(url)
	inventoryUpdated=smilyResponse.json()
	fullData = inventoryUpdated['message']

	open_order_old = fullData['open_orders']
	cancel_order_old = fullData['cancelled_orders']
	wallet_transaction_old = fullData['wallet_transaction']

	
#Open orders
	query = "SELECT * FROM `tabSales Order` WHERE `docstatus`!=2 AND `customer`='{}'".format(phone)
	open_order_new=frappe.db.sql(query,as_dict=1)
	new_erp_po_no = []
	for index, open_order in enumerate(open_order_new):
		new_erp_po_no.append(open_order['po_no'])

	reply['new_erp_open_order_count']=len(open_order_new)
	reply['new_erp_open_order']=len(new_erp_po_no)

	for index, open_order in enumerate(open_order_old):
		if open_order['name'] not in new_erp_po_no:
			d = frappe.get_doc({
				"doctype": "sync Process",
				"reason":'ORDER_NOT_FETCH',
				"order_no":open_order['name'],
			})
			d = d.insert(ignore_permissions=True)



#Cancelled orders
	query = "SELECT * FROM `tabSales Order` WHERE `docstatus`=2 AND `customer`='{}'".format(phone)
	cancle_order_new=frappe.db.sql(query,as_dict=1)
	new_erp_cancel_po_no = []
	for index, cancel_order in enumerate(cancle_order_new):
		new_erp_cancel_po_no.append(cancel_order['po_no'])


	for index, cancelled_order in enumerate(cancel_order_old):
		if cancelled_order['name'] not in new_erp_cancel_po_no:
			d = frappe.get_doc({
				"doctype": "sync Process",
				"reason":'ORDER_CANCELLED',
				"order_no":cancelled_order['name'],
			})
			d = d.insert(ignore_permissions=True)	

#Remove orders from new ERP
	old_erp_po_no=[]

	for index, open_order in enumerate(open_order_old):
		old_erp_po_no.append(open_order['name'])

	reply['old_erp_open_order_count']=len(open_order_old)
	reply['old_erp_open_order']=len(old_erp_po_no)		

	not_found_so_new=[]
	for index, new_erp_po_no_single in enumerate(new_erp_po_no):
		if new_erp_po_no_single not in old_erp_po_no:
			not_found_so_new.append(new_erp_po_no_single)

	reply['extra_in_new_erp']=len(not_found_so_new)

	for index, not_match_order in enumerate(not_found_so_new):
		d = frappe.get_doc({
			"doctype": "sync Process",
			"reason":'ORDER_CANCELLED',
			"order_no":not_match_order,
		})
		d = d.insert(ignore_permissions=True)	


#Wallete entry
	query = "SELECT * FROM `tabWallet` WHERE `customer`='{}'".format(phone)
	previous_wallet_entry = frappe.db.sql(query,as_dict=True)
	new_erp_wallet_reference=[]
	for index, wallet_entry in enumerate(previous_wallet_entry):
		new_erp_wallet_reference.append(wallet_entry['old_erp_reference'])

	for index, wallet_entry in enumerate(wallet_transaction_old):
		if wallet_entry['name'] not in new_erp_wallet_reference:
			d = frappe.get_doc({
				"doctype": "sync Process",
				"reason":'WALLET_ENTRY_NOT_FETCH',
				"order_no":wallet_entry['name'],
				'result':phone
			})
			d = d.insert(ignore_permissions=True)	

	frappe.enqueue(reconsilation_order_not_fetch,queue='long',job_name="Order not fetch",timeout=100000)

	return reply

@frappe.whitelist(allow_guest=True)
def reconsilation_order_not_fetch(allow_guest=True):

	salesorderlist = frappe.get_all('sync Process', filters=[
							["sync Process","reason","=",'ORDER_NOT_FETCH']], fields=['*'])

	for order in salesorderlist:
		jobname="Sales Order Cancelled: {}".format(order["order_no"])
		frappe.enqueue(getSalesOrderDetail,queue='long',job_name=jobname,timeout=100000,so_no=order["order_no"])
		query = "DELETE FROM `tabsync Process` WHERE `order_no`='{}' AND `reason`='ORDER_NOT_FETCH'".format(order["order_no"])
		previousentry = frappe.db.sql(query,as_dict=True)

	reply={}
	reply["Total Order Scheduled"] = str(len(salesorderlist))
	frappe.enqueue(reconsilation_order_cancelled,queue='long',job_name="Cancelled orders",timeout=100000)
	return reply

@frappe.whitelist(allow_guest=True)
def todaysDataConsilation(date):

	reply = {}
	reply['message']='Sales orders list'
	reply['status_code']='200'
	reply['data']=[]

	url="http://130.211.193.136/api/method/erpnext.flutter_wallet.getSalesOrderForDate?date={}".format(date)
	smilyResponse = requests.post(url)
	inventoryUpdated=smilyResponse.json()
	
	for index, order in enumerate(inventoryUpdated['message']):
		frappe.enqueue(reconsilation_user_detail,queue='long',job_name="Createing todays Order",timeout=100000,phone=order['customer'])

	reply['respomse']=inventoryUpdated['message']

	return reply

@frappe.whitelist(allow_guest=True)
def reconsilation_user_detail(phone):

	reply = {}
	reply['message']='Sales orders list'
	reply['status_code']='200'
	reply['data']=[]

	try:
		url="http://130.211.193.136/api/method/erpnext.flutter_wallet.getUserDetails?phone='{}'".format(str(phone))
		smilyResponse = requests.post(url)
		inventoryUpdated=smilyResponse.json()
		reply['response_get']=inventoryUpdated

		if inventoryUpdated['message']["status_code"]=="200":
			userDetails = inventoryUpdated['message']['data']
			reply['user_detail']=userDetails
			allKeysInOrder = userDetails.keys()
			# appErrorLog("Going for sign up","")
			# appErrorLog("Going for sign up",findKeys('first_name',allKeysInOrder,userDetails))
			# appErrorLog("Going for sign up",findKeys('last_name',allKeysInOrder,userDetails))
			# appErrorLog("Going for sign up",findKeys('city',allKeysInOrder,userDetails))
			# appErrorLog("Going for sign up",findKeys('pincode',allKeysInOrder,userDetails))

			# frappe.enqueue(SyncSignUpUpdate,queue='long',job_name="Createing sync user: {}".format(phone),timeout=100000,phoneNo=phone,firstName=str(findKeys('first_name',allKeysInOrder,userDetails)),lastName=str(findKeys('last_name',allKeysInOrder,userDetails)),city=findKeys('city',allKeysInOrder,userDetails),pincode=findKeys('pincode',allKeysInOrder,userDetails))

			firstName = str(findKeys('first_name',allKeysInOrder,userDetails))
			if firstName in [None,"","None","NoneType"]:
				firstName = ""
			firstName = firstName.encode("utf-8")


			lastName = str(findKeys('last_name',allKeysInOrder,userDetails))
			if lastName in [None,"","None","NoneType"]:
				lastName = ""
			lastName = lastName.encode("utf-8")


			city = str(findKeys('city',allKeysInOrder,userDetails))
			if city in [None,"","None","NoneType"]:
				city = ""
			city = city.encode("utf-8")


			pincode = str(findKeys('pincode',allKeysInOrder,userDetails))
			if pincode in [None,"","None","NoneType"]:
				pincode = ""
			pincode = pincode.encode("utf-8")
			

			return create_user_in_erp(phone.encode("utf-8"),firstName,lastName,city,pincode)
		else:
			reply['response_fail']="Not get customer detail {}".format(phone)
			reply['response_fail_traceable']="Not get customer detail {} \n {}".format(phone,traceback.format_exc())
			appErrorLog("Customer Create Error: {}".format(phone),"")
			appErrorLog("Customer Create Error Traceable: {}".format(phone),traceback.format_exc())
			

		return reply
	except Exception as e:
		reply['error']=str(e)
		appErrorLog("Customer Create Error Except: {}".format(phone),str(e))
		appErrorLog("Customer Create Error Except Traceable: {}".format(phone),traceback.format_exc())
		return reply


@frappe.whitelist(allow_guest=True)
def reconsilation_user_detail_New(phone):

	reply = {}
	reply['message']='Sales orders list'
	reply['status_code']='200'
	reply['data']=[]

	try:

		url="http://130.211.193.136/api/method/erpnext.flutter_wallet.getUserDetailsNew?phone='{}'".format(str(phone))

		payload = {}
		headers = {
		'Cookie': 'full_name=Guest; sid=Guest; system_user=yes; user_id=Guest; user_image='
		}

		response = requests.request("POST", url, headers=headers, data=payload)

	


		# url="http://130.211.193.136/api/method/erpnext.flutter_wallet.getUserDetailsNew?phone='{}'".format(str(phone))
		# smilyResponse = requests.post(url)
		# inventoryUpdated=smilyResponse.json()
		inventoryUpdated=response.json()
		reply['response_get']=inventoryUpdated

		if inventoryUpdated['message']["status_code"]=="200":
			userDetails = inventoryUpdated['message']['data']
			reply['user_detail']=userDetails
			allKeysInOrder = userDetails.keys()
			# appErrorLog("Going for sign up","")
			# appErrorLog("Going for sign up",findKeys('first_name',allKeysInOrder,userDetails))
			# appErrorLog("Going for sign up",findKeys('last_name',allKeysInOrder,userDetails))
			# appErrorLog("Going for sign up",findKeys('city',allKeysInOrder,userDetails))
			# appErrorLog("Going for sign up",findKeys('pincode',allKeysInOrder,userDetails))

			# frappe.enqueue(SyncSignUpUpdate,queue='long',job_name="Createing sync user: {}".format(phone),timeout=100000,phoneNo=phone,firstName=str(findKeys('first_name',allKeysInOrder,userDetails)),lastName=str(findKeys('last_name',allKeysInOrder,userDetails)),city=findKeys('city',allKeysInOrder,userDetails),pincode=findKeys('pincode',allKeysInOrder,userDetails))

			firstName = str(findKeys('first_name',allKeysInOrder,userDetails))
			if firstName in [None,"","None","NoneType"]:
				firstName = ""
			firstName = firstName.encode("utf-8")


			lastName = str(findKeys('last_name',allKeysInOrder,userDetails))
			if lastName in [None,"","None","NoneType"]:
				lastName = ""
			lastName = lastName.encode("utf-8")


			city = str(findKeys('city',allKeysInOrder,userDetails))
			if city in [None,"","None","NoneType"]:
				city = ""
			city = city.encode("utf-8")


			pincode = str(findKeys('pincode',allKeysInOrder,userDetails))
			if pincode in [None,"","None","NoneType"]:
				pincode = ""
			pincode = pincode.encode("utf-8")
			

			return create_user_in_erp(phone.encode("utf-8"),firstName,lastName,city,pincode)
		else:
			reply['response_fail']="Not get customer detail {}".format(phone)
			reply['response_fail_traceable']="Not get customer detail {} \n {}".format(phone,traceback.format_exc())
			appErrorLog("Customer Create Error: {}".format(phone),"")
			appErrorLog("Customer Create Error Traceable: {}".format(phone),traceback.format_exc())
			

		return reply
	except Exception as e:
		reply['error']=str(e)
		appErrorLog("Customer Create Error Except: {}".format(phone),str(e))
		appErrorLog("Customer Create Error Except Traceable: {}".format(phone),traceback.format_exc())
		return reply



@frappe.whitelist(allow_guest=True)
def create_user_in_erp(phone,firstName,lastName,city,pincode):

	response= {}
	if firstName in ['',None,'None']:
		firstName = ""

	if lastName in ['',None,'None']:
		lastName = ""

	if city in ['',None,'None']:
		city = ""

	if pincode in ['',None,'None']:
		pincode = ""

	phone = str(str(phone).replace("b'", ""))
	firstName = str(str(firstName).replace("b'", ""))
	lastName = str(str(lastName).replace("b'", ""))
	city = str(str(city).replace("b'", ""))
	pincode = str(str(pincode).replace("b'", ""))

	# response['phone_type']= type(phone)
	# response['firstName_type']= type(firstName)
	# response['lastName_type']= type(lastName)
	# response['pincode_type']= type(pincode)



	phone = str(str(phone).replace("'", ""))
	firstName = str(str(firstName).replace("'", ""))
	lastName = str(str(lastName).replace("'", ""))
	city = str(str(city).replace("'", ""))
	pincode = str(str(pincode).replace("'", ""))


	# return response


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
		frappe.enqueue(getReconsilationData,queue='long',job_name="Get Sales Order List: {}".format(phone),timeout=100000,phone=phone)
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
def reconsilation_order_cancelled(allow_guest=True):

	salesorderlist = frappe.get_all('sync Process', filters=[
							["sync Process","reason","=",'ORDER_CANCELLED']], fields=['*'])

	for order in salesorderlist:
		jobname="Sales Order: {}".format(order["order_no"])
		frappe.enqueue(order_cancelled,queue='long',job_name=jobname,timeout=100000,so_no=order["order_no"])
		query = "DELETE FROM `tabsync Process` WHERE `order_no`='{}' AND `reason`='ORDER_CANCELLED'".format(order["order_no"])
		previousentry = frappe.db.sql(query,as_dict=True)

	reply={}
	reply["Total Order Scheduled"] = str(len(salesorderlist))
	frappe.enqueue(reconsilation_wallet_list,queue='long',job_name="Wallet Entrys",timeout=100000)
	return reply

@frappe.whitelist(allow_guest=True)
def order_cancelled(so_no):

	# frappe.local.form_dict = globleUserLogin()
	# frappe.local.cookie_manager = CookieManager()
	# frappe.local.login_manager = LoginManager()

	# url="https://cloud.satvaras.com/api/method/login?usr=satvarasautosystem@gmail.com&pwd=Satvaras2020*"
	# smilyResponse = requests.post(url)
	# inventoryUpdated=smilyResponse.json()




	query = "SELECT name FROM `tabSales Order` WHERE `po_no`='{}'".format(so_no)
	previousentry = frappe.db.sql(query,as_dict=True)

	if len(previousentry)==0:
		return "Order not found"

	doc1so_temp=frappe.get_doc("Sales Order",previousentry[0]['name'])

	if doc1so_temp.status in ['Cancelled']:
		return "Order is already cancelled."
	
	if doc1so_temp.docstatus==2:
		return "Order is already cancelled."

	if doc1so_temp.docstatus==0:

		# login_manager = LoginManager()
		# login_manager.authenticate('satvarasautosystem@gmail.com','Satvaras2020*')
		# login_manager.post_login()
		# if frappe.response['message'] == 'Logged In':
		# temp = frappe.delete_doc('Sales Order',previousentry[0]['name'])


		# temp = frappe.delete_doc('Sales Order',previousentry[0]['name'])

		query = "DELETE FROM `tabSales Order` WHERE `name`='{}'".format(previousentry[0]['name'])
		previousentry11 = frappe.db.sql(query,as_dict=True)
		query1 = "DELETE FROM `tabSales Order Item` WHERE `parent`='{}'".format(previousentry[0]['name'])
		previousentry111 = frappe.db.sql(query1,as_dict=True)
		return "order going to delete"

	if doc1so_temp.docstatus==1:
		frappe.enqueue(doc1so_temp.cancel,queue='long',job_name="Cancel order: {}".format(previousentry[0]['name']),timeout=100000)
		return "Going to cancelled order."

	return "Order prossed"

@frappe.whitelist(allow_guest=True)
def reconsilation_wallet_list(allow_guest=True):

	salesorderlist = frappe.get_all('sync Process', filters=[
							["sync Process","reason","=",'WALLET_ENTRY_NOT_FETCH']], fields=['*'])

	process_phone = []
	for order in salesorderlist:
		if order["result"] not in process_phone:
			jobname="Wallet Entry List for: {}".format(order["result"])
			process_phone.append(order["result"])
			frappe.enqueue(reconsilation_wallet_single,queue='long',job_name=jobname,timeout=100000,phone=order["result"])
			query = "DELETE FROM `tabsync Process` WHERE `result`='{}' AND `reason`='WALLET_ENTRY_NOT_FETCH'".format(order["result"])
			previousentry = frappe.db.sql(query,as_dict=True)

	reply={}
	reply["Total Order Scheduled"] = str(len(salesorderlist))
	# frappe.enqueue(reconsilation_order_cancelled,queue='long',job_name="Cancelled orders",timeout=100000)
	return reply


@frappe.whitelist(allow_guest=True)
def reconsilation_wallet_single(phone):

	reply = {}
	reply['message']='Wallet list'
	reply['status_code']='200'
	reply['data']=[]

	url="http://130.211.193.136/api/method/erpnext.flutter_wallet.getAllWalletTransacation?phone={}".format(phone)
	smilyResponse = requests.post(url)
	inventoryUpdated=smilyResponse.json()
	if len(inventoryUpdated.keys())!=0:
		totalWallet = inventoryUpdated["message"]
		for index, wallet in enumerate(totalWallet):
			frappe.enqueue(createWalletEntry,queue='long',job_name="Create Wallet Entry: {}".format(wallet['name']),timeout=100000,walletEntry=wallet)

		return totalWallet
	
	return "No wallet transaction found"



################Reconsilation End##############################

##### Create Orders
@frappe.whitelist(allow_guest=True)
def findKeys(keysName,keysList,orderDetails):

	if keysName in keysList:
		return orderDetails[keysName]

	return ""

@frappe.whitelist(allow_guest=True)
def getSalesOrderDetail(so_no):

	query = "SELECT name FROM `tabSales Order` WHERE `po_no`='{}'".format(so_no)
	previousentry = frappe.db.sql(query,as_dict=True)

	if len(previousentry)!=0:
		return "Order is already there"

	reply = {}
	reply['message']='Sales Order detail'
	reply['status_code']='200'
	reply['data']={}

	url="http://130.211.193.136/api/method/erpnext.flutter_wallet.orderDetail?so_no={}".format(so_no)
	smilyResponse = requests.post(url)
	inventoryUpdated=smilyResponse.json()
	orderDetails = inventoryUpdated["message"]
	reply['data']=orderDetails


	allKeysInOrder = orderDetails.keys()

	# dd = findKeys('delivery_date',allKeysInOrder,orderDetails)
	dd = findKeys('transaction_date',allKeysInOrder,orderDetails)
	dt = findKeys('delivery_time',allKeysInOrder,orderDetails)

	format = '%Y-%M-%d'
	datetime_str = getdate(findKeys('transaction_date',allKeysInOrder,orderDetails))

	reply['data_condition_match']='No'
	if datetime_str<getdate():
		reply['data_condition_match']='Yes'
		dd = frappe.utils.now_datetime()
		dt = frappe.utils.now_datetime()

	try:
		d1=frappe.get_doc({
			"docstatus": 0,
			"doctype": "Sales Order",
			"name": "New Sales Order 1",
			"__islocal": 1,
			"__unsaved": 1,
			"company": "Satvaras",
			"territory": "India",
			"currency": "INR",
			"status": "Draft",
			"order_type": findKeys('order_type',allKeysInOrder,orderDetails),
			"po_no":so_no,
			"items": updateItemObject(orderDetails['items']),
			# "delivery_date":findKeys('delivery_date',allKeysInOrder,orderDetails),
			# "delivery_time":findKeys('delivery_time',allKeysInOrder,orderDetails),
			"delivery_date":dd,
			"custom_delivery_time":dt,
			"transaction_date": findKeys('transaction_date',allKeysInOrder,orderDetails),
			"payment":findKeys('payment',allKeysInOrder,orderDetails),
			"customer_name":findKeys('customer_name',allKeysInOrder,orderDetails),
			"custom_order_category":findKeys('order_category',allKeysInOrder,orderDetails),
			"customer":findKeys('customer',allKeysInOrder,orderDetails),
			"owner":findKeys('owner',allKeysInOrder,orderDetails),
			"special_note":findKeys('special_note',allKeysInOrder,orderDetails),
			"terms":findKeys('terms',allKeysInOrder,orderDetails),
			"address_display":findKeys('address_display',allKeysInOrder,orderDetails),
			"contact_mobile":findKeys('contact_mobile',allKeysInOrder,orderDetails),
			"custom_subscription_plan_id":findKeys('subscription_plan_id',allKeysInOrder,orderDetails),
		})
		reply['Createddata']=d1
		d2=d1.insert(ignore_permissions=True)

		return orderDetails
	except Exception as e:
		reply['error']=str(e)
		appErrorLog("Sales Order Create Error: {}".format(so_no),str(e))
		appErrorLog("Sales Order Create Error traceable: {}".format(so_no),str(traceback.format_exc()))
		return reply

@frappe.whitelist(allow_guest=True)
def updateItemObject(itemList):
	
	obj_update=[]
	for item in itemList:
		newitem = {}
		item_code = item['item_code']

		if item_code not in ['Green Lug Cap']:
			if item['qty'] not in ['0',0,'']:
				if item_code in ["Groundnut Cold Pressed Oil 1L","Cold Pressed Groundnut Oil 1L"]:
					item_code = "CPOG1L"
				elif item_code in ["Cold Pressed Groundnut Oil 5L"]:
					item_code = "CPOG5L"
				elif item_code in ["Groundnut Cold Pressed Oil 250ML",'Cold Pressed Groundnut Oil 250ML']:
					item_code = "CPOG250ML"
				elif item_code in ['Flaxseed Cold Pressed Oil 250ML','Cold Pressed Flaxseed Oil 250ml']:
					item_code = "CPOFL250ML"
				elif item_code in ['Cold Pressed flaxseed Oil 1liter','Cold Pressed flaxseed Oil 1liter','Flaxseed Cold Pressed Oil 1L']:
					item_code = "CPOFL1L"
				elif item_code in ['Coconut Cold Pressed Oil 1 kg','Coconut Cold Pressed Oil 1L','Cold Pressed Coconut Oil1L']:
					item_code = "CPOCO1kg"
				elif item_code in ['Coconut Cold Pressed Oil 250ML','Cold Pressed Coconut Oil 250ML']:
					item_code = "CPOCO250kg"
				elif item_code in ['Sesame Cold Pressed Oil 250ML','Cold Pressed Sesame Oil 250ml']:
					item_code = "CPOSE250ML"
				elif item_code in ['Sesame Cold Pressed Oil 1 kg','Sesame oil','Sesame Cold Pressed Oil 1L','Cold Pressed Sesame Oil 1L']:
					item_code = "CPOSE1L"
				elif item_code in ['Jamun Shot']:
					item_code = "CPSJ"
				elif item_code in ['ALMOND COLD PRESSED OIL 250 ML']:
					item_code = "CPOAL250"			

				newitem["item_code"]=item_code
				newitem["rate"]=item['net_rate']
				newitem["qty"]=item['qty']
				obj_update.append(newitem)
	return obj_update


##### Create Wallet
@frappe.whitelist(allow_guest=True)
def createWalletEntry(walletEntry):

	# frappe.local.form_dict = globleUserLogin()
	# frappe.local.cookie_manager = CookieManager()
	# frappe.local.login_manager = LoginManager()

	#appErrorLog("Wallet entry",walletEntry['name'])

	try:
		query = "SELECT name FROM `tabWallet` WHERE `old_erp_reference`='{}'".format(walletEntry['name'])
		previousentry = frappe.db.sql(query,as_dict=True)

		if len(previousentry)==0:
			d1=frappe.get_doc({
				"docstatus": 0,
				"doctype": "Wallet",
				"name": "New Wallet 1",
				"__islocal": 1,
				"__unsaved": 1,
				"status": "Draft",
				"transaction_date": walletEntry['transaction_date'],
				"payment_type":walletEntry['payment_type'],
				"payment_method":walletEntry['payment_method'],
				"payable_amount":walletEntry['payable_amount'],
				"wallet_balance":walletEntry['wallet_balance'],
				"customer":walletEntry['customer'],
				"owner":walletEntry['owner'],
				"payment_id":walletEntry['payment_id'],
				"creation":walletEntry['creation'],
				"modified":walletEntry['modified'],
				"customer_name":walletEntry['customer_name'],
				"sales_order":walletEntry['sales_order'],
				"old_erp_reference":walletEntry['name'],
			})
			d2=d1.insert(ignore_permissions=True)
			return d2
	
		return True
	except Exception as e:
		response={}
		appErrorLog("Wallet entry error".format(walletEntry['customer']),str(e))
		appErrorLog("Wallet entry error traceable".format(walletEntry['customer']),str(traceback.format_exc()))
		frappe.local.response['http_status_code'] = 500
		response["status"]="500"
		response["message"]=str(e)
		return response
































@frappe.whitelist(allow_guest=True)
def getYesterdayOrders100(allow_guest=True):
	
	today = datetime.today()
	firstDayTemp = today-timedelta(days=1)
	yesterdayDate = str(firstDayTemp).split(" ")[0]
	return getOrderListForDate(yesterdayDate)

@frappe.whitelist(allow_guest=True)
def getYesterdayOrders300(allow_guest=True):
	
	today = datetime.today()
	firstDayTemp = today-timedelta(days=1)
	yesterdayDate = str(firstDayTemp).split(" ")[0]
	return getOrderListForDate(yesterdayDate)

@frappe.whitelist(allow_guest=True)
def getYesterdayOrders500(allow_guest=True):
	
	today = datetime.today()
	firstDayTemp = today-timedelta(days=1)
	yesterdayDate = str(firstDayTemp).split(" ")[0]
	return getOrderListForDate(yesterdayDate)







@frappe.whitelist(allow_guest=True)
def getTodaysOrdersComparision(allow_guest=True):

	reply = {}
	reply['message']='Sales orders list'
	reply['status_code']='200'
	reply['data']=[]

	url="http://130.211.193.136/api/method/erpnext.flutter_wallet.getSalesOrderForDate?date={}".format(nowdate())
	smilyResponse = requests.post(url)
	inventoryUpdated=smilyResponse.json()
	oldERPOrders = inventoryUpdated['message']
	reply['oldERPOrders']=oldERPOrders

	query = "SELECT * FROM `tabSales Order` WHERE `docstatus`!=2 AND `transaction_date`='{}'".format(nowdate())
	dataList=frappe.db.sql(query,as_dict=1)
	newERPOrders = inventoryUpdated['message']
	reply['newERPOrders']=newERPOrders

	reply['different']=len(oldERPOrders)-len(newERPOrders)

	oldSoNumber = []
	for index, order in enumerate(oldERPOrders):
		oldSoNumber.append(order['name'])
		frappe.enqueue(walletBalanceComparision,queue='long',job_name="Createing todays Order",timeout=100000,phone=order['customer'])
		frappe.enqueue(orderComparision,queue='long',job_name="Compare Order",timeout=100000,order=order)

	differentOrders = []
	for index, order in enumerate(newERPOrders):
		if order['name'] not in oldSoNumber:
			differentOrders.append(order['name'])

	reply['different_orders']=differentOrders
	reply['different_orders_count']=len(differentOrders)

	return reply


@frappe.whitelist(allow_guest=True)
def orderComparision(order):

	reply={}

	query = "SELECT name FROM `tabSales Order` WHERE `po_no`='{}'".format(order['name'])
	previousentry = frappe.db.sql(query,as_dict=True)

	if len(previousentry)==0:
		d = frappe.get_doc({
			"doctype": "sync Process",
			"reason":'ORDER_NOT_FETCH',
			"order_no":order['name'],
		})
		d = d.insert(ignore_permissions=True)

	return reply




@frappe.whitelist(allow_guest=True)
def walletBalanceComparision(phone):

	reply={}
	url="http://130.211.193.136/api/method/erpnext.flutter_wallet.GetBalance?phone={}".format(phone)
	smilyResponse = requests.post(url)
	inventoryUpdated=smilyResponse.json()

	oldERPBalance = inventoryUpdated['message']
	reply['oldERPBalance']=oldERPBalance
	NewERPBalance = GetBalanceNew(phone)
	reply['NewERPBalance']=NewERPBalance

	matchthebalance = True
	result = 'MATCH'
	if oldERPBalance['AvailableBalance'] != NewERPBalance['AvailableBalance']:
		matchthebalance = False
		result = 'NOTMATCH'

	if oldERPBalance['WalletBalance'] != NewERPBalance['WalletBalance']:
		matchthebalance = False
		result = 'NOTMATCH'

	query = "DELETE FROM `tabsync Process` WHERE `order_no`='{}' AND `reason`='WALLET_MATCH'".format(phone)
	previousentry = frappe.db.sql(query,as_dict=True)

	if result=="NOTMATCH":
		d = frappe.get_doc({
			"doctype": "sync Process",
			"reason":'WALLET_MATCH',
			"order_no":phone,
			"old_erp_available":oldERPBalance['AvailableBalance'],
			"new_erp_available":oldERPBalance['AvailableBalance'],
			"old_erp_wallet_balance":oldERPBalance['WalletBalance'],
			"new_erp_wallet_balance":NewERPBalance['WalletBalance'],
			"result":result,
		})
		d = d.insert(ignore_permissions=True)


	# if not matchthebalance:
	# 	appErrorLog("Customer Wallet Not Match: {}".format(phone),str(reply))
		# appErrorLog("Customer Wallet Match: {}".format(phone),str(reply))
	# else:
	# 	appErrorLog("Customer Wallet Not Match: {}".format(phone),str(reply))

	return reply

@frappe.whitelist(allow_guest=True)
def GetBalanceNew(phono):

	try:
		totalUsedAmount= frappe.db.sql("""SELECT SUM(total) FROM `tabSales Order` where customer = '"""+phono+"""'""")
		
		totalSaleOrderAmount= frappe.db.sql("""SELECT SUM(total) FROM `tabSales Order` where customer = '"""+phono+"""' and `status`<>'Cancelled'""")
		
		# totalwalletamount=frappe.db.sql("""SELECT SUM(wallet_balance) FROM `tabWallet` where docstatus=1 and customer = '"""+phono+"""'""")
		totalwalletamount=frappe.db.sql("""SELECT SUM(wallet_balance) FROM `tabWallet` where customer = '"""+phono+"""'""")
		
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
def process_not_fetch_orders(allow_guest=True):

	salesorderlist = frappe.get_all('sync Process', filters=[
							["sync Process","reason","=",'ORDER_NOT_FETCH']], fields=['*'])

	for order in salesorderlist:
		jobname="Sales Order: {}".format(order["order_no"])
		frappe.enqueue(getSalesOrderDetail,queue='long',job_name=jobname,timeout=100000,so_no=order["order_no"])
		query = "DELETE FROM `tabsync Process` WHERE `order_no`='{}' AND `reason`='ORDER_NOT_FETCH'".format(order["order_no"])
		previousentry = frappe.db.sql(query,as_dict=True)

	reply={}
	reply["Total Order Scheduled"] = str(len(salesorderlist))

	return reply






##################### SYNC Process 

##### User
@frappe.whitelist(allow_guest=True)
def getUserDetails(phone):

	reply = {}
	reply['message']='Sales orders list'
	reply['status_code']='200'
	reply['data']=[]

	try:
		url="http://130.211.193.136/api/method/erpnext.flutter_wallet.getUserDetails?phone={}".format(phone)
		smilyResponse = requests.post(url)
		inventoryUpdated=smilyResponse.json()
		reply['response_get']=inventoryUpdated

		if inventoryUpdated['message']["status_code"]=="200":
			userDetails = inventoryUpdated['message']['data']
			reply['user_detail']=userDetails
			allKeysInOrder = userDetails.keys()
			# appErrorLog("Going for sign up","")
			# appErrorLog("Going for sign up",findKeys('first_name',allKeysInOrder,userDetails))
			# appErrorLog("Going for sign up",findKeys('last_name',allKeysInOrder,userDetails))
			# appErrorLog("Going for sign up",findKeys('city',allKeysInOrder,userDetails))
			# appErrorLog("Going for sign up",findKeys('pincode',allKeysInOrder,userDetails))

			# frappe.enqueue(SyncSignUpUpdate,queue='long',job_name="Createing sync user: {}".format(phone),timeout=100000,phoneNo=phone,firstName=str(findKeys('first_name',allKeysInOrder,userDetails)),lastName=str(findKeys('last_name',allKeysInOrder,userDetails)),city=findKeys('city',allKeysInOrder,userDetails),pincode=findKeys('pincode',allKeysInOrder,userDetails))
			return SyncSignUpUpdate(phone,str(findKeys('first_name',allKeysInOrder,userDetails)),str(findKeys('last_name',allKeysInOrder,userDetails)),findKeys('city',allKeysInOrder,userDetails),findKeys('pincode',allKeysInOrder,userDetails))
		else:
			reply['response_fail']="Not get customer detail"
			appErrorLog("Customer Create Error: {}".format(phone),"")

		return reply
	except Exception as e:
		reply['error']=str(e)
		appErrorLog("Customer Create Error: {}".format(phone),str(e))
		return reply


@frappe.whitelist(allow_guest=True)
def SyncSignUpUpdate(phoneNo,firstName,lastName,city,pincode):

	response= {}
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
		user = frappe.db.get("User", {"name": phoneNo})
 
		if user:
			response['user_found']="true"
			# appErrorLog("User updated","")
			response["customer_found"]="Yes"
			frappe.db.sql("""UPDATE `tabUser` SET `last_name`='"""+lastName+"""',`location`='"""+city+"""',`bio`='"""+pincode+"""', `first_name`='"""+firstName+"""' WHERE `name`='"""+phoneNo+"""'""")


			customerdetail = frappe.db.get("Customer", {"name": phoneNo})
			if not customerdetail:
				response['customer_not_found']="true"
				frappe.db.sql("""INSERT INTO `tabCustomer` (`name`, `owner`, `docstatus`,  `idx`, `naming_series`, `disabled`, `customer_name`, `territory`, `customer_group`, `customer_type`, `is_frozen`, `custom_city`, `custom_pincode`,`creation`,`modified`) VALUES ('"""+phoneNo+"""', '"""+phoneNo+"""', '0',  '0', 'CUST-', '0', '"""+firstName+""" """+lastName+"""', 'India','Individual', 'Individual', '0', '"""+city+"""', '"""+pincode+"""', '"""+str(frappe.utils.now_datetime())+"""', '"""+str(frappe.utils.now_datetime())+"""')""")
				# d = frappe.get_doc({
				# 	"doctype": "Customer",
				# 	"name": phoneNo,
				# 	"owner": phoneNo,
				# 	"docstatus": "0",
				# 	"idx": "0",
				# 	"naming_series": 'CUST-',
				# 	"disabled": '0',
				# 	"customer_name": "{} {}".format(firstName,lastName),
				# 	"territory": "India",
				# 	"customer_group": "Individual",
				# 	"customer_type": 'Individual',
				# 	"is_frozen": '0',
				# 	"custom_city": city,
				# 	"custom_pincode": pincode,
				# })
				# d.insert(ignore_permissions=True)

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


			frappe.db.sql("""UPDATE `tabCustomer` SET `customer_name`='"""+firstName+"""' '"""+lastName+"""',`custom_city`='"""+city+"""',`custom_pincode`='"""+pincode+"""' WHERE `name`='"""+phoneNo+"""'""")
		else:
			response["user_not_found"]="No"
			frappe.db.sql("""INSERT INTO `tabUser` (`name`, `owner`, `docstatus`, `idx`, `user_type`, `last_name`, `thread_notify`, `first_name`, `login_after`, `email`, `username`, `location`, `bio`,`creation`,`modified`) VALUES ('"""+phoneNo+"""', 'Guest', '0', '0', 'System User', '"""+lastName+"""', '1', '"""+firstName+"""', '0', '"""+phoneNo+"""@example.com', '"""+phoneNo+"""', '"""+city+"""', '"""+pincode+"""', '"""+str(frappe.utils.now_datetime())+"""', '"""+str(frappe.utils.now_datetime())+"""')""")			
			#	frappe.utils.now_datetime()	
			# d = frappe.get_doc({
			# 	"doctype": "User",
			# 	"name": phoneNo,
			# 	"owner": "Guest",
			# 	"docstatus": "0",
			# 	"idx": "0",
			# 	"user_type": 'System User',
			# 	"first_name": firstName,
			# 	"last_name": lastName,
			# 	"thread_notify": "1",
			# 	"login_after": "0",
			# 	"email": '{}@example.com'.format(phoneNo),
			# 	"username": phoneNo,
			# 	"location": city,
			# })
			# d.insert(ignore_permissions=True)

			frappe.db.sql("""INSERT INTO `tabCustomer` (`name`, `owner`, `docstatus`,  `idx`, `naming_series`, `disabled`, `customer_name`, `territory`, `customer_group`, `customer_type`, `is_frozen`, `custom_city`, `custom_pincode`,`creation`,`modified`) VALUES ('"""+phoneNo+"""', '"""+phoneNo+"""', '0',  '0', 'CUST-', '0', '"""+firstName+""" """+lastName+"""', 'India','Individual', 'Individual', '0', '"""+city+"""', '"""+pincode+"""', '"""+str(frappe.utils.now_datetime())+"""', '"""+str(frappe.utils.now_datetime())+"""')""")
			# d = frappe.get_doc({
			# 	"doctype": "Customer",
			# 	"name": phoneNo,
			# 	"owner": phoneNo,
			# 	"docstatus": "0",
			# 	"idx": "0",
			# 	"naming_series": 'CUST-',
			# 	"disabled": '0',
			# 	"customer_name": "{} {}".format(firstName,lastName),
			# 	"territory": "India",
			# 	"customer_group": "Individual",
			# 	"customer_type": 'Individual',
			# 	"is_frozen": '0',
			# 	"custom_city": city,
			# 	"custom_pincode": pincode,
			# })
			# d.insert(ignore_permissions=True)


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
		

		frappe.db.commit()
		# appErrorLog("Start for Sales order creatation","")
		frappe.enqueue(getSalesOrders,queue='long',job_name="Get Sales Order List: {}".format(phoneNo),timeout=100000,phone=phoneNo)
		response["status"]=200
		response["message"]="customer created"
		return response
	except Exception as e:
		error_log=app_error_log(phoneNo,str(e))
		response["status"]=500
		response["message"]=str(e)
		response["message_trackeable"]=traceback.format_exc()
		return response


##### Orders
@frappe.whitelist(allow_guest=True)
def getSalesOrders(phone):

	reply = {}
	reply['message']='Sales orders list'
	reply['status_code']='200'
	reply['data']=[]

	url="http://130.211.193.136/api/method/erpnext.flutter_wallet.getAllSalesOrder?phone={}".format(phone)
	smilyResponse = requests.post(url)
	inventoryUpdated=smilyResponse.json()
	totalWallet = inventoryUpdated["message"]

	for index, order in enumerate(totalWallet):
		frappe.enqueue(getSalesOrderDetail,queue='long',job_name="Create Sales Order: {}".format(order['name']),timeout=100000,so_no=order['name'])

	# appErrorLog("Start for wallet creatation","")
	frappe.enqueue(getAllWalletTransacation,queue='long',job_name="Get All Wallets: {}".format(phone),timeout=100000,phone=phone)
	return totalWallet




##### Wallet
@frappe.whitelist(allow_guest=True)
def getAllWalletTransacation(phone):

	reply = {}
	reply['message']='Wallet list'
	reply['status_code']='200'
	reply['data']=[]

	url="http://130.211.193.136/api/method/erpnext.flutter_wallet.getAllWalletTransacation?phone={}".format(phone)
	smilyResponse = requests.post(url)
	inventoryUpdated=smilyResponse.json()
	if len(inventoryUpdated.keys())!=0:
		totalWallet = inventoryUpdated["message"]

		for index, order in enumerate(totalWallet):
			frappe.enqueue(createWalletEntry,queue='long',job_name="Create Wallet Entry: {}".format(order['name']),timeout=100000,walletEntry=order)

		return totalWallet
	
	return "No wallet transaction found"








@frappe.whitelist()
def app_error_log(title,error):
	d = frappe.get_doc({
			"doctype": "App Error Log",
			"title":title,
			"error":error
		})
	d = d.insert(ignore_permissions=True)
	return d	

@frappe.whitelist()
def appErrorLog(title,error):
	d = frappe.get_doc({
			"doctype": "App Error Log",
			"title":title,
			"error":error
		})
	d = d.insert(ignore_permissions=True)
	return d

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
