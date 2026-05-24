from django.contrib import admin

from .models import (
    ChatMessage,
    ChatRoom,
    Match,
    Notification,
    PaymentHistory,
    PremiumPlan,
    PremiumSubscription,
    Profile,
    ProfileAction,
)


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "gender",
        "interested_in",
        "looking_for",
        "age",
        "college_name",
        "onboarding_completed",
    )
    list_filter = ("gender", "interested_in", "looking_for", "onboarding_completed")
    search_fields = ("user__username", "college_name", "department", "interests", "bio")


@admin.register(ProfileAction)
class ProfileActionAdmin(admin.ModelAdmin):
    list_display = ("from_user", "to_user", "action", "updated_at")
    list_filter = ("action", "created_at")
    search_fields = ("from_user__username", "to_user__username")


@admin.register(Match)
class MatchAdmin(admin.ModelAdmin):
    list_display = ("user_one", "user_two", "created_at")
    search_fields = ("user_one__username", "user_two__username")


@admin.register(ChatRoom)
class ChatRoomAdmin(admin.ModelAdmin):
    list_display = ("match", "created_at")
    search_fields = ("match__user_one__username", "match__user_two__username")


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ("room", "sender", "created_at")
    search_fields = ("sender__username", "content")


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("recipient", "sender", "notification_type", "is_read", "timestamp")
    list_filter = ("notification_type", "is_read", "timestamp")
    search_fields = ("recipient__username", "sender__username", "title", "message")


@admin.register(PremiumPlan)
class PremiumPlanAdmin(admin.ModelAdmin):
    list_display = ("name", "price_inr", "duration_days", "is_active")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(PremiumSubscription)
class PremiumSubscriptionAdmin(admin.ModelAdmin):
    list_display = ("user", "plan", "is_active", "expires_at", "profile_boost_active")
    search_fields = ("user__username",)


@admin.register(PaymentHistory)
class PaymentHistoryAdmin(admin.ModelAdmin):
    list_display = ("user", "plan", "amount_inr", "status", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("user__username", "razorpay_order_id", "razorpay_payment_id")
