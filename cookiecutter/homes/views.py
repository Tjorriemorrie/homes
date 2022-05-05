import logging
from operator import or_

from django.db.models import Q
from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse, reverse_lazy
from django.views.generic import ListView, RedirectView, DeleteView

from homes.constants import HA_MIN_SIZE, TOP_PRICE, HA_MAX_SIZE, ONE_MILLION, MIN_PRICE
from homes.models import Home, Match
from homes.selectors import get_next_match
from homes.tasks import scrape_task, time_since_updated, drop_matches


logger = logging.getLogger(__name__)

class MainView(ListView):
    template_name = 'homes/list.html'
    # model = Home
    queryset = Home.objects.filter(
        Q(price__gte=MIN_PRICE),
        Q(price__lte=TOP_PRICE),
        Q(size__gt=HA_MIN_SIZE),
        Q(size__lt=HA_MAX_SIZE) | Q(price__lte=ONE_MILLION),
    ).exclude(
        hidden=True
    )
    ordering = ['-rating', 'rated', '-created_at']

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        context['match'] = match = get_next_match()
        self.request.session['match_ids'] = (match[0].id, match[1].id) if match else None
        return context


class ScrapeView(RedirectView):
    permanent = False

    def get_redirect_url(self):
        scrape_task.delay()
        time_since_updated.apply_async(countdown=60*10)
        return reverse("homes:main")


class MatchView(RedirectView):
    permanent = False

    def get_redirect_url(self, *args, **kwargs):
        match_ids = self.request.session['match_ids']
        if match_ids:
            winner_id = kwargs['pk']
            if winner_id not in match_ids:
                raise Exception(f'invalid pk {winner_id} in match_ids {match_ids}')
            winner = Home.objects.get(pk=winner_id)
            loser_id = [i for i in match_ids if i != winner_id][0]
            loser = Home.objects.get(pk=loser_id)
            match = Match.objects.create(
                winner=winner,
                loser=loser)
        return reverse("homes:main")


class DeleteHomeView(DeleteView):
    model = Home
    success_url = reverse_lazy('homes:main')


def hide_view(request, pk: int = None):
    home = get_object_or_404(Home, pk=pk)
    home.hidden = True
    home.save()
    return redirect('homes:main')


class DropView(RedirectView):
    permanent = False

    def get_redirect_url(self, *args, **kwargs):
        hidden = Home.objects.filter(
            hidden=True
        ).filter(
            Q(rated__lt=2)  # Q(rating__gte=0.75) |
        ).all()
        logger.info(f'Unhiding {len(hidden)} homes...')
        for home in hidden:
            home.hidden = False
            home.save()

        drop_matches()
        return reverse("homes:main")
