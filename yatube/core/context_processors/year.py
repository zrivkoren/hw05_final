from datetime import datetime

year_now = datetime.now().year


def year(request):
    """Добавляет переменную с текущим годом."""
    return {
        'year': year_now
    }
