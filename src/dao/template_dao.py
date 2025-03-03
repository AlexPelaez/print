# # file: dao/template_dao.py

# import json
# from config.db_connection import DBConnection

# from models.printify_template_models import (
#     PrintifyTemplateModel,  
#     PrintifyVariantModel,
#     PrintifyOptionModel,
#     PrintifyPrintAreaModel,
#     PrintifyImageModel,
#     PrintifyTagModel,
#     PrintifyExternalModel,
#     PrintifySalesChannelPropertyModel,
#     PrintifyViewModel
# )

# class TemplateDAO:
#     def __init__(self, db_conn: DBConnection):
#         self.db = db_conn
#         self._create_all_tables()


#     # ---------------------------------------------------------
#     # TABLE CREATION
#     # ---------------------------------------------------------
#     def _create_all_tables(self):
#         """
#         Combines table creation for the main templates table, its sub-tables,
#         and the template_status table.
#         """
#         self.create_tables()
#         self.create_status_table()

#     def create_status_table(self):
#         """
#         Creates the 'template_status' table referencing templates.id
#         and holding status (DRAFT, PUBLISHED).
#         """
#         status_sql = """
#         CREATE TABLE IF NOT EXISTS template_status (
#             template_fk INT PRIMARY KEY,
#             status ENUM('DRAFT','PUBLISHED') NOT NULL,
#             FOREIGN KEY (template_fk) REFERENCES templates(id)
#               ON DELETE CASCADE
#         );
#         """
#         self.db.cursor.execute(status_sql)
#         self.db.connection.commit()
#         print("Created 'template_status' table if not present.")

#     def create_tables(self):
#         """
#         Creates the main 'templates' table + all sub-tables
#         referencing 'templates' in place of 'products'.
#         """
#         main_template_sql = """
#         CREATE TABLE IF NOT EXISTS templates (
#             id INT AUTO_INCREMENT PRIMARY KEY,
#             template_id VARCHAR(100) NOT NULL,
#             title VARCHAR(255),
#             description TEXT,
#             blueprint_id INT,
#             print_provider_id INT,
#             user_id INT,
#             shop_id INT,
#             visible TINYINT(1),
#             is_locked TINYINT(1),
#             reviewed TINYINT(1),
#             created_at DATETIME,
#             updated_at DATETIME,
#             UNIQUE KEY unique_template_id (template_id)
#         );
#         """
#         self.db.cursor.execute(main_template_sql)

#         tags_sql = """
#         CREATE TABLE IF NOT EXISTS template_tags (
#             id INT AUTO_INCREMENT PRIMARY KEY,
#             template_id VARCHAR(100),
#             tag VARCHAR(255),
#             FOREIGN KEY (template_id) REFERENCES templates(template_id)
#               ON DELETE CASCADE
#         );
#         """
#         self.db.cursor.execute(tags_sql)

#         variants_sql = """
#         CREATE TABLE IF NOT EXISTS template_variants (
#             id INT AUTO_INCREMENT PRIMARY KEY,
#             template_id VARCHAR(100),
#             variant_id INT,
#             sku VARCHAR(50),
#             cost INT,
#             price INT,
#             title VARCHAR(255),
#             grams INT,
#             is_enabled TINYINT(1),
#             is_default TINYINT(1),
#             is_available TINYINT(1),
#             is_printify_express_eligible TINYINT(1),
#             quantity INT,
#             options JSON,
#             FOREIGN KEY (template_id) REFERENCES templates(template_id)
#               ON DELETE CASCADE
#         );
#         """
#         self.db.cursor.execute(variants_sql)

#         images_sql = """
#         CREATE TABLE IF NOT EXISTS template_images (
#             id INT AUTO_INCREMENT PRIMARY KEY,
#             template_id VARCHAR(100),
#             src TEXT,
#             variant_ids JSON,
#             position VARCHAR(50),
#             is_default TINYINT(1),
#             is_selected_for_publishing TINYINT(1),
#             order_index INT NULL,
#             FOREIGN KEY (template_id) REFERENCES templates(template_id)
#               ON DELETE CASCADE
#         );
#         """
#         self.db.cursor.execute(images_sql)

#         print_areas_sql = """
#         CREATE TABLE IF NOT EXISTS template_print_areas (
#             id INT AUTO_INCREMENT PRIMARY KEY,
#             template_id VARCHAR(100),
#             variant_ids JSON,
#             background VARCHAR(7),
#             FOREIGN KEY (template_id) REFERENCES templates(template_id)
#               ON DELETE CASCADE
#         );
#         """
#         self.db.cursor.execute(print_areas_sql)

#         placeholders_sql = """
#         CREATE TABLE IF NOT EXISTS template_placeholders (
#             id INT AUTO_INCREMENT PRIMARY KEY,
#             print_area_id INT,
#             position VARCHAR(50),
#             images JSON,
#             FOREIGN KEY (print_area_id) REFERENCES template_print_areas(id)
#               ON DELETE CASCADE
#         );
#         """
#         self.db.cursor.execute(placeholders_sql)

#         external_sql = """
#         CREATE TABLE IF NOT EXISTS template_external (
#             template_id VARCHAR(100) PRIMARY KEY,
#             external_id VARCHAR(100),
#             handle TEXT,
#             FOREIGN KEY (template_id) REFERENCES templates(template_id)
#               ON DELETE CASCADE
#         );
#         """
#         self.db.cursor.execute(external_sql)

#         scp_sql = """
#         CREATE TABLE IF NOT EXISTS template_sales_channel_properties (
#             id INT AUTO_INCREMENT PRIMARY KEY,
#             template_id VARCHAR(100),
#             data JSON,
#             FOREIGN KEY (template_id) REFERENCES templates(template_id)
#               ON DELETE CASCADE
#         );
#         """
#         self.db.cursor.execute(scp_sql)

