# file: template_product_mapper.py

from typing import Optional
import random
import string
import secrets
from models.printify_template_models import (
	PrintifyTemplateModel,
	PrintifyTagModel as TemplateTagModel,
	PrintifyOptionModel as TemplateOptionModel,
	PrintifyVariantModel as TemplateVariantModel,
	PrintifyImageModel as TemplateImageModel,
	PrintifyPrintAreaModel as TemplatePrintAreaModel,
	PrintifyExternalModel as TemplateExternalModel,
	PrintifySalesChannelPropertyModel as TemplateSalesChannelPropertyModel,
	PrintifyFileModel as TemplateFileModel,
	PrintifyAdditionalOptionModel as TemplateAdditionalOptionModel,
	PrintifyTemplateionPartnerModel,
	PrintifySellingPriceModel as TemplateSellingPriceModel,
	PrintifyViewModel as TemplateViewModel,
)

from models.printify_product_models import (
	PrintifyProductModel,
	PrintifyTagModel as ProductTagModel,
	PrintifyOptionModel as ProductOptionModel,
	PrintifyVariantModel as ProductVariantModel,
	PrintifyImageModel as ProductImageModel,
	PrintifyPrintAreaModel as ProductPrintAreaModel,
	PrintifyExternalModel as ProductExternalModel,
	PrintifySalesChannelPropertyModel as ProductSalesChannelPropertyModel,
	PrintifyFileModel as ProductFileModel,
	PrintifyAdditionalOptionModel as ProductAdditionalOptionModel,
	PrintifyProductionPartnerModel,
	PrintifySellingPriceModel as ProductSellingPriceModel,
	PrintifyViewModel as ProductViewModel,
)


class TemplateProductMapper:
	"""
	Maps a PrintifyTemplateModel to a PrintifyProductModel, copying over relevant fields
	and converting all references to 'template_id' into 'product_id' where appropriate.
	"""

	@staticmethod
	def map_template_to_product(
		template: PrintifyTemplateModel, 
		new_product_id: Optional[str] = None
	) -> PrintifyProductModel:
		"""
		Given a PrintifyTemplateModel, create and return a new PrintifyProductModel.
		If 'new_product_id' is provided, use that as the product's ID; otherwise, 
		the product ID will be the same as the template's ID.
		"""

		# Decide what product_id to use
		product_id = new_product_id if new_product_id else template.id

		# Create the product model with top-level fields.
		product = PrintifyProductModel(
			id=product_id,
			title=template.title,
			description=template.description,
			blueprint_id=template.blueprint_id,
			user_id=template.user_id,
			shop_id=template.shop_id,
			visible=template.visible,
			is_locked=template.is_locked,
			reviewed=template.reviewed,
			created_at=template.created_at,
			updated_at=template.updated_at,
			print_provider_id=template.print_provider_id,
		)

		# --- Transfer sub-model lists ---

		# Tags
		for t in template.tags:
			# t is a PrintifyTagModel with a "template_id" and a string "tag"
			product.tags.append(ProductTagModel(product_id, t.tag))

		# Options
		for opt in template.options:
			# opt is a PrintifyOptionModel with "template_id" and a dict "data"
			product.options.append(ProductOptionModel(product_id, opt.data))

		# Variants
		for var in template.variants:
			product.variants.append(ProductVariantModel(product_id, var.data))

		# Images
		for img in template.images:
			product.images.append(ProductImageModel(product_id, img.data))

		# Print Areas
		for pa in template.print_areas:
			product.print_areas.append(ProductPrintAreaModel(product_id, pa.data))

		# External
		if template.external is not None:
			product.external = ProductExternalModel(product_id, template.external.data)

		# Sales Channel Properties
		for scp in template.sales_channel_properties:
			product.sales_channel_properties.append(
				ProductSalesChannelPropertyModel(product_id, scp.data)
			)

		# Files
		for f in template.files:
			product.files.append(ProductFileModel(product_id, f.data))

		# Additional Options
		for ao in template.additional_options:
			product.additional_options.append(ProductAdditionalOptionModel(product_id, ao.data))

		# Selling Prices
		for sp in template.selling_prices:
			product.selling_prices.append(ProductSellingPriceModel(product_id, sp.data))

		# Views
		for v in template.views:
			product.views.append(ProductViewModel(product_id, v.data))

		return product

	@staticmethod
	def generate_sku(length: int) -> str:
		"""
		Generates a random SKU of the given length consisting of uppercase letters and digits.
		"""
		return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))

	@staticmethod
	def replace_product_id(product: PrintifyProductModel, id: str) -> PrintifyProductModel:
		"""
		Update the product's od.
		"""
		product.id = id
		return product
	
	@staticmethod
	def replace_product_id(product: PrintifyProductModel) -> PrintifyProductModel:
		"""
		Update the product's od.
		"""
		product.internal_id = str(uuid.uuid4())
		return product

	@staticmethod
	def replace_all_sku(product: PrintifyProductModel) -> PrintifyProductModel:
		"""
		Update SKUs in all variants of the product using the generate_sku method.
		"""
		for variant in product.variants:
			original_sku = variant.data.get('sku', '')
			if original_sku:
				sku_length = len(original_sku)  # Maintain the same length for new SKU
				variant.data['sku'] = TemplateProductMapper.generate_sku(sku_length)
		return product

	@staticmethod
	def replace_product_title(product: PrintifyProductModel, title: str) -> PrintifyProductModel:
		"""
		Update the product's title.
		"""
		product.title = title
		return product

	@staticmethod
	def replace_product_description(product: PrintifyProductModel, description: str) -> PrintifyProductModel:
		"""
		Update the product's description.
		"""
		product.description = description
		return product

	@staticmethod
	def replace_all_image_ids(product: PrintifyProductModel, new_image_id: str) -> PrintifyProductModel:
		"""
		Update image IDs in all print areas of the product.

		Iterates over each print area and its placeholders, then updates each image's 'id'
		with the provided new image ID.
		"""
		for print_area in product.print_areas:
			placeholders = print_area.data.get('placeholders', [])
			for placeholder in placeholders:
				images = placeholder.get('images', [])
				for image in images:
					image['id'] = new_image_id['id']
		return product

	@staticmethod
	def replace_product_tags(product: PrintifyProductModel, new_tags: list[str]) -> PrintifyProductModel:
		"""
		Update the product's tags with a new list of strings.

		Args:
			product: The PrintifyProductModel to update
			new_tags: List of strings representing the new tags

		Returns:
			The updated PrintifyProductModel
		"""
		product.tags = [ProductTagModel(product.id, tag) for tag in new_tags]
		return product

	@staticmethod
	def replace_product_bullet_points(product: PrintifyProductModel, bullet_points: list[str]) -> PrintifyProductModel:
		"""
		Update the product's bullet points in the sales channel properties.

		Args:
			product: The PrintifyProductModel to update
			bullet_points: List of strings representing the new bullet points

		Returns:
			The updated PrintifyProductModel
		"""
		# Iterate through all sales channel properties
		for sales_channel_property in product.sales_channel_properties:
			if hasattr(sales_channel_property, 'data') and isinstance(sales_channel_property.data, dict):
				# Update the bullet_points field in the data dictionary
				sales_channel_property.data['bullet_points'] = bullet_points
		
		return product

