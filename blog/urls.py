from django.urls import path
from . import views
app_name = "blog"


urlpatterns = [
    # path("", views.post_list, name="post_list"), # Url fbv
    path('<int:year>/<int:month>/<int:day>/<slug:post>/', views.post_detail, name='post_detail'),
    path('',views.PostListView.as_view(), name='post_list'),

]