#         views_sql = """
#         CREATE TABLE IF NOT EXISTS template_views (
#             id INT AUTO_INCREMENT PRIMARY KEY,
#             template_id VARCHAR(100),
#             view_id INT,
#             label VARCHAR(255),
#             position VARCHAR(50),
#             FOREIGN KEY (template_id) REFERENCES templates(template_id)
#               ON DELETE CASCADE
#         );
#         """
#         self.db.cursor.execute(views_sql)

#         view_files_sql = """
#         CREATE TABLE IF NOT EXISTS template_view_files (
#             id INT AUTO_INCREMENT PRIMARY KEY,
#             view_id INT,
#             src TEXT,
#             variant_ids JSON,
#             FOREIGN KEY (view_id) REFERENCES template_views(id)
#               ON DELETE CASCADE
#         );
#         """
#         self.db.cursor.execute(view_files_sql)

#         self.db.connection.commit()
#         print("Created all 'templates' tables if not present.")

#     # ---------------------------------------------------------
#     # INSERT / UPDATE
#     # ---------------------------------------------------------
#     def _delete_sub_models(self, template_id: str):
#         """
#         Delete sub-rows referencing template_id from all sub-tables.
#         """
#         tables_to_clear = [
#             "template_tags",
#             "template_variants",
#             "template_images",
#             "template_print_areas",
#             "template_external",
#             "template_sales_channel_properties",
#             "template_views"
#         ]
#         for tbl in tables_to_clear:
#             sql = f"DELETE FROM {tbl} WHERE template_id = %s"
#             self.db.cursor.execute(sql, (template_id,))
#         self.db.connection.commit()

#     def insert_or_update_template(self, template_model):
#         """
#         Insert or update a template using a Printify-style Model.
#         We'll treat 'id' as 'template_id' for naming consistency.
#         The rest is the same logic as the ProductDAO, but referencing
#         'templates' and sub-tables named 'template_*'.
#         """
#         def bool_to_int(b):
#             return 1 if b else 0

#         # 1) Upsert main row
#         upsert_query = """
#         INSERT INTO templates (
#             template_id, title, description, 
#             blueprint_id, print_provider_id, 
#             user_id, shop_id, 
#             visible, is_locked, reviewed,
#             created_at, updated_at
#         )
#         VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
#         ON DUPLICATE KEY UPDATE
#             title = VALUES(title),
#             description = VALUES(description),
#             blueprint_id = VALUES(blueprint_id),
#             print_provider_id = VALUES(print_provider_id),
#             user_id = VALUES(user_id),
#             shop_id = VALUES(shop_id),
#             visible = VALUES(visible),
#             is_locked = VALUES(is_locked),
#             reviewed = VALUES(reviewed),
#             created_at = VALUES(created_at),
#             updated_at = VALUES(updated_at)
#         ;
#         """
#         upsert_values = (
#             template_model.id,
#             template_model.title,
#             template_model.description,
#             template_model.blueprint_id,
#             template_model.print_provider_id,
#             template_model.user_id,
#             template_model.shop_id,
#             bool_to_int(template_model.visible),
#             bool_to_int(template_model.is_locked),
#             bool_to_int(template_model.reviewed),
#             template_model.created_at,
#             template_model.updated_at
#         )

#         try:
#             self.db.cursor.execute(upsert_query, upsert_values)
#             self.db.connection.commit()
#             print(f"Upserted template row for template_id={template_model.id}")
#         except Exception as e:
#             print(f"Error upserting template {template_model.id}: {e}")
#             return

#         # 2) Remove old sub-model rows
#         self._delete_sub_models(template_model.id)

#         # 3) Insert tags
#         insert_tag_sql = "INSERT INTO template_tags (template_id, tag) VALUES (%s, %s)"
#         for tmodel in template_model.tags:
#             self.db.cursor.execute(insert_tag_sql, (template_model.id, tmodel.tag))

#         # 4) Insert variants
#         insert_variant_sql = """
#         INSERT INTO template_variants (
#             template_id, variant_id, sku, cost, price, title,
#             grams, is_enabled, is_default, is_available,
#             is_printify_express_eligible, quantity, options
#         )
#         VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
#         """
#         for vmodel in template_model.variants:
#             vdata = vmodel.data
#             if not isinstance(vdata, dict):
#                 continue
#             variant_id = vdata.get("id")
#             sku = vdata.get("sku")
#             cost = vdata.get("cost")
#             price = vdata.get("price")
#             title = vdata.get("title")
#             grams = vdata.get("grams")
#             is_enabled = bool_to_int(vdata.get("is_enabled", False))
#             is_default = bool_to_int(vdata.get("is_default", False))
#             is_available = bool_to_int(vdata.get("is_available", False))
#             is_express = bool_to_int(vdata.get("is_printify_express_eligible", False))
#             quantity = vdata.get("quantity", 1)
#             options_json = json.dumps(vdata.get("options", []))

#             self.db.cursor.execute(insert_variant_sql, (
#                 template_model.id,
#                 variant_id, sku, cost, price, title,
#                 grams, is_enabled, is_default, is_available,
#                 is_express, quantity, options_json
#             ))

#         # 5) Insert images
#         insert_img_sql = """
#         INSERT INTO template_images (
#             template_id, src, variant_ids, position,
#             is_default, is_selected_for_publishing, order_index
#         )
#         VALUES (%s, %s, %s, %s, %s, %s, %s)
#         """
#         for imodel in template_model.images:
#             idata = imodel.data
#             if not isinstance(idata, dict):
#                 continue
#             src = idata.get("src")
#             variant_ids = json.dumps(idata.get("variant_ids", []))
#             position = idata.get("position")
#             is_def = bool_to_int(idata.get("is_default", False))
#             is_pub = bool_to_int(idata.get("is_selected_for_publishing", False))
#             order_i = idata.get("order", None)

