from __future__ import unicode_literals
from frappe import throw, msgprint, _
import frappe
import traceback
from svakara.globle import appErrorLog,defaultResponseBody,defaultResponseErrorBody
from datetime import datetime


@frappe.whitelist(allow_guest=True)
def customer_create(**kwargs):

	parameters=frappe._dict(kwargs)
    # allParamKeys = parameters.keys()
	phoneNo = parameters['phone']
	firstName = parameters['first_name']
	lastName = parameters['last_name']
	city = parameters['city']
	pincode = parameters['pincode']


	reply=defaultResponseBody()
	reply['data']={}

	try:
		
		customerName = "{} {}".format(firstName,lastName)
		qury = "INSERT INTO `tabUser` (`name`,`full_name`, `owner`, `docstatus`, `idx`, `user_type`, `last_name`, `thread_notify`, `first_name`, `login_after`, `email`, `username`, `location`, `bio`,`creation`,`modified`,`modified_by`,`phone`,`mobile_no`) VALUES ('{}','{}', 'Guest', '0', '0', 'Website User', '{}', '1', '{}', '0', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}')".format(phoneNo,customerName, lastName,firstName,phoneNo+'@example.com', phoneNo,city,pincode,datetime.now(),datetime.now(),phoneNo,phoneNo,phoneNo)
		frappe.db.sql(qury)
		# frappe.db.sql("""INSERT INTO `tabUser` (`name`, `owner`, `docstatus`, `idx`, `user_type`, `last_name`, `thread_notify`, `first_name`, `login_after`, `email`, `username`, `location`, `bio`) VALUES ('"""+phoneNo+"""', 'Guest', '0', '0', 'Website User', '"""+lastName+"""', '1', '"""+firstName+"""', '0', '"""+phoneNo+"""@example.com', '"""+phoneNo+"""', '"""+city+"""', '"""+pincode+"""')""")			

		# d = frappe.get_doc({
		# 	"doctype": "User",
		# 	"docstatus": 0,
		# 	"__islocal": 1,
		# 	"__unsaved": 1,
		# 	"name": phoneNo,
		# 	"user_type": 'Website User',
		# 	"last_name": lastName,
		# 	"first_name": firstName,
		# 	"email": "{}@example.com".format(phoneNo),
		# 	"username": phoneNo,
		# 	"location": city,
		# 	"bio": pincode,
		# })
		# d1 = d.insert(ignore_permissions=True)

		# frappe.rename_doc("User", d1.name, phoneNo)

		# return reply

		
		qury = "INSERT INTO `tabCustomer` (`name`, `owner`, `docstatus`,  `idx`, `naming_series`, `disabled`, `customer_name`, `territory`, `customer_group`, `customer_type`, `is_frozen`, `custom_city`, `custom_pincode`,`creation`,`modified`,`modified_by`,`mobile_no`) VALUES ('{}', '{}', '0',  '0', 'CUST-', '0', '{}', 'India','Individual', 'Individual', '0', '{}', '{}', '{}', '{}', '{}', '{}')".format(phoneNo, phoneNo, customerName, city, pincode,datetime.now(),datetime.now(),phoneNo,phoneNo)
		frappe.db.sql(qury)
		# frappe.db.sql("""INSERT INTO `tabCustomer` (`name`, `owner`, `docstatus`,  `idx`, `naming_series`, `disabled`, `customer_name`, `territory`, `customer_group`, `customer_type`, `is_frozen`, `custom_city`, `custom_pincode`,`creation`,`modified`,`modified_by`) VALUES ('"""+phoneNo+"""', '"""+phoneNo+"""', '0',  '0', 'CUST-', '0', '"""+customerName+"""', 'India','Individual', 'Individual', '0', '"""+city+"""', '"""+pincode+"""')""")		
		# doc_customer = frappe.get_doc({
		# 	"doctype": "Customer",
		# 	"docstatus": 0,
		# 	"__islocal": 1,
		# 	"__unsaved": 1,
		# 	"name": phoneNo,
		# 	"customer_name": "{} {}".format(firstName,lastName),
		# 	"customer_group": 'Individual',
		# 	"customer_type": 'Individual',
		# 	"custom_city": city,
		# 	"custom_pincode": pincode,
		# })
		# doc_customer.insert(ignore_permissions=True)


		# d = frappe.get_doc({
		# 	"doctype": "DefaultValue",
		# 	"parent": "" + phoneNo,
		# 	"parenttype": "User Permission",
		# 	"parentfield": "system_defaults",
		# 	"defkey": "Customer",
		# 	"defvalue": phoneNo
		# })
		# d.insert(ignore_permissions=True)

		# p = frappe.get_doc({
		# 	"docstatus":0,
		# 	"doctype":"User Permission",
		# 	"name":"New User Permission 1",
		# 	"__islocal":1,
		# 	"__unsaved":1,
		# 	"apply_for_all_roles":0,
		# 	"__run_link_triggers":0,
		# 	"user":phoneNo,
		# 	"allow":"Customer",
		# 	"for_value":phoneNo})        
		# p.insert(ignore_permissions=True)
		reply["message"]="customer created"

	except Exception as e:
		frappe.local.response['http_status_code'] = 500
		reply = defaultResponseErrorBody(reply,str(e),str(traceback.format_exc()),'api_staff_customer','create_customer')

	return reply




