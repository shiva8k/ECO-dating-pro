from django.contrib.auth.models import User
from django.db import models
from django.urls import reverse
from django.utils import timezone


class Profile(models.Model):
    GENDER_MALE = "male"
    GENDER_FEMALE = "female"
    GENDER_NON_BINARY = "non_binary"
    GENDER_CHOICES = [
        (GENDER_MALE, "Male"),
        (GENDER_FEMALE, "Female"),
        (GENDER_NON_BINARY, "Non-binary"),
    ]

    INTERESTED_MALE = "male"
    INTERESTED_FEMALE = "female"
    INTERESTED_EVERYONE = "everyone"
    INTERESTED_IN_CHOICES = [
        (INTERESTED_MALE, "Male"),
        (INTERESTED_FEMALE, "Female"),
        (INTERESTED_EVERYONE, "Everyone"),
    ]

    LOOKING_FRIENDSHIP = "friendship"
    LOOKING_RELATIONSHIP = "relationship"
    LOOKING_SITUATIONSHIP = "situationship"
    LOOKING_STUDY_PARTNER = "study_partner"
    LOOKING_NETWORKING = "networking"
    LOOKING_FOR_CHOICES = [
        (LOOKING_FRIENDSHIP, "Friendship"),
        (LOOKING_RELATIONSHIP, "Relationship"),
        (LOOKING_SITUATIONSHIP, "Situationship"),
        (LOOKING_STUDY_PARTNER, "Study Partner"),
        (LOOKING_NETWORKING, "Networking"),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    profile_picture = models.ImageField(upload_to="profile_pictures/", blank=True, null=True)
    bio = models.TextField(blank=True, max_length=500)
    college_name = models.CharField(max_length=120, blank=True)
    department = models.CharField(max_length=120, blank=True)
    gender = models.CharField(max_length=20, choices=GENDER_CHOICES, blank=True)
    interested_in = models.CharField(max_length=20, choices=INTERESTED_IN_CHOICES, blank=True)
    looking_for = models.CharField(max_length=20, choices=LOOKING_FOR_CHOICES, blank=True)
    age = models.PositiveSmallIntegerField(null=True, blank=True)
    interests = models.CharField(
        max_length=255,
        blank=True,
        help_text="Comma-separated interest slugs, e.g. coding,gaming,travel.",
    )
    onboarding_completed = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.username}'s profile"

    def get_absolute_url(self):
        return reverse("profile_detail", kwargs={"username": self.user.username})

    def get_interest_list(self):
        if not self.interests:
            return []
        return [item.strip() for item in self.interests.split(",") if item.strip()]

    def get_interest_labels(self):
        from .matching import INTEREST_CHOICES

        labels = dict(INTEREST_CHOICES)
        return [labels.get(slug, slug.replace("_", " ").title()) for slug in self.get_interest_list()]

    def get_gender_display_label(self):
        return dict(self.GENDER_CHOICES).get(self.gender, "")

    def get_interested_in_display_label(self):
        return dict(self.INTERESTED_IN_CHOICES).get(self.interested_in, "")

    def get_looking_for_display_label(self):
        return dict(self.LOOKING_FOR_CHOICES).get(self.looking_for, "")

    def needs_onboarding(self):
        return not self.onboarding_completed


class ProfileAction(models.Model):
    LIKE = "like"
    PASS = "pass"
    ACTION_CHOICES = [
        (LIKE, "Like"),
        (PASS, "Pass"),
    ]

    from_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="sent_profile_actions")
    to_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="received_profile_actions")
    action = models.CharField(max_length=10, choices=ACTION_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["from_user", "to_user"], name="unique_profile_action")
        ]

    def __str__(self):
        return f"{self.from_user.username} {self.action}d {self.to_user.username}"


