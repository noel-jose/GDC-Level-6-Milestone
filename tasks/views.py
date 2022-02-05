# Add your Views Here

from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView
from django.core.exceptions import ValidationError
from django.forms import ModelForm
from django.http import HttpResponse, HttpResponseRedirect, request
from django.shortcuts import render
from django.views import View
from django.views.generic import ListView
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, DeleteView, UpdateView

from django.db import transaction

from tasks.models import Task


class AuthorisedTaskManager(LoginRequiredMixin):
    def get_queryset(self):
        return Task.objects.filter(deleted=False, user=self.request.user)


class PrioirtyValidation(AuthorisedTaskManager):
    def validate_priority(self, object):
        # getting priority of the task to be created
        current_priority = object.priority
        # checking if a task with the priority exists in the db
        if Task.objects.filter(
            user=self.request.user,
            deleted=False,
            completed=False,
            priority=current_priority,
        ).exists():

            # getting all the tasks from db that are not deleted,not completed and of this user
            tasks = (
                Task.objects.select_for_update()
                .filter(user=self.request.user, deleted=False, completed=False)
                .order_by("priority")
            )
            # a dictinary to hold id and the new priority of the task
            tasks_to_be_updated = {}

            # adding the tasks whose values are to be modified to the dictionary with their new priority
            for task in tasks:
                if task.priority == current_priority:
                    tasks_to_be_updated[task.id] = current_priority + 1
                    current_priority = current_priority + 1

            # updating the priority of the tasks in an atomic manner
            with transaction.atomic():
                for key in tasks_to_be_updated:
                    Task.objects.filter(id=key).update(
                        priority=tasks_to_be_updated[key]
                    )

    def form_valid(self, form):
        """If the form is valid, save the associated model."""
        self.object = form.save()
        self.object.user = self.request.user
        self.validate_priority(self.object)
        self.object.save()
        return HttpResponseRedirect(self.get_success_url())


class CustomUserCreationForm(UserCreationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].widget.attrs.update(
            {"class": "p-2 bg-slate-100 rounded-md outline-0", "size": 39}
        )
        self.fields["password1"].widget.attrs.update(
            {"class": "p-2 bg-slate-100 rounded-md outline-0", "size": 40}
        )
        self.fields["password2"].widget.attrs.update(
            {"class": "p-2 bg-slate-100 rounded-md outline-0", "size": 40}
        )


class CustomUserAuthenticationForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].widget.attrs.update(
            {"class": "p-2 bg-slate-100 rounded-md outline-0", "size": 39}
        )
        self.fields["password"].widget.attrs.update(
            {"class": "p-2 bg-slate-100 rounded-md outline-0", "size": 40}
        )


class UserLoginView(LoginView):
    form_class = CustomUserAuthenticationForm
    template_name = "user_login.html"


class UserCreateView(CreateView):
    form_class = CustomUserCreationForm
    template_name = "user_create.html"
    success_url = "/user/login"


def session_storage_view(request):
    total_views = request.session.get("total_views", 0)
    age = request.session.get_session_cookie_age()
    request.session["total_views"] = total_views + 1
    return HttpResponse(
        f"Total views is { total_views } { age } and the user is { request.user.is_authenticated }"
    )


class GenericTaskCompleteView(AuthorisedTaskManager, DeleteView):
    model = Task
    template_name = "task_complete.html"

    def form_valid(self, form):
        self.object.completed = not (self.object.completed)
        self.object.save()
        return HttpResponseRedirect("/tasks")


class GenericTaskDeleteView(AuthorisedTaskManager, DeleteView):
    model = Task
    template_name = "task_delete.html"
    success_url = "/tasks"


class GenericTaskDetailView(AuthorisedTaskManager, DetailView):
    model = Task
    template_name = "task_detail.html"


class TaskCreateForm(ModelForm):
    def clean_title(self):
        title = self.cleaned_data["title"]
        if len(title) < 5:
            raise ValidationError("Title too small")
        return title

    def clean_priority(self):
        priority = self.cleaned_data.get("priority")
        if priority <= 0:
            raise ValidationError("Priority should be greater than 0")
        return priority

    class Meta:
        model = Task
        fields = ["title", "description", "priority", "completed"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["title"].widget.attrs.update(
            {"class": "p-2 bg-slate-100 rounded-md outline-0", "size": 39}
        )
        self.fields["description"].widget.attrs.update(
            {"class": "p-2 bg-slate-100 rounded-md outline-0", "size": 40}
        )
        self.fields["priority"].widget.attrs.update(
            {
                "class": "p-2 bg-slate-100 rounded-md outline-0",
                "size": 40,
            }
        )


class GenericTaskUpdateView(PrioirtyValidation, UpdateView):
    model = Task
    form_class = TaskCreateForm
    template_name = "task_update.html"
    success_url = "/tasks"


class GenericTaskCreateView(PrioirtyValidation, CreateView):
    form_class = TaskCreateForm
    template_name = "task_create.html"
    success_url = "/tasks"


class GenericTaskView(LoginRequiredMixin, ListView):

    template_name = "task.html"
    context_object_name = "tasks"
    # extra_context = "context"

    # def get_context_data(self):
    #     user_name = self.request.user
    #     completed = Task.objects.filter(deleted=False, completed=True)
    #     total = Task.objects.filter(deleted=False, completed=False)
    #     context = {
    #         "user_name": user_name,
    #         "completed": completed.count,
    #         "total": total.count,
    #     }
    #     return context

    def get_queryset(self):
        search_term = self.request.GET.get("search")
        tasks = Task.objects.filter(
            completed=False, deleted=False, user=self.request.user
        ).order_by("priority")
        if search_term:
            tasks = tasks.filter(title__icontains=search_term)
        return tasks


class GenericCompletedTaskView(LoginRequiredMixin, ListView):
    template_name = "completed.html"
    context_object_name = "tasks"

    def get_queryset(self):
        tasks = Task.objects.filter(
            completed=True, deleted=False, user=self.request.user
        )
        return tasks


class GenericAllTaskView(LoginRequiredMixin, ListView):
    template_name = "all.html"
    context_object_name = "alltasks"

    def get_queryset(self):
        pending = Task.objects.filter(
            user=self.request.user, completed=False, deleted=False
        )
        completed = Task.objects.filter(
            user=self.request.user, completed=True, deleted=False
        )
        name = self.request.user
        completed_count = completed.count()
        total_count = Task.objects.filter(user=self.request.user, deleted=False).count()
        alltasks = {
            "pending": pending,
            "completed": completed,
            "name": name,
            "completed_count": completed_count,
            "total_count": total_count,
        }
        return alltasks
