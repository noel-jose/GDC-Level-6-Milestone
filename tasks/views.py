# Add your Views Here

from django.contrib.auth.forms import UserCreationForm
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

from tasks.models import Task


class AuthorisedTaskManager(LoginRequiredMixin):
    def get_queryset(self):
        return Task.objects.filter(deleted=False, user=self.request.user)


class UserLoginView(LoginView):
    template_name = "user_login.html"


class UserCreateView(CreateView):
    form_class = UserCreationForm
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
        return title.upper()

    # def clean_priority(self):
    #     priority = self.cleaned_data["priority"]
    #     if priority <= 0:
    #         raise ValidationError("Priority should be greater than 0")

    class Meta:
        model = Task
        fields = ["title", "description", "completed", "priority"]


class GenericTaskUpdateView(AuthorisedTaskManager, UpdateView):
    model = Task
    form_class = TaskCreateForm
    template_name = "task_update.html"
    success_url = "/tasks"


class GenericTaskCreateView(LoginRequiredMixin, CreateView):
    form_class = TaskCreateForm
    template_name = "task_create.html"
    success_url = "/tasks"

    def validate_priority(self, object):
        # to check if the current submitted task will meet the constraint of priority
        current_priority = object.priority  # fetched the priority of the current task
        tasks = Task.objects.filter(
            user=self.request.user, completed=False, deleted=False
        )  # fetched the tasks from the query set
        if tasks.filter(priority=current_priority).exists():
            task = tasks.get(priority=current_priority)
            while tasks.filter(priority=current_priority).exists():
                current_priority += 1
                if tasks.filter(priority=current_priority).exists():
                    temp = tasks.get(priority=current_priority)
                    task.priority = task.priority + 1
                    task.save()
                    task = temp
                else:
                    task.priority = task.priority + 1
                    task.save()

    def form_valid(self, form):
        """If the form is valid, save the associated model."""
        self.object = form.save()
        self.object.user = self.request.user
        self.validate_priority(self.object)
        self.object.save()
        return HttpResponseRedirect(self.get_success_url())


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
        alltasks = {"pending": pending, "completed": completed}
        return alltasks
