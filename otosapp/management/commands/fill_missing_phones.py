from django.core.management.base import BaseCommand, CommandError
from otosapp.models import User
import csv

class Command(BaseCommand):
    help = (
        'Fill or export users without phone_number.\n'
        'Usage:\n'
        '  python manage.py fill_missing_phones --export-csv path.csv\n'
        '  python manage.py fill_missing_phones --set-default "+628000000000"\n'
    )

    def add_arguments(self, parser):
        parser.add_argument('--export-csv', type=str, help='Export users without phone_number to CSV file path')
        parser.add_argument('--set-default', type=str, help='Set a default phone number for users without it')

    def handle(self, *args, **options):
        export_path = options.get('export_csv')
        default_phone = options.get('set_default')

        users_without = User.objects.filter(phone_number__isnull=True) | User.objects.filter(phone_number__exact='')
        users_without = users_without.distinct()

        if export_path:
            with open(export_path, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(['id', 'email', 'first_name', 'last_name'])
                for u in users_without:
                    writer.writerow([u.id, u.email, u.first_name, u.last_name])
            self.stdout.write(self.style.SUCCESS(f'Exported {users_without.count()} users to {export_path}'))
            return

        if default_phone:
            count = 0
            for u in users_without:
                u.phone_number = default_phone
                u.save()
                count += 1
            self.stdout.write(self.style.SUCCESS(f'Set default phone for {count} users'))
            return

        # If no option provided, just list count and sample
        sample = users_without[:20]
        self.stdout.write(f'Users without phone_number: {users_without.count()}')
        for u in sample:
            self.stdout.write(f'- {u.id} {u.email} {u.get_full_name()}')
