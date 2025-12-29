from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from users.models import Employee

class Command(BaseCommand):
    help = 'Initialize permissions for employee groups based on their positions'

    def handle(self, *args, **options):
        self.stdout.write("Initializing permissions...")

        # Define permission mappings
        # Format: 'app_label.action_modelname'
        
        # Common read-only permissions for everyone (optional, but good practice)
        # For now, we stick to specific roles.

        # 1. Manager (All permissions)
        # We won't explicitly list all, but usually managers are superusers or have all perms.
        # But if we want to use groups, we can give them all perms on our apps.
        
        # 2. Purchaser (采购员)
        purchaser_perms = [
            # Biz - Purchase
            'biz.view_purchaseorder', 'biz.add_purchaseorder', 'biz.change_purchaseorder', 'biz.delete_purchaseorder',
            'biz.view_purchasedetail', 'biz.add_purchasedetail', 'biz.change_purchasedetail', 'biz.delete_purchasedetail',
            # Base - Supplier & Medicine
            'base.view_supplier', 'base.add_supplier', 'base.change_supplier',
            'base.view_medicine', 'base.add_medicine', # Purchasers might add new medicines
        ]

        # 3. Warehouse (库管员)
        warehouse_perms = [
            # Base - Inventory
            'base.view_inventory', 'base.add_inventory', 'base.change_inventory',
            'base.view_medicine',
            # Explicitly NO access to Purchase/Sales orders as requested
        ]

        # 4. Sales (销售员)
        sales_perms = [
            # Biz - Sales
            'biz.view_salesorder', 'biz.add_salesorder', 'biz.change_salesorder', 'biz.delete_salesorder',
            'biz.view_salesdetail', 'biz.add_salesdetail', 'biz.change_salesdetail', 'biz.delete_salesdetail',
            # Base - Customer & Inventory
            'base.view_customer', 'base.add_customer', 'base.change_customer',
            'base.view_inventory', # Need to see stock
            'base.view_medicine',
        ]

        # 5. Finance (财务)
        finance_perms = [
            # Read-only access to orders for stats
            'biz.view_purchaseorder', 'biz.view_salesorder',
            'base.view_supplier', 'base.view_customer',
        ]

        # Map positions to permission lists
        # keys must match keys in Employee.POSITION_CHOICES
        position_perms_map = {
            'manager': '__all__', # Special flag
            'purchaser': purchaser_perms,
            'warehouse': warehouse_perms,
            'sales': sales_perms,
            'finance': finance_perms,
        }

        for position_code, position_name in Employee.POSITION_CHOICES:
            group, created = Group.objects.get_or_create(name=position_code)
            if created:
                self.stdout.write(f"Created group: {position_code}")
            else:
                self.stdout.write(f"Updating group: {position_code}")

            # Clear existing permissions to ensure strict adherence to the definition
            group.permissions.clear()

            perms_to_add = []
            target_perms = position_perms_map.get(position_code, [])

            if target_perms == '__all__':
                # Give all permissions for our apps
                for app in ['base', 'biz', 'users']:
                    perms = Permission.objects.filter(content_type__app_label=app)
                    perms_to_add.extend(perms)
            else:
                for perm_str in target_perms:
                    try:
                        app_label, codename = perm_str.split('.')
                        perm = Permission.objects.get(content_type__app_label=app_label, codename=codename)
                        perms_to_add.append(perm)
                    except Permission.DoesNotExist:
                        self.stdout.write(self.style.WARNING(f"Permission not found: {perm_str}"))

            if perms_to_add:
                group.permissions.add(*perms_to_add)
                self.stdout.write(f"  Added {len(perms_to_add)} permissions to {position_code}")

        self.stdout.write(self.style.SUCCESS("Permissions initialized successfully."))
