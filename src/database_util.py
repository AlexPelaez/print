# file: database_util.py

import mysql.connector
from mysql.connector import Error
import json

# Import the model definitions
from printify_product_models import (
    PrintifyProductModel,
    PrintifyVariantModel,
    PrintifyOptionModel,
    PrintifyPrintAreaModel,
    PrintifyImageModel,
    PrintifyTagModel,
    PrintifyExternalModel,
    PrintifySalesChannelPropertyModel,
    PrintifyViewModel
    # etc. if you want all of them
)

class DatabaseUtil:
    def __init__(self, host="localhost", user="root", password="", database="my_database"):
        self.host = host
        self.user = user
        self.password = password
        self.database = database
        self.connection = None
        self.cursor = None

        self.connect()

    def connect(self):
        try:
            self.connection = mysql.connector.connect(
                host=self.host,
                user=self.user,
                password=self.password,
                database=self.database
            )
            self.cursor = self.connection.cursor(dictionary=True)
            print("Connected to the database successfully!")
        except Error as e:
            print(f"Error connecting to MySQL: {e}")

    # ---------------------------------------------------------
    # TABLE CREATION (optional if you have them already)
    # ---------------------------------------------------------
    def create_tables(self):
        """
        Example of how you'd create the main product table + sub-tables.
        Adjust as needed.
        """
        main_product_sql = """
        CREATE TABLE IF NOT EXISTS products (
            id INT AUTO_INCREMENT PRIMARY KEY,
            product_id VARCHAR(100) NOT NULL,
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
            UNIQUE KEY unique_product_id (product_id)
        );
        """
        self.cursor.execute(main_product_sql)

        # Example sub-table: tags
        tags_sql = """
        CREATE TABLE IF NOT EXISTS product_tags (
            id INT AUTO_INCREMENT PRIMARY KEY,
            product_id VARCHAR(100),
            tag VARCHAR(255),
            FOREIGN KEY (product_id) REFERENCES products(product_id)
              ON DELETE CASCADE
        );
        """
        self.cursor.execute(tags_sql)

        # Example sub-table: variants
        variants_sql = """
        CREATE TABLE IF NOT EXISTS product_variants (
            id INT AUTO_INCREMENT PRIMARY KEY,
            product_id VARCHAR(100),
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
            FOREIGN KEY (product_id) REFERENCES products(product_id)
              ON DELETE CASCADE
        );
        """
        self.cursor.execute(variants_sql)

        # Example sub-table: images
        images_sql = """
        CREATE TABLE IF NOT EXISTS product_images (
            id INT AUTO_INCREMENT PRIMARY KEY,
            product_id VARCHAR(100),
            src TEXT,
            variant_ids JSON,
            position VARCHAR(50),
            is_default TINYINT(1),
            is_selected_for_publishing TINYINT(1),
            order_index INT NULL,
            FOREIGN KEY (product_id) REFERENCES products(product_id)
              ON DELETE CASCADE
        );
        """
        self.cursor.execute(images_sql)

        # Example sub-table: print_areas
        print_areas_sql = """
        CREATE TABLE IF NOT EXISTS product_print_areas (
            id INT AUTO_INCREMENT PRIMARY KEY,
            product_id VARCHAR(100),
            variant_ids JSON,
            background VARCHAR(7),
            FOREIGN KEY (product_id) REFERENCES products(product_id)
              ON DELETE CASCADE
        );
        """
        self.cursor.execute(print_areas_sql)

        # Example sub-table: placeholders in each print_area
        placeholders_sql = """
        CREATE TABLE IF NOT EXISTS product_placeholders (
            id INT AUTO_INCREMENT PRIMARY KEY,
            print_area_id INT,
            position VARCHAR(50),
            images JSON,
            FOREIGN KEY (print_area_id) REFERENCES product_print_areas(id)
              ON DELETE CASCADE
        );
        """
        self.cursor.execute(placeholders_sql)

        # Example: external
        external_sql = """
        CREATE TABLE IF NOT EXISTS product_external (
            product_id VARCHAR(100) PRIMARY KEY,
            external_id VARCHAR(100),
            handle TEXT,
            FOREIGN KEY (product_id) REFERENCES products(product_id)
              ON DELETE CASCADE
        );
        """
        self.cursor.execute(external_sql)

        # Example: sales_channel_properties
        scp_sql = """
        CREATE TABLE IF NOT EXISTS product_sales_channel_properties (
            id INT AUTO_INCREMENT PRIMARY KEY,
            product_id VARCHAR(100),
            data JSON,
            FOREIGN KEY (product_id) REFERENCES products(product_id)
              ON DELETE CASCADE
        );
        """
        self.cursor.execute(scp_sql)

        # Example: views
        views_sql = """
        CREATE TABLE IF NOT EXISTS product_views (
            id INT AUTO_INCREMENT PRIMARY KEY,
            product_id VARCHAR(100),
            view_id INT,
            label VARCHAR(255),
            position VARCHAR(50),
            FOREIGN KEY (product_id) REFERENCES products(product_id)
              ON DELETE CASCADE
        );
        """
        self.cursor.execute(views_sql)

        # Example: view_files
        view_files_sql = """
        CREATE TABLE IF NOT EXISTS product_view_files (
            id INT AUTO_INCREMENT PRIMARY KEY,
            view_id INT,
            src TEXT,
            variant_ids JSON,
            FOREIGN KEY (view_id) REFERENCES product_views(id)
              ON DELETE CASCADE
        );
        """
        self.cursor.execute(view_files_sql)

        self.connection.commit()
        print("Created all tables if not present.")

    # ---------------------------------------------------------
    # INSERT / UPDATE
    # ---------------------------------------------------------

    def _delete_sub_models(self, product_id: str):
        """
        Delete sub-rows referencing product_id.
        This ensures we can re-insert fresh data each time.
        """
        tables_to_clear = [
            "product_tags",
            "product_variants",
            "product_images",
            "product_print_areas",
            "product_external",
            "product_sales_channel_properties",
            "product_views"
            # placeholders will be deleted via CASCADE from product_print_areas
            # view_files will be deleted via CASCADE from product_views
        ]
        for tbl in tables_to_clear:
            sql = f"DELETE FROM {tbl} WHERE product_id = %s"
            self.cursor.execute(sql, (product_id,))
        self.connection.commit()

    def insert_or_update_product(self, product_model: PrintifyProductModel):
        """
        Insert or update a product using a PrintifyProductModel object
        (instead of a dict). Then insert sub-model rows:
            tags, variants, images, print_areas, placeholders, external, etc.
        """

        def bool_to_int(b):
            return 1 if b else 0

        # 1) Upsert the main product row
        upsert_query = """
        INSERT INTO products (
            product_id, title, description, 
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
            product_model.id,
            product_model.title,
            product_model.description,
            product_model.blueprint_id,
            product_model.print_provider_id,
            product_model.user_id,
            product_model.shop_id,
            bool_to_int(product_model.visible),
            bool_to_int(product_model.is_locked),
            bool_to_int(product_model.reviewed),
            product_model.created_at,
            product_model.updated_at
        )

        try:
            self.cursor.execute(upsert_query, upsert_values)
            self.connection.commit()
            print(f"Upserted main product row for ID = {product_model.id}")
        except Exception as e:
            print(f"Error upserting product {product_model.id}: {e}")
            return

        # 2) Clear sub-rows for this product
        self._delete_sub_models(product_model.id)

        # 3) Insert tags
        insert_tag_sql = "INSERT INTO product_tags (product_id, tag) VALUES (%s, %s)"
        for tmodel in product_model.tags:
            self.cursor.execute(insert_tag_sql, (product_model.id, tmodel.tag))

        # 4) Insert variants
        insert_variant_sql = """
        INSERT INTO product_variants (
            product_id, variant_id, sku, cost, price, title,
            grams, is_enabled, is_default, is_available,
            is_printify_express_eligible, quantity, options
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        for vmodel in product_model.variants:
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

            self.cursor.execute(insert_variant_sql, (
                product_model.id,
                variant_id, sku, cost, price, title,
                grams, is_enabled, is_default, is_available,
                is_express, quantity, options_json
            ))

        # 5) Insert images
        insert_img_sql = """
        INSERT INTO product_images (
            product_id, src, variant_ids, position,
            is_default, is_selected_for_publishing, order_index
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        for imodel in product_model.images:
            idata = imodel.data
            if not isinstance(idata, dict):
                continue
            src = idata.get("src")
            variant_ids = json.dumps(idata.get("variant_ids", []))
            position = idata.get("position")
            is_def = bool_to_int(idata.get("is_default", False))
            is_pub = bool_to_int(idata.get("is_selected_for_publishing", False))
            order_i = idata.get("order", None)

            self.cursor.execute(insert_img_sql, (
                product_model.id,
                src, variant_ids,
                position, is_def, is_pub, order_i
            ))

        # 6) Insert print_areas + placeholders
        insert_pa_sql = """
        INSERT INTO product_print_areas (product_id, variant_ids, background)
        VALUES (%s, %s, %s)
        """
        insert_ph_sql = """
        INSERT INTO product_placeholders (print_area_id, position, images)
        VALUES (%s, %s, %s)
        """
        for pa_model in product_model.print_areas:
            pa_data = pa_model.data
            if not isinstance(pa_data, dict):
                continue

            variant_ids = json.dumps(pa_data.get("variant_ids", []))
            background = pa_data.get("background")

            self.cursor.execute(insert_pa_sql, (product_model.id, variant_ids, background))
            pa_db_id = self.cursor.lastrowid

            # placeholders
            for ph in pa_data.get("placeholders", []):
                images_json = json.dumps(ph.get("images", []))
                position_val = ph.get("position")
                self.cursor.execute(insert_ph_sql, (pa_db_id, position_val, images_json))

        # 7) Insert external
        if product_model.external and isinstance(product_model.external.data, dict):
            ext_data = product_model.external.data
            insert_ext_sql = """
            INSERT INTO product_external (product_id, external_id, handle)
            VALUES (%s, %s, %s)
            ON DUPLICATE KEY UPDATE
                external_id = VALUES(external_id),
                handle = VALUES(handle)
            """
            self.cursor.execute(insert_ext_sql, (
                product_model.id,
                ext_data.get("id"),
                ext_data.get("handle")
            ))

        # 8) Insert sales_channel_properties
        insert_scp_sql = """
        INSERT INTO product_sales_channel_properties (product_id, data)
        VALUES (%s, %s)
        """
        for scp in product_model.sales_channel_properties:
            scp_data = scp.data if isinstance(scp.data, dict) else {}
            self.cursor.execute(insert_scp_sql, (product_model.id, json.dumps(scp_data)))

        # 9) Insert views
        insert_view_sql = """
        INSERT INTO product_views (
            product_id, view_id, label, position
        ) VALUES (%s, %s, %s, %s)
        """
        insert_view_file_sql = """
        INSERT INTO product_view_files (view_id, src, variant_ids)
        VALUES (%s, %s, %s)
        """
        for v_model in product_model.views:
            vdata = v_model.data
            if not isinstance(vdata, dict):
                continue
            view_id = vdata.get("id")
            label = vdata.get("label")
            position = vdata.get("position")

            self.cursor.execute(insert_view_sql, (product_model.id, view_id, label, position))
            db_view_id = self.cursor.lastrowid

            # files array
            for vf in vdata.get("files", []):
                variant_ids_json = json.dumps(vf.get("variant_ids", []))
                src = vf.get("src")
                self.cursor.execute(insert_view_file_sql, (db_view_id, src, variant_ids_json))

        self.connection.commit()
        print(f"Upserted product {product_model.id} + sub-models from model.")

    # ---------------------------------------------------------
    # FETCH
    # ---------------------------------------------------------

    def fetch_product_as_model(self, product_id: str) -> PrintifyProductModel | None:
        """
        Example method that loads from DB and builds a PrintifyProductModel.
        """
        # 1) Fetch main row
        main_q = "SELECT * FROM products WHERE product_id = %s"
        self.cursor.execute(main_q, (product_id,))
        row = self.cursor.fetchone()
        if not row:
            return None

        pm = PrintifyProductModel(
            id=row["product_id"],
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

        # 2) tags
        self.cursor.execute("SELECT tag FROM product_tags WHERE product_id = %s", (product_id,))
        for trow in self.cursor.fetchall():
            pm.tags.append(PrintifyTagModel(product_id, trow["tag"]))

        # 3) variants
        self.cursor.execute("SELECT * FROM product_variants WHERE product_id = %s", (product_id,))
        for vrow in self.cursor.fetchall():
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
            pm.variants.append(PrintifyVariantModel(product_id, data_dict))

        # 4) images
        self.cursor.execute("SELECT * FROM product_images WHERE product_id = %s", (product_id,))
        for irow in self.cursor.fetchall():
            data_dict = {
                "src": irow["src"],
                "variant_ids": json.loads(irow["variant_ids"]) if irow["variant_ids"] else [],
                "position": irow["position"],
                "is_default": bool(irow["is_default"]),
                "is_selected_for_publishing": bool(irow["is_selected_for_publishing"]),
                "order": irow["order_index"]
            }
            pm.images.append(PrintifyImageModel(product_id, data_dict))

        # 5) print_areas + placeholders
        self.cursor.execute("SELECT * FROM product_print_areas WHERE product_id = %s", (product_id,))
        pa_rows = self.cursor.fetchall()
        for par in pa_rows:
            pa_id = par["id"]
            self.cursor.execute("SELECT * FROM product_placeholders WHERE print_area_id = %s", (pa_id,))
            ph_rows = self.cursor.fetchall()
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
            pm.print_areas.append(PrintifyPrintAreaModel(product_id, pa_data))

        # 6) external
        self.cursor.execute("SELECT * FROM product_external WHERE product_id = %s", (product_id,))
        er = self.cursor.fetchone()
        if er:
            pm.external = PrintifyExternalModel(product_id, {
                "id": er["external_id"],
                "handle": er["handle"]
            })

        # 7) sales_channel_properties
        self.cursor.execute("SELECT data FROM product_sales_channel_properties WHERE product_id = %s", (product_id,))
        for scp_row in self.cursor.fetchall():
            scp_data = json.loads(scp_row["data"]) if scp_row["data"] else {}
            pm.sales_channel_properties.append(PrintifySalesChannelPropertyModel(product_id, scp_data))

        # 8) views
        self.cursor.execute("SELECT * FROM product_views WHERE product_id = %s", (product_id,))
        view_rows = self.cursor.fetchall()
        for vr in view_rows:
            view_id = vr["view_id"]
            label = vr["label"]
            position = vr["position"]
            # fetch files
            self.cursor.execute("SELECT * FROM product_view_files WHERE view_id = %s", (vr["id"],))
            vf_rows = self.cursor.fetchall()
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
            pm.views.append(PrintifyViewModel(product_id, view_data))

        return pm

    def close(self):
        if self.cursor:
            self.cursor.close()
        if self.connection:
            self.connection.close()
        print("Database connection closed.")