#             self.db.cursor.execute(insert_img_sql, (
#                 template_model.id, src, variant_ids,
#                 position, is_def, is_pub, order_i
#             ))

#         # 6) Insert print_areas + placeholders
#         insert_pa_sql = """
#         INSERT INTO template_print_areas (template_id, variant_ids, background)
#         VALUES (%s, %s, %s)
#         """
#         insert_ph_sql = """
#         INSERT INTO template_placeholders (print_area_id, position, images)
#         VALUES (%s, %s, %s)
#         """
#         for pa_model in template_model.print_areas:
#             pa_data = pa_model.data
#             if not isinstance(pa_data, dict):
#                 continue

#             variant_ids_json = json.dumps(pa_data.get("variant_ids", []))
#             background = pa_data.get("background")

#             self.db.cursor.execute(insert_pa_sql, (template_model.id, variant_ids_json, background))
#             pa_db_id = self.db.cursor.lastrowid

#             for ph in pa_data.get("placeholders", []):
#                 images_json = json.dumps(ph.get("images", []))
#                 position_val = ph.get("position")
#                 self.db.cursor.execute(insert_ph_sql, (pa_db_id, position_val, images_json))

#         # 7) Insert external
#         if template_model.external and isinstance(template_model.external.data, dict):
#             ext_data = template_model.external.data
#             insert_ext_sql = """
#             INSERT INTO template_external (template_id, external_id, handle)
#             VALUES (%s, %s, %s)
#             ON DUPLICATE KEY UPDATE
#                 external_id = VALUES(external_id),
#                 handle = VALUES(handle)
#             """
#             self.db.cursor.execute(insert_ext_sql, (
#                 template_model.id,
#                 ext_data.get("id"),
#                 ext_data.get("handle")
#             ))

#         # 8) Insert sales_channel_properties with debug logging
#         insert_scp_sql = """
#         INSERT INTO template_sales_channel_properties (template_id, data)
#         VALUES (%s, %s)
#         """
#         for scp_model in template_model.sales_channel_properties:
#             scp_data = scp_model.data if isinstance(scp_model.data, dict) else {}
#             json_data = json.dumps(scp_data)
#             print(f"DEBUG: Inserting sales_channel_properties for template_id {template_model.id} with data: {json_data}")
#             self.db.cursor.execute(insert_scp_sql, (template_model.id, json_data))

#         # 9) Insert views and view files
#         insert_view_sql = """
#         INSERT INTO template_views (
#             template_id, view_id, label, position
#         ) VALUES (%s, %s, %s, %s)
#         """
#         insert_view_file_sql = """
#         INSERT INTO template_view_files (view_id, src, variant_ids)
#         VALUES (%s, %s, %s)
#         """
#         for v_model in template_model.views:
#             vdata = v_model.data
#             if not isinstance(vdata, dict):
#                 continue
#             view_id = vdata.get("id")
#             label = vdata.get("label")
#             position = vdata.get("position")

#             self.db.cursor.execute(insert_view_sql, (template_model.id, view_id, label, position))
#             db_view_id = self.db.cursor.lastrowid

#             for vf in vdata.get("files", []):
#                 variant_ids_json = json.dumps(vf.get("variant_ids", []))
#                 src = vf.get("src")
#                 self.db.cursor.execute(insert_view_file_sql, (db_view_id, src, variant_ids_json))

#         self.db.connection.commit()
#         print(f"Upserted template {template_model.id} + sub-models from model.")

#     # ---------------------------------------------------------
#     # FETCH
#     # ---------------------------------------------------------
#     def fetch_template_from_template_id(self, template_id: str) -> PrintifyTemplateModel | None:
#         """
#         Loads from DB, reconstructs a PrintifyTemplateModel (or 'template' model).
#         """
#         main_q = "SELECT * FROM templates WHERE template_id = %s"
#         self.db.cursor.execute(main_q, (template_id,))
#         row = self.db.cursor.fetchone()
#         if not row:
#             return None

#         pm = PrintifyTemplateModel(
#             id=row["template_id"],
#             title=row["title"],
#             description=row["description"],
#             blueprint_id=row["blueprint_id"],
#             user_id=row["user_id"],
#             shop_id=row["shop_id"],
#             visible=bool(row["visible"]),
#             is_locked=bool(row["is_locked"]),
#             reviewed=bool(row["reviewed"]),
#             created_at=str(row["created_at"]) if row["created_at"] else None,
#             updated_at=str(row["updated_at"]) if row["updated_at"] else None,
#             print_provider_id=row["print_provider_id"]
#         )

#         # tags
#         self.db.cursor.execute("SELECT tag FROM template_tags WHERE template_id = %s", (template_id,))
#         for trow in self.db.cursor.fetchall():
#             pm.tags.append(PrintifyTagModel(template_id, trow["tag"]))

#         # variants
#         self.db.cursor.execute("SELECT * FROM template_variants WHERE template_id = %s", (template_id,))
#         for vrow in self.db.cursor.fetchall():
#             data_dict = {
#                 "id": vrow["variant_id"],
#                 "sku": vrow["sku"],
#                 "cost": vrow["cost"],
#                 "price": vrow["price"],
#                 "title": vrow["title"],
#                 "grams": vrow["grams"],
#                 "is_enabled": bool(vrow["is_enabled"]),
#                 "is_default": bool(vrow["is_default"]),
#                 "is_available": bool(vrow["is_available"]),
#                 "is_printify_express_eligible": bool(vrow["is_printify_express_eligible"]),
#                 "quantity": vrow["quantity"],
#                 "options": json.loads(vrow["options"]) if vrow["options"] else []
#             }
#             pm.variants.append(PrintifyVariantModel(template_id, data_dict))

