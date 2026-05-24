import json

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.conf import settings
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_GET, require_POST

from .forms import (
    OnboardingStepFourForm,
    OnboardingStepOneForm,
    OnboardingStepThreeForm,
    OnboardingStepTwoForm,
    ProfileForm,
    SignUpForm,
)
from .chat_service import save_chat_message, serialize_chat_message
from .matching import INTEREST_CHOICES, get_explore_profiles, profiles_are_compatible
from .models import (
    ChatRoom,
    Match,
    Notification,
    PaymentHistory,
    PremiumPlan,
    PremiumSubscription,
    Profile,
    ProfileAction,
)
from .payments import create_razorpay_order, verify_razorpay_signature

ONBOARDING_STEPS = 4


def signup(request):
    if request.user.is_authenticated:
        profile, _ = Profile.objects.get_or_create(user=request.user)
        if profile.needs_onboarding():
            return redirect("onboarding")
        return redirect("home")

    if request.method == "POST":
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Welcome to ECO. Let's set up your profile.")
            return redirect("onboarding")
    else:
        form = SignUpForm()

    return render(request, "registration/signup.html", {"form": form})


@login_required
def onboarding(request):
    profile, _ = Profile.objects.get_or_create(user=request.user)
    if not profile.needs_onboarding():
        return redirect("explore_profiles")

    step = int(request.GET.get("step", 1))
    if step < 1 or step > ONBOARDING_STEPS:
        step = 1

    form = None
    if request.method == "POST":
        if step == 1:
            form = OnboardingStepOneForm(request.POST, instance=profile)
            if form.is_valid():
                form.save()
                return redirect(f"{request.path}?step=2")
        elif step == 2:
            form = OnboardingStepTwoForm(request.POST, instance=profile)
            if form.is_valid():
                form.save()
                return redirect(f"{request.path}?step=3")
        elif step == 3:
            form = OnboardingStepThreeForm(request.POST, profile=profile)
            if form.is_valid():
                form.save()
                return redirect(f"{request.path}?step=4")
        elif step == 4:
            form = OnboardingStepFourForm(request.POST, request.FILES, instance=profile)
            if form.is_valid():
                profile = form.save()
                profile.onboarding_completed = True
                profile.save(update_fields=["onboarding_completed"])
                messages.success(request, "Your ECO profile is ready. Start exploring campus.")
                return redirect("explore_profiles")

    if form is None:
        if step == 1:
            form = OnboardingStepOneForm(instance=profile)
        elif step == 2:
            form = OnboardingStepTwoForm(instance=profile)
        elif step == 3:
            form = OnboardingStepThreeForm(profile=profile)
        elif step == 4:
            form = OnboardingStepFourForm(instance=profile)

    progress_percent = int((step / ONBOARDING_STEPS) * 100)
    return render(
        request,
        "accounts/onboarding.html",
        {
            "form": form,
            "step": step,
            "total_steps": ONBOARDING_STEPS,
            "progress_percent": progress_percent,
            "interest_choices": INTEREST_CHOICES,
        },
    )


@login_required
def my_profile(request):
    profile, _ = Profile.objects.get_or_create(user=request.user)
    return redirect(profile.get_absolute_url())


def profile_detail(request, username):
    profile_user = get_object_or_404(User, username=username)
    profile, _ = Profile.objects.get_or_create(user=profile_user)
    subscription, _ = PremiumSubscription.objects.get_or_create(user=profile_user)
    return render(
        request,
        "accounts/profile_detail.html",
        {
            "profile": profile,
            "profile_user": profile_user,
            "subscription": subscription,
            "interests": profile.get_interest_labels(),
            "is_owner": request.user.is_authenticated and request.user == profile_user,
        },
    )


@login_required
def edit_profile(request):
    profile, _ = Profile.objects.get_or_create(user=request.user)
    if request.method == "POST":
        form = ProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, "Your ECO profile was updated.")
            return redirect(profile.get_absolute_url())
    else:
        form = ProfileForm(instance=profile)

    return render(request, "accounts/profile_edit.html", {"form": form, "profile": profile})


