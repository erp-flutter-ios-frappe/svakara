import frappe
from frappe import throw, _, scrub
import traceback



@frappe.whitelist(allow_guest=True)
def Item_list_production(allow_guest=True):
	
	item_res=[]
	item_list=frappe.get_all("Item",filters=[["Item","item_group","in",["Raw Material"]],["Item","disabled","=",0]],fields=['*'],order_by="custom_sort_order")
	for item in item_list:
		item["stock_balance"]=getItemBalanceNew(item["item_code"],"Stores - SAT")
		item_res.append(item)
	return item_res

@frappe.whitelist(allow_guest=True)
def Item_list_finish_item(allow_guest=True):
	
	item_res=[]
	item_list=frappe.get_all("Item",filters=[["Item","item_group","in",["Products"]],["Item","disabled","=",0]],fields=['*'],order_by="custom_sort_order")
	for item in item_list:
		item["stock_balance"]=getItemBalanceNew(item["item_code"],"Finished Goods - SAT")
		item_res.append(item)
	return item_res

@frappe.whitelist(allow_guest=True)
def Item_list_finish_item_app(allow_guest=True):
	# Use to fetch product list into applications
	item_res=[]
	item_list=frappe.get_all("Item",filters=[["Item","item_group","in",["Products"]],["Item","disabled","=",0]],fields=['*'],order_by="custom_sort_order")
	for item in item_list:
		item["stock_balance"]=1
		item["servicibility"]=1
		item['qty'] = '0'
		item_res.append(item)
	return item_res

@frappe.whitelist(allow_guest=True)
def Item_list_airport(allow_guest=True):
	
	item_res=[]
	item_list=frappe.get_all("Item",filters=[["Item","item_group","in",["Products"]],["Item","disabled","=",0]],fields=['*'],order_by="custom_sort_order")
	for item in item_list:
		item["stock_balance"]=getItemBalanceNew(item["item_code"],"Airport Ahmedabad - SAT")
		item_res.append(item)
	return item_res



@frappe.whitelist()
def getItemBalanceNew(item_code,warehouse):

	query = "SELECT qty_after_transaction FROM `tabStock Ledger Entry` WHERE `item_code`='{}' AND `warehouse`='{}' AND `is_cancelled`='No' ORDER BY `posting_date` desc, `posting_time` desc, `name` desc LIMIT 1".format(item_code,warehouse)
	balance=frappe.db.sql(query)
	if not len(balance)==0:
		return balance[0][0]
	else:
		return 0
















