from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.contacts.doctype.address.address import get_company_address
from frappe.model.utils import get_fetch_values
from frappe.model.mapper import get_mapped_doc
from erpnext.stock.doctype.delivery_note.delivery_note import make_sales_invoice
from erpnext.stock.stock_ledger import NegativeStockError
from erpnext.stock.doctype.batch.batch import UnableToSelectBatchError
from frappe.utils import flt,get_last_day
from erpnext.selling.doctype.sales_order.sales_order import update_status
from datetime import datetime
from svakara.globle import appErrorLog,globleLoginUser

@frappe.whitelist(allow_guest=True)
def salesOrderSubmit(so_no):

	frappe.enqueue(salesOrderSubmit_Process,queue='long',job_name="Submiting Order: {}".format(so_no),timeout=50000,so_no=so_no)	

	reply={}
	reply['message']='Order start processing'
	reply['status_code']='200'
	return reply


@frappe.whitelist(allow_guest=True)
def salesOrderSubmit_Process(so_no):

	current_user = frappe.session.user
	frappe.set_user(globleLoginUser())
	
	reply={}
	reply['status_code']="200"
	reply['message']="Order is in processing."

	if not frappe.db.exists("Sales Order", so_no):
		appErrorLog("Order Sumbmit- order not found","")
		return "Order not found in erp."

	doc1so_temp=frappe.get_doc("Sales Order",so_no)

	if doc1so_temp.status in ['Completed','Closed','Cancelled']:
		reply['message']= "Order is {}".format(str(doc1so_temp.status))
		return reply


	doc1so=frappe.get_doc("Sales Order",so_no)
	
	if doc1so.docstatus==2:
		reply['message']= "Order is cancelled"
		return reply

	if doc1so.docstatus==0:
		temp = doc1so.submit()

	# return "Order submited"

	return make_delivery_note(doc1so.name,current_user)

@frappe.whitelist(allow_guest=True)
def make_delivery_note(source_name,current_user, target_doc=None):

	reply={}

	try:
		def set_missing_values(source, target):
			if source.po_no:
				if target.po_no:
					target_po_no = target.po_no.split(", ")
					target_po_no.append(source.po_no)
					target.po_no = ", ".join(list(set(target_po_no))) if len(target_po_no) > 1 else target_po_no[0]
				else:
					target.po_no = source.po_no

			target.ignore_pricing_rule = 1
			target.run_method("calculate_taxes_and_totals")
		
			# set company address
			target.company_address = source.company_address
			target.company_address_display = source.company_address_display

		def update_item(source, target, source_parent):
			target.base_amount = (flt(source.qty) - flt(source.delivered_qty)) * flt(source.base_rate)
			target.amount = (flt(source.qty) - flt(source.delivered_qty)) * flt(source.rate)
			target.qty = flt(source.qty) - flt(source.delivered_qty)

			# item = frappe.db.get_value("Item", target.item_code, ["item_group", "selling_cost_center"], as_dict=1)

			# if item:
			# 	target.cost_center = frappe.db.get_value("Project", source_parent.project, "cost_center") \
			# 		or item.selling_cost_center \
			# 		or frappe.db.get_value("Item Group", item.item_group, "default_cost_center")

		target_doc = get_mapped_doc("Sales Order", source_name, {
			"Sales Order": {
				"doctype": "Delivery Note",
				"validation": {
					"docstatus": ["=", 1]
				},
			},
			"Sales Order Item": {
				"doctype": "Delivery Note Item",
				"field_map": {
					"rate": "rate",
					"name": "so_detail",
					"parent": "against_sales_order",
					"expense_account":"expense_account",
					"warehouse":"warehouse"
				},
				"postprocess": update_item,
				"condition": lambda doc: abs(doc.delivered_qty) < abs(doc.qty) and doc.delivered_by_supplier!=1
			},
			"Sales Taxes and Charges": {
				"doctype": "Sales Taxes and Charges",
				"add_if_empty": True
			},
			"Sales Team": {
				"doctype": "Sales Team",
				"add_if_empty": True
			}
		}, target_doc, set_missing_values,ignore_permissions=True)
		
		doc=''
		doc=target_doc.insert(ignore_permissions=True)
		doc.submit()
		frappe.enqueue(make_auto_invoice,queue='short',job_name="Create Sales Invoice: {}".format(source_name),timeout=50000,so_no=source_name,doc=doc,current_user=current_user)
		return "Start invocie" 

	except (NegativeStockError,UnableToSelectBatchError) as e:

		frappe.db.rollback()
		return str(e)

	except Exception as e:
		frappe.db.rollback()
		return str(e)

@frappe.whitelist(allow_guest=True)
def make_auto_invoice(so_no, doc,current_user):


######################   Start Invoice creation
	sinv_doc = ''
	sinv_doc = make_sales_invoice(doc.name)

	sinv_doc.company_address_display = doc.company_address_display
	sinv_doc.dispatch_address_name=doc.company_address
	sinv_doc.dispatch_address=doc.dispatch_address

	if sinv_doc.items:
		for p_item in sinv_doc.items:
			if p_item.rate==0:
				p_item.is_free_item=1

	sinv_doc.set_posting_time = 1

	sinv_after_save = sinv_doc.insert(ignore_permissions = True)
	sinv_after_save.submit()
	frappe.set_user(current_user)
	
	return "Sales invoice done"