@login_required
def explore_profiles(request):
    subscription, _ = PremiumSubscription.objects.get_or_create(user=request.user)
    daily_like_limit = 5
    like_window_start = timezone.now() - timezone.timedelta(days=1)
    likes_today = ProfileAction.objects.filter(
        from_user=request.user,
        action=ProfileAction.LIKE,
        updated_at__gte=like_window_start,
    ).count()

    compatible_profiles = get_explore_profiles(request.user)
    current_profile = compatible_profiles[0] if compatible_profiles else None
    current_card = None
    if current_profile:
        current_card = {
            "profile": current_profile,
            "interests": current_profile.get_interest_labels(),
            "remaining_count": len(compatible_profiles) - 1,
        }

    return render(
        request,
        "accounts/explore.html",
        {
            "current_card": current_card,
            "can_like": subscription.is_valid or likes_today < daily_like_limit,
            "likes_remaining": "Unlimited" if subscription.is_valid else max(daily_like_limit - likes_today, 0),
        },
    )


@login_required
@require_POST
def react_to_profile(request, username, action):
    if action not in {ProfileAction.LIKE, ProfileAction.PASS}:
        messages.error(request, "That action is not available.")
        return redirect("explore_profiles")

    target_user = get_object_or_404(User, username=username)
    if target_user == request.user:
        messages.error(request, "You cannot react to your own profile.")
        return redirect("explore_profiles")

    viewer_profile, _ = Profile.objects.get_or_create(user=request.user)
    target_profile, _ = Profile.objects.get_or_create(user=target_user)
    if not profiles_are_compatible(viewer_profile, target_profile):
        messages.error(request, "This profile is not available in your explore feed.")
        return redirect("explore_profiles")

    subscription, _ = PremiumSubscription.objects.get_or_create(user=request.user)
    if action == ProfileAction.LIKE and not subscription.is_valid:
        like_window_start = timezone.now() - timezone.timedelta(days=1)
        likes_today = ProfileAction.objects.filter(
            from_user=request.user,
            action=ProfileAction.LIKE,
            updated_at__gte=like_window_start,
        ).count()
        if likes_today >= 5:
            messages.error(request, "Free users get 5 likes per day. Upgrade to ECO Premium for unlimited likes.")
            return redirect("premium_plans")

    previous_action = ProfileAction.objects.filter(
        from_user=request.user,
        to_user=target_user,
    ).values_list("action", flat=True).first()

    ProfileAction.objects.update_or_create(
        from_user=request.user,
        to_user=target_user,
        defaults={"action": action},
    )

    if action == ProfileAction.LIKE:
        if previous_action != ProfileAction.LIKE:
            Notification.objects.create(
                recipient=target_user,
                sender=request.user,
                notification_type=Notification.LIKE,
                title="New like",
                message=f"{request.user.username} liked your profile.",
                link=request.user.profile.get_absolute_url(),
            )
        mutual_like_exists = ProfileAction.objects.filter(
            from_user=target_user,
            to_user=request.user,
            action=ProfileAction.LIKE,
        ).exists()
        if mutual_like_exists:
            match, match_created = Match.create_for_users(request.user, target_user)
            room, _ = ChatRoom.objects.get_or_create(match=match)
            if match_created:
                Notification.objects.create(
                    recipient=target_user,
                    sender=request.user,
                    notification_type=Notification.MATCH,
                    title="New match",
                    message=f"You and {request.user.username} matched.",
                    link=room.get_absolute_url(),
                )
                Notification.objects.create(
                    recipient=request.user,
                    sender=target_user,
                    notification_type=Notification.MATCH,
                    title="New match",
                    message=f"You and {target_user.username} matched.",
                    link=room.get_absolute_url(),
                )
            messages.success(request, f"You matched with {target_user.username}.")
        else:
            messages.success(request, f"You liked {target_user.username}.")
    else:
        messages.info(request, f"You passed on {target_user.username}.")

    return redirect("explore_profiles")


