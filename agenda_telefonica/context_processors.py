from agenda_telefonica.models import MenuSidebar


def menu_sidebar(request):
    menu_items = MenuSidebar.objects.filter(is_active=True, mostrar=True).order_by('orden')
    return {
        'sidebar_menu_items': menu_items
    }
