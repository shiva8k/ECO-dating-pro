from django.shortcuts import render


def home(request):
    features = [
        {
            "title": "Find Your Campus Circle",
            "text": "Meet classmates by interests, departments, clubs, and events.",
        },
        {
            "title": "Smart Matching",
            "text": "Discover study partners, project teammates, and social matches.",
        },
        {
            "title": "College-First Community",
            "text": "A focused space for students to connect beyond crowded group chats.",
        },
    ]
    return render(request, "core/home.html", {"features": features})
