from django.contrib import admin
from django.urls import path, include
from django.contrib.auth.views import LogoutView
from django.conf import settings
from django.conf.urls.static import static
from fitness_api.views import landing_page, login_view, signup_view, index

urlpatterns = [
    path('admin/', admin.site.urls),
    path('landing/', landing_page, name='landing'),
    path('login/', login_view, name='login'),
    path('signup/', signup_view, name='signup'),
    path('logout/', LogoutView.as_view(next_page='/landing/'), name='logout'),
    path('api/', include('fitness_api.urls')),
    path('', index, name='home'),
]

# Serve static files during development
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