#         # images
#         self.db.cursor.execute("SELECT * FROM template_images WHERE template_id = %s", (template_id,))
#         for irow in self.db.cursor.fetchall():
#             data_dict = {
#                 "src": irow["src"],
#                 "variant_ids": json.loads(irow["variant_ids"]) if irow["variant_ids"] else [],
#                 "position": irow["position"],
#                 "is_default": bool(irow["is_default"]),
#                 "is_selected_for_publishing": bool(irow["is_selected_for_publishing"]),
#                 "order": irow["order_index"]
#             }
#             pm.images.append(PrintifyImageModel(template_id, data_dict))

#         # print_areas + placeholders
#         self.db.cursor.execute("SELECT * FROM template_print_areas WHERE template_id = %s", (template_id,))
#         pa_rows = self.db.cursor.fetchall()
#         for par in pa_rows:
#             pa_id = par["id"]
#             self.db.cursor.execute("SELECT * FROM template_placeholders WHERE print_area_id = %s", (pa_id,))
#             ph_rows = self.db.cursor.fetchall()
#             placeholders_list = []
#             for ph in ph_rows:
#                 placeholders_list.append({
#                     "position": ph["position"],
#                     "images": json.loads(ph["images"]) if ph["images"] else []
#                 })
#             pa_data = {
#                 "variant_ids": json.loads(par["variant_ids"]) if par["variant_ids"] else [],
#                 "background": par["background"],
#                 "placeholders": placeholders_list
#             }
#             pm.print_areas.append(PrintifyPrintAreaModel(template_id, pa_data))

#         # external
#         self.db.cursor.execute("SELECT * FROM template_external WHERE template_id = %s", (template_id,))
#         er = self.db.cursor.fetchone()
#         if er:
#             pm.external = PrintifyExternalModel(template_id, {
#                 "id": er["external_id"],
#                 "handle": er["handle"]
#             })

#         # sales_channel_properties
#         self.db.cursor.execute("SELECT data FROM template_sales_channel_properties WHERE template_id = %s", (template_id,))
#         for scp_row in self.db.cursor.fetchall():
#             scp_data = json.loads(scp_row["data"]) if scp_row["data"] else {}
#             pm.sales_channel_properties.append(PrintifySalesChannelPropertyModel(template_id, scp_data))

#         # views
#         self.db.cursor.execute("SELECT * FROM template_views WHERE template_id = %s", (template_id,))
#         view_rows = self.db.cursor.fetchall()
#         for vr in view_rows:
#             view_id = vr["view_id"]
#             label = vr["label"]
#             position = vr["position"]
#             self.db.cursor.execute("SELECT * FROM template_view_files WHERE view_id = %s", (vr["id"],))
#             vf_rows = self.db.cursor.fetchall()
#             files_list = []
#             for vfr in vf_rows:
#                 files_list.append({
#                     "src": vfr["src"],
#                     "variant_ids": json.loads(vfr["variant_ids"]) if vfr["variant_ids"] else []
#                 })
#             view_data = {
#                 "id": view_id,
#                 "label": label,
#                 "position": position,
#                 "files": files_list
#             }
#             pm.views.append(PrintifyViewModel(template_id, view_data))

#         return pm

#     def set_status_by_template_id(self, template_id: str, new_status: str):
#         if new_status not in ("DRAFT", "PUBLISHED"):
#             raise ValueError(f"Invalid status '{new_status}'.")

#         select_q = "SELECT id FROM templates WHERE template_id = %s"
#         self.db.cursor.execute(select_q, (template_id,))
#         row = self.db.cursor.fetchone()
#         if not row:
#             print(f"No template found with template_id={template_id}")
#             return

#         local_id = row["id"]

#         upsert_sql = """
#         INSERT INTO template_status (template_fk, status)
#         VALUES (%s, %s)
#         ON DUPLICATE KEY UPDATE status = VALUES(status);
#         """
#         self.db.cursor.execute(upsert_sql, (local_id, new_status))
#         self.db.connection.commit()
#         print(f"Set status for template_id={template_id} (id={local_id}) to '{new_status}'.")

#     def set_status_by_id(self, db_id: int, new_status: str):
#         if new_status not in ("DRAFT", "PUBLISHED"):
#             raise ValueError(f"Invalid status '{new_status}'.")

#         check_q = "SELECT id FROM templates WHERE id = %s"
#         self.db.cursor.execute(check_q, (db_id,))
#         row = self.db.cursor.fetchone()
#         if not row:
#             print(f"No template found with id={db_id}")
#             return

#         upsert_sql = """
#         INSERT INTO template_status (template_fk, status)
#         VALUES (%s, %s)
#         ON DUPLICATE KEY UPDATE status = VALUES(status)
#         """
#         self.db.cursor.execute(upsert_sql, (db_id, new_status))
#         self.db.connection.commit()
#         print(f"Set status for local id={db_id} to '{new_status}'.")

#     def fetch_max_draft_template_id(self) -> int | None:
#         """
#         Same as product, but referencing template_status and templates.
#         """
#         query = """
#             SELECT MAX(t.template_id) AS max_id
#             FROM templates t
#             JOIN template_status ts ON t.id = ts.template_fk
#             WHERE ts.status = 'DRAFT';
#         """
#         self.db.cursor.execute(query)
#         row = self.db.cursor.fetchone()
#         if row and row["max_id"]:
#             return row["max_id"]
#         return None

#     def close(self):
#         self.db.close()








# here

# file: dao/template_dao.py

import json
import uuid
from config.db_connection import DBConnection
from models.printify_template_models import (
	PrintifyTemplateModel,  
	PrintifyVariantModel,
	PrintifyOptionModel,
	PrintifyPrintAreaModel,
	PrintifyImageModel,
	PrintifyTagModel,
	PrintifyExternalModel,
	PrintifySalesChannelPropertyModel,
	PrintifyViewModel
)

