import frappe
from frappe import throw, _, scrub
import traceback
import json
import collections
import random
from frappe.utils import nowdate,add_days


@frappe.whitelist()
def appErrorLog(title,error):
	d = frappe.get_doc({
			"doctype": "App Error Log",
			"title":title,
			"error":traceback.format_exc()
		})
	d = d.insert(ignore_permissions=True)
	return d

@frappe.whitelist()
def appErrorLog1(title,error):
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
			response["status"]=int(status)
		else:
			frappe.local.response['http_status_code'] = 200
			response["status"]=200
		response["message"]=message
		response["data"]=data
	else:
		error_log=appErrorLog(frappe.session.user,str(error))
		frappe.local.response['http_status_code'] = 500

		if status:
			response["status"]=status
		else:
			response["status"]=500
		response["message"]=str(error)
		response["data"]=None
	return response


@frappe.whitelist()
def updateItemObject(obj):
	
	obj_update=[]
	for item in json.loads(obj):
		if int(item["is_free"])==1:
			item["rate"]=0
			item["price_list_rate"]=0
			item["amount"]=0
			item["expense_account"] = 'Quantity Purchase Scheme - BSPL'
		obj_update.append(item)
	return obj_update


@frappe.whitelist()
def salesOrderCheckMessage(message):
	response={}
	frappe.local.response['http_status_code'] = 200
	response["status"]="200"
	response["status_message"]=message
	response["message"]=message
	return response


@frappe.whitelist(allow_guest=True)
def itemStatus(delivery_date,pincode):
	response={}
	try:
		totalItems = json.loads(item_object)

		return giftMessage("Sucessfully","SUCCESS")

	except Exception as e:
		error_log=appErrorLog(frappe.session.user,e)
		frappe.local.response['http_status_code'] = 500
		response["status"]="500"
		response["message"]=str(e)
		response["data"]=None
		return response

@frappe.whitelist(allow_guest=True)
def checkSalesOrder(item_object,delivery_date,delivery_time,coupencode,pincode):
	response={}
	try:
		totalItems = json.loads(item_object)

		return giftMessage("Sucessfully","SUCCESS")

	except Exception as e:
		error_log=appErrorLog(frappe.session.user,e)
		frappe.local.response['http_status_code'] = 500
		response["status"]="500"
		response["message"]=str(e)
		response["data"]=None
		return response

@frappe.whitelist()
def salesOrderMessage(message,data):
	response={}
	frappe.local.response['http_status_code'] = 200
	response["status"]="200"
	response["message"]=message
	response["data"]=data
	return response

def itemType(item_code):
	item_list=frappe.get_list("Item",filters=[["Item","item_group","=","Products"],["Item","item_code","=",item_code]],fields=['*'],order_by="sort_order")
	if len(item_list)!=0:
		if item_list[0]["item_type"]=="juice":
			return 1

	return 0		


@frappe.whitelist(allow_guest=True)
def createSalesOrder(item_object,delivery_date,delivery_time,order_type,address,addresscode,payment_type,payment_id,amount,customer,customer_name,order_cat,special_note,terms,contact_mobile,coupencode,rechrgeAmount):

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
					"order_type": order_type,
					"items": json.loads(item_object),
					"delivery_date":delivery_date,
					"custom_delivery_time":delivery_time,
					"transaction_date": delivery_date,
					"custom_payment_mode":payment_type,
					"customer_name":customer_name,
					"custom_order_category":order_cat,
					"customer":customer,
					"owner":customer,
					"custom_special_note":special_note,
					"terms":terms,
					"address_display":address,
					"contact_mobile":contact_mobile,
					"po_no":"APP"
				})
		d2=d1.insert(ignore_permissions=True)

		if coupencode != None:
			if(coupencode.upper()=="STRS"):
				totalItems = json.loads(item_object)
				totalJuiceCount = 0
				totalWalletEntry = 0
				for itm in totalItems:
					itmTypeinDB = int(itemType(itm["item_code"]))
					if itmTypeinDB == 1:
						totalJuiceCount += int(itm["qty"])
						itemRate = float(itm["rate"])
						tempdis = itemRate - 100
						tempdis = tempdis * int(itm["qty"])
						if tempdis > 0:
							totalWalletEntry += int(tempdis)

				if totalJuiceCount >= 5 and totalWalletEntry > 0:
					d11=frappe.get_doc({
						"docstatus": 0,
						"doctype": "Wallet",
						"name": "New Wallet 1",
						"__islocal": 1,
						"__unsaved": 1,
						"status": "Draft",
						"transaction_date": nowdate(),
						"payment_type":"Payment",
						"payment_method":"Wallet",
						"payable_amount":totalWalletEntry,
						"wallet_balance":totalWalletEntry,
						"customer":customer,
						"owner":customer,
						"payment_id":"",
					})
					d22=d11.insert(ignore_permissions=True)
					if d22:
						d22.submit()


		return salesOrderMessage("Successfully Order Placed",d2)

	except Exception as e:
		response={}
		error_log=appErrorLog(frappe.session.user,e)
		frappe.local.response['http_status_code'] = 500
		response["status"]="500"
		response["message"]=str(e)
		return response


