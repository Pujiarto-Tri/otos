from django.core.management.base import BaseCommand
from otosapp.models import Role


class Command(BaseCommand):
    help = 'Menambahkan role Operator ke database'

    def handle(self, *args, **options):
        """Menambahkan role Operator jika belum ada"""
        try:
            # Cek apakah role Operator sudah ada
            operator_role, created = Role.objects.get_or_create(
                role_name='Operator'
            )
            
            if created:
                self.stdout.write(
                    self.style.SUCCESS("✅ Role 'Operator' berhasil ditambahkan ke database")
                )
            else:
                self.stdout.write(
                    self.style.WARNING("ℹ️  Role 'Operator' sudah ada di database")
                )
                
            # Tampilkan semua role yang ada
            self.stdout.write("\n📋 Daftar semua role:")
            for role in Role.objects.all():
                self.stdout.write(f"  - {role.role_name}")
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"❌ Error: {e}")
            )
