from django.core.management import BaseCommand

from translations.models.textbase import TextBase
from translations.models.translation import Translation


class Command(BaseCommand):
    help = 'Replace old domain references with Animate a Drawing'

    def handle(self, *args, **options):
        # Replace any legacy domain references with animateadrawing.com
        old_domains = [
            ('estacaido.com', 'animateadrawing.com'),
            ('EstaCaido.com', 'Animate a Drawing'),
            ('https://estacaido.com', 'https://animateadrawing.com'),
        ]

        for old, new in old_domains:
            # Update Translation objects
            variables = Translation.objects.filter(text__contains=old)
            count = variables.count()
            if count:
                print(f'Replacing {count} Translation entries: {old} -> {new}')
                for v in variables:
                    v.text = v.text.replace(old, new)
                    v.save()

            # Update TextBase objects
            variables = TextBase.objects.filter(text__contains=old)
            count = variables.count()
            if count:
                print(f'Replacing {count} TextBase entries: {old} -> {new}')
                for v in variables:
                    v.text = v.text.replace(old, new)
                    v.save()

        print('Domain replacement complete.')