@frappe.whitelist(allow_guest=True)
def getPlanList(allow_guest=True):
	try:
		#planList=frappe.get_all('Plan List', fields=['*'])

		queryCCCOrder = "SELECT * FROM `tabPlan List`"
		planList = frappe.db.sql(queryCCCOrder,as_dict=1)

		response={}
		if len(planList) > 0:
			response["data"]=planList
		else:
			response["data"]=[]

		return response	
	except Exception as e:
		return generateResponse("F",error=e)


@frappe.whitelist(allow_guest=True)
def deteleTestingOrder(allow_guest=True):
	itemList=frappe.db.sql("""DELETE FROM `tabSales Order` WHERE customer=9426435057""")
	return 'deleted'


@frappe.whitelist(allow_guest=True)
def deleteSalesOrderFromSchedule(planid,salesOrderno):
	response={}

	plan=frappe.get_all('Plan Subscriber List', fields=['*'], filters=[["Plan Subscriber List","name","=",planid]])

	totaldeleted = 0
	salesOrders = []
	if len(plan)!=0:
		totaldeleted = plan[0]['deleted_order_count']
		salesOrders=frappe.get_all('Sales Order', fields=['delivery_date'], filters=[["Sales Order","custom_subscription_plan_id","=",planid],["Sales Order","customer","=",plan[0]['customer']]],order_by="delivery_date")

	response['salesorder']=salesOrders[len(salesOrders)-1]

	if int(totaldeleted) > 3:
		frappe.local.response['http_status_code'] = 200
		response["status"]=str(300)
		response["status_message"]='DELETED'
		response["message"]="You can delete maximum 3 order in one subcription plan"
		return response

	delivery_date = add_days(salesOrders[len(salesOrders)-1]['delivery_date'],1)
	frappe.db.set_value("Sales Order",salesOrderno,"delivery_date",delivery_date)

	#updated deleted count in list	
	updateddeletedcount = int(totaldeleted) + 1
	frappe.db.set_value("Plan Subscriber List",planid,"deleted_order_count",str(updateddeletedcount))
	frappe.db.commit()
	frappe.local.response['http_status_code'] = 200
	response["status"]=str(200)
	response["status_message"]='DELETED'
	response["message"]="Delete Sucessfully"
	return response

@frappe.whitelist(allow_guest=True)
def deleteSalesOrder(salesOrderno):
	response={}

	queryCCCOrder = "SELECT * FROM `tabSales Order` WHERE `name`='{}'".format(salesOrderno)
	planList = frappe.db.sql(queryCCCOrder,as_dict=1)
	if len(planList)!=0:
		if int(planList[0]['docstatus'])==0:
			frappe.db.sql("""DELETE FROM `tabSales Order` WHERE name='"""+salesOrderno+"""'""")
			test = frappe.delete_doc("Sales Order",salesOrderno)
			frappe.db.commit()
			frappe.local.response['http_status_code'] = 200
			response["status"]=str(200)
			response["status_message"]='DELETED'
			response["message"]="Delete Sucessfully"
		else:
			response["status"]=str(500)
			response["status_message"]='NOTDELETED'
			response["message"]="Delete Sucessfully"
	else:
			response["status"]=str(500)
			response["status_message"]='NOTDELETED'
			response["message"]="Delete Sucessfully"
	
	return response


