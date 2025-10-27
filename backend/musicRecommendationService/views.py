import secrets
from urllib.parse import urlencode
from django_ratelimit.decorators import ratelimit
from django.views.decorators.http import require_GET
from django.shortcuts import redirect
from django.middleware.csrf import get_token
from django.conf import settings
from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model, login
from .models import LastfmLinking

# Create your views here.

User = get_user_model()
STATE_KEY = "lfm_state"

# Start the authentication process with last.fm
# Rate limit so people don't abuse the endpoint 
@ratelimit(key='ip', rate='3/m', block=False)
def lastfm_start(request):
    state = secrets.token_urlsafe(24)
    request.session[STATE_KEY] = state
    cb = f"{settings.LAST_FM_CALLBACK_URL}?{urlencode({'state': state})}"
    auth_url = "https://www.last.fm/api/auth?" + urlencode({
        "api_key": settings.LASTFM_API_KEY,
        "cb": cb,  
    })

    # Return the ur; as a json, front end will handle the navigation
    # to the specified page
    return JsonResponse({"auth_url": auth_url})

# Exchange token with the session key, store on database,
# then go back to front end
@ratelimit(key='ip', rate='3/m', block=False)
def lastfm_callback(request):
    from .lastfm_stuff import get_session
    token = request.GET.get("token")
    request.session.pop(STATE_KEY, None)

    sesh = get_session(token)
    lfm_username, sk = sesh["name"], sesh["key"]

    user, _ = User.objects.get_or_create(username=f"lfm:{lfm_username}")
    login(request, user)

    # Create user entry in the database
    LastfmLinking.objects.update_or_create(
        user=user,
        defaults={"lastfm_username": lfm_username, "sk": sk}
    )

    # Change to vercel url when deploying
    return redirect("https://firstfm.vercel.app/dashboard")

# Verifies the logged in user and returns their info
@login_required
def itsMe(request):
    link = LastfmLinking.objects.filter(user=request.user).first()
    return JsonResponse({
        "username": link.lastfm_username if link else None
    })
    

@require_GET # For session based CSRF
def csrfTokenView(request):
    print("CSRF TOKEN!!!!")
    token = get_token(request)
    return JsonResponse({'csrfToken': token})