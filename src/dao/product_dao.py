# file: dao/product_dao.py

import json
import uuid
from config.db_connection import DBConnection
from models.printify_product_models import (
    PrintifyProductModel,
    PrintifyVariantModel,
    PrintifyOptionModel,
    PrintifyPrintAreaModel,
    PrintifyImageModel,
    PrintifyTagModel,
    PrintifyExternalModel,
    PrintifySalesChannelPropertyModel,
    PrintifyViewModel
)

class ProductDAO:
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
        Creates the 'product_status' table that references products.id
        and holds a status (DRAFT, PUBLISHED).
        """
        status_sql = """
        CREATE TABLE IF NOT EXISTS product_status (
            product_fk VARCHAR(36) PRIMARY KEY,
            status ENUM('DRAFT','PUBLISHED') NOT NULL,
            FOREIGN KEY (product_fk) REFERENCES products(id)
              ON DELETE CASCADE
        );
        """
        self.db.cursor.execute(status_sql)
        self.db.connection.commit()
        print("Created 'product_status' table if not present.")

    def create_tables(self):
        """
        Creates the main 'products' table and all product sub-tables.
        The main table includes:
          - id: internal primary key (VARCHAR(36))
          - product_id: external product identifier (VARCHAR(100), UNIQUE)

        Note: We removed (or you can ignore) DEFAULT (UUID()) because
        we'll generate UUIDs in Python for clarity.
        """
        # Main products table
        main_product_sql = """
        CREATE TABLE IF NOT EXISTS products (
            id VARCHAR(36) PRIMARY KEY,
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
        self.db.cursor.execute(main_product_sql)

        # Sub-tables
        tags_sql = """
        CREATE TABLE IF NOT EXISTS product_tags (
            id VARCHAR(36) PRIMARY KEY,
            product_id VARCHAR(36),
            tag VARCHAR(255),
            FOREIGN KEY (product_id) REFERENCES products(id)
              ON DELETE CASCADE
        );
        """
        self.db.cursor.execute(tags_sql)

        variants_sql = """
        CREATE TABLE IF NOT EXISTS product_variants (
            id VARCHAR(36) PRIMARY KEY,
            product_id VARCHAR(36),
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
            FOREIGN KEY (product_id) REFERENCES products(id)
              ON DELETE CASCADE
        );
        """
        self.db.cursor.execute(variants_sql)

        images_sql = """
        CREATE TABLE IF NOT EXISTS product_images (
            id VARCHAR(36) PRIMARY KEY,
            product_id VARCHAR(36),
            src TEXT,
            variant_ids JSON,
            position VARCHAR(50),
            is_default TINYINT(1),
            is_selected_for_publishing TINYINT(1),
            order_index INT NULL,
            FOREIGN KEY (product_id) REFERENCES products(id)
              ON DELETE CASCADE
        );
        """
        self.db.cursor.execute(images_sql)

        print_areas_sql = """
        CREATE TABLE IF NOT EXISTS product_print_areas (
            id VARCHAR(36) PRIMARY KEY,
            product_id VARCHAR(36),
            variant_ids JSON,
            background VARCHAR(7),
            FOREIGN KEY (product_id) REFERENCES products(id)
              ON DELETE CASCADE
        );
        """
        self.db.cursor.execute(print_areas_sql)

        placeholders_sql = """
        CREATE TABLE IF NOT EXISTS product_placeholders (
            id VARCHAR(36) PRIMARY KEY,
            print_area_id VARCHAR(36),
            position VARCHAR(50),
            images JSON,
            FOREIGN KEY (print_area_id) REFERENCES product_print_areas(id)
              ON DELETE CASCADE
        );
        """
        self.db.cursor.execute(placeholders_sql)

        external_sql = """
        CREATE TABLE IF NOT EXISTS product_external (
            id VARCHAR(36) PRIMARY KEY,
            product_id VARCHAR(36) UNIQUE,
            external_id VARCHAR(100),
            handle TEXT,
            FOREIGN KEY (product_id) REFERENCES products(id)
              ON DELETE CASCADE
        );
        """
        self.db.cursor.execute(external_sql)

        scp_sql = """
        CREATE TABLE IF NOT EXISTS product_sales_channel_properties (
            id VARCHAR(36) PRIMARY KEY,
            product_id VARCHAR(36),
            data JSON,
            FOREIGN KEY (product_id) REFERENCES products(id)
              ON DELETE CASCADE
        );
        """
        self.db.cursor.execute(scp_sql)

        views_sql = """
        CREATE TABLE IF NOT EXISTS product_views (
            id VARCHAR(36) PRIMARY KEY,
            product_id VARCHAR(36),
            view_id INT,
            label VARCHAR(255),
            position VARCHAR(50),
            FOREIGN KEY (product_id) REFERENCES products(id)
              ON DELETE CASCADE
        );
        """
        self.db.cursor.execute(views_sql)

        view_files_sql = """
        CREATE TABLE IF NOT EXISTS product_view_files (
            id VARCHAR(36) PRIMARY KEY,
            view_id VARCHAR(36),
            src TEXT,
            variant_ids JSON,
            FOREIGN KEY (view_id) REFERENCES product_views(id)
              ON DELETE CASCADE
        );
        """
        self.db.cursor.execute(view_files_sql)

        self.db.connection.commit()
        print("Created all 'products' tables if not present.")

    # ---------------------------------------------------------
    # INSERT / UPDATE
    # ---------------------------------------------------------
    def _delete_sub_models(self, internal_id: str):
        """
        Delete sub-rows referencing the internal id from all sub-tables.
        """
        tables_to_clear = [
            "product_tags",
            "product_variants",
            "product_images",
            "product_print_areas",
            "product_external",
            "product_sales_channel_properties",
            "product_views"
        ]
        for tbl in tables_to_clear:
            sql = f"DELETE FROM {tbl} WHERE product_id = %s"
            self.db.cursor.execute(sql, (internal_id,))
        self.db.connection.commit()

    def insert_or_update_product(self, product_model: PrintifyProductModel):
        """
        Insert or update a product from a PrintifyProductModel,
        then re-insert all sub-model data.
        The product_model.id holds the external product identifier (product_id).
        We generate an internal UUID if it doesn't already exist.
        """
        def bool_to_int(b):
            return 1 if b else 0

        # 1) Check if we already have a row for this external product_id
        select_q = "SELECT id FROM products WHERE product_id = %s"
        self.db.cursor.execute(select_q, (product_model.id,))
        existing = self.db.cursor.fetchone()

        if existing:
            # Re-use the existing internal ID
            internal_id = existing["id"]
        else:
            # Generate a new internal UUID for this product
            internal_id = str(uuid.uuid4())

        # 2) Upsert main product row using REPLACE to ensure 'id' is what we want
        upsert_sql = """
        REPLACE INTO products (
            id, product_id, title, description,
            blueprint_id, print_provider_id,
            user_id, shop_id, visible, is_locked,
            reviewed, created_at, updated_at
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        upsert_values = (
            internal_id,
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
            self.db.cursor.execute(upsert_sql, upsert_values)
            self.db.connection.commit()
            print(f"Upserted product row for external product_id={product_model.id}")
        except Exception as e:
            print(f"Error upserting product {product_model.id}: {e}")
            return

        # Save internal_id to the model
        product_model.internal_id = internal_id

        # 3) Remove old sub-model rows
        self._delete_sub_models(internal_id)

        # 4) Insert tags
        insert_tag_sql = """
        REPLACE INTO product_tags (id, product_id, tag)
        VALUES (%s, %s, %s)
        """
        for tmodel in product_model.tags:
            new_tag_id = str(uuid.uuid4())
            self.db.cursor.execute(insert_tag_sql, (new_tag_id, internal_id, tmodel.tag))

        # 5) Insert variants
        insert_variant_sql = """
        REPLACE INTO product_variants (
            id, product_id, variant_id, sku, cost, price, title,
            grams, is_enabled, is_default, is_available,
            is_printify_express_eligible, quantity, options
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        for vmodel in product_model.variants:
            vdata = vmodel.data or {}
            new_variant_id = str(uuid.uuid4())
            self.db.cursor.execute(
                insert_variant_sql,
                (
                    new_variant_id,
                    internal_id,
                    vdata.get("id"),
                    vdata.get("sku"),
                    vdata.get("cost"),
                    vdata.get("price"),
                    vdata.get("title"),
                    vdata.get("grams"),
                    bool_to_int(vdata.get("is_enabled", False)),
                    bool_to_int(vdata.get("is_default", False)),
                    bool_to_int(vdata.get("is_available", False)),
                    bool_to_int(vdata.get("is_printify_express_eligible", False)),
                    vdata.get("quantity", 1),
                    json.dumps(vdata.get("options", []))
                )
            )

        # 6) Insert images
        insert_img_sql = """
        REPLACE INTO product_images (
            id, product_id, src, variant_ids, position,
            is_default, is_selected_for_publishing, order_index
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        for imodel in product_model.images:
            idata = imodel.data or {}
            new_image_id = str(uuid.uuid4())
            self.db.cursor.execute(
                insert_img_sql,
                (
                    new_image_id,
                    internal_id,
                    idata.get("src"),
                    json.dumps(idata.get("variant_ids", [])),
                    idata.get("position"),
                    bool_to_int(idata.get("is_default", False)),
                    bool_to_int(idata.get("is_selected_for_publishing", False)),
                    idata.get("order")
                )
            )

        # 7) Insert print areas and placeholders
        insert_pa_sql = """
        REPLACE INTO product_print_areas (
            id, product_id, variant_ids, background
        ) VALUES (%s, %s, %s, %s)
        """
        insert_ph_sql = """
        REPLACE INTO product_placeholders (
            id, print_area_id, position, images
        ) VALUES (%s, %s, %s, %s)
        """
        for pa_model in product_model.print_areas:
            pa_data = pa_model.data or {}
            new_area_id = str(uuid.uuid4())
            self.db.cursor.execute(
                insert_pa_sql,
                (
                    new_area_id,
                    internal_id,
                    json.dumps(pa_data.get("variant_ids", [])),
                    pa_data.get("background")
                )
            )

            # Now insert placeholders referencing that new_area_id
            for ph in pa_data.get("placeholders", []):
                new_ph_id = str(uuid.uuid4())
                self.db.cursor.execute(
                    insert_ph_sql,
                    (
                        new_ph_id,
                        new_area_id,
                        ph.get("position"),
                        json.dumps(ph.get("images", []))
                    )
                )

        # 8) Insert external
        if product_model.external and isinstance(product_model.external.data, dict):
            ext_data = product_model.external.data
            insert_ext_sql = """
            REPLACE INTO product_external (
                id, product_id, external_id, handle
            ) VALUES (%s, %s, %s, %s)
            """
            new_ext_id = str(uuid.uuid4())
            self.db.cursor.execute(
                insert_ext_sql,
                (
                    new_ext_id,
                    internal_id,
                    ext_data.get("id"),
                    ext_data.get("handle")
                )
            )

        # 9) Insert sales channel properties
        insert_scp_sql = """
        REPLACE INTO product_sales_channel_properties (id, product_id, data)
        VALUES (%s, %s, %s)
        """
        for scp_model in product_model.sales_channel_properties:
            new_scp_id = str(uuid.uuid4())
            scp_data = scp_model.data if isinstance(scp_model.data, dict) else {}
            self.db.cursor.execute(
                insert_scp_sql,
                (
                    new_scp_id,
                    internal_id,
                    json.dumps(scp_data)
                )
            )

        # 10) Insert views and view files
        insert_view_sql = """
        REPLACE INTO product_views (id, product_id, view_id, label, position)
        VALUES (%s, %s, %s, %s, %s)
        """
        insert_view_file_sql = """
        REPLACE INTO product_view_files (
            id, view_id, src, variant_ids
        ) VALUES (%s, %s, %s, %s)
        """
        for v_model in product_model.views:
            vdata = v_model.data or {}
            new_view_uuid = str(uuid.uuid4())
            self.db.cursor.execute(
                insert_view_sql,
                (
                    new_view_uuid,
                    internal_id,
                    vdata.get("id"),
                    vdata.get("label"),
                    vdata.get("position")
                )
            )

            # Insert the files for this view
            for vf in vdata.get("files", []):
                new_file_id = str(uuid.uuid4())
                self.db.cursor.execute(
                    insert_view_file_sql,
                    (
                        new_file_id,
                        new_view_uuid,
                        vf.get("src"),
                        json.dumps(vf.get("variant_ids", []))
                    )
                )

        # Commit everything
        self.db.connection.commit()
        print(
            f"Upserted product with internal id={internal_id} "
            f"and external product_id={product_model.id} + sub-models from model."
        )

    # ---------------------------------------------------------
    # FETCH
    # ---------------------------------------------------------
    def fetch_product_from_product_id(self, external_product_id: str) -> PrintifyProductModel | None:
        """
        Loads from DB and reconstructs a PrintifyProductModel.
        Here the lookup is performed using the external product identifier
        (the value stored in the 'product_id' column).
        Once found, the internal primary key (from the 'id' column)
        is used to query the sub-tables.
        """
        main_q = "SELECT * FROM products WHERE product_id = %s"
        self.db.cursor.execute(main_q, (external_product_id,))
        row = self.db.cursor.fetchone()
        if not row:
            return None

        internal_id = row["id"]

        pm = PrintifyProductModel(
            id=row["product_id"],  # external product id
            title=row["title"],
            description=row["description"],
            blueprint_id=row["blueprint_id"],
            print_provider_id=row["print_provider_id"],
            user_id=row["user_id"],
            shop_id=row["shop_id"],
            visible=bool(row["visible"]),
            is_locked=bool(row["is_locked"]),
            reviewed=bool(row["reviewed"]),
            created_at=str(row["created_at"]) if row["created_at"] else None,
            updated_at=str(row["updated_at"]) if row["updated_at"] else None
        )
        # Save the internal id in the model for later reference.
        pm.internal_id = internal_id

        # Fetch tags using the internal id.
        self.db.cursor.execute("SELECT tag FROM product_tags WHERE product_id = %s", (internal_id,))
        for trow in self.db.cursor.fetchall():
            pm.tags.append(PrintifyTagModel(external_product_id, trow["tag"]))

        # Fetch variants
        self.db.cursor.execute("SELECT * FROM product_variants WHERE product_id = %s", (internal_id,))
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
            pm.variants.append(PrintifyVariantModel(external_product_id, data_dict))

        # Fetch images
        self.db.cursor.execute("SELECT * FROM product_images WHERE product_id = %s", (internal_id,))
        for irow in self.db.cursor.fetchall():
            data_dict = {
                "src": irow["src"],
                "variant_ids": json.loads(irow["variant_ids"]) if irow["variant_ids"] else [],
                "position": irow["position"],
                "is_default": bool(irow["is_default"]),
                "is_selected_for_publishing": bool(irow["is_selected_for_publishing"]),
                "order": irow["order_index"]
            }
            pm.images.append(PrintifyImageModel(external_product_id, data_dict))

        # Fetch print areas + placeholders
        self.db.cursor.execute("SELECT * FROM product_print_areas WHERE product_id = %s", (internal_id,))
        pa_rows = self.db.cursor.fetchall()
        for par in pa_rows:
            pa_id = par["id"]
            self.db.cursor.execute("SELECT * FROM product_placeholders WHERE print_area_id = %s", (pa_id,))
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
            pm.print_areas.append(PrintifyPrintAreaModel(external_product_id, pa_data))

        # Fetch external
        self.db.cursor.execute("SELECT * FROM product_external WHERE product_id = %s", (internal_id,))
        er = self.db.cursor.fetchone()
        if er:
            pm.external = PrintifyExternalModel(external_product_id, {
                "id": er["external_id"],
                "handle": er["handle"]
            })

        # Fetch sales channel properties
        self.db.cursor.execute("SELECT data FROM product_sales_channel_properties WHERE product_id = %s", (internal_id,))
        for scp_row in self.db.cursor.fetchall():
            scp_data = json.loads(scp_row["data"]) if scp_row["data"] else {}
            pm.sales_channel_properties.append(PrintifySalesChannelPropertyModel(external_product_id, scp_data))

        # Fetch views + view files
        self.db.cursor.execute("SELECT * FROM product_views WHERE product_id = %s", (internal_id,))
        view_rows = self.db.cursor.fetchall()
        for vr in view_rows:
            view_id = vr["view_id"]
            label = vr["label"]
            position = vr["position"]
            self.db.cursor.execute("SELECT * FROM product_view_files WHERE view_id = %s", (vr["id"],))
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
            pm.views.append(PrintifyViewModel(external_product_id, view_data))

        return pm

    def set_status_by_product_id(self, external_product_id: str, new_status: str):
        if new_status not in ("DRAFT", "PUBLISHED"):
            raise ValueError(f"Invalid status '{new_status}'.")
        select_q = "SELECT id FROM products WHERE product_id = %s"
        self.db.cursor.execute(select_q, (external_product_id,))
        row = self.db.cursor.fetchone()
        if not row:
            print(f"No product found with product_id={external_product_id}")
            return
        local_id = row["id"]
        upsert_sql = """
        INSERT INTO product_status (product_fk, status)
        VALUES (%s, %s)
        ON DUPLICATE KEY UPDATE status = VALUES(status);
        """
        self.db.cursor.execute(upsert_sql, (local_id, new_status))
        self.db.connection.commit()
        print(f"Set status for product_id={external_product_id} to '{new_status}'.")

    def set_status_by_id(self, db_id: int, new_status: str):
        if new_status not in ("DRAFT", "PUBLISHED"):
            raise ValueError(f"Invalid status '{new_status}'.")
        check_q = "SELECT id FROM products WHERE id = %s"
        self.db.cursor.execute(check_q, (db_id,))
        row = self.db.cursor.fetchone()
        if not row:
            print(f"No product found with id={db_id}")
            return
        upsert_sql = """
        INSERT INTO product_status (product_fk, status)
        VALUES (%s, %s)
        ON DUPLICATE KEY UPDATE status = VALUES(status)
        """
        self.db.cursor.execute(upsert_sql, (db_id, new_status))
        self.db.connection.commit()
        print(f"Set status for id={db_id} to '{new_status}'.")

    def fetch_max_draft_product_id(self) -> int | None:
        """
        Returns the maximum external product_id among products with status 'DRAFT'.
        """
        query = """
            SELECT MAX(p.product_id) AS max_id
            FROM products p
            JOIN product_status ps ON p.id = ps.product_fk
            WHERE ps.status = 'DRAFT';
        """
        self.db.cursor.execute(query)
        row = self.db.cursor.fetchone()
        if row and row["max_id"]:
            return row["max_id"]
        return None

    def fetch_all_products(self):
        """
        Fetch all products from the database with their Printify IDs.
        
        Returns:
            list: A list of dictionaries containing product information with 'id' and 'printify_id' fields
        """
        query = """
        SELECT p.id, p.product_id as printify_id
        FROM products p
        """
        self.db.cursor.execute(query)
        return self.db.cursor.fetchall()

    def delete_product(self, product_id: str) -> bool:
        """
        Delete a product from the database by its internal ID.
        This will cascade delete all related records from:
        - product_status
        - product_tags
        - product_variants
        - product_images
        - product_print_areas (and product_placeholders)
        - product_external
        - product_sales_channel_properties
        - product_views (and product_view_files)
        
        Args:
            product_id: The internal database ID of the product
            
        Returns:
            bool: True if the product was successfully deleted, False otherwise
        """
        try:
            # First get counts of related records for verification
            tables_and_columns = {
                "product_status": "product_fk",
                "product_tags": "product_id",
                "product_variants": "product_id",
                "product_images": "product_id",
                "product_print_areas": "product_id",
                "product_external": "product_id",
                "product_sales_channel_properties": "product_id",
                "product_views": "product_id"
            }
            
            counts_before = {}
            for table, column in tables_and_columns.items():
                self.db.cursor.execute(f"SELECT COUNT(*) as count FROM {table} WHERE {column} = %s", (product_id,))
                counts_before[table] = self.db.cursor.fetchone()['count']
            
            # Also check placeholders and view files
            self.db.cursor.execute("""
                SELECT COUNT(*) as count 
                FROM product_placeholders ph 
                JOIN product_print_areas pa ON ph.print_area_id = pa.id 
                WHERE pa.product_id = %s
            """, (product_id,))
            counts_before['product_placeholders'] = self.db.cursor.fetchone()['count']
            
            self.db.cursor.execute("""
                SELECT COUNT(*) as count 
                FROM product_view_files vf 
                JOIN product_views v ON vf.view_id = v.id 
                WHERE v.product_id = %s
            """, (product_id,))
            counts_before['product_view_files'] = self.db.cursor.fetchone()['count']

            # Delete the product (this will cascade to all related tables)
            sql = "DELETE FROM products WHERE id = %s"
            self.db.cursor.execute(sql, (product_id,))
            self.db.connection.commit()

            # Verify that all related records were deleted
            for table, column in tables_and_columns.items():
                self.db.cursor.execute(f"SELECT COUNT(*) as count FROM {table} WHERE {column} = %s", (product_id,))
                count_after = self.db.cursor.fetchone()['count']
                if count_after > 0:
                    print(f"Warning: {count_after} records remain in {table} after deletion")
                elif counts_before[table] > 0:
                    print(f"Successfully deleted {counts_before[table]} records from {table}")

            # Also verify placeholders and view files
            self.db.cursor.execute("""
                SELECT COUNT(*) as count 
                FROM product_placeholders ph 
                JOIN product_print_areas pa ON ph.print_area_id = pa.id 
                WHERE pa.product_id = %s
            """, (product_id,))
            count_after = self.db.cursor.fetchone()['count']
            if count_after > 0:
                print(f"Warning: {count_after} records remain in product_placeholders after deletion")
            elif counts_before['product_placeholders'] > 0:
                print(f"Successfully deleted {counts_before['product_placeholders']} records from product_placeholders")

            self.db.cursor.execute("""
                SELECT COUNT(*) as count 
                FROM product_view_files vf 
                JOIN product_views v ON vf.view_id = v.id 
                WHERE v.product_id = %s
            """, (product_id,))
            count_after = self.db.cursor.fetchone()['count']
            if count_after > 0:
                print(f"Warning: {count_after} records remain in product_view_files after deletion")
            elif counts_before['product_view_files'] > 0:
                print(f"Successfully deleted {counts_before['product_view_files']} records from product_view_files")

            return True

        except Exception as e:
            print(f"Error deleting product {product_id}: {e}")
            return False

    def close(self):
        self.db.close()
