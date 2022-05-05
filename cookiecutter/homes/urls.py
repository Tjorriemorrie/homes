from django.urls import path

from homes import views

app_name = "homes"
urlpatterns = [
    path("", view=views.MainView.as_view(), name="main"),
    path("scrape", view=views.ScrapeView.as_view(), name="scrape"),
    path("match/drop", view=views.DropView.as_view(), name="drop"),
    path("match/<int:pk>", view=views.MatchView.as_view(), name="match"),
    path("remove/<int:pk>", view=views.DeleteHomeView.as_view(), name="delete"),
    path("hide/<int:pk>", view=views.hide_view, name="hide"),
]
