from datetime import timedelta
from itertools import combinations
from operator import or_, and_

from django.db.models import Q
from django.utils.timezone import now

from homes.constants import HA_MIN_SIZE, TOP_PRICE, HA_MAX_SIZE, ONE_MILLION, MIN_PRICE
from homes.models import Home, Match


def get_next_match():
    hour_ago = now() - timedelta(hours=1)
    two_ago = now() - timedelta(minutes=2)
    homes = Home.objects.filter(
        Q(price__gte=MIN_PRICE),
        Q(price__lte=TOP_PRICE),
        Q(size__gt=HA_MIN_SIZE),
        Q(size__lt=HA_MAX_SIZE) | Q(price__lte=ONE_MILLION),
    ).exclude(
        hidden=True
    ).order_by('rated', 'rating').all()
    for home1, home2 in combinations(homes, 2):
        try:
            Match.objects.get(Q(winner=home1, loser=home2) | Q(winner=home2, loser=home1))
        except Match.DoesNotExist:
            return home1, home2