@login_required
def matches_page(request):
    matches = (
        Match.objects.filter(Q(user_one=request.user) | Q(user_two=request.user))
        .select_related("user_one__profile", "user_two__profile")
        .order_by("-created_at")
    )

    match_cards = []
    for match in matches:
        matched_user = match.user_two if match.user_one == request.user else match.user_one
        profile, _ = Profile.objects.get_or_create(user=matched_user)
        room, _ = ChatRoom.objects.get_or_create(match=match)
        match_cards.append(
            {
                "match": match,
                "room": room,
                "user": matched_user,
                "profile": profile,
                "interests": profile.get_interest_labels(),
            }
        )

    return render(request, "accounts/matches.html", {"match_cards": match_cards})


@login_required
def chat_list(request):
    rooms = (
        ChatRoom.objects.filter(Q(match__user_one=request.user) | Q(match__user_two=request.user))
        .select_related("match__user_one__profile", "match__user_two__profile")
        .prefetch_related("messages")
        .order_by("-created_at")
    )

    chat_cards = []
    for room in rooms:
        matched_user = room.other_user(request.user)
        profile, _ = Profile.objects.get_or_create(user=matched_user)
        last_message = room.messages.order_by("-created_at").first()
        chat_cards.append(
            {
                "room": room,
                "user": matched_user,
                "profile": profile,
                "last_message": last_message,
            }
        )

    return render(request, "accounts/chat_list.html", {"chat_cards": chat_cards})


@login_required
def chat_room(request, room_id):
    room = get_object_or_404(
        ChatRoom.objects.select_related("match__user_one__profile", "match__user_two__profile"),
        id=room_id,
    )
    if not room.has_member(request.user):
        messages.error(request, "You can only chat with matched students.")
        return redirect("chat_list")

    matched_user = room.other_user(request.user)
    profile, _ = Profile.objects.get_or_create(user=matched_user)
    room_messages = room.messages.select_related("sender").order_by("created_at")
    last_message = room_messages.last()
    return render(
        request,
        "accounts/chat_room.html",
        {
            "room": room,
            "matched_user": matched_user,
            "profile": profile,
            "room_messages": room_messages,
            "last_message_id": last_message.id if last_message else 0,
        },
    )


@login_required
@require_POST
def send_chat_message(request, room_id):
    room = get_object_or_404(ChatRoom, id=room_id)
    if not room.has_member(request.user):
        return JsonResponse({"error": "Forbidden"}, status=403)

    try:
        if request.content_type == "application/json":
            payload = json.loads(request.body.decode("utf-8"))
            content = payload.get("message", "")
        else:
            content = request.POST.get("message", "")
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    chat_message = save_chat_message(room, request.user, content)
    if chat_message is None:
        return JsonResponse({"error": "Message cannot be empty."}, status=400)

    return JsonResponse(serialize_chat_message(chat_message))


@login_required
@require_GET
def chat_messages_poll(request, room_id):
    room = get_object_or_404(ChatRoom, id=room_id)
    if not room.has_member(request.user):
        return JsonResponse({"error": "Forbidden"}, status=403)

    try:
        after_id = int(request.GET.get("after", 0))
    except (TypeError, ValueError):
        after_id = 0

    new_messages = room.messages.filter(id__gt=after_id).select_related("sender").order_by("created_at")
    return JsonResponse(
        {
            "messages": [serialize_chat_message(message) for message in new_messages],
        }
    )


@login_required
def notifications_page(request):
    notifications = Notification.objects.filter(recipient=request.user).select_related("sender")
    return render(request, "accounts/notifications.html", {"notifications": notifications})


@login_required
@require_POST
def mark_notification_read(request, notification_id):
    notification = get_object_or_404(Notification, id=notification_id, recipient=request.user)
    notification.is_read = True
    notification.save(update_fields=["is_read"])
    return redirect(notification.link or "notifications_page")


