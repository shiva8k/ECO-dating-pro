from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.contrib.auth.forms import AuthenticationForm

from .matching import INTEREST_CHOICES, INTEREST_SLUGS
from .models import Profile


class SignUpForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        help_text="Use your college email if you have one.",
        widget=forms.EmailInput(attrs={
            'class': 'w-full px-4 py-3 rounded-lg bg-white/5 border border-white/20 text-white placeholder-white/50 focus:outline-none focus:border-pink-500 focus:ring-1 focus:ring-pink-500 transition-all'
        })
    )

    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({
            'class': 'w-full px-4 py-3 rounded-lg bg-white/5 border border-white/20 text-white placeholder-white/50 focus:outline-none focus:border-pink-500 focus:ring-1 focus:ring-pink-500 transition-all',
            'placeholder': 'Username'
        })
        self.fields['password1'].widget.attrs.update({
            'class': 'w-full px-4 py-3 rounded-lg bg-white/5 border border-white/20 text-white placeholder-white/50 focus:outline-none focus:border-pink-500 focus:ring-1 focus:ring-pink-500 transition-all',
            'placeholder': 'Password'
        })
        self.fields['password2'].widget.attrs.update({
            'class': 'w-full px-4 py-3 rounded-lg bg-white/5 border border-white/20 text-white placeholder-white/50 focus:outline-none focus:border-pink-500 focus:ring-1 focus:ring-pink-500 transition-all',
            'placeholder': 'Confirm Password'
        })


class ProfileForm(forms.ModelForm):
    interest_selection = forms.MultipleChoiceField(
        choices=INTEREST_CHOICES,
        required=False,
        widget=forms.CheckboxSelectMultiple,
        label="Interests",
    )

    class Meta:
        model = Profile
        fields = (
            "profile_picture",
            "bio",
            "college_name",
            "department",
            "gender",
            "interested_in",
            "looking_for",
            "age",
        )
        widgets = {
            "bio": forms.Textarea(
                attrs={
                    "rows": 4,
                    "placeholder": "Tell campus what you are into, what you are building, or who you want to meet.",
                    "class": "w-full px-4 py-3 rounded-lg bg-white/5 border border-white/20 text-white placeholder-white/50 focus:outline-none focus:border-pink-500 focus:ring-1 focus:ring-pink-500 transition-all"
                }
            ),
            "college_name": forms.TextInput(attrs={
                "placeholder": "Example: ECO Institute of Technology",
                "class": "w-full px-4 py-3 rounded-lg bg-white/5 border border-white/20 text-white placeholder-white/50 focus:outline-none focus:border-pink-500 focus:ring-1 focus:ring-pink-500 transition-all"
            }),
            "department": forms.TextInput(attrs={
                "placeholder": "Example: Computer Science",
                "class": "w-full px-4 py-3 rounded-lg bg-white/5 border border-white/20 text-white placeholder-white/50 focus:outline-none focus:border-pink-500 focus:ring-1 focus:ring-pink-500 transition-all"
            }),
            "age": forms.NumberInput(attrs={
                "min": 16,
                "max": 100,
                "placeholder": "20",
                "class": "w-full px-4 py-3 rounded-lg bg-white/5 border border-white/20 text-white placeholder-white/50 focus:outline-none focus:border-pink-500 focus:ring-1 focus:ring-pink-500 transition-all"
            }),
            "gender": forms.RadioSelect,
            "interested_in": forms.RadioSelect,
            "looking_for": forms.RadioSelect,
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name in ("gender", "interested_in", "looking_for"):
            self.fields[field_name].choices = Profile._meta.get_field(field_name).choices
        if self.instance and self.instance.pk:
            self.fields["interest_selection"].initial = self.instance.get_interest_list()
        for field in self.fields.values():
            if hasattr(field.widget, "attrs"):
                if "class" not in field.widget.attrs:
                    field.widget.attrs.setdefault("class", "w-full px-4 py-3 rounded-lg bg-white/5 border border-white/20 text-white placeholder-white/50 focus:outline-none focus:border-pink-500 focus:ring-1 focus:ring-pink-500 transition-all")

    def save(self, commit=True):
        profile = super().save(commit=False)
        selected = self.cleaned_data.get("interest_selection") or []
        profile.interests = ",".join(selected)
        if commit:
            profile.save()
        return profile


class OnboardingStepOneForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ("gender", "interested_in", "looking_for", "age")
        widgets = {
           "gender": forms.RadioSelect(),
            "interested_in": forms.RadioSelect(),
            "looking_for": forms.RadioSelect(),
            "age": forms.NumberInput(attrs={"min": 16, "max": 100, "placeholder": "Your age"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name in self.fields:
            self.fields[field_name].required = True

    def clean_age(self):
        age = self.cleaned_data.get("age")
        if age is not None and (age < 16 or age > 100):
            raise ValidationError("Age must be between 16 and 100.")
        return age


class OnboardingStepTwoForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ("college_name", "bio")
        widgets = {
            "college_name": forms.TextInput(attrs={"placeholder": "Your college or university"}),
            "bio": forms.Textarea(
                attrs={
                    "rows": 4,
                    "placeholder": "A short intro that shows your vibe on campus.",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["college_name"].required = True
        self.fields["bio"].required = True


class OnboardingStepThreeForm(forms.Form):
    interests = forms.MultipleChoiceField(
        choices=INTEREST_CHOICES,
        widget=forms.CheckboxSelectMultiple,
        required=True,
        label="Pick your interests",
    )

    def __init__(self, *args, profile=None, **kwargs):
        self.profile = profile
        super().__init__(*args, **kwargs)
        if profile:
            self.fields["interests"].initial = profile.get_interest_list()

    def clean_interests(self):
        selected = self.cleaned_data.get("interests") or []
        if not selected:
            raise ValidationError("Select at least one interest.")
        invalid = [item for item in selected if item not in INTEREST_SLUGS]
        if invalid:
            raise ValidationError("One or more interests are invalid.")
        return selected

    def save(self):
        self.profile.interests = ",".join(self.cleaned_data["interests"])
        self.profile.save(update_fields=["interests"])
        return self.profile


class OnboardingStepFourForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ("profile_picture",)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["profile_picture"].required = True

from django.contrib.auth.forms import AuthenticationForm

class LoginForm(AuthenticationForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['username'].widget.attrs.update({
            'class': 'w-full px-4 py-3 rounded-lg bg-white/5 border border-pink-500/30 text-white placeholder-white/50 focus:outline-none focus:border-pink-500 focus:ring-1 focus:ring-pink-500 transition-all',
            'placeholder': 'Enter username'
        })

        self.fields['password'].widget.attrs.update({
            'class': 'w-full px-4 py-3 rounded-lg bg-white/5 border border-pink-500/30 text-white placeholder-white/50 focus:outline-none focus:border-pink-500 focus:ring-1 focus:ring-pink-500 transition-all',
            'placeholder': 'Enter password'
        })



class LoginForm(AuthenticationForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['username'].widget.attrs.update({
            'class': 'w-full px-4 py-3 rounded-lg bg-white/5 border border-white/20 text-white placeholder-white/50 focus:outline-none focus:border-pink-500 focus:ring-1 focus:ring-pink-500 transition-all',
            'placeholder': 'Enter username'
        })

        self.fields['password'].widget.attrs.update({
            'class': 'w-full px-4 py-3 rounded-lg bg-white/5 border border-white/20 text-white placeholder-white/50 focus:outline-none focus:border-pink-500 focus:ring-1 focus:ring-pink-500 transition-all',
            'placeholder': 'Enter password'
        })

