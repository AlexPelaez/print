# file: printify_template_models.py

from typing import Any, Dict, List, Optional

class PrintifyVariantModel:
	def __init__(self, template_id: str, data: Dict[str, Any]):
		self.template_id = template_id
		self.data = data  # e.g. {"id": 42386, "sku": "...", "cost": ...}

class PrintifyOptionModel:
	def __init__(self, template_id: str, data: Dict[str, Any]):
		self.template_id = template_id
		self.data = data  # e.g. {"name": "Phone Models", "type": "size", "values": [...]}

class PrintifyPrintAreaModel:
	def __init__(self, template_id: str, data: Dict[str, Any]):
		self.template_id = template_id
		self.data = data  # e.g. {"variant_ids": [...], "placeholders": [...]}

class PrintifyImageModel:
	def __init__(self, template_id: str, data: Dict[str, Any]):
		self.template_id = template_id
		self.data = data  # e.g. {"src": "...", "variant_ids": [...], ...}

class PrintifyFileModel:
	def __init__(self, template_id: str, data: Dict[str, Any]):
		self.template_id = template_id
		self.data = data

class PrintifyExternalModel:
	def __init__(self, template_id: str, data: Dict[str, Any]):
		self.template_id = template_id
		self.data = data  # e.g. {"id": "...", "handle": "..."}

class PrintifyAdditionalOptionModel:
	def __init__(self, template_id: str, data: Dict[str, Any]):
		self.template_id = template_id
		self.data = data

class PrintifyTemplateionPartnerModel:
	def __init__(self, template_id: str, data: Dict[str, Any]):
		self.template_id = template_id
		self.data = data

class PrintifySalesChannelPropertyModel:
	def __init__(self, template_id: str, data: Dict[str, Any]):
		self.template_id = template_id
		self.data = data

class PrintifyPublishedModel:
	def __init__(self, template_id: str, data: Dict[str, Any]):
		self.template_id = template_id
		self.data = data

class PrintifyTagModel:
	"""Represents a single string tag from 'tags'."""
	def __init__(self, template_id: str, tag: str):
		self.template_id = template_id
		self.tag = tag

class PrintifySellingPriceModel:
	def __init__(self, template_id: str, data: Dict[str, Any]):
		self.template_id = template_id
		self.data = data

class PrintifyViewFileModel:
	def __init__(self, src: str, variant_ids: List[int]):
		self.src = src
		self.variant_ids = variant_ids

class PrintifyViewModel:
	def __init__(self, template_id: str, data: Dict[str, Any]):
		"""
		data might be something like:
		{
		  "id": 133089,
		  "label": "Phone cover back",
		  "position": "front",
		  "files": [{"src": "...", "variant_ids": [...]}, ...]
		}
		"""
		self.template_id = template_id
		self.data = data

# ----------------------------------------------------------------------

