
# home/views.py
import json
from django.shortcuts import render          # ← EKLEYİN
from django.http import JsonResponse, Http404
from django.contrib.staticfiles import finders
from django.utils import translation                # override(), get_language_from_request vs.
from django.utils.translation import gettext as _    # çeviri işlevi



TRANSLATABLE_KEYS = {"place", "title", "title2", "description", "details"}

def slides_json(request):
    # ① Dil tespiti → tr / en …
    lang = translation.get_language_from_request(request, check_path=True)
    with translation.override(lang):          # ← bağlamı ‘tr’ yap
        src = finders.find("data/slides.json")
        if not src:
            raise Http404("slides.json not found")
        slides = json.load(open(src, encoding="utf-8"))

        for slide in slides:                  # ② Çevir
            for k in TRANSLATABLE_KEYS:
                if k in slide:
                    slide[k] = _(slide[k])

        return JsonResponse(slides, safe=False)


def index(request):
    return render(request,"home/index/index.html")

def kripto(request):
    return render(request, 'home/kripto/index.html')

# print("=> aktif dil:", translation.get_language())

def belgeNet_wizardList(request):
    return render(request, "belgeNet/wizardList/wizard_ex_property_listing.html")