from __future__ import unicode_literals
import frappe
from frappe.utils import nowdate
import json
import traceback
from frappe.auth import LoginManager, CookieManager
from erpnext.globle import globleUserLogin
from erpnext.selling.doctype.sales_order.sales_order import update_status
from frappe.utils import flt
from frappe.model.mapper import get_mapped_doc
from erpnext.stock.stock_ledger import NegativeStockError
from erpnext.stock.doctype.batch.batch import UnableToSelectBatchError



@frappe.whitelist(allow_guest=True)
def delivery_note_auto(so_no):
	return delivery_note(so_no)

@frappe.whitelist(allow_guest=True)
def delivery_note(so_no, target_doc=None):

	reply={}
	reply["data"] = []
	reply["status_code"] = '200'
	reply['message']="Order is in processing."

	frappe.local.form_dict = globleUserLogin()
	frappe.local.cookie_manager = CookieManager()
	frappe.local.login_manager = LoginManager()

	if not frappe.db.exists("Sales Order", so_no):
		reply['message']= "Order not found in erp."
		reply["status_code"] = '500'
		return "Order not found in erp."

	doc1so_temp=frappe.get_doc("Sales Order",so_no)

	if doc1so_temp.status in ['Completed','Closed','Cancelled']:
		reply["status_code"] = '500'
		reply['message']= "Order is {} {}".format(str(doc1so_temp.status),str(doc1so_temp.status))
		return reply

	doc1so=frappe.get_doc("Sales Order",so_no)

	if doc1so.status in ['To Bill']:
		if float(doc1so.per_delivered)==100:
			if float(doc1so.per_billed)>=99:
				update_status("Closed",doc1so.name)
				reply["status_code"] = '500'
				reply['message']= "Order is 100 percentage deliver so make it close."
				return reply

	if doc1so.docstatus==2:
		reply['message']= "Order is cancelled"
		reply["status_code"] = '500'
		return reply

	if doc1so.docstatus==0:
		temp = doc1so.submit()

	try:
		def set_missing_values(source, target):

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

		target_doc = get_mapped_doc("Sales Order", so_no, {
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
		reply["message"]="Delivery note created"
		return reply

	except (NegativeStockError,UnableToSelectBatchError) as e:

		frappe.db.rollback()
		return str(e)

	except Exception as e:
		frappe.db.rollback()
		return str(e)