@frappe.whitelist()
def appErrorLog(title,error):
	d = frappe.get_doc({
			"doctype": "App Error Log",
			"title":str("User:")+str(title+" "+"Website Error"),
			"error":traceback.format_exc()
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
			response["status"]=200
		response["message"]=message
		response["data"]=data
	else:
		error_log=appErrorLog(frappe.session.user,str(error))
		if status:
			response["status"]=status
		else:
			response["status"]=500
		if message:
			response["message"]=message
		else:
			response["message"]="Something Went Wrong"		
		response["message"]=message
		response["data"]=None
	return response

@frappe.whitelist(allow_guest=True)
def planList():
	item_list=frappe.get_list("plan",fields=['*'])
	balance=frappe.db.sql("""select * from `tabplan`""")
	return balance


@frappe.whitelist(allow_guest=True)
def itemDisableEnable(item_code,enable):

	if enable==1:
		test = frappe.db.sql("""UPDATE `tabItem` SET `item_group`= 'Products' WHERE item_code=%s""",item_code)
	elif enable==0:
		test = frappe.db.sql("""UPDATE `tabItem` SET `item_group`= 'Raw Material' WHERE item_code=%s""",item_code)

	frappe.db.commit()

	return True



@frappe.whitelist()
def getItemBalance(item_code):
	return 1
	#0 means out of stock
	balance=frappe.db.sql("""select qty_after_transaction from `tabStock Ledger Entry`
		where item_code=%s and warehouse='Finished Goods - S' and is_cancelled='No'
		order by posting_date desc, posting_time desc, name desc
		limit 1""",item_code)
	if not len(balance)==0:
		return balance[0][0]
	else:
		return 0

@frappe.whitelist()
def getItemService(item_code):
	#0 means No serviceable 
	return 1


@frappe.whitelist(allow_guest=True)
def getItemServiceWithPincode(itemType,pincode):

	return 1

	#0 means not serviable 
	pincode_list=frappe.get_list("Pincode",filters=[["Pincode","pincode","=",pincode]],fields=['*'])
	#return pincode_list
	if len(pincode_list)==0:
		if itemType=="oil":
			return 1
		else:
			return 0
	else:
		if int(pincode_list[0]["juice"])==1:
			if itemType=="juice":
				return 1

		if int(pincode_list[0]["shot"])==1:
			if itemType=="shot":
				return 1

		if int(pincode_list[0]["oil"])==1:
			if itemType=="oil":
				return 1

	return 0


@frappe.whitelist(allow_guest=True)
def itemStatus(delivery_date,pincode):
	item_res=[]
	item_list=frappe.get_all("Item",filters=[["Item","item_group","=","Products"]],fields=['*'],order_by="custom_sort_order")
	for item in item_list:
		item["stock_balance"]=getItemBalance(item["item_code"])
		item["servicibility"]=getItemServiceWithPincode(item["custom_item_type"],pincode)
		item_res.append(item)
	return item_res


@frappe.whitelist(allow_guest=True)
def FlutterItemList():
	item_res=[]
	item_list=frappe.get_all("Item",filters=[["Item","item_group","=","Products"]],fields=['*'],order_by="custom_sort_order")
	for item in item_list:
		item["stock_balance"]=getItemBalance(item["item_code"])
		item["servicibility"]=getItemService(item["item_code"])
		item_res.append(item)
	return item_res

@frappe.whitelist()
def FlutterItemListAll(allow_guest=True):
	item_res=[]
	item_list=frappe.get_list("Item",filters=[["Item","show_in_website","=","1"],["Item","disabled","=","0"],["Item","category","!=","Discontinue"]],fields=["item_name", "item_code", "standard_rate", "weight_per_unit", "weight_uom", "item_group", "brand", "image", "thumbnail", "description","website_image","clp","slp","category","standard_discount","additional_discount","offer_price","available_offer","treatment","is_new_product"])
	for item in item_list:
		item["stock_balance"]=getItemBalance(item["item_code"])
		item["servicibility"]=getItemService(item["item_code"])
		item_res.append(item)
	return item_res


@frappe.whitelist(allow_guest=True)
def FlutterFiltersList():

	filter_list = frappe.db.sql("""SELECT (SELECT filter_name FROM `tabFilter` O WHERE O.name = C.parent),(SELECT item_field_mapping FROM `tabFilter` O WHERE O.name = C.parent),(SELECT order_sort FROM `tabFilter` O WHERE O.name = C.parent),name,filter_name,filter_field_mapping,order_sort FROM `tabFilterSub` C WHERE hide=0""",as_list=1)
	newList=[]
	for i, obj1 in enumerate(filter_list):
		newdict={}
		newdict["mainfilter"]=obj1[0]
		newdict["mainfiltermapping"]=obj1[1]
		newdict["mainfiltersort"]=obj1[2]
		newdict["id"]=obj1[3]
		newdict["subfilter"]=obj1[4]
		newdict["subfiltermapping"]=obj1[5]
		newdict["subfiltersort"]=obj1[6]
		newList.append(newdict)

	returnvalue={}
	returnvalue["data"]=newList
	returnvalue["filterprefix"]='["show_in_application","=","1"]'

	return returnvalue

@frappe.whitelist(allow_guest=True)
def FlutterItemListFilters(appfilters):

	item_list=frappe.get_list("Item",
		filters=appfilters,
		fields=["item_code"])

	return item_list