@frappe.whitelist(allow_guest=True)
def salesOrderDetail(salesOrderno):
	salesOrder=frappe.get_all('Sales Order', fields=['*'], filters=[["Sales Order","name","=",salesOrderno]])

	salesOrderItem=frappe.get_all('Sales Order Item', fields=['*'], filters=[["Sales Order Item","parent","=",salesOrderno]])

	

	response={}
	frappe.local.response['http_status_code'] = 200
	response["status"]=str(200)
	response["status_message"]='FETCH'
	response["message"]="Fetch Sucessfully"
	response["data"]=salesOrder
	response["items"]=salesOrderItem


	return response



@frappe.whitelist(allow_guest=True)
def updateSalesOrderFromSchedule(item_object,salesOrderno):

	salesOrder=frappe.get_all('Sales Order', fields=['*'], filters=[["Sales Order","name","=",salesOrderno]],order_by="delivery_date")
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
					"order_type": salesOrder[0]['order_type'],
					"items": json.loads(item_object),
					"delivery_date":salesOrder[0]['delivery_date'],
					"custom_delivery_time":salesOrder[0]['custom_delivery_time'],
					"transaction_date": salesOrder[0]['transaction_date'],
					"custom_payment_mode":salesOrder[0]['custom_payment_mode'],
					"customer_name":salesOrder[0]['customer_name'],
					"custom_order_category":salesOrder[0]['custom_order_category'],
					"customer":salesOrder[0]['customer'],
					"owner":salesOrder[0]['owner'],
					"custom_special_note":salesOrder[0]['custom_special_note'],
					"terms":salesOrder[0]['terms'],
					"address_display":salesOrder[0]['address_display'],
					"contact_mobile":salesOrder[0]['contact_mobile'],
					"custom_subscription_plan_id":salesOrder[0]['custom_subscription_plan_id']

				})
		d2=d1.insert(ignore_permissions=True)
		frappe.db.sql("""DELETE FROM `tabSales Order` WHERE name='"""+salesOrderno+"""'""")
		frappe.db.commit()
		return salesOrderMessage("Successfully Order Placed",d2)

	except Exception as e:
		response={}
		error_log=appErrorLog(frappe.session.user,e)
		frappe.local.response['http_status_code'] = 500
		response["status"]="500"
		response["message"]=str(e)
		return response


@frappe.whitelist(allow_guest=True)
def getSalesOrderDetailSchedule(planid,salesOrderno):
	response={}

	subc=frappe.get_all('Plan Subscriber List', fields=['*'], filters=[["Plan Subscriber List","name","=",planid]])
	salesOrder=frappe.get_all('Sales Order', fields=['*'], filters=[["Sales Order","name","=",salesOrderno],["Sales Order","custom_subscription_plan_id","=",planid],["Sales Order","customer","=",subc[0]['customer']]],order_by="delivery_date")
	itemAdded=frappe.db.sql("""SELECT * FROM `tabSales Order Item` WHERE parent LIKE %s""",salesOrderno,as_dict=True)
	plan=frappe.get_all('Plan List', fields=['*'], filters=[["Plan List","name","=",subc[0]['plan_id']]])

	planItemList=frappe.db.sql("""SELECT * FROM `tabplanlistitem` WHERE parent LIKE %s""",subc[0]['plan_id'],as_dict=True)

	response['orderdetail']=salesOrder
	response['items']=itemAdded
	response['plan_items']=planItemList
	response['subscriptiondetail']=subc
	response['plandetail']=plan


	frappe.local.response['http_status_code'] = 200
	response["status"]=str(200)
	response["status_message"]='LISED'
	response["message"]="List Sucessfully"
	return response


