from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import get_user_model
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy

from .forms import SalesRepForm, StyledAuthenticationForm
from audit.utils import log_action

User = get_user_model()


class StoreLoginView(auth_views.LoginView):
    template_name = "registration/login.html"
    authentication_form = StyledAuthenticationForm
    redirect_authenticated_user = True

    def form_valid(self, form):
        user = form.get_user()
        if not user.active_staff:
            messages.error(self.request, "Your account has been deactivated. Contact the owner/admin.")
            return self.form_invalid(form)
        response = super().form_valid(form)
        log_action(user, "LOGIN", f"{user.username} logged in")
        return response


@login_required
def post_login_redirect(request):
    if request.user.is_admin_role:
        return redirect("core:dashboard")
    return redirect("sales:pos")


def _is_admin(user):
    return user.is_authenticated and user.is_admin_role


@user_passes_test(_is_admin)
def rep_list(request):
    reps = User.objects.filter(role=User.Role.SALESREP).order_by("username")
    return render(request, "admin_dash/reps_list.html", {"reps": reps})


@user_passes_test(_is_admin)
def rep_edit(request, pk=None):
    instance = get_object_or_404(User, pk=pk) if pk else None
    if request.method == "POST":
        form = SalesRepForm(request.POST, instance=instance)
        if form.is_valid():
            is_new = instance is None
            user = form.save(commit=False)
            if is_new:
                user.role = User.Role.SALESREP
                if not form.cleaned_data.get("password"):
                    messages.error(request, "Password is required for a new sales representative.")
                    return render(request, "admin_dash/rep_form.html", {"form": form})
                user.set_password(form.cleaned_data["password"])
            user.save()
            log_action(request.user, "USER_CHANGE", f"Saved user {user.username}")
            messages.success(request, f"Saved sales representative '{user.username}'.")
            return redirect("accounts:rep_list")
    else:
        form = SalesRepForm(instance=instance)
    return render(request, "admin_dash/rep_form.html", {"form": form, "instance": instance})
