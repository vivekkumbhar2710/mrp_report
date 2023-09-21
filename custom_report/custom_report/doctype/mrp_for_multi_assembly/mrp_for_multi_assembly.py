# Copyright (c) 2023, Vivek.kumbhar@erpdata.in and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
# from frappe.utils.xlsxutils import make_xlsx
# from frappe.utils.csvutils import get_csv

class MRPforMultiAssembly(Document):
	@frappe.whitelist()
	def get_report(self):
		if self.sales_order and (not self.production_plan):
			
			sales_order_data_list = [d.sales_order for d in self.sales_order]
			sales_order_parent_list = set()
			
			production_plan_sales_order = doc=frappe.get_all('Production Plan Sales Order',filters={"sales_order": ['in',sales_order_data_list], "docstatus": 1},fields=['parent'])
			if production_plan_sales_order:
				for vsk in production_plan_sales_order:
					sales_order_parent_list.add(vsk.parent)
			else:
				frappe.throw(f'There is not any Production plane against {sales_order_data_list} sales order ')


			variable_for_names_in_sales_order_parent_list = ','.join(sales_order_parent_list)



			all_bom_in_production_plane = frappe.get_all('Production Plan Item',filters={"parent": ["in",sales_order_parent_list], "docstatus": 1},fields=['bom_no'])
			list_bom_in_production_plane = sorted(set(item['bom_no'] for item in all_bom_in_production_plane))
			all_bom_exploded_items_filter =  {'parent': ['in',list_bom_in_production_plane] ,"docstatus": 1}

		if self.production_plan and (not self.sales_order) :
			

			doc=frappe.get_all('Production Plan Sales Order',filters={"parent": self.production_plan, "docstatus": 1},fields=['sales_order'])
			for d in doc:
				self.append('sales_order', {
					'sales_order': d.sales_order
				})

			all_bom_in_production_plane = frappe.get_all('Production Plan Item',filters={"parent": self.production_plan, "docstatus": 1},fields=['bom_no'])
			list_bom_in_production_plane = sorted(set(item['bom_no'] for item in all_bom_in_production_plane))
			all_bom_exploded_items_filter =  {'parent': ['in',list_bom_in_production_plane] ,"docstatus": 1}

			variable_for_names_in_sales_order_parent_list=None
		if (not self.production_plan) and (not self.sales_order):
			
			variable_for_names_in_sales_order_parent_list=None
			all_bom_exploded_items_filter = { "docstatus": 1}



		all_bom_exploded_items =frappe.get_all('BOM Explosion Item',filters= all_bom_exploded_items_filter,fields=['item_code','parent'])  
		total_items = {}
		for item in all_bom_exploded_items:
			item_code = item['item_code']
			parent = item['parent']
			if item_code in total_items:
				total_items[item_code]['parent'].append(parent)
			else:
				total_items[item_code] = {'parent': [parent] }

		bom_exploded_items = [{'item_code': item_code, 'parent': values['parent']} for item_code, values in total_items.items()]
		bom_exploded_items_sorted = sorted(bom_exploded_items, key=lambda x: x['item_code'])



		for row in bom_exploded_items_sorted:

			xoxoxo = frappe.get_all("Production Plan Item", filters={"bom_no": ["in", row['parent']]}, fields=['parent'])
			filtered_plans =[]
			for plan in xoxoxo:
				filtered_plans.append(plan.parent)
			gogogog = frappe.get_all("Production Plan", filters={"name": ["in", filtered_plans],'status' : ["in", ["Submitted", "Material Requested", "In Process"]]}, fields=['name'])

			variable_for_names_in_gogogog = ','.join(set(item['name'] for item in gogogog))
			variable_for_names_of_production_plane = variable_for_names_in_sales_order_parent_list if variable_for_names_in_sales_order_parent_list else variable_for_names_in_gogogog
			production_plane_names = self.production_plan if self.production_plan else variable_for_names_of_production_plane

			unique_valuex = set(frappe.get_value("Production Plan", x.parent, "for_warehouse") for x in xoxoxo if frappe.get_value("Production Plan", x.parent, "for_warehouse") is not None)
			if production_plane_names:
				stock_qty=0
				work_order_list=[]
				total_alloted_qty=0
				total_material_to_request=0
				total_materialrequestedqty =0
				total_materialorderedqty =0
				total_materialreceivedqty=0
				material_request_list =[]
				production_plane_list = production_plane_names.split(',')
				for pj in  production_plane_list:

					bom_for_each_pp = frappe.get_all("Production Plan Item", filters={"parent": pj}, fields=['bom_no','planned_qty'] )
					for vd in bom_for_each_pp:
						items_req_qty = frappe.get_all("BOM Explosion Item", filters={"parent": vd.bom_no , 'item_code': row['item_code']  }, fields=['stock_qty'] )
						for vk in items_req_qty:
							stock_qty += round((vk.stock_qty * vd.planned_qty),2)

					work_order_doc_list = frappe.get_all("Work Order", filters={"production_plan": pj}, fields=['source_warehouse','name'] )
					unique_warehouses = set()
					for am in work_order_doc_list:
						item_work_order_made_ahe_ka_nahi = frappe.get_all("Work Order Item", filters={"parent": am.name ,"item_code" : row['item_code']}, fields=['source_warehouse','name'] )
						if item_work_order_made_ahe_ka_nahi:

							if am.source_warehouse:
								unique_warehouses.add(am.source_warehouse)
								stock_entry_doctype=frappe.get_all("Stock Entry",filters={"work_order": am.name ,"docstatus": 1},fields=['name'])
								for jp in stock_entry_doctype:
									get_stock_entry_child_table = frappe.get_all("Stock Entry Detail",filters={"parent": jp.name ,"docstatus": 1,'t_warehouse': am.source_warehouse ,'item_code': row['item_code']},fields=['qty'] )
									if get_stock_entry_child_table:
										for gc in get_stock_entry_child_table:
											total_alloted_qty += gc.qty

								
					work_order_list.extend(list(unique_warehouses))

					material_request_plan_item =frappe.get_all("Material Request Plan Item",filters={"parent": pj ,"docstatus": 1, 'item_code' : row['item_code']},fields=['quantity'])
					if 	material_request_plan_item:
						for sp in material_request_plan_item:
							total_material_to_request += sp.quantity

					material_request_item = frappe.get_all("Material Request Item",filters={"production_plan": pj ,"docstatus": 1, 'item_code' : row['item_code']},fields=['qty','parent'])
					if 	material_request_item:
						for sk in material_request_item:
							total_materialrequestedqty += sk.qty
							material_request_list.append(sk.parent)

							purchase_order_item = frappe.get_all("Purchase Order Item",filters={"material_request": sk.parent ,"docstatus": 1, 'item_code' : row['item_code']},fields=['qty'])
							if 	purchase_order_item:
								for pk in purchase_order_item:
									total_materialorderedqty += pk.qty


							purchase_receipt_item = frappe.get_all("Purchase Receipt Item",filters={"material_request": sk.parent ,"docstatus": 1, 'item_code' : row['item_code']},fields=['qty'])
							if 	purchase_receipt_item:
								for rc in purchase_receipt_item:
									total_materialreceivedqty += rc.qty


						
					
				self.append("table", {
					"itemcode": row['item_code'],
					"itemname": frappe.get_value("Item",row['item_code'],'item_name'),
					"requiredbomqty" : stock_qty,
					"actualqty": (frappe.get_all('Bin', filters={'item_code': row['item_code'], 'warehouse': 'Store-MFG - SEP'}, fields=['SUM(actual_qty) as qty']))[0]['qty'],
					"productionplan": production_plane_names,
					"prodplanwarehouse":  frappe.get_value("Production Plan", self.production_plan, "for_warehouse") if self.production_plan else   ", ".join(f"'{item}'" for item in unique_valuex),
					"material_to_request" : total_material_to_request -total_materialrequestedqty,
					"materialrequestedqty" : total_materialrequestedqty,
					"materialorderedqty" : total_materialorderedqty,
					"materialreceivedqty" : total_materialreceivedqty ,
					"material_ordered_but_pending_to_receive_qty": total_materialorderedqty - total_materialreceivedqty ,
					"material_to_order" : total_material_to_request - total_materialorderedqty,
					"material_request_list" : str(list(set(material_request_list)))
				})

		self.save()