@frappe.whitelist(allow_guest=True)
def getSalesOrderScheduleList(planid):
	plan=frappe.get_all('Plan Subscriber List', fields=['*'], filters=[["Plan Subscriber List","name","=",planid]])
	plandetail=frappe.get_all('Plan List', fields=['*'], filters=[["Plan List","name","=",plan[0]['plan_id']]])

	salesOrdersReturn=[]
	if len(plan)!=0:
		salesOrders=frappe.get_all('Sales Order', fields=['*'], filters=[["Sales Order","custom_subscription_plan_id","=",planid],["Sales Order","customer","=",plan[0]['customer']]],order_by="delivery_date")
		if len(salesOrders)!=0:
			for order in salesOrders:
				salesOrdersItems=frappe.get_all('Sales Order Item', fields=['*'], filters=[["Sales Order Item","parent","=",order['name']]])
				#itemAdded=frappe.get_all('Item', fields=['*'], filters=[["Item","item_code","=",salesOrdersItems[0]['item_code']]])

				itemAdded=frappe.db.sql("""SELECT * FROM `tabItem` WHERE item_code IN (SELECT item_code FROM `tabSales Order Item` WHERE parent LIKE %s)""",order['name'],as_dict=True)

				order['items']=itemAdded
				order['itemsInOrder']=salesOrdersItems
				order['perdaybottol']=plandetail[0]['bottol_per_day']
				salesOrdersReturn.append(order)

	return salesOrdersReturn


@frappe.whitelist(allow_guest=True)
#def salesOrderSchedule(planid,customer_name,customer,address,addresscode,daysdifferent,paymentType,PaymentID,walletused,amountPaid,orderTime):
def salesOrderSchedule(planid,customer_name,customer,address,addresscode,daysdifferent,paymentType,PaymentID,walletused,amountPaid,orderTime11):


	if paymentType=="Cash On Delivery":
		paymentType="Cash"

	plan=frappe.get_all('Plan List', fields=['*'], filters=[["Plan List","name","=",planid]])

	# appErrorLog1("Plan List",str(plan))


	planitems=frappe.db.sql("""select itemcode from `tabplanlistitem` where parent LIKE %s""",(planid),as_dict=True)
	response={}

	if paymentType!="Wallet":
		#wallet entry
		w1=frappe.get_doc({
					"docstatus": 0,
					"doctype": "Wallet",
					"name": "New Wallet 1",
					"__islocal": 1,
					"__unsaved": 1,
					"status": "Draft",
					"transaction_date": nowdate(),
					"payment_type":"Payment",
					"payment_method":paymentType,
					"payable_amount":int(str(amountPaid)),
					"wallet_balance":int(str(amountPaid)),
					"customer":customer,
					"owner":customer,
				})
		w2=w1.insert(ignore_permissions=True)

		if paymentType != 'Cash':
			w2.submit()

	# To make enry in plan list
	planentry=frappe.get_doc({
						"docstatus": 0,
						"doctype": "Plan Subscriber List",
						"name": "New Plan Subscriber List 1",
						"__islocal": 1,
						"__unsaved": 1,
						"owner":customer,
						"customer":customer,
						"plan_id":planid
					})
	planentryresponse=planentry.insert(ignore_permissions=True)
	response["name"]=str(planentryresponse.name)

	#get plan item list
	itemList=frappe.db.sql("""SELECT * FROM `tabItem` WHERE item_code IN (SELECT itemcode FROM `tabplanlistitem` WHERE parent LIKE %s)""",planid,as_dict=True)
	itemsStr = ""

	itemsObjecs=[]
	index1=0
	for y in range(0, int(str(plan[0]['bottol_per_day']))):
		if index1 >= len(itemList):
			index1 = 0

		itemsObjecs.append(itemList[index1])
		index1 = index1 + 1

	for y in range(0, int(str(plan[0]['bottol_per_day']))):
		#itemObject = random.choice(itemList)
		itemObject = itemsObjecs[y]

		if y==0:
			itemsStr = itemsStr + "{"
		else:
			itemsStr = itemsStr + ",{"

		#itemsStr = itemsStr + '"qty":"{}",'.format(str(plan[0]['bottol_per_day']))
		itemsStr = itemsStr + '"qty":"1",'

		itemsStr = itemsStr + '"item_code":"{}",'.format(itemObject['item_code'])
		itemsStr = itemsStr + '"rate":"{}"'.format(str(plan[0]['per_bottle_cost']))
		#itemsStr = itemsStr + '"discount_amount":"{}"'.format(int(str(plan[0]['per_bollot_discount'])))
		itemsStr = itemsStr + "}"

	itemsStr = "[" + itemsStr + "]"


	# appErrorLog1("Item String",itemsStr)

	totalOrderProcess=[]
	for x in range(0, int(str(plan[0]['days']))):
		delivery_date = add_days(frappe.utils.data.get_datetime(),int(str(x))+int(daysdifferent))

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
						"order_type": "Sales",
						"items": json.loads(itemsStr),
						"delivery_date":delivery_date,
						"custom_delivery_time":orderTime11,
						#"delivery_time":'Morning 5 to 7',
						"transaction_date": delivery_date,
						"custom_payment_mode":"Paid",
						"customer_name":customer_name,
						"custom_order_category":"Subscription",
						"customer":customer,
						"owner":customer,
						"custom_special_note":"Subscription Order",
						"terms":"Paid",
						"address_display":address,
						"contact_mobile":customer,
						"custom_subscription_plan_id":str(planentryresponse.name),
						"apply_discount_on":"Grand Total",
						"discount_amount":0,
						"po_no":"APP"
						#"discount_amount":int(str(plan[0]['discount_per_day'])),
					})
			d2=d1.insert(ignore_permissions=True)
			totalOrderProcess.append(d2)
		except Exception as e:
			response={}
			error_log=appErrorLog(frappe.session.user,e)
			frappe.local.response['http_status_code'] = 500
			response["status"]="500"
			response["message"]=str(e)
			totalOrderProcess.append(response)


	response["totalorderprocess"]=totalOrderProcess

	return response