class PrintifyTemplateModel:
	"""
	Main template model for top-level fields from Printify.
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
		self.templateion_partners: List[PrintifyTemplateionPartnerModel] = []
		self.selling_prices: List[PrintifySellingPriceModel] = []
		self.views: List[PrintifyViewModel] = []
		# self.published: Optional[PrintifyPublishedModel] = None
		# etc.

	def __str__(self) -> str:
		"""
		Provides a human-readable summary of this PrintifyTemplateModel instance.
		"""
		fields = [
			f"PrintifyTemplateModel:",
			f"  id: {self.id}",
			f"  title: {self.title or ''}",
			f"  description: {self.description or ''}",
			f"  blueprint_id: {self.blueprint_id}",
			f"  user_id: {self.user_id}",
			f"  shop_id: {self.shop_id}",
			f"  visible: {self.visible}",
			f"  is_locked: {self.is_locked}",
			f"  reviewed: {self.reviewed}",
			f"  created_at: {self.created_at or ''}",
			f"  updated_at: {self.updated_at or ''}",
			f"  print_provider_id: {self.print_provider_id or ''}",
			"",
			f"  # of tags: {len(self.tags)}",
			f"  # of options: {len(self.options)}",
			f"  # of variants: {len(self.variants)}",
			f"  # of images: {len(self.images)}",
			f"  # of print_areas: {len(self.print_areas)}",
			f"  # of sales_channel_properties: {len(self.sales_channel_properties)}",
			f"  # of files: {len(self.files)}",
			f"  # of additional_options: {len(self.additional_options)}",
			f"  # of selling_prices: {len(self.selling_prices)}",
			f"  # of views: {len(self.views)}",
			f"  external: {self.external.data if self.external else None}",
		]
		return "\n".join(fields)

	def print_string_verbose(self) -> str:
		"""
		Provides a human-readable summary of this PrintifyTemplateModel instance,
		expanding each top-level field and sub-object in a hierarchical format.
		"""
		lines = []
		lines.append("========================================")
		lines.append("           PrintifyTemplateModel        ")
		lines.append("========================================")
		lines.append("Top-level Fields:")
		lines.append(f"  id                : {self.id}")
		lines.append(f"  title             : {self.title or ''}")
		lines.append(f"  description       : {self.description or ''}")
		lines.append(f"  blueprint_id      : {self.blueprint_id}")
		lines.append(f"  user_id           : {self.user_id}")
		lines.append(f"  shop_id           : {self.shop_id}")
		lines.append(f"  visible           : {self.visible}")
		lines.append(f"  is_locked         : {self.is_locked}")
		lines.append(f"  reviewed          : {self.reviewed}")
		lines.append(f"  created_at        : {self.created_at or ''}")
		lines.append(f"  updated_at        : {self.updated_at or ''}")
		lines.append(f"  print_provider_id : {self.print_provider_id or ''}")

		lines.append("")
		lines.append("Sub-objects:")

		# Tags
		lines.append(f"  Tags ({len(self.tags)}):")
		for i, tag_obj in enumerate(self.tags, start=1):
			lines.append(f"    [{i}] PrintifyTagModel")
			lines.append(f"         template_id : {tag_obj.template_id}")
			lines.append(f"         tag         : {tag_obj.tag}")

		# Options
		lines.append(f"\n  Options ({len(self.options)}):")
		for i, opt in enumerate(self.options, start=1):
			lines.append(f"    [{i}] PrintifyOptionModel")
			lines.append(f"         template_id : {opt.template_id}")
			lines.append("         data:")
			for k, v in opt.data.items():
				lines.append(f"           - {k}: {v}")

		# Variants
		lines.append(f"\n  Variants ({len(self.variants)}):")
		for i, var in enumerate(self.variants, start=1):
			lines.append(f"    [{i}] PrintifyVariantModel")
			lines.append(f"         template_id : {var.template_id}")
			lines.append("         data:")
			for k, v in var.data.items():
				lines.append(f"           - {k}: {v}")

		# Images
		lines.append(f"\n  Images ({len(self.images)}):")
		for i, img in enumerate(self.images, start=1):
			lines.append(f"    [{i}] PrintifyImageModel")
			lines.append(f"         template_id : {img.template_id}")
			lines.append("         data:")
			for k, v in img.data.items():
				lines.append(f"           - {k}: {v}")

		# Print areas
		lines.append(f"\n  Print Areas ({len(self.print_areas)}):")
		for i, pa in enumerate(self.print_areas, start=1):
			lines.append(f"    [{i}] PrintifyPrintAreaModel")
			lines.append(f"         template_id : {pa.template_id}")
			lines.append("         data:")
			for k, v in pa.data.items():
				lines.append(f"           - {k}: {v}")

		# External
		lines.append("\n  External:")
		if self.external:
			lines.append("    PrintifyExternalModel")
			lines.append(f"      template_id : {self.external.template_id}")
			lines.append("      data:")
			for k, v in self.external.data.items():
				lines.append(f"        - {k}: {v}")
		else:
			lines.append("    None")

		# Sales channel properties
		lines.append(f"\n  Sales Channel Properties ({len(self.sales_channel_properties)}):")
		for i, scp in enumerate(self.sales_channel_properties, start=1):
			lines.append(f"    [{i}] PrintifySalesChannelPropertyModel")
			lines.append(f"         template_id : {scp.template_id}")
			lines.append("         data:")
			for k, v in scp.data.items():
				lines.append(f"           - {k}: {v}")

		# Files
		lines.append(f"\n  Files ({len(self.files)}):")
		for i, file_obj in enumerate(self.files, start=1):
			lines.append(f"    [{i}] PrintifyFileModel")
			lines.append(f"         template_id : {file_obj.template_id}")
			lines.append("         data:")
			for k, v in file_obj.data.items():
				lines.append(f"           - {k}: {v}")

		# Additional options
		lines.append(f"\n  Additional Options ({len(self.additional_options)}):")
		for i, ao in enumerate(self.additional_options, start=1):
			lines.append(f"    [{i}] PrintifyAdditionalOptionModel")
			lines.append(f"         template_id : {ao.template_id}")
			lines.append("         data:")
			for k, v in ao.data.items():
				lines.append(f"           - {k}: {v}")

		# Templateion partners
		lines.append(f"\n  Templateion Partners ({len(self.templateion_partners)}):")
		for i, tp in enumerate(self.templateion_partners, start=1):
			lines.append(f"    [{i}] PrintifyTemplateionPartnerModel")
			lines.append(f"         template_id : {tp.template_id}")
			lines.append("         data:")
			for k, v in tp.data.items():
				lines.append(f"           - {k}: {v}")

		# Selling prices
		lines.append(f"\n  Selling Prices ({len(self.selling_prices)}):")
		for i, sp in enumerate(self.selling_prices, start=1):
			lines.append(f"    [{i}] PrintifySellingPriceModel")
			lines.append(f"         template_id : {sp.template_id}")
			lines.append("         data:")
			for k, v in sp.data.items():
				lines.append(f"           - {k}: {v}")

		# Views
		lines.append(f"\n  Views ({len(self.views)}):")
		for i, view in enumerate(self.views, start=1):
			lines.append(f"    [{i}] PrintifyViewModel")
			lines.append(f"         template_id : {view.template_id}")
			lines.append("         data:")
			for k, v in view.data.items():
				# If "files" is in data, you might want to expand that, too
				if k == "files" and isinstance(v, list):
					lines.append(f"           - files:")
					for idx, file_dict in enumerate(v, start=1):
						lines.append(f"               [{idx}]")
						for fk, fv in file_dict.items():
							lines.append(f"                 {fk}: {fv}")
				else:
					lines.append(f"           - {k}: {v}")

		lines.append("")
		return "\n".join(lines)
	
	@staticmethod
	def from_dict(data: Dict[str, Any]) -> "PrintifyTemplateModel":
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

		model = PrintifyTemplateModel(
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

		# Sales channel properties
		scp_data = data.get("sales_channel_properties", {})
		if isinstance(scp_data, dict):
			model.sales_channel_properties.append(PrintifySalesChannelPropertyModel(pid, scp_data))
		elif isinstance(scp_data, list):
			for scp in scp_data:
				model.sales_channel_properties.append(PrintifySalesChannelPropertyModel(pid, scp))

		# Views
		for v in data.get("views", []):
			model.views.append(PrintifyViewModel(pid, v))

		return model