@frappe.whitelist(allow_guest=True)
def customer_list(**kwargs):

	parameter = frappe._dict(kwargs)

	reply=defaultResponseBody()
	reply["parameters"]=parameter
	reply["data"]=[]

	query = "SELECT * FROM `tabCustomer`"
	reply["data"] = frappe.db.sql(query,as_dict=1)

	return reply

@frappe.whitelist(allow_guest=True)
def customer_detail(**kwargs):

	parameters=frappe._dict(kwargs)
	reply=defaultResponseBody()
	reply['data']={}
	reply["parameters"]=parameters
	reply["data"]={}
	reply['address']=[]
	reply['contact']=[]

	allParamKeys = parameters.keys()

	if "name" not in allParamKeys:
		reply["status_code"]="500"
		reply["message"]="Name key parameter is missing."
		return reply
	



	try:
		query = "SELECT * FROM `tabCustomer` WHERE `name`='{}'".format(parameters['name'])
		custmoerDetailList = frappe.db.sql(query,as_dict=1)
		if len(custmoerDetailList)!=0:
			custmoerDetail = custmoerDetailList[0]
			custmoerDetail['address']=[]
			custmoerDetail['contact']=[]
			
			
			address_id=frappe.db.sql("""SELECT `tabAddress`.name FROM `tabAddress` inner join `tabDynamic Link` on `tabAddress`.name=`tabDynamic Link`.parent WHERE `tabDynamic Link`.link_name=%s AND `tabDynamic Link`.link_doctype='Customer' AND `tabDynamic Link`.parenttype='Address' AND `tabAddress`.disabled=0""",custmoerDetail['name'])
			if not len(address_id)==0:
				addresslist = []
				for add in address_id:
					addDetail=frappe.get_doc("Address",add[0])
					addresslist.append(addDetail)

				custmoerDetail['address']=addresslist


			contact_id=frappe.db.sql("""SELECT `tabContact`.name FROM `tabContact` inner join `tabDynamic Link` on `tabContact`.name=`tabDynamic Link`.parent WHERE `tabDynamic Link`.link_name=%s AND `tabDynamic Link`.link_doctype='Customer' AND `tabDynamic Link`.parenttype='Contact'""",custmoerDetail['name'])
			# reply['contact_id']=contact_id
			contact_list = []
			for contac in contact_id:
				query = "SELECT * FROM `tabContact Phone` WHERE `parent`='{}'".format(contac[0])
				# reply['contact_child_query']=query
				allcontact = frappe.db.sql(query,as_dict=1)
				# reply['contact_child_response']=allcontact

				for rec in allcontact:
					contact_list.append(rec)

				# conDetail=frappe.get_doc("Contact",contac[0])
				# contact_list.append(conDetail)

			custmoerDetail['contact']=contact_list



			reply["data"] = custmoerDetail

		return reply
	except Exception as e:
		frappe.local.response['http_status_code'] = 500
		reply = defaultResponseErrorBody(reply,str(e),str(traceback.format_exc()),'api_staff_customer','customer_detail')
	
	return reply
