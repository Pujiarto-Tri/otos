from django.core.management.base import BaseCommand
from otosapp.models import Category, Test

class Command(BaseCommand):
    help = 'Update UTBK difficulty coefficients for all categories or specific category'

    def add_arguments(self, parser):
        parser.add_argument(
            '--category-id',
            type=int,
            help='Update coefficients for specific category ID',
        )
        parser.add_argument(
            '--all',
            action='store_true',
            help='Update coefficients for all categories with UTBK scoring',
        )

    def handle(self, *args, **options):
        if options['category_id']:
            # Update specific category
            try:
                category = Category.objects.get(id=options['category_id'])
                if category.scoring_method == 'utbk':
                    Test.update_utbk_difficulty_coefficients(category.id)
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'Successfully updated UTBK coefficients for category: {category.category_name}'
                        )
                    )
                else:
                    self.stdout.write(
                        self.style.WARNING(
                            f'Category "{category.category_name}" is not using UTBK scoring method'
                        )
                    )
            except Category.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'Category with ID {options["category_id"]} does not exist')
                )
        
        elif options['all']:
            # Update all UTBK categories
            utbk_categories = Category.objects.filter(scoring_method='utbk')
            if not utbk_categories.exists():
                self.stdout.write(
                    self.style.WARNING('No categories found with UTBK scoring method')
                )
                return
            
            for category in utbk_categories:
                Test.update_utbk_difficulty_coefficients(category.id)
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Updated UTBK coefficients for: {category.category_name}'
                    )
                )
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully updated {utbk_categories.count()} categories'
                )
            )
        
        else:
            # Show help
            self.stdout.write(
                self.style.WARNING(
                    'Please specify either --category-id <ID> or --all\n'
                    'Use --help for more information'
                )
            )
