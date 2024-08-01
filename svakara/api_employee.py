from __future__ import unicode_literals
import frappe


@frappe.whitelist(allow_guest=True)
def emp_check_employee(mobileNo):

	reply = {}
	reply['isEmployee'] = False
	reply['deliveryTeam'] = {}
	reply['pageList'] = []
	reply['customer_list'] = ["Airport - Ahmedabad","Guest - Office","Swiggy - Office","Zomato - Office"]
	reply['payment_mode'] = ["Cash On Delivery","Card","Paytm","Google Pay","Phone Pay","UPI","Wallet"]

	totalPages = []

	query_dl = "SELECT * FROM `tabDelivery Team` WHERE `mobile`='{}'".format(mobileNo)
	dl_list = frappe.db.sql(query_dl,as_dict=1)
	
	if len(dl_list)!=0:
		reply['deliveryTeam'] = dl_list[0]
		query_employee2 = "SELECT * FROM `tabStaff Page Permission` WHERE `mobile`='{}'".format(dl_list[0]["employee_id"])
		employee_list2 = frappe.db.sql(query_employee2,as_dict=1)
		for i in employee_list2 :
			totalPages.append(i)

	query_employee = "SELECT * FROM `tabStaff Page Permission` WHERE `mobile`='{}' AND `page`='Login'".format(mobileNo)
	employee_list = frappe.db.sql(query_employee,as_dict=1)

	if len(employee_list)==0:
		if len(dl_list)!=0:
			query_employee2 = "SELECT * FROM `tabStaff Page Permission` WHERE `mobile`='{}' AND `page`='Login'".format(dl_list[0]["employee_id"])
			employee_list2 = frappe.db.sql(query_employee2,as_dict=1)
			if len(employee_list2)!=0:
				reply['isEmployee'] = True
	else:
		reply['isEmployee'] = True
		for i in employee_list :
			totalPages.append(i)
	

	query_employee22 = "SELECT * FROM `tabStaff Page Permission` WHERE `mobile`='{}'".format(mobileNo)
	employee_list22 = frappe.db.sql(query_employee22,as_dict=1)
	for i in employee_list22 :
		totalPages.append(i)


	reply['pageList'] = totalPages

	return reply