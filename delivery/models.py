from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import AbstractUser, AbstractBaseUser, PermissionsMixin, User

from pytz import timezone as tz
from queue import Queue

from datetime import datetime

delay_queue = Queue()


class DeliveryStatus(models.TextChoices):
    ASSIGNED = 'AS', _('Assigned')
    AT_VENDOR = 'AV', _('At_Bendor')
    PICKED = 'PI', _('Picked')
    DELIVERED = 'DE', _('Delivered')


class DelayStatus(models.TextChoices):
    ASSIGNED = 'AS', _('Assigned')
    UNASSIGNED = 'UN', _('Unassigned')
    RESOLVED = 'RE', _('Resolved')


class Agent(models.Model):
    name = models.CharField(max_length=256)

    def __str__(self) -> str:
        return f'{self.id} -- {self.name}'


class Vendor(models.Model):
    name = models.CharField(max_length=256)

    def __str__(self) -> str:
        return self.name + ' - ' + str(self.id)


class Order(models.Model):
    vendor = models.ForeignKey(
        Vendor, on_delete=models.CASCADE, related_name='orders'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    delivery_time = models.DateTimeField()

    def __str__(self) -> str:
        return str(self.id) + f' --- Vendor({self.vendor})'


class Trip(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='trip')
    status = models.CharField(choices=DeliveryStatus.choices, max_length=3)

    def __str__(self) -> str:
        return f'{str(self.id)} -- order({str(self.order.id)}) -- {self.status}'


class DelayReport(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='delays')
    delay = models.DurationField()
    created_at = models.DateTimeField(default=datetime.now)

    def __str__(self) -> str:
        return f'order({self.order}) -- delay({self.delay})'


class DelayQueue(models.Model):
    """
    This is the table for queue.
    """

    # order = models.ForeignKey(Order, on_delete=models.CASCADE)
    report = models.ForeignKey(DelayReport, on_delete=models.CASCADE, related_name='delay_items')
    agent = models.ForeignKey(Agent, null=True, on_delete=models.SET_NULL)
    status = models.CharField(choices=DelayStatus.choices, max_length=2, default=DelayStatus.UNASSIGNED)
    created_at = models.DateTimeField(auto_now_add=True)
