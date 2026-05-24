from django.contrib.auth import views as auth_views
from django.urls import path

from . import views


urlpatterns = [
    path("signup/", views.signup, name="signup"),
    path("onboarding/", views.onboarding, name="onboarding"),
    path("explore/", views.explore_profiles, name="explore_profiles"),
    path("matches/", views.matches_page, name="matches_page"),
    path("chats/", views.chat_list, name="chat_list"),
    path("chats/<int:room_id>/", views.chat_room, name="chat_room"),
    path("chats/<int:room_id>/send/", views.send_chat_message, name="send_chat_message"),
    path("chats/<int:room_id>/messages/", views.chat_messages_poll, name="chat_messages_poll"),
    path("notifications/", views.notifications_page, name="notifications_page"),
    path("notifications/<int:notification_id>/read/", views.mark_notification_read, name="mark_notification_read"),
    path("notifications/read/", views.mark_notifications_read, name="mark_notifications_read"),
    path("premium/", views.premium_plans, name="premium_plans"),
    path("premium/order/<int:plan_id>/", views.create_premium_order, name="create_premium_order"),
    path("premium/payment/success/", views.payment_success, name="payment_success"),
    path("premium/payment/failure/", views.payment_failure, name="payment_failure"),
    path("premium/payments/", views.payment_history, name="payment_history"),
    path("premium/who-liked-you/", views.who_liked_you, name="who_liked_you"),
    path("explore/<str:username>/<str:action>/", views.react_to_profile, name="react_to_profile"),
    path("profile/", views.my_profile, name="my_profile"),
    path("profile/edit/", views.edit_profile, name="edit_profile"),
    path("profile/<str:username>/", views.profile_detail, name="profile_detail"),
    path(
        "login/",
        auth_views.LoginView.as_view(template_name="registration/login.html"),
        name="login",
    ),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
]
