"""Profile compatibility and explore ranking for ECO."""

from .models import Profile, ProfileAction


# Shared interest slugs (stored comma-separated on Profile.interests)
INTEREST_CHOICES = [
    ("coding", "Coding"),
    ("gaming", "Gaming"),
    ("gym", "Gym"),
    ("anime", "Anime"),
    ("movies", "Movies"),
    ("music", "Music"),
    ("football", "Football"),
    ("startups", "Startups"),
    ("photography", "Photography"),
    ("travel", "Travel"),
    ("fashion", "Fashion"),
]

INTEREST_SLUGS = {slug for slug, _ in INTEREST_CHOICES}

LOOKING_FOR_COMPATIBILITY = {
    Profile.LOOKING_FRIENDSHIP: {
        Profile.LOOKING_FRIENDSHIP,
        Profile.LOOKING_STUDY_PARTNER,
        Profile.LOOKING_NETWORKING,
    },
    Profile.LOOKING_RELATIONSHIP: {
        Profile.LOOKING_RELATIONSHIP,
        Profile.LOOKING_SITUATIONSHIP,
    },
    Profile.LOOKING_SITUATIONSHIP: {
        Profile.LOOKING_SITUATIONSHIP,
        Profile.LOOKING_RELATIONSHIP,
        Profile.LOOKING_FRIENDSHIP,
    },
    Profile.LOOKING_STUDY_PARTNER: {
        Profile.LOOKING_STUDY_PARTNER,
        Profile.LOOKING_FRIENDSHIP,
        Profile.LOOKING_NETWORKING,
    },
    Profile.LOOKING_NETWORKING: {
        Profile.LOOKING_NETWORKING,
        Profile.LOOKING_STUDY_PARTNER,
        Profile.LOOKING_FRIENDSHIP,
    },
}


def parse_interests(interests_value):
    if not interests_value:
        return set()
    return {
        item.strip().lower()
        for item in interests_value.split(",")
        if item.strip().lower() in INTEREST_SLUGS
    }


def gender_matches_preference(gender, interested_in):
    if not gender or not interested_in:
        return False
    if interested_in == Profile.INTERESTED_EVERYONE:
        return True
    if interested_in == Profile.INTERESTED_MALE:
        return gender == Profile.GENDER_MALE
    if interested_in == Profile.INTERESTED_FEMALE:
        return gender == Profile.GENDER_FEMALE
    return False


def looking_for_compatible(looking_a, looking_b):
    if not looking_a or not looking_b:
        return False
    compatible = LOOKING_FOR_COMPATIBILITY.get(looking_a, set())
    return looking_b in compatible


def profiles_are_compatible(viewer_profile, candidate_profile):
    if not viewer_profile or not candidate_profile:
        return False
    if viewer_profile.user_id == candidate_profile.user_id:
        return False

    viewer_to_candidate = gender_matches_preference(
        candidate_profile.gender, viewer_profile.interested_in
    )
    candidate_to_viewer = gender_matches_preference(
        viewer_profile.gender, candidate_profile.interested_in
    )
    if not (viewer_to_candidate and candidate_to_viewer):
        return False

    return looking_for_compatible(viewer_profile.looking_for, candidate_profile.looking_for)


def score_profile_match(viewer_profile, candidate_profile):
    """Higher score = better explore ranking."""
    score = 0

    viewer_interests = parse_interests(viewer_profile.interests)
    candidate_interests = parse_interests(candidate_profile.interests)
    shared_interests = viewer_interests & candidate_interests
    score += len(shared_interests) * 100

    if (
        viewer_profile.college_name
        and candidate_profile.college_name
        and viewer_profile.college_name.strip().lower()
        == candidate_profile.college_name.strip().lower()
    ):
        score += 50

    if viewer_profile.age and candidate_profile.age:
        age_gap = abs(viewer_profile.age - candidate_profile.age)
        if age_gap <= 1:
            score += 40
        elif age_gap <= 2:
            score += 25
        elif age_gap <= 4:
            score += 10

    if (
        viewer_profile.looking_for
        and candidate_profile.looking_for
        and viewer_profile.looking_for == candidate_profile.looking_for
    ):
        score += 30

    return score


def get_explore_profiles(user):
    viewer_profile, _ = Profile.objects.get_or_create(user=user)
    if not viewer_profile.onboarding_completed:
        return Profile.objects.none()

    acted_user_ids = ProfileAction.objects.filter(from_user=user).values_list("to_user_id", flat=True)

    candidates = (
        Profile.objects.exclude(user=user)
        .exclude(user_id__in=acted_user_ids)
        .select_related("user", "user__premium_subscription")
    )

    compatible = [
        profile
        for profile in candidates
        if profiles_are_compatible(viewer_profile, profile)
    ]

    compatible.sort(
        key=lambda profile: (
            -score_profile_match(viewer_profile, profile),
            -int(
                getattr(
                    getattr(profile.user, "premium_subscription", None),
                    "profile_boost_active",
                    False,
                )
            ),
            profile.user.username,
        )
    )
    return compatible
