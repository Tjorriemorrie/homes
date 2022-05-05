from django import template
from django.utils.timezone import now

register = template.Library()


@register.filter
def mil(value, *args):
    """Show price in million"""
    return f'R{round(value / 1_000_000, 1):.1f} mil'


@register.filter
def ha(value, *args):
    """Show size in hectar"""
    return f'{round(value / 10_000, 1):.1f} ha'


@register.filter
def bbc(value):
    """Show value for bedrooms, bathrooms and cars"""
    if int(value) == value:
        return int(value)
    return value


@register.filter
def perc(value: float, decimals: int = 0):
    if not decimals:
        return f'{int(value * 100)}%'
    return f'{round(value * 100, decimals)}%'


@register.filter
def ppu(home):
    price_per_unit = home.size * 1_000 // home.price
    return f'{price_per_unit}'


@register.filter
def daysold(timestamp):
    delta = now() - timestamp
    days = delta.total_seconds() // 86400
    return f'{days:.0f}'


@register.filter
def outdated(home):
    delta = now() - home.updated_at
    if delta.total_seconds() > 86400:
        return f' {delta.total_seconds() // 86400}!'
    return ''