@frappe.whitelist()
def applyCoupnCodeMessage(message,status_message,code):
	response={}
	frappe.local.response['http_status_code'] = 200
	response["status"]=str(code)
	response["status_message"]=status_message
	response["message"]=message
	return response


@frappe.whitelist(allow_guest=True)
def applyCoupanCode(item_object,coupencode,order_type):
	response={}
	#ordertype = sales, gift
	try:
		totalItems = json.loads(item_object)
		if(coupencode.upper()=="STRS"):
			return applyCoupnCodeMessage("Any 5 juices at 500. You can order 5 juices you will get discount in your wallet.","Eligiable",211)

		return applyCoupnCodeMessage("You are not eligible","NotEligiable",201)

	except Exception as e:
		error_log=appErrorLog(frappe.session.user,e)
		frappe.local.response['http_status_code'] = 500
		response["status"]="500"
		response["message"]=str(e)
		response["data"]=None
		return response

@frappe.whitelist()
def giftMessage(message,status_message):
	response={}
	frappe.local.response['http_status_code'] = 200
	response["status"]="200"
	response["status_message"]=status_message
	response["message"]=message
	return response


@frappe.whitelist(allow_guest=True)
def giftValidation(item_object,pincode):

	response={}
	try:
		totalItems = json.loads(item_object)

		return giftMessage("Sucessfully","SUCCESS")

	except Exception as e:
		error_log=appErrorLog(frappe.session.user,e)
		frappe.local.response['http_status_code'] = 500
		response["status"]="500"
		response["message"]=str(e)
		response["data"]=None
		return response







@frappe.whitelist()
def getSalesOrderListPast():
	try:
		salesorder_list=frappe.get_all('Sales Order',filters=[["Sales Order","delivery_date","<",nowdate()],["Sales Order","status","!=","Cancelled"],["Sales Order","customer","=",frappe.session.user]],fields=['*'],limit_page_length=100,order_by="delivery_date desc")
		
		response={}
		if len(salesorder_list) > 0:
			response["data"]=salesorder_list
		else:
			response["data"]=[]

		return response	
	except Exception as e:
		return generateResponse("F",error=e)

@frappe.whitelist(allow_guest=True)
def getSalesOrderListFeature(allow_guest=True):
	try:
		salesorder_list=frappe.get_all('Sales Order',fields=['*'], filters=[["Sales Order","delivery_date",">=",nowdate()],["Sales Order","status","!=","Cancelled"],["Sales Order","customer","=",frappe.session.user]],order_by="delivery_date")
		response={}
		if len(salesorder_list) > 0:
			response["data"]=salesorder_list
		else:
			response["data"]=[]

		return response	
	except Exception as e:
		return generateResponse("F",error=e)











