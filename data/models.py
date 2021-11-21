from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.db.models.fields import CharField

class Data(models.Model):
    hour = ArrayField(
        models.JSONField(default=dict),
        default = list
    )
    h_last_updated = models.IntegerField(default=0)
    day = ArrayField(
        models.JSONField(default=dict),
        default = list
    )
    d_last_updated = models.IntegerField(default=0)
    week = ArrayField(
        models.JSONField(default=dict),
        default = list
    )
    w_last_updated = models.IntegerField(default=0)
    month = ArrayField(
        models.JSONField(default=dict),
        default = list
    )
    m_last_updated = models.IntegerField(default=0)
    year = ArrayField(
        models.JSONField(default=dict),
        default = list
    )
    y_last_updated = models.IntegerField(default=0)
    all = ArrayField(
        models.JSONField(default=dict),
        default = list
    )
    a_last_updated = models.IntegerField(default=0)

    def get_data(self, span):
        if span == 'H':
            return self.hour
        if span == 'D':
            return self.day
        if span == 'W':
            return self.week
        if span == 'M':
            return self.month
        if span == 'Y':
            return self.year
        if span == 'A':
            return self.all

    def last_update(self, span):
        if span == 'H':
            return self.h_last_updated
        if span == 'D':
            return self.d_last_updated
        if span == 'W':
            return self.w_last_updated
        if span == 'M':
            return self.m_last_updated
        if span == 'Y':
            return self.y_last_updated
        if span == 'A':
            return self.a_last_updated



class Symbol(models.Model):
    symbol = models.CharField(max_length=8)
    crypto = models.BooleanField(default=True)
    name = models.CharField(max_length=80)    
    image = models.CharField(max_length=1000)
    data = models.ForeignKey(Data, on_delete=models.CASCADE)


    def get_data(self):
        data = Data.objects.filter(id=self.data_id)
        return data[0]


