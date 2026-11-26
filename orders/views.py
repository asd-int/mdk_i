from decimal import Decimal
from django.db import DatabaseError
from django.db.models import Sum
from django.shortcuts import render

from .models import Customer, Order

SORT_FIELD_MAP = {
    'customer': 'customer__name',
    'order_date': 'order_date',
    'amount': 'amount',
}


def make_message(msg_type, title, text):
    return {'type': msg_type, 'title': title, 'text': text}


def order_list(request):
    action = request.GET.get('action', '')
    selected_customer_id = request.GET.get('customer_id', '').strip()
    sort_field = request.GET.get('sort_field') or request.GET.get('current_sort_field', '')
    sort_dir = request.GET.get('sort_dir') or request.GET.get('current_sort_dir', '')
    search_query = request.GET.get('search_query', '').strip()

    if action == 'show_all':
        selected_customer_id = ''
    elif action == 'reset_search':
        search_query = ''

    modal_message = None
    customers = []
    orders_rows = []
    orders_count = 0
    total_amount = Decimal('0.00')

    try:
        customers = list(Customer.objects.all())
        orders = Order.objects.select_related('customer').all()

        # 1. Фильтрация по заказчику
        if selected_customer_id:
            if selected_customer_id.isdigit() and Customer.objects.filter(id=int(selected_customer_id)).exists():
                orders = orders.filter(customer_id=int(selected_customer_id))
            else:
                modal_message = make_message(
                    'warning',
                    'Предупреждение',
                    'Выбранный заказчик не найден. Нажмите «Показать все» или выберите другого.',
                )
                selected_customer_id = ''
        elif action == 'filter':
            modal_message = make_message(
                'warning',
                'Предупреждение',
                'Выберите заказчика из списка и нажмите «Фильтровать».',
            )

        # 2. Сортировка по выбранному полю и направлению
        if sort_field in SORT_FIELD_MAP:
            if sort_dir not in ('asc', 'desc'):
                sort_dir = 'asc'
            order_by_field = SORT_FIELD_MAP[sort_field]
            if sort_dir == 'desc':
                order_by_field = '-' + order_by_field
            orders = orders.order_by(order_by_field)
        elif sort_dir in ('asc', 'desc'):
            modal_message = make_message(
                'warning',
                'Предупреждение',
                'Сначала выберите поле для сортировки («Заказчик», «Дата заказа» или «Сумма заказа»).',
            )

        # 3. Итоги по текущей выборке
        orders_count = orders.count()
        total_amount = orders.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

        # 4. Поиск и подготовка ячеек таблицы
        if action == 'search' and not search_query:
            modal_message = make_message(
                'warning',
                'Предупреждение',
                'Введите строку поиска и нажмите «Найти».',
            )

        query_lower = search_query.lower()
        match_found = False

        for order in orders:
            values = [
                order.customer.name,
                order.customer.city,
                order.customer.phone,
                order.order_date.strftime('%d.%m.%Y'),
                f'{order.amount:.2f}',
            ]
            row = []
            for value in values:
                is_match = bool(search_query and query_lower in value.lower())
                if is_match:
                    match_found = True
                row.append({'value': value, 'match': is_match})
            orders_rows.append(row)

        if action == 'search' and search_query and not match_found:
            modal_message = make_message(
                'info',
                'Информация',
                f'По запросу «{search_query}» совпадений не найдено.',
            )

    except DatabaseError as exc:
        modal_message = make_message(
            'error',
            'Ошибка',
            f'Ошибка базы данных: {exc}. Проверьте подключение к PostgreSQL.',
        )

    context = {
        'customers': customers,
        'orders_rows': orders_rows,
        'orders_count': orders_count,
        'total_amount_display': f'{total_amount:.2f}',
        'selected_customer_id': selected_customer_id,
        'sort_field': sort_field,
        'sort_dir': sort_dir,
        'search_query': search_query,
        'modal_message': modal_message,
    }
    return render(request, 'orders/order_list.html', context)