class Match(models.Model):
    user_one = models.ForeignKey(User, on_delete=models.CASCADE, related_name="matches_as_user_one")
    user_two = models.ForeignKey(User, on_delete=models.CASCADE, related_name="matches_as_user_two")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user_one", "user_two"], name="unique_match_pair")
        ]

    def __str__(self):
        return f"{self.user_one.username} matched with {self.user_two.username}"

    @classmethod
    def create_for_users(cls, first_user, second_user):
        user_one, user_two = sorted([first_user, second_user], key=lambda user: user.id)
        return cls.objects.get_or_create(user_one=user_one, user_two=user_two)


class ChatRoom(models.Model):
    match = models.OneToOneField(Match, on_delete=models.CASCADE, related_name="chat_room")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Chat room for {self.match}"

    def get_absolute_url(self):
        return reverse("chat_room", kwargs={"room_id": self.id})

    def has_member(self, user):
        return user.is_authenticated and user in {self.match.user_one, self.match.user_two}

    def other_user(self, user):
        if user == self.match.user_one:
            return self.match.user_two
        return self.match.user_one


class ChatMessage(models.Model):
    room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE, related_name="messages")
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name="chat_messages")
    content = models.TextField(max_length=1000)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.sender.username}: {self.content[:40]}"


class Notification(models.Model):
    LIKE = "like"
    MATCH = "match"
    MESSAGE = "message"
    PROFILE_VIEW = "profile_view"
    PREMIUM = "premium"
    TYPE_CHOICES = [
        (LIKE, "Like"),
        (MATCH, "Match"),
        (MESSAGE, "Message"),
        (PROFILE_VIEW, "Profile View"),
        (PREMIUM, "Premium"),
    ]

    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name="notifications")
    sender = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="sent_notifications",
        blank=True,
        null=True,
    )
    notification_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    title = models.CharField(max_length=120)
    message = models.CharField(max_length=255)
    link = models.CharField(max_length=255, blank=True)
    is_read = models.BooleanField(default=False)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-timestamp"]

    def __str__(self):
        return f"{self.title} for {self.recipient.username}"


class PremiumPlan(models.Model):
    name = models.CharField(max_length=80)
    slug = models.SlugField(unique=True)
    price_inr = models.PositiveIntegerField()
    duration_days = models.PositiveIntegerField(default=30)
    description = models.CharField(max_length=255, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["price_inr"]

    def __str__(self):
        return f"{self.name} - ₹{self.price_inr}"

    @property
    def amount_in_paise(self):
        return self.price_inr * 100


class PremiumSubscription(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="premium_subscription")
    plan = models.ForeignKey(PremiumPlan, on_delete=models.SET_NULL, blank=True, null=True)
    is_active = models.BooleanField(default=False)
    started_at = models.DateTimeField(blank=True, null=True)
    expires_at = models.DateTimeField(blank=True, null=True)
    profile_boost_active = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.username} premium"

    def activate(self, plan):
        now = timezone.now()
        self.plan = plan
        self.is_active = True
        self.started_at = now
        self.expires_at = now + timezone.timedelta(days=plan.duration_days)
        self.profile_boost_active = True
        self.save()

    @property
    def is_valid(self):
        return self.is_active and self.expires_at and self.expires_at > timezone.now()


class PaymentHistory(models.Model):
    CREATED = "created"
    SUCCESS = "success"
    FAILED = "failed"
    STATUS_CHOICES = [
        (CREATED, "Created"),
        (SUCCESS, "Success"),
        (FAILED, "Failed"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="payments")
    plan = models.ForeignKey(PremiumPlan, on_delete=models.SET_NULL, blank=True, null=True)
    amount_inr = models.PositiveIntegerField()
    razorpay_order_id = models.CharField(max_length=120, unique=True)
    razorpay_payment_id = models.CharField(max_length=120, blank=True)
    razorpay_signature = models.CharField(max_length=255, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=CREATED)
    failure_reason = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    paid_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user.username} - {self.plan} - {self.status}"
