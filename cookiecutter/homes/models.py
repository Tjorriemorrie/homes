from django.db import models
from django.db.models import Max, Q


class Home(models.Model):
    CATEGORY_FARM = 1
    CATEGORY_CHOICES = (
        (CATEGORY_FARM, 'Farm'),
    )
    url = models.URLField(null=False, unique=True)
    size = models.IntegerField(null=False)
    category = models.IntegerField(choices=CATEGORY_CHOICES)
    area = models.CharField(max_length=255)
    address = models.CharField(max_length=255)
    price = models.IntegerField()
    bedrooms = models.FloatField()
    bathrooms = models.FloatField()
    cars = models.FloatField()
    img = models.URLField(null=True)
    hidden = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    rated_at = models.DateTimeField(null=True)
    rated = models.IntegerField(default=0)
    rating = models.FloatField(default=0.5)

    def __str__(self):
        return f'[{self.area}] {self.address} {self.price}'

    def update_rating(self):
        q = Match.objects.filter(Q(winner=self) | Q(loser=self))
        self.rated_at = q.aggregate(Max('created_at'))['created_at__max']
        self.rated = q.count()
        try:
            self.rating = self.wins.count() / self.rated
        except ZeroDivisionError:
            self.rating = 0.50

    def should_hide(self):
        return self.rated >= 2 and self.rating < 0.7 and self.rating / self.rated < 0.05


class Match(models.Model):
    winner = models.ForeignKey(Home, on_delete=models.CASCADE,
                               related_name='wins')
    loser = models.ForeignKey(Home, on_delete=models.CASCADE,
                              related_name='losses')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = (('winner', 'loser'),)