@login_required
@require_POST
def mark_notifications_read(request):
    Notification.objects.filter(recipient=request.user, is_read=False).update(is_read=True)
    messages.success(request, "Notifications marked as read.")
    return redirect("notifications_page")


@login_required
def premium_plans(request):
    plans = PremiumPlan.objects.filter(is_active=True)
    subscription, _ = PremiumSubscription.objects.get_or_create(user=request.user)
    return render(
        request,
        "accounts/premium_plans.html",
        {
            "plans": plans,
            "subscription": subscription,
            "razorpay_key_id": settings.RAZORPAY_KEY_ID,
        },
    )


@login_required
@require_POST
def create_premium_order(request, plan_id):
    plan = get_object_or_404(PremiumPlan, id=plan_id, is_active=True)
    try:
        payment = PaymentHistory.objects.create(
            user=request.user,
            plan=plan,
            amount_inr=plan.price_inr,
            razorpay_order_id=f"pending-{request.user.id}-{timezone.now().timestamp()}",
        )
        order = create_razorpay_order(plan, receipt=f"eco-premium-{payment.id}")
    except ValueError as exc:
        messages.error(request, str(exc))
        return redirect("premium_plans")
    except Exception:
        messages.error(request, "Could not create Razorpay order. Please try again.")
        return redirect("premium_plans")

    payment.razorpay_order_id = order["id"]
    payment.save(update_fields=["razorpay_order_id"])
    return render(
        request,
        "accounts/payment_checkout.html",
        {
            "plan": plan,
            "payment": payment,
            "order": order,
            "razorpay_key_id": settings.RAZORPAY_KEY_ID,
        },
    )


@login_required
@require_POST
def payment_success(request):
    razorpay_order_id = request.POST.get("razorpay_order_id", "")
    razorpay_payment_id = request.POST.get("razorpay_payment_id", "")
    razorpay_signature = request.POST.get("razorpay_signature", "")
    payment = get_object_or_404(PaymentHistory, razorpay_order_id=razorpay_order_id, user=request.user)

    try:
        verify_razorpay_signature(
            {
                "razorpay_order_id": razorpay_order_id,
                "razorpay_payment_id": razorpay_payment_id,
                "razorpay_signature": razorpay_signature,
            }
        )
    except Exception:
        payment.status = PaymentHistory.FAILED
        payment.failure_reason = "Razorpay signature verification failed."
        payment.save(update_fields=["status", "failure_reason"])
        messages.error(request, "Payment verification failed. Your subscription was not activated.")
        return redirect("payment_failure")

    payment.status = PaymentHistory.SUCCESS
    payment.razorpay_payment_id = razorpay_payment_id
    payment.razorpay_signature = razorpay_signature
    payment.paid_at = timezone.now()
    payment.save(update_fields=["status", "razorpay_payment_id", "razorpay_signature", "paid_at"])

    subscription, _ = PremiumSubscription.objects.get_or_create(user=request.user)
    subscription.activate(payment.plan)
    messages.success(request, "Welcome to ECO Premium. Your subscription is active.")
    return redirect("payment_history")


@login_required
def payment_failure(request):
    return render(request, "accounts/payment_failure.html")


@login_required
def payment_history(request):
    payments = PaymentHistory.objects.filter(user=request.user).select_related("plan")
    subscription, _ = PremiumSubscription.objects.get_or_create(user=request.user)
    return render(
        request,
        "accounts/payment_history.html",
        {"payments": payments, "subscription": subscription},
    )


@login_required
def who_liked_you(request):
    subscription, _ = PremiumSubscription.objects.get_or_create(user=request.user)
    if not subscription.is_valid:
        messages.error(request, "Upgrade to ECO Premium to see who liked you.")
        return redirect("premium_plans")

    likes = ProfileAction.objects.filter(to_user=request.user, action=ProfileAction.LIKE).select_related(
        "from_user__profile"
    )
    return render(request, "accounts/who_liked_you.html", {"likes": likes})
