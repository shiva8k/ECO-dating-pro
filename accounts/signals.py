from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import ChatRoom, Match, PremiumSubscription, Profile


@receiver(post_save, sender=User)
def create_or_save_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)
        PremiumSubscription.objects.create(user=instance)
    else:
        Profile.objects.get_or_create(user=instance)
        PremiumSubscription.objects.get_or_create(user=instance)
        instance.profile.save()


@receiver(post_save, sender=Match)
def create_match_chat_room(sender, instance, created, **kwargs):
    if created:
        ChatRoom.objects.get_or_create(match=instance)
