from datetime import datetime
import requests
from requests import HTTPError
from django.db import models

# Quick hack to see colors on cards
category_colors = {
    'Desarrollo e Infraestructura': '#80cbc4',
    'Transportación': '#e6ee9c',
    'Turismo': '#ffe082',
    'Economía y Finanzas': '#c5e1a5',
    'Salud': '#ef9a9a',
    'Educación': '#ffcc80',
    'Negocios y Corporaciones': '#ffab91',
    'Familia y Servicio Social': '#fff59d',
    'Tecnologias': '#9fa8da',
    'Permisos y Ambiente': '#a5d6a7',
    'Seguridad Pública': '#b0bec5',
}

# Quick hack to see icons on cards
category_icons = {
    'Desarrollo e Infraestructura': 'images/lightbulb.svg',
    'Transportación': 'images/traffic-light.svg',
    'Turismo': 'images/white-balance-sunny.svg',
    'Economía y Finanzas': 'images/cash.svg',
    'Salud': 'images/hospital.svg',
    'Educación': 'images/school.svg',
    'Negocios y Corporaciones': 'images/wallet-travel.svg',
    'Familia y Servicio Social': 'images/human.svg ',
    'Tecnologias': 'images/laptop.svg',
    'Permisos y Ambiente': 'images/file-document-box.svg',
    'Seguridad Pública': 'images/security.svg',
}

class Category(models.Model):
    name = models.CharField(max_length=100, verbose_name='category')

    def __str__(self):
        return u'%s' % self.name

    class Meta:
        verbose_name = u'category'
        verbose_name_plural = u'categories'

# Future functionality: Sum, grouping...
# class Action(models.Model):
#     name = models.CharField(max_length=100, verbose_name='action')


class DataPoint(models.Model):
    name = models.CharField(max_length=100, verbose_name='data point')
    category = models.ForeignKey('Category', verbose_name='category')
    resource = models.URLField(max_length=200)
    date_field = models.CharField(max_length=100, verbose_name='date field')
    data_field = models.CharField(max_length=100, verbose_name='data field')
    # action = models.ForeignKey('Action', verbose_name='action')
    # Is it a good thing that this stat went up? Unemployment went up? Bad! Labor participation went up? Good!
    # Used for stat color
    trend_upwards_positive = models.BooleanField(default=False, verbose_name='upward trend positive?')
    featured = models.BooleanField(default=False, verbose_name='featured set?')

    def __str__(self):
        return u'%s' % self.name

    def check_previous_month(self, latest_month, previous_month):
        if ((latest_month['date'].month-1) == previous_month['date'].month) and \
                (latest_month['date'].year == previous_month['date'].year):
            return previous_month
        else:
            return None

    def check_month_last_year(self, latest_month, month_last_year):
        if (latest_month['date'].month == month_last_year['date'].month) and \
                ((latest_month['date'].year-1) == month_last_year['date'].year):
            return month_last_year
        else:
            return None

    def check_percent_change(self, latest_month, month_last_year):
        change = latest_month - month_last_year

        percent_change = (change / month_last_year) * 100

        return round(percent_change, 2)

    def display_data(self):
        #Bring the current month plus year, for comparing and charting.
        try:
            data_request = '%s?$select=%s, %s&$order=%s DESC&$limit=13' % (self.resource, self.date_field,
                                                                           self.data_field, self.date_field)
            r = requests.get(data_request)
            r.raise_for_status()

            data_set = [{'date': datetime.strptime(x[self.date_field][:10], '%Y-%m-%d'),
                         'value': x[self.data_field]} for x in r.json()]
            latest_month = data_set[0]
            previous_month = self.check_previous_month(latest_month, data_set[1])
            month_last_year = self.check_month_last_year(latest_month, data_set[-1])

            return {'data': self.name, 'data_set': data_set, 'latest_month': latest_month,
                    'previous_month': previous_month, 'month_last_year': month_last_year}

        except HTTPError as e:
            return e

    def display_summary(self):
        try:
            data_request = '%s?$select=%s, %s&$order=%s DESC&$limit=13' % (self.resource, self.date_field,
                                                                           self.data_field, self.date_field)
            r = requests.get(data_request)
            r.raise_for_status()

            data_set = [{'date': datetime.strptime(x[self.date_field][:10], '%Y-%m-%d'),
                         'value': x[self.data_field]} for x in r.json()]
            latest_month = data_set[0]
            month_last_year = self.check_month_last_year(latest_month, data_set[-1])
            percent_change = self.check_percent_change(float(latest_month['value']), float(month_last_year['value']))
            # Trend direction - If going up, is True. If going down, is False.
            trend_direction = True if percent_change > 0 else False
            trend_positive = True if self.trend_upwards_positive else False
            # if trend_direction True and trend_positive True - positive stat going up (green up arrow)
            # if trend_direction False and trend_positive True - positive stat going down (red down arrow)
            # if trend_direction True and trend_positive False - negative stat going up (red up arrow)
            # if trend_direction False and trend_positive False - negative stat going down (green down arrow)

            return {'data': self.name, 'latest_month': latest_month, 'percent_change': abs(percent_change),
                    'trend_direction': trend_direction, 'trend_positive': trend_positive,
                    'category': self.category, 'category_color': category_colors[self.category.name],
                    'category_icon': category_icons[self.category.name]}

        except HTTPError as e:
            return e