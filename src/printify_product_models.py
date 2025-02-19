# file: printify_product_models.py

from typing import Any, Dict, List, Optional

class PrintifyVariantModel:
    def __init__(self, product_id: str, data: Dict[str, Any]):
        self.product_id = product_id
        self.data = data  # e.g. {"id": 42386, "sku": "...", "cost": ...}

class PrintifyOptionModel:
    def __init__(self, product_id: str, data: Dict[str, Any]):
        self.product_id = product_id
        self.data = data  # e.g. {"name": "Phone Models", "type": "size", "values": [...]}

class PrintifyPrintAreaModel:
    def __init__(self, product_id: str, data: Dict[str, Any]):
        self.product_id = product_id
        self.data = data  # e.g. {"variant_ids": [...], "placeholders": [...]}

class PrintifyImageModel:
    def __init__(self, product_id: str, data: Dict[str, Any]):
        self.product_id = product_id
        self.data = data  # e.g. {"src": "...", "variant_ids": [...], ...}

class PrintifyFileModel:
    def __init__(self, product_id: str, data: Dict[str, Any]):
        self.product_id = product_id
        self.data = data

class PrintifyExternalModel:
    def __init__(self, product_id: str, data: Dict[str, Any]):
        self.product_id = product_id
        self.data = data  # e.g. {"id": "...", "handle": "..."}

class PrintifyAdditionalOptionModel:
    def __init__(self, product_id: str, data: Dict[str, Any]):
        self.product_id = product_id
        self.data = data

class PrintifyProductionPartnerModel:
    def __init__(self, product_id: str, data: Dict[str, Any]):
        self.product_id = product_id
        self.data = data

class PrintifySalesChannelPropertyModel:
    def __init__(self, product_id: str, data: Dict[str, Any]):
        self.product_id = product_id
        self.data = data

class PrintifyPublishedModel:
    def __init__(self, product_id: str, data: Dict[str, Any]):
        self.product_id = product_id
        self.data = data

class PrintifyTagModel:
    """Represents a single string tag from 'tags'."""
    def __init__(self, product_id: str, tag: str):
        self.product_id = product_id
        self.tag = tag

class PrintifySellingPriceModel:
    def __init__(self, product_id: str, data: Dict[str, Any]):
        self.product_id = product_id
        self.data = data

class PrintifyViewFileModel:
    def __init__(self, src: str, variant_ids: List[int]):
        self.src = src
        self.variant_ids = variant_ids

class PrintifyViewModel:
    def __init__(self, product_id: str, data: Dict[str, Any]):
        """
        data might be something like:
        {
          "id": 133089,
          "label": "Phone cover back",
          "position": "front",
          "files": [{"src": "...", "variant_ids": [...]}, ...]
        }
        """
        self.product_id = product_id
        self.data = data

# ----------------------------------------------------------------------

class PrintifyProductModel:
    """
    Main product model for top-level fields from Printify.
    Also has lists of sub-models for variants, images, tags, etc.
    """
    def __init__(
        self,
        id: str,
        title: Optional[str],
        description: Optional[str],
        blueprint_id: Optional[int],
        user_id: Optional[int],
        shop_id: Optional[int],
        visible: bool,
        is_locked: bool,
        reviewed: bool,
        created_at: Optional[str],
        updated_at: Optional[str],
        print_provider_id: Optional[int] = None,
        # Additional top-level fields
        # e.g. status, category, brand, campaign_id...
    ):
        self.id = id
        self.title = title
        self.description = description
        self.blueprint_id = blueprint_id
        self.user_id = user_id
        self.shop_id = shop_id
        self.visible = visible
        self.is_locked = is_locked
        self.reviewed = reviewed
        self.created_at = created_at
        self.updated_at = updated_at
        self.print_provider_id = print_provider_id

        # Sub-model lists
        self.tags: List[PrintifyTagModel] = []
        self.options: List[PrintifyOptionModel] = []
        self.variants: List[PrintifyVariantModel] = []
        self.images: List[PrintifyImageModel] = []
        self.print_areas: List[PrintifyPrintAreaModel] = []
        self.external: Optional[PrintifyExternalModel] = None
        self.sales_channel_properties: List[PrintifySalesChannelPropertyModel] = []
        self.files: List[PrintifyFileModel] = []
        self.additional_options: List[PrintifyAdditionalOptionModel] = []
        self.production_partners: List[PrintifyProductionPartnerModel] = []
        self.selling_prices: List[PrintifySellingPriceModel] = []
        self.views: List[PrintifyViewModel] = []
        # self.published: Optional[PrintifyPublishedModel] = None
        # etc.

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "PrintifyProductModel":
        """
        Parse raw Printify product JSON into a PrintifyProductModel object
        with sub-model instances for arrays like variants, images, etc.
        """
        pid = data["id"]
        title = data.get("title")
        description = data.get("description")
        blueprint_id = data.get("blueprint_id")
        user_id = data.get("user_id")
        shop_id = data.get("shop_id")
        visible = data.get("visible", False)
        is_locked = data.get("is_locked", False)
        reviewed = data.get("reviewed", False)
        created_at = data.get("created_at")
        updated_at = data.get("updated_at")
        print_provider_id = data.get("print_provider_id")

        model = PrintifyProductModel(
            id=pid,
            title=title,
            description=description,
            blueprint_id=blueprint_id,
            user_id=user_id,
            shop_id=shop_id,
            visible=visible,
            is_locked=is_locked,
            reviewed=reviewed,
            created_at=created_at,
            updated_at=updated_at,
            print_provider_id=print_provider_id
        )

        # Tags
        for t in data.get("tags", []):
            model.tags.append(PrintifyTagModel(pid, t))

        # Options
        for opt in data.get("options", []):
            model.options.append(PrintifyOptionModel(pid, opt))

        # Variants
        for var in data.get("variants", []):
            model.variants.append(PrintifyVariantModel(pid, var))

        # Images
        for img in data.get("images", []):
            model.images.append(PrintifyImageModel(pid, img))

        # Print areas
        for pa in data.get("print_areas", []):
            model.print_areas.append(PrintifyPrintAreaModel(pid, pa))

        # External
        if "external" in data and isinstance(data["external"], dict):
            model.external = PrintifyExternalModel(pid, data["external"])

        # sales_channel_properties
        for scp in data.get("sales_channel_properties", []):
            model.sales_channel_properties.append(PrintifySalesChannelPropertyModel(pid, scp))

        # If you have "files", "additional_options", "production_partners", etc.
        # see if data includes them, then parse similarly.

        # Views
        for v in data.get("views", []):
            model.views.append(PrintifyViewModel(pid, v))

        return model
