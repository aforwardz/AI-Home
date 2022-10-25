from datetime import datetime, timedelta
from django.db import models

# Create your models here.


class Purchase(models.Model):
    CATEGORY_LIST = (
        ('normal', '日常'),
        ('furniture', '家具'),
        ('kitchen', '厨房'),
        ('bathroom', '卫浴'),
        ('digital', '数码'),
        ('gift', '礼品'),
    )
    URGENT_DAYS = (
        (1, '明天'),
        (3, '三天'),
        (7, '一周'),
        (15, '半个月'),
        (30, '一个月'),
        (180, '半年'),
        (365, '明年'),
    )

    create_time = models.DateTimeField(verbose_name='创建时间', auto_now_add=True)
    update_time = models.DateTimeField(verbose_name='更新时间', auto_now=True)

    name = models.CharField(
        verbose_name='名称',
        max_length=255,
        blank=True,
    )
    category = models.CharField(
        verbose_name='类型',
        max_length=50,
        choices=CATEGORY_LIST,
        blank=True,
        default='normal',
        db_index=True
    )
    urgent_day = models.IntegerField(
        verbose_name='类型',
        choices=URGENT_DAYS,
        blank=True,
        default=7
    )

    @property
    def status(self):
        today = datetime.today().date()
        td = (today - self.create_time.date()).days

        return 'active' if td <= int(self.urgent_day) else 'expire'

