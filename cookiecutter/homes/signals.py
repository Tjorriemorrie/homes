import logging

from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

from homes.models import Match, Home

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Match)
def update_home_ratings(sender, instance, created, **kwargs):
    instance.winner.update_rating()
    instance.winner.save()
    instance.loser.update_rating()
    instance.loser.save()
    logger.info(f'Updating ratings for {instance.winner} and {instance.loser} after match')


@receiver(post_delete, sender=Match)
def delete_home_ratings(sender, instance: Match, **kwargs):
    # logger.info(f'Match {instance} deleted')

    winner_home = instance.winner
    if Home.objects.filter(pk=winner_home.pk).exists():
        if winner_home.hidden and not winner_home.should_hide():
            winner_home.hidden = False
            logger.info(f'Setting {winner_home} visible again due to ratio')
        else:
            logger.info(f'No change to {winner_home} on ratio')
        winner_home.update_rating()
        winner_home.save()

    loser_home = instance.loser
    if Home.objects.filter(pk=loser_home.pk).exists():
        if loser_home.hidden and not loser_home.should_hide():
            loser_home.hidden = False
            logger.info(f'Setting {loser_home} visible again due to ratio')
        else:
            logger.info(f'No change to {loser_home} on ratio')
        loser_home.update_rating()
        loser_home.save()


