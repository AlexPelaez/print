# file: dao/template_dao.py

import json
from config.db_connection import DBConnection

# If you have a separate model definitions for "templates", e.g. PrintifyTemplateModel, 
# replicate them. If they are the same structure as PrintifyProductModel, you can reuse or 
# create a new class. Here, we assume you have PrintifyProductModel or a similar structure:
from printify_product_models import (
    PrintifyProductModel,  # or PrintifyTemplateModel if you prefer
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
            template_fk INT PRIMARY KEY,
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
        Creates the main 'templates' table + all sub-tables
        referencing 'templates' in place of 'products'.
        """
        main_template_sql = """
        CREATE TABLE IF NOT EXISTS templates (
            id INT AUTO_INCREMENT PRIMARY KEY,
            template_id VARCHAR(100) NOT NULL,
            title VARCHAR(255),
            description TEXT,
            blueprint_id INT,
            print_provider_id INT,
            user_id INT,
            shop_id INT,
            visible TINYINT(1),
            is_locked TINYINT(1),
            reviewed TINYINT(1),
            created_at DATETIME,
            updated_at DATETIME,
            UNIQUE KEY unique_template_id (template_id)
        );
        """
        self.db.cursor.execute(main_template_sql)

        tags_sql = """
        CREATE TABLE IF NOT EXISTS template_tags (
            id INT AUTO_INCREMENT PRIMARY KEY,
            template_id VARCHAR(100),
            tag VARCHAR(255),
            FOREIGN KEY (template_id) REFERENCES templates(template_id)
              ON DELETE CASCADE
        );
        """
        self.db.cursor.execute(tags_sql)

        variants_sql = """
        CREATE TABLE IF NOT EXISTS template_variants (
            id INT AUTO_INCREMENT PRIMARY KEY,
            template_id VARCHAR(100),
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
            FOREIGN KEY (template_id) REFERENCES templates(template_id)
              ON DELETE CASCADE
        );
        """
        self.db.cursor.execute(variants_sql)

        images_sql = """
        CREATE TABLE IF NOT EXISTS template_images (
            id INT AUTO_INCREMENT PRIMARY KEY,
            template_id VARCHAR(100),
            src TEXT,
            variant_ids JSON,
            position VARCHAR(50),
            is_default TINYINT(1),
            is_selected_for_publishing TINYINT(1),
            order_index INT NULL,
            FOREIGN KEY (template_id) REFERENCES templates(template_id)
              ON DELETE CASCADE
        );
        """
        self.db.cursor.execute(images_sql)

        print_areas_sql = """
        CREATE TABLE IF NOT EXISTS template_print_areas (
            id INT AUTO_INCREMENT PRIMARY KEY,
            template_id VARCHAR(100),
            variant_ids JSON,
            background VARCHAR(7),
            FOREIGN KEY (template_id) REFERENCES templates(template_id)
              ON DELETE CASCADE
        );
        """
        self.db.cursor.execute(print_areas_sql)

        placeholders_sql = """
        CREATE TABLE IF NOT EXISTS template_placeholders (
            id INT AUTO_INCREMENT PRIMARY KEY,
            print_area_id INT,
            position VARCHAR(50),
            images JSON,
            FOREIGN KEY (print_area_id) REFERENCES template_print_areas(id)
              ON DELETE CASCADE
        );
        """
        self.db.cursor.execute(placeholders_sql)

        external_sql = """
        CREATE TABLE IF NOT EXISTS template_external (
            template_id VARCHAR(100) PRIMARY KEY,
            external_id VARCHAR(100),
            handle TEXT,
            FOREIGN KEY (template_id) REFERENCES templates(template_id)
              ON DELETE CASCADE
        );
        """
        self.db.cursor.execute(external_sql)

        scp_sql = """
        CREATE TABLE IF NOT EXISTS template_sales_channel_properties (
            id INT AUTO_INCREMENT PRIMARY KEY,
            template_id VARCHAR(100),
            data JSON,
            FOREIGN KEY (template_id) REFERENCES templates(template_id)
              ON DELETE CASCADE
        );
        """
        self.db.cursor.execute(scp_sql)

        views_sql = """
        CREATE TABLE IF NOT EXISTS template_views (
            id INT AUTO_INCREMENT PRIMARY KEY,
            template_id VARCHAR(100),
            view_id INT,
            label VARCHAR(255),
            position VARCHAR(50),
            FOREIGN KEY (template_id) REFERENCES templates(template_id)
              ON DELETE CASCADE
        );
        """
        self.db.cursor.execute(views_sql)

        view_files_sql = """
        CREATE TABLE IF NOT EXISTS template_view_files (
            id INT AUTO_INCREMENT PRIMARY KEY,
            view_id INT,
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
    def _delete_sub_models(self, template_id: str):
        """
        Delete sub-rows referencing template_id from all sub-tables.
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
            self.db.cursor.execute(sql, (template_id,))
        self.db.connection.commit()

    def insert_or_update_template(self, template_model: PrintifyProductModel):
        """
        Insert or update a template using a Printify-style Model.
        We'll treat 'id' as 'template_id' for naming consistency.
        The rest is the same logic as the ProductDAO, but referencing
        'templates' and sub-tables named 'template_*'.
        """
        def bool_to_int(b):
            return 1 if b else 0

        # 1) Upsert main row
        upsert_query = """
        INSERT INTO templates (
            template_id, title, description, 
            blueprint_id, print_provider_id, 
            user_id, shop_id, 
            visible, is_locked, reviewed,
            created_at, updated_at
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            title = VALUES(title),
            description = VALUES(description),
            blueprint_id = VALUES(blueprint_id),
            print_provider_id = VALUES(print_provider_id),
            user_id = VALUES(user_id),
            shop_id = VALUES(shop_id),
            visible = VALUES(visible),
            is_locked = VALUES(is_locked),
            reviewed = VALUES(reviewed),
            created_at = VALUES(created_at),
            updated_at = VALUES(updated_at)
        ;
        """
        upsert_values = (
            template_model.id,
            template_model.title,
            template_model.description,
            template_model.blueprint_id,
            template_model.print_provider_id,
            template_model.user_id,
            template_model.shop_id,
            bool_to_int(template_model.visible),
            bool_to_int(template_model.is_locked),
            bool_to_int(template_model.reviewed),
            template_model.created_at,
            template_model.updated_at
        )

        try:
            self.db.cursor.execute(upsert_query, upsert_values)
            self.db.connection.commit()
            print(f"Upserted template row for template_id={template_model.id}")
        except Exception as e:
            print(f"Error upserting template {template_model.id}: {e}")
            return

        # 2) Remove old sub-model rows
        self._delete_sub_models(template_model.id)

        # 3) Insert tags
        insert_tag_sql = "INSERT INTO template_tags (template_id, tag) VALUES (%s, %s)"
        for tmodel in template_model.tags:
            self.db.cursor.execute(insert_tag_sql, (template_model.id, tmodel.tag))

        # 4) Insert variants
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

            self.db.cursor.execute(insert_variant_sql, (
                template_model.id,
                variant_id, sku, cost, price, title,
                grams, is_enabled, is_default, is_available,
                is_express, quantity, options_json
            ))

        # 5) Insert images
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

            self.db.cursor.execute(insert_img_sql, (
                template_model.id, src, variant_ids,
                position, is_def, is_pub, order_i
            ))

        # 6) Insert print_areas + placeholders
        insert_pa_sql = """
        INSERT INTO template_print_areas (template_id, variant_ids, background)
        VALUES (%s, %s, %s)
        """
        insert_ph_sql = """
        INSERT INTO template_placeholders (print_area_id, position, images)
        VALUES (%s, %s, %s)
        """
        for pa_model in template_model.print_areas:
            pa_data = pa_model.data
            if not isinstance(pa_data, dict):
                continue

            variant_ids_json = json.dumps(pa_data.get("variant_ids", []))
            background = pa_data.get("background")

            self.db.cursor.execute(insert_pa_sql, (template_model.id, variant_ids_json, background))
            pa_db_id = self.db.cursor.lastrowid

            for ph in pa_data.get("placeholders", []):
                images_json = json.dumps(ph.get("images", []))
                position_val = ph.get("position")
                self.db.cursor.execute(insert_ph_sql, (pa_db_id, position_val, images_json))

        # 7) Insert external
        if template_model.external and isinstance(template_model.external.data, dict):
            ext_data = template_model.external.data
            insert_ext_sql = """
            INSERT INTO template_external (template_id, external_id, handle)
            VALUES (%s, %s, %s)
            ON DUPLICATE KEY UPDATE
                external_id = VALUES(external_id),
                handle = VALUES(handle)
            """
            self.db.cursor.execute(insert_ext_sql, (
                template_model.id,
                ext_data.get("id"),
                ext_data.get("handle")
            ))

        # 8) Insert sales_channel_properties
        insert_scp_sql = """
        INSERT INTO template_sales_channel_properties (template_id, data)
        VALUES (%s, %s)
        """
        for scp_model in template_model.sales_channel_properties:
            scp_data = scp_model.data if isinstance(scp_model.data, dict) else {}
            self.db.cursor.execute(insert_scp_sql, (template_model.id, json.dumps(scp_data)))

        # 9) Insert views
        insert_view_sql = """
        INSERT INTO template_views (
            template_id, view_id, label, position
        ) VALUES (%s, %s, %s, %s)
        """
        insert_view_file_sql = """
        INSERT INTO template_view_files (view_id, src, variant_ids)
        VALUES (%s, %s, %s)
        """
        for v_model in template_model.views:
            vdata = v_model.data
            if not isinstance(vdata, dict):
                continue
            view_id = vdata.get("id")
            label = vdata.get("label")
            position = vdata.get("position")

            self.db.cursor.execute(insert_view_sql, (template_model.id, view_id, label, position))
            db_view_id = self.db.cursor.lastrowid

            for vf in vdata.get("files", []):
                variant_ids_json = json.dumps(vf.get("variant_ids", []))
                src = vf.get("src")
                self.db.cursor.execute(insert_view_file_sql, (db_view_id, src, variant_ids_json))

        self.db.connection.commit()
        print(f"Upserted template {template_model.id} + sub-models from model.")

    # ---------------------------------------------------------
    # FETCH
    # ---------------------------------------------------------
    def fetch_template_from_template_id(self, template_id: str) -> PrintifyProductModel | None:
        """
        Loads from DB, reconstructs a PrintifyProductModel (or 'template' model).
        """
        main_q = "SELECT * FROM templates WHERE template_id = %s"
        self.db.cursor.execute(main_q, (template_id,))
        row = self.db.cursor.fetchone()
        if not row:
            return None

        pm = PrintifyProductModel(  # or a separate PrintifyTemplateModel
            id=row["template_id"],
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

        # tags
        self.db.cursor.execute("SELECT tag FROM template_tags WHERE template_id = %s", (template_id,))
        for trow in self.db.cursor.fetchall():
            pm.tags.append(PrintifyTagModel(template_id, trow["tag"]))

        # variants
        self.db.cursor.execute("SELECT * FROM template_variants WHERE template_id = %s", (template_id,))
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
            pm.variants.append(PrintifyVariantModel(template_id, data_dict))

        # images
        self.db.cursor.execute("SELECT * FROM template_images WHERE template_id = %s", (template_id,))
        for irow in self.db.cursor.fetchall():
            data_dict = {
                "src": irow["src"],
                "variant_ids": json.loads(irow["variant_ids"]) if irow["variant_ids"] else [],
                "position": irow["position"],
                "is_default": bool(irow["is_default"]),
                "is_selected_for_publishing": bool(irow["is_selected_for_publishing"]),
                "order": irow["order_index"]
            }
            pm.images.append(PrintifyImageModel(template_id, data_dict))

        # print_areas + placeholders
        self.db.cursor.execute("SELECT * FROM template_print_areas WHERE template_id = %s", (template_id,))
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
            pm.print_areas.append(PrintifyPrintAreaModel(template_id, pa_data))

        # external
        self.db.cursor.execute("SELECT * FROM template_external WHERE template_id = %s", (template_id,))
        er = self.db.cursor.fetchone()
        if er:
            pm.external = PrintifyExternalModel(template_id, {
                "id": er["external_id"],
                "handle": er["handle"]
            })

        # sales_channel_properties
        self.db.cursor.execute("SELECT data FROM template_sales_channel_properties WHERE template_id = %s", (template_id,))
        for scp_row in self.db.cursor.fetchall():
            scp_data = json.loads(scp_row["data"]) if scp_row["data"] else {}
            pm.sales_channel_properties.append(PrintifySalesChannelPropertyModel(template_id, scp_data))

        # views
        self.db.cursor.execute("SELECT * FROM template_views WHERE template_id = %s", (template_id,))
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
            pm.views.append(PrintifyViewModel(template_id, view_data))

        return pm

    def set_status_by_template_id(self, template_id: str, new_status: str):
        if new_status not in ("DRAFT", "PUBLISHED"):
            raise ValueError(f"Invalid status '{new_status}'.")

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
        print(f"Set status for template_id={template_id} (id={local_id}) to '{new_status}'.")

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
        print(f"Set status for local id={db_id} to '{new_status}'.")

    def fetch_max_draft_template_id(self) -> int | None:
        """
        Same as product, but referencing template_status and templates.
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
