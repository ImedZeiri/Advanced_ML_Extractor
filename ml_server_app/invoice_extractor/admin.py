from django.contrib import admin
from .models import Invoice, InvoiceTemplate, InvoiceLineItem, TrainingData

class InvoiceLineItemInline(admin.TabularInline):
    model = InvoiceLineItem
    extra = 0

@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ('id', 'original_filename', 'vendor_name', 'invoice_number', 'invoice_date', 'total_amount', 'status', 'uploaded_at')
    list_filter = ('status', 'uploaded_at', 'processed_at')
    search_fields = ('original_filename', 'vendor_name', 'invoice_number')
    readonly_fields = ('uploaded_at', 'processed_at', 'extracted_data')
    inlines = [InvoiceLineItemInline]
    fieldsets = (
        ('Fichier', {
            'fields': ('file', 'original_filename', 'uploaded_at', 'processed_at', 'status', 'error_message')
        }),
        ('Informations extraites', {
            'fields': ('vendor_name', 'invoice_number', 'invoice_date', 'due_date', 'total_amount', 'tax_amount', 'currency', 'template')
        }),
        ('Données brutes', {
            'fields': ('extracted_data',),
            'classes': ('collapse',)
        }),
    )

@admin.register(InvoiceTemplate)
class InvoiceTemplateAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'vendor', 'created_at', 'updated_at')
    list_filter = ('created_at', 'updated_at')
    search_fields = ('name', 'vendor', 'description')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('Informations générales', {
            'fields': ('name', 'description', 'vendor', 'created_at', 'updated_at')
        }),
        ('Règles d\'extraction', {
            'fields': ('amount_regex', 'date_regex', 'invoice_number_regex', 'tax_regex')
        }),
    )

@admin.register(TrainingData)
class TrainingDataAdmin(admin.ModelAdmin):
    list_display = ('id', 'original_filename', 'dataset_type', 'is_validated', 'uploaded_at')
    list_filter = ('dataset_type', 'is_validated', 'uploaded_at')
    search_fields = ('original_filename',)
    readonly_fields = ('uploaded_at',)
    fieldsets = (
        ('Fichier', {
            'fields': ('file', 'original_filename', 'uploaded_at')
        }),
        ('Informations', {
            'fields': ('dataset_type', 'is_validated')
        }),
        ('Annotations', {
            'fields': ('annotations',),
            'classes': ('collapse',)
        }),
    )