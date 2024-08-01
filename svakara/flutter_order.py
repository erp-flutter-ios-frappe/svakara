import frappe
from frappe import throw, _, scrub
import traceback
import json
import collections
import random
from frappe.utils import nowdate,add_days
from svakara.globle import appErrorLog
from svakara.order_submit import salesOrderSubmit



@frappe.whitelist(allow_guest=True)
def order_cart_created(**kwargs):

	param=frappe._dict(kwargs)

	reply={}
	reply["status_code"]="200"
	reply["message"]="Sucessfully"
	reply["data"]={}
	
	try:

		# query = "SELECT * from `tabCart Sales Order` WHERE `customer`='{}' AND `sync`=0 AND `name`='{}'".format(param['customer'],param['previousCart'])
		# data = frappe.db.sql(query,as_dict=True)
		# if len(data)!=0:

		d1=frappe.get_doc({
			"docstatus": 0,
			"doctype": "Cart Sales Order",
			"name": "New Cart Sales Order 1",
			"__islocal": 1,
			"__unsaved": 1,
			"customer": param['customer'],
			"transaction_date": str(nowdate()),
			"delivery_date": param['delivery_date'],
		})
		if d1.insert(ignore_permissions=True):
			reply["data"]=d1
			reply["message"]="Cart created."
			return reply
		else:
			frappe.local.response['http_status_code'] = 500
			reply["data"]={}
			reply["message"]="Cart not created."
			reply["status_code"]="500"
			return reply
		
		
	except Exception as e:
		frappe.local.response['http_status_code'] = 500
		reply["status_code"]="500"
		reply["message"]=str(e)
		reply['message_traceable']=traceback.format_exc()
		appErrorLog('Cart - flutter_order',str(e))
		appErrorLog('Cart - flutter_order - traceback',str(traceback.format_exc()))
		return reply


@frappe.whitelist(allow_guest=True) 
def order_cart_item_upload(**kwargs):

	param=frappe._dict(kwargs)

	reply={}
	reply["status_code"]="200"
	reply["message"]=""
	reply["data"]={}
	
	try:
		parent = frappe.get_doc('Cart Sales Order', param['cardID'])

		child = frappe.new_doc("Cart Sales Order Child")
		child.update({'item_code': param['item_code'],
		'qty': param['qty'],
		'rate': param['rate'],
		'parent': parent.name,
		'parenttype': 'Cart Sales Order',
		'parentfield': 'items'})
		parent.items.append(child)
		parent.save(ignore_permissions=True)
		frappe.db.commit()

		reply["message"]="child added sucessfully"
		reply["status_code"]="200"
		frappe.local.response['http_status_code'] = 200
		
	except Exception as e:
		frappe.local.response['http_status_code'] = 500
		reply["status_code"]="500"
		reply["message"]=str(e)
		reply['message_traceable']=traceback.format_exc()
		appErrorLog('Cart Items - flutter_order',str(e))
		appErrorLog('Cart Items - flutter_order - traceback',str(traceback.format_exc()))

	return reply


@frappe.whitelist(allow_guest=True)
def Order_Place(**kwargs):
	
	param=frappe._dict(kwargs)

	reply={}
	reply["status_code"]="200"
	reply["message"]=""
	reply["data"]={}

	cartID = param['cartID']

	try:
		if not frappe.db.exists("Cart Sales Order", cartID):
			reply["message"]="Cart not found."
			reply["status_code"]="500"
			frappe.local.response['http_status_code'] = 500
			return reply

		doc_cart=frappe.get_doc("Cart Sales Order",cartID)

		query_so = "SELECT * FROM `tabSales Order` WHERE `po_no`='{}'".format(doc_cart.name)
		previousOrderList = frappe.db.sql(query_so,as_dict=1)
		if len(previousOrderList)!=0:
			reply["message"]="Sales order is already placed."
			frappe.local.response['http_status_code'] = 500
			reply["status_code"]="500"
			return reply

		cart_orderItems=frappe.get_all("Cart Sales Order Child",filters=[["Cart Sales Order Child","parent","=",doc_cart.name]],fields=["*"])
		if len(cart_orderItems)>0:
			customer_code = doc_cart.customer
			transaction_date = doc_cart.transaction_date
			delivery_date = param['delivery_date']
			orderNumber = doc_cart.name

			address_id=frappe.db.sql("""select `tabAddress`.name from `tabAddress` inner join `tabDynamic Link` on `tabAddress`.name=`tabDynamic Link`.parent where `tabDynamic Link`.link_name=%s""",customer_code)

			#return address_id
			if not len(address_id)==0:
				address_doc=frappe.get_doc("Address",address_id[0][0])

			payment_type = param['payment_type']

			d2 = {}
			d1=frappe.get_doc({
				"docstatus": 0,
				"doctype": "Sales Order",
				"name": "New Sales Order 1",
				"__islocal": 1,
				"__unsaved": 1,
				"company": "Svakara",
				"order_type": "Sales",
				# "territory": "India",
				# "currency": "INR",
				# "price_list_currency": "INR",
				# "apply_discount_on": "Net Total",
				# "party_account_currency": "INR",
				"status": "Draft",
				"apply_discount_on":"Grand Total",
				"transaction_date": str(transaction_date),
				"delivery_date":str(delivery_date),
				"items":order_item_preparation(cart_orderItems,customer_code),
				# "terms": "",
				"customer": str(customer_code),
				# "discount_amount":flt(discount),
				# "taxes":json.loads(tax_type),
				"payment_type":payment_type,
				# "order_payment_type":payment_type,
				"po_no": orderNumber,
				# "brillare_order_type": brillare_order_type,
				# "sales_person":salesPerson,
				# "employee":salesPerson,
				# "courier_partner_order_id":distributor,
				# "cumulative_scheme_order":int(offerGet),
				# "user":userName
			})
			d2=d1.insert(ignore_permissions=True)
			reply["status_code"]="200"
			reply["message"]="Order place sucessfully."
			reply["data"]=d2
			reply['name']=str(d2.name)
			frappe.enqueue(salesOrderSubmit,queue='long',job_name="Submit order: {}".format(d2.name),timeout=100000,so_no=str(d2.name))



			return reply
		else:
			reply["status"]="500"
			reply["message"]="Sales order items not found."
			reply["data"]=None
			return reply
				
	except Exception as e:
		frappe.local.response['http_status_code'] = 500
		reply["status_code"]="500"
		reply["message"]=str(e)
		reply["message_error"]=str(e)
		reply["message_traceable"] = str(traceback.format_exc())
		reply["data"]={}
		return reply


