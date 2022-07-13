from django.core.paginator import Paginator
from yatube.settings import POSTS_PER_PAGE


def pagination(request, obj):
    paginator = Paginator(obj, POSTS_PER_PAGE)
    page = request.GET.get('page')
    page_obj = paginator.get_page(page)
    return page_obj