class TemplateDAO:
	def __init__(self, db_conn: DBConnection):
		self.db = db_conn
		# Automatically create all tables when this object is instantiated.
		self._create_all_tables()

	def _create_all_tables(self):
		self.create_tables()
		self.create_status_table()

	# ---------------------------------------------------------
	# TABLE CREATION
	# ---------------------------------------------------------
	def create_status_table(self):
		"""
		Creates the 'template_status' table referencing templates.id
		and holding status (DRAFT, PUBLISHED).
		"""
		status_sql = """
		CREATE TABLE IF NOT EXISTS template_status (
			template_fk VARCHAR(36) PRIMARY KEY,
			status ENUM('DRAFT','PUBLISHED') NOT NULL,
			FOREIGN KEY (template_fk) REFERENCES templates(id)
			  ON DELETE CASCADE
		);
		"""
		self.db.cursor.execute(status_sql)
		self.db.connection.commit()
		print("Created 'template_status' table if not present.")

	def create_tables(self):
		"""
		Creates the main 'templates' table and all sub-tables.
		The main table now includes:
		  - id: internal primary key (UUID auto-generated by the database)
		  - template_id: external identifier (VARCHAR(100), UNIQUE)
		Every table’s primary key is a UUID. For sub-tables,
		if the row is referenced later, we will generate the UUID in the DAO.
		"""
		# Main templates table
		main_template_sql = """
		CREATE TABLE IF NOT EXISTS templates (
			id VARCHAR(36) PRIMARY KEY DEFAULT (UUID()),
			template_id VARCHAR(100) NOT NULL,
			title VARCHAR(255),
			description TEXT,
			blueprint_id INT,
			user_id INT,
			shop_id INT,
			visible TINYINT(1),
			is_locked TINYINT(1),
			reviewed TINYINT(1),
			created_at DATETIME,
			updated_at DATETIME,
			print_provider_id INT,
			UNIQUE KEY unique_template_id (template_id)
		);
		"""
		self.db.cursor.execute(main_template_sql)

		# Sub-tables: For these, we use UUIDs generated by the DB (or explicitly for rows that must be referenced)
		tags_sql = """
		CREATE TABLE IF NOT EXISTS template_tags (
			id VARCHAR(36) PRIMARY KEY DEFAULT (UUID()),
			template_id VARCHAR(36),
			tag VARCHAR(255),
			FOREIGN KEY (template_id) REFERENCES templates(id)
			  ON DELETE CASCADE
		);
		"""
		self.db.cursor.execute(tags_sql)

		variants_sql = """
		CREATE TABLE IF NOT EXISTS template_variants (
			id VARCHAR(36) PRIMARY KEY DEFAULT (UUID()),
			template_id VARCHAR(36),
			variant_id INT,
			sku VARCHAR(50),
			cost INT,
			price INT,
			title VARCHAR(255),
			grams INT,
			is_enabled TINYINT(1),
			is_default TINYINT(1),
			is_available TINYINT(1),
			is_printify_express_eligible TINYINT(1),
			quantity INT,
			options JSON,
			FOREIGN KEY (template_id) REFERENCES templates(id)
			  ON DELETE CASCADE
		);
		"""
		self.db.cursor.execute(variants_sql)

		images_sql = """
		CREATE TABLE IF NOT EXISTS template_images (
			id VARCHAR(36) PRIMARY KEY DEFAULT (UUID()),
			template_id VARCHAR(36),
			src TEXT,
			variant_ids JSON,
			position VARCHAR(50),
			is_default TINYINT(1),
			is_selected_for_publishing TINYINT(1),
			order_index INT NULL,
			FOREIGN KEY (template_id) REFERENCES templates(id)
			  ON DELETE CASCADE
		);
		"""
		self.db.cursor.execute(images_sql)

		print_areas_sql = """
		CREATE TABLE IF NOT EXISTS template_print_areas (
			id VARCHAR(36) PRIMARY KEY DEFAULT (UUID()),
			template_id VARCHAR(36),
			variant_ids JSON,
			background VARCHAR(7),
			FOREIGN KEY (template_id) REFERENCES templates(id)
			  ON DELETE CASCADE
		);
		"""
		self.db.cursor.execute(print_areas_sql)

		placeholders_sql = """
		CREATE TABLE IF NOT EXISTS template_placeholders (
			id VARCHAR(36) PRIMARY KEY DEFAULT (UUID()),
			print_area_id VARCHAR(36),
			position VARCHAR(50),
			images JSON,
			FOREIGN KEY (print_area_id) REFERENCES template_print_areas(id)
			  ON DELETE CASCADE
		);
		"""
		self.db.cursor.execute(placeholders_sql)

		external_sql = """
		CREATE TABLE IF NOT EXISTS template_external (
			id VARCHAR(36) PRIMARY KEY DEFAULT (UUID()),
			template_id VARCHAR(36) UNIQUE,
			external_id VARCHAR(100),
			handle TEXT,
			FOREIGN KEY (template_id) REFERENCES templates(id)
			  ON DELETE CASCADE
		);
		"""
		self.db.cursor.execute(external_sql)

		scp_sql = """
		CREATE TABLE IF NOT EXISTS template_sales_channel_properties (
			id VARCHAR(36) PRIMARY KEY DEFAULT (UUID()),
			template_id VARCHAR(36),
			data JSON,
			FOREIGN KEY (template_id) REFERENCES templates(id)
			  ON DELETE CASCADE
		);
		"""
		self.db.cursor.execute(scp_sql)

		views_sql = """
		CREATE TABLE IF NOT EXISTS template_views (
			id VARCHAR(36) PRIMARY KEY DEFAULT (UUID()),
			template_id VARCHAR(36),
			view_id INT,
			label VARCHAR(255),
			position VARCHAR(50),
			FOREIGN KEY (template_id) REFERENCES templates(id)
			  ON DELETE CASCADE
		);
		"""
		self.db.cursor.execute(views_sql)

		view_files_sql = """
		CREATE TABLE IF NOT EXISTS template_view_files (
			id VARCHAR(36) PRIMARY KEY DEFAULT (UUID()),
			view_id VARCHAR(36),
			src TEXT,
			variant_ids JSON,
			FOREIGN KEY (view_id) REFERENCES template_views(id)
			  ON DELETE CASCADE
		);
		"""
		self.db.cursor.execute(view_files_sql)

		self.db.connection.commit()
		print("Created all 'templates' tables if not present.")

	# ---------------------------------------------------------
	# INSERT / UPDATE
	# ---------------------------------------------------------
	def _delete_sub_models(self, internal_id: str):
		"""
		Delete sub-rows referencing the internal id from all sub-tables.
		"""
		tables_to_clear = [
			"template_tags",
			"template_variants",
			"template_images",
			"template_print_areas",
			"template_external",
			"template_sales_channel_properties",
			"template_views"
		]
		for tbl in tables_to_clear:
			sql = f"DELETE FROM {tbl} WHERE template_id = %s"
			self.db.cursor.execute(sql, (internal_id,))
		self.db.connection.commit()

	def insert_or_update_template(self, template_model: PrintifyTemplateModel):
		"""
		Insert or update a template using a PrintifyTemplateModel.
		The model's external identifier is stored in 'template_id' while the
		internal id is auto-generated by the database.
		After the upsert, the internal id is retrieved using the external template_id.
		"""
		import json
		import uuid

		def bool_to_int(b: bool) -> int:
			return 1 if b else 0

		# 1) Upsert main template row.
		#    Include print_provider_id as well.
		upsert_query = """
		INSERT INTO templates (
			template_id,
			title,
			description,
			blueprint_id,
			user_id,
			shop_id,
			visible,
			is_locked,
			reviewed,
			created_at,
			updated_at,
			print_provider_id
		)
		VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
		ON DUPLICATE KEY UPDATE
			title               = VALUES(title),
			description         = VALUES(description),
			blueprint_id        = VALUES(blueprint_id),
			user_id             = VALUES(user_id),
			shop_id             = VALUES(shop_id),
			visible             = VALUES(visible),
			is_locked           = VALUES(is_locked),
			reviewed            = VALUES(reviewed),
			created_at          = VALUES(created_at),
			updated_at          = VALUES(updated_at),
			print_provider_id   = VALUES(print_provider_id)
		;
		"""

		upsert_values = (
			template_model.id,  # external template_id
			template_model.title,
			template_model.description,
			template_model.blueprint_id,
			template_model.user_id,
			template_model.shop_id,
			bool_to_int(template_model.visible),
			bool_to_int(template_model.is_locked),
			bool_to_int(template_model.reviewed),
			template_model.created_at,
			template_model.updated_at,
			template_model.print_provider_id
		)

		try:
			self.db.cursor.execute(upsert_query, upsert_values)
			self.db.connection.commit()
			print(f"Upserted template row for external template_id={template_model.id}")
		except Exception as e:
			print(f"Error upserting template {template_model.id}: {e}")
			return

		# 2) Retrieve the internal id generated by the database.
		self.db.cursor.execute("SELECT id FROM templates WHERE template_id = %s", (template_model.id,))
		row = self.db.cursor.fetchone()
		if not row:
			print("Error: Could not retrieve internal id after upsert.")
			return
		internal_id = row["id"]
		template_model.internal_id = internal_id

		# 3) Remove old sub-model rows using the internal id.
		self._delete_sub_models(internal_id)

		# 4) Insert tags
		insert_tag_sql = "INSERT INTO template_tags (template_id, tag) VALUES (%s, %s)"
		for tmodel in template_model.tags:
			self.db.cursor.execute(insert_tag_sql, (internal_id, tmodel.tag))

		# 5) Insert variants
		insert_variant_sql = """
		INSERT INTO template_variants (
			template_id, variant_id, sku, cost, price, title,
			grams, is_enabled, is_default, is_available,
			is_printify_express_eligible, quantity, options
		)
		VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
		"""
		for vmodel in template_model.variants:
			vdata = vmodel.data
			if not isinstance(vdata, dict):
				continue
			variant_id = vdata.get("id")
			sku = vdata.get("sku")
			cost = vdata.get("cost")
			price = vdata.get("price")
			title = vdata.get("title")
			grams = vdata.get("grams")
			is_enabled = bool_to_int(vdata.get("is_enabled", False))
			is_default = bool_to_int(vdata.get("is_default", False))
			is_available = bool_to_int(vdata.get("is_available", False))
			is_express = bool_to_int(vdata.get("is_printify_express_eligible", False))
			quantity = vdata.get("quantity", 1)
			options_json = json.dumps(vdata.get("options", []))

			self.db.cursor.execute(
				insert_variant_sql,
				(
					internal_id,
					variant_id,
					sku,
					cost,
					price,
					title,
					grams,
					is_enabled,
					is_default,
					is_available,
					is_express,
					quantity,
					options_json
				)
			)

		# 6) Insert images
		insert_img_sql = """
		INSERT INTO template_images (
			template_id, src, variant_ids, position,
			is_default, is_selected_for_publishing, order_index
		)
		VALUES (%s, %s, %s, %s, %s, %s, %s)
		"""
		for imodel in template_model.images:
			idata = imodel.data
			if not isinstance(idata, dict):
				continue
			src = idata.get("src")
			variant_ids = json.dumps(idata.get("variant_ids", []))
			position = idata.get("position")
			is_def = bool_to_int(idata.get("is_default", False))
			is_pub = bool_to_int(idata.get("is_selected_for_publishing", False))
			order_i = idata.get("order", None)

			self.db.cursor.execute(
				insert_img_sql,
				(
					internal_id,
					src,
					variant_ids,
					position,
					is_def,
					is_pub,
					order_i
				)
			)

		# 7) Insert print areas and placeholders.
		insert_pa_sql = """
		INSERT INTO template_print_areas (id, template_id, variant_ids, background)
		VALUES (%s, %s, %s, %s)
		"""
		insert_ph_sql = """
		INSERT INTO template_placeholders (id, print_area_id, position, images)
		VALUES (%s, %s, %s, %s)
		"""
		for pa_model in template_model.print_areas:
			pa_data = pa_model.data
			if not isinstance(pa_data, dict):
				continue
			variant_ids_json = json.dumps(pa_data.get("variant_ids", []))
			background = pa_data.get("background")
			pa_internal_id = str(uuid.uuid4())

			self.db.cursor.execute(insert_pa_sql, (pa_internal_id, internal_id, variant_ids_json, background))

			for ph in pa_data.get("placeholders", []):
				ph_internal_id = str(uuid.uuid4())
				images_json = json.dumps(ph.get("images", []))
				position_val = ph.get("position")
				self.db.cursor.execute(
					insert_ph_sql,
					(ph_internal_id, pa_internal_id, position_val, images_json)
				)

		# 8) Insert external
		if template_model.external and isinstance(template_model.external.data, dict):
			ext_data = template_model.external.data
			insert_ext_sql = """
			INSERT INTO template_external (id, template_id, external_id, handle)
			VALUES (UUID(), %s, %s, %s)
			ON DUPLICATE KEY UPDATE
				external_id = VALUES(external_id),
				handle = VALUES(handle)
			"""
			self.db.cursor.execute(
				insert_ext_sql,
				(
					internal_id,
					ext_data.get("id"),
					ext_data.get("handle")
				)
			)

		# 9) Insert sales channel properties
		insert_scp_sql = """
		INSERT INTO template_sales_channel_properties (id, template_id, data)
		VALUES (UUID(), %s, %s)
		"""
		for scp_model in template_model.sales_channel_properties:
			scp_data = scp_model.data if isinstance(scp_model.data, dict) else {}
			json_data = json.dumps(scp_data)
			self.db.cursor.execute(insert_scp_sql, (internal_id, json_data))

		# 10) Insert views and view files
		insert_view_sql = """
		INSERT INTO template_views (id, template_id, view_id, label, position)
		VALUES (UUID(), %s, %s, %s, %s)
		"""
		insert_view_file_sql = """
		INSERT INTO template_view_files (id, view_id, src, variant_ids)
		VALUES (UUID(), %s, %s, %s)
		"""
		for v_model in template_model.views:
			vdata = v_model.data
			if not isinstance(vdata, dict):
				continue

			view_id = vdata.get("id")
			label = vdata.get("label")
			position = vdata.get("position")

			# Insert the view row
			self.db.cursor.execute(
				insert_view_sql,
				(internal_id, view_id, label, position)
			)

			# Retrieve the newly created row ID for the template_views row
			self.db.cursor.execute(
				"SELECT id FROM template_views WHERE template_id = %s AND view_id = %s",
				(internal_id, view_id)
			)
			view_row = self.db.cursor.fetchone()
			if view_row:
				internal_view_id = view_row["id"]
				# Insert the files for this view
				for vf in vdata.get("files", []):
					variant_ids_json = json.dumps(vf.get("variant_ids", []))
					src = vf.get("src")
					self.db.cursor.execute(
						insert_view_file_sql,
						(internal_view_id, src, variant_ids_json)
					)

		self.db.connection.commit()
		print(
			f"Upserted template with internal id={internal_id} "
			f"(external template_id={template_model.id}) and its sub-models."
		)


	# ---------------------------------------------------------
	# FETCH
	# ---------------------------------------------------------
	def fetch_template_from_template_id(self, external_template_id: str) -> PrintifyTemplateModel | None:
		"""
		Loads from DB, reconstructs a PrintifyTemplateModel.
		Here the lookup is performed using the external template identifier
		(the value stored in the column 'template_id'). Once found, the internal
		primary key (from the 'id' column) is used to query the sub-tables.
		"""
		# Look up the main record using the external template id.
		main_q = "SELECT * FROM templates WHERE template_id = %s"
		self.db.cursor.execute(main_q, (external_template_id,))
		row = self.db.cursor.fetchone()
		if not row:
			return None

		# Retrieve the internally generated id.
		internal_id = row["id"]

		pm = PrintifyTemplateModel(
			id=row["template_id"],  # external template id
			title=row["title"],
			description=row["description"],
			blueprint_id=row["blueprint_id"],
			user_id=row["user_id"],
			shop_id=row["shop_id"],
			visible=bool(row["visible"]),
			is_locked=bool(row["is_locked"]),
			reviewed=bool(row["reviewed"]),
			created_at=str(row["created_at"]) if row["created_at"] else None,
			updated_at=str(row["updated_at"]) if row["updated_at"] else None,
			print_provider_id=row["print_provider_id"]
		)
		# Save the internal id in the model for later reference.
		pm.internal_id = internal_id

		# Now use the internal id to fetch sub-model rows.
		self.db.cursor.execute("SELECT tag FROM template_tags WHERE template_id = %s", (internal_id,))
		for trow in self.db.cursor.fetchall():
			pm.tags.append(PrintifyTagModel(external_template_id, trow["tag"]))

		self.db.cursor.execute("SELECT * FROM template_variants WHERE template_id = %s", (internal_id,))
		for vrow in self.db.cursor.fetchall():
			data_dict = {
				"id": vrow["variant_id"],
				"sku": vrow["sku"],
				"cost": vrow["cost"],
				"price": vrow["price"],
				"title": vrow["title"],
				"grams": vrow["grams"],
				"is_enabled": bool(vrow["is_enabled"]),
				"is_default": bool(vrow["is_default"]),
				"is_available": bool(vrow["is_available"]),
				"is_printify_express_eligible": bool(vrow["is_printify_express_eligible"]),
				"quantity": vrow["quantity"],
				"options": json.loads(vrow["options"]) if vrow["options"] else []
			}
			pm.variants.append(PrintifyVariantModel(external_template_id, data_dict))

		self.db.cursor.execute("SELECT * FROM template_images WHERE template_id = %s", (internal_id,))
		for irow in self.db.cursor.fetchall():
			data_dict = {
				"src": irow["src"],
				"variant_ids": json.loads(irow["variant_ids"]) if irow["variant_ids"] else [],
				"position": irow["position"],
				"is_default": bool(irow["is_default"]),
				"is_selected_for_publishing": bool(irow["is_selected_for_publishing"]),
				"order": irow["order_index"]
			}
			pm.images.append(PrintifyImageModel(external_template_id, data_dict))

		self.db.cursor.execute("SELECT * FROM template_print_areas WHERE template_id = %s", (internal_id,))
		pa_rows = self.db.cursor.fetchall()
		for par in pa_rows:
			pa_id = par["id"]
			self.db.cursor.execute("SELECT * FROM template_placeholders WHERE print_area_id = %s", (pa_id,))
			ph_rows = self.db.cursor.fetchall()
			placeholders_list = []
			for ph in ph_rows:
				placeholders_list.append({
					"position": ph["position"],
					"images": json.loads(ph["images"]) if ph["images"] else []
				})
			pa_data = {
				"variant_ids": json.loads(par["variant_ids"]) if par["variant_ids"] else [],
				"background": par["background"],
				"placeholders": placeholders_list
			}
			pm.print_areas.append(PrintifyPrintAreaModel(external_template_id, pa_data))

		self.db.cursor.execute("SELECT * FROM template_external WHERE template_id = %s", (internal_id,))
		er = self.db.cursor.fetchone()
		if er:
			pm.external = PrintifyExternalModel(external_template_id, {
				"id": er["external_id"],
				"handle": er["handle"]
			})

		self.db.cursor.execute("SELECT data FROM template_sales_channel_properties WHERE template_id = %s", (internal_id,))
		for scp_row in self.db.cursor.fetchall():
			scp_data = json.loads(scp_row["data"]) if scp_row["data"] else {}
			pm.sales_channel_properties.append(PrintifySalesChannelPropertyModel(external_template_id, scp_data))

		self.db.cursor.execute("SELECT * FROM template_views WHERE template_id = %s", (internal_id,))
		view_rows = self.db.cursor.fetchall()
		for vr in view_rows:
			view_id = vr["view_id"]
			label = vr["label"]
			position = vr["position"]
			self.db.cursor.execute("SELECT * FROM template_view_files WHERE view_id = %s", (vr["id"],))
			vf_rows = self.db.cursor.fetchall()
			files_list = []
			for vfr in vf_rows:
				files_list.append({
					"src": vfr["src"],
					"variant_ids": json.loads(vfr["variant_ids"]) if vfr["variant_ids"] else []
				})
			view_data = {
				"id": view_id,
				"label": label,
				"position": position,
				"files": files_list
			}
			pm.views.append(PrintifyViewModel(external_template_id, view_data))

		return pm


	def set_status_by_template_id(self, template_id: str, new_status: str):
		if new_status not in ("DRAFT", "PUBLISHED"):
			raise ValueError(f"Invalid status '{new_status}'.")
		# Use the template_id column to search for the record.
		select_q = "SELECT id FROM templates WHERE template_id = %s"
		self.db.cursor.execute(select_q, (template_id,))
		row = self.db.cursor.fetchone()
		if not row:
			print(f"No template found with template_id={template_id}")
			return
		local_id = row["id"]
		upsert_sql = """
		INSERT INTO template_status (template_fk, status)
		VALUES (%s, %s)
		ON DUPLICATE KEY UPDATE status = VALUES(status);
		"""
		self.db.cursor.execute(upsert_sql, (local_id, new_status))
		self.db.connection.commit()
		print(f"Set status for template id={template_id} to '{new_status}'.")


	def set_status_by_id(self, db_id: int, new_status: str):
		if new_status not in ("DRAFT", "PUBLISHED"):
			raise ValueError(f"Invalid status '{new_status}'.")

		check_q = "SELECT id FROM templates WHERE id = %s"
		self.db.cursor.execute(check_q, (db_id,))
		row = self.db.cursor.fetchone()
		if not row:
			print(f"No template found with id={db_id}")
			return

		upsert_sql = """
		INSERT INTO template_status (template_fk, status)
		VALUES (%s, %s)
		ON DUPLICATE KEY UPDATE status = VALUES(status)
		"""
		self.db.cursor.execute(upsert_sql, (db_id, new_status))
		self.db.connection.commit()
		print(f"Set status for id={db_id} to '{new_status}'.")

	def fetch_max_draft_template_id(self) -> int | None:
		"""
		Returns the maximum external template_id among templates with status 'DRAFT'.
		"""
		query = """
			SELECT MAX(t.template_id) AS max_id
			FROM templates t
			JOIN template_status ts ON t.id = ts.template_fk
			WHERE ts.status = 'DRAFT';
		"""
		self.db.cursor.execute(query)
		row = self.db.cursor.fetchone()
		if row and row["max_id"]:
			return row["max_id"]
		return None

	def close(self):
		self.db.close()