@frappe.whitelist(allow_guest=True)
def order_item_preparation(item_list,customer_code):

	finalItemList=[]
	for item in item_list:
		itemObject = {}
		itemObject['item_code']=item['item_code']
		itemObject['qty']=item['qty']
		itemObject['rate']=item['rate']
		finalItemList.append(itemObject)

	return finalItemList



























































@frappe.whitelist(allow_guest=True)
def subscription_start(**kwargs):

	parameters=frappe._dict(kwargs)
	allParamKeys = parameters.keys()

	reply={}
	reply['message']=""
	reply['status_code']="200"


	if 'customer' not in allParamKeys:
		frappe.local.response['http_status_code'] = 500
		reply['message']="Customer not found."
		reply['status_code']="500"
		return reply

	if 'item_code' not in allParamKeys:
		frappe.local.response['http_status_code'] = 500
		reply['message']="Item not found."
		reply['status_code']="500"
		return reply		
		
	if parameters['isEdit'] in ['1',True,'true','True']:
		update_query = "UPDATE `tabSubscription Item` SET `start_date`= '{}', `end_date`='{}', `monday`='{}', `tuesday`='{}', `wednesday`='{}', `thursday`='{}', `friday`='{}', `saturday`='{}', `sunday`='{}' WHERE `name`='{}'".format(parameters['start_date'],parameters['end_date'],parameters['monday'],parameters['tuesday'],parameters['wednesday'],parameters['thursday'],parameters['friday'],parameters['saturday'],parameters['sunday'],parameters['subscription_id'])
		test = frappe.db.sql(update_query)
		reply['message']="Subscription update sucessfully. Your subscription number is {}.".format(parameters['subscription_id'])
		reply['status_code']="200"
		return reply




	try:
		d1=frappe.get_doc({
			"docstatus": 0,
			"doctype": "Subscription Item",
			"name": "New Subscription Item 1",
			"__islocal": 1,
			"__unsaved": 1,
			"customer":parameters['customer'],
			"start_date":parameters['start_date'],
			"end_date":parameters['end_date'],
			"item_code":parameters['item_code'],
			"monday":parameters['monday'],
			"tuesday":parameters['tuesday'],
			"wednesday":parameters['wednesday'],
			"thursday":parameters['thursday'],
			"friday":parameters['friday'],
			"saturday":parameters['saturday'],
			"sunday":parameters['sunday'],
		})
		d2=d1.insert(ignore_permissions=True)
		if d2:
			reply['message']="Subscription start sucessfully. Your subscription number is {}.".format(d2.name)
			reply['status_code']="200"
			return reply

	except Exception as e:
		frappe.local.response['http_status_code'] = 500
		reply["status"]=500
		reply["message"]=str(e)
		reply['message_traceable']=traceback.format_exc()

	return reply


@frappe.whitelist(allow_guest=True)
def subscription_check(**kwargs):

	parameters=frappe._dict(kwargs)
	allParamKeys = parameters.keys()

	reply={}
	reply['message']="Subscription not found."
	reply['status_code']="200"
	reply['data']={}


	if 'customer' not in allParamKeys:
		frappe.local.response['http_status_code'] = 500
		reply['message']="Customer not found."
		reply['status_code']="500"
		return reply

	if 'item_code' not in allParamKeys:
		frappe.local.response['http_status_code'] = 500
		reply['message']="Item not found."
		reply['status_code']="500"
		return reply		




	try:
		query = "SELECT * from `tabSubscription Item` WHERE `customer`='{}' AND `item_code`='{}'".format(parameters['customer'],parameters['item_code'])
		data = frappe.db.sql(query,as_dict=True)
		if len(data)!=0:
			reply['message']="Subscription found."
			reply['status_code']="200"
			reply['data']=data[0]

	except Exception as e:
		frappe.local.response['http_status_code'] = 500
		reply["status"]=500
		reply["message"]=str(e)
		reply['message_traceable']=traceback.format_exc()

	return reply







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











