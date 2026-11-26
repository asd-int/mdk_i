from django.db import models


class Customer(models.Model):
    """Заказчик (клиент), оформляющий заказы."""

    name = models.CharField(max_length=255, verbose_name='Заказчик')
    city = models.CharField(max_length=100, verbose_name='Город')
    phone = models.CharField(max_length=30, verbose_name='Телефон')

    class Meta:
        verbose_name = 'Заказчик'
        verbose_name_plural = 'Заказчики'
        ordering = ['name']

    def __str__(self):
        return self.name


class Order(models.Model):
    """Заказ клиента с датой и суммой."""

    customer = models.ForeignKey(
        Customer,
        on_delete=models.CASCADE,
        related_name='orders',
        verbose_name='Заказчик',
    )
    order_date = models.DateField(verbose_name='Дата заказа')
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name='Сумма заказа',
    )

    class Meta:
        verbose_name = 'Заказ'
        verbose_name_plural = 'Заказы'
        ordering = ['customer__name', 'order_date']

    def __str__(self):
        return f'{self.customer.name} — {self.order_date} ({self.amount})'
