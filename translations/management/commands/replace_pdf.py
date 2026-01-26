from django.core.management import BaseCommand

from translations.models.textbase import TextBase
from translations.models.translation import Translation


class Command(BaseCommand):
    help = 'Set text backup'
    def handle(self, *args, **options):
        variables = Translation.objects.filter(text__contains = "JPEG.to")
        print(variables.count())
        for v in variables:
            text = v.text
            text = text.replace('JPEG.to', "EstaCaido.com")
            v.text = text
            v.save()
        variables = Translation.objects.filter(text__contains = "https://jpeg.to")
        print(variables.count())

        for v in variables:
            text = v.text
            text = text.replace('https://jpeg.to', "https://estacaido.com")
            v.text = text
            v.save()
        variables = Translation.objects.filter(text__contains = "jpeg.to")
        print(variables.count())

        for v in variables:
            text = v.text
            text = text.replace('jpeg.to', "estacaido.com")
            v.text = text
            v.save()
        variables = Translation.objects.filter(text__contains = "Jpeg.to")
        print(variables.count())

        for v in variables:
            text = v.text
            text = text.replace('Jpeg.to', "estacaido.com")
            v.text = text
            v.save()

        variables = Translation.objects.filter(text__contains = "JPEg.to")
        print(variables.count())

        for v in variables:
            text = v.text
            text = text.replace('JPEg.to', "estacaido.com")
            v.text = text
            v.save()

        variables = TextBase.objects.filter(text__contains = "JPEG.to")
        print(variables.count())
        for v in variables:
            text = v.text
            text = text.replace('JPEG.to', "EstaCaido.com")
            v.text = text
            v.save()
        variables = TextBase.objects.filter(text__contains = "https://jpeg.to")
        print(variables.count())

        for v in variables:
            text = v.text
            text = text.replace('https://jpeg.to', "https://estacaido.com")
            v.text = text
            v.save()
        variables = TextBase.objects.filter(text__contains = "jpeg.to")
        print(variables.count())

        for v in variables:
            text = v.text
            text = text.replace('jpeg.to', "estacaido.com")
            v.text = text
            v.save()
        variables = TextBase.objects.filter(text__contains = "Jpeg.to")
        print(variables.count())

        for v in variables:
            text = v.text
            text = text.replace('Jpeg.to', "estacaido.com")
            v.text = text
            v.save()

        variables = TextBase.objects.filter(text__contains = "Jpeg.to")
        print(variables.count())

        for v in variables:
            text = v.text
            text = text.replace('JPEg.to', "estacaido.com")
            v.text = text
            v.save()

        variables = TextBase.objects.filter(text__contains = "JPEG")
        print(variables.count())

        for v in variables:
            text = v.text
            text = text.replace('JPEG', "JPG")
            v.text = text
            v.save()

        variables = Translation.objects.filter(text__contains = "JPEG")
        print(variables.count())

        for v in variables:
            text = v.text
            text = text.replace('JPEG', "JPG")
            v.text = text
            v.save()
