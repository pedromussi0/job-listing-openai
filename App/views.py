from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from .forms import JobListingForm
from .langchain_integration import *
from .models import *
from django.contrib.auth.views import LoginView
from django.urls import reverse_lazy
from django.shortcuts import redirect
from django.views.decorators.cache import cache_control


@login_required()
def create_job_listing(request):
    if request.method == 'POST':
        form = JobListingForm(request.POST)
        if form.is_valid():
            # Get the logged-in user
            creator = request.user

            # Assign the logged-in user as the creator to the session
            request.session['creator'] = creator.id

            # get job position and save it in the session so it's converted later to 'job_title from model'
            job_position = form.cleaned_data['job_position']
            request.session['job_position'] = job_position

            # get tech stack and assign it to the filtering function so that only technical words are passed in the form
            tech_stack = form.cleaned_data['tech_stack']
            request.session['tech_stack'] = filter_tech_stack(tech_stack)

            company_name = form.cleaned_data['company_name']
            company_values = form.cleaned_data['company_values']

            # Assign the logged-in user as the creator

            # Pass user input as input variables to generate_job_listing function
            job_listing = generate_job_listing(
                job_position=job_position,
                tech_stack=tech_stack,
                company_name=company_name,
                company_values=company_values
            )

            return render(request, 'App/create.html', {'job_listing': job_listing})
    else:
        form = JobListingForm()

    return render(request, 'App/create.html', {'form': form})


def save_textarea(request):
    if request.method == 'POST':
        content = request.POST.get('textarea_content')
        job_position = request.session.get('job_position')
        creator_id = request.session.get('creator')

        if content and job_position and creator_id:
            creator = User.objects.get(id=creator_id)
            instance = JobListing(
                job_title=job_position,
                description=summarize_job_listing(job_listing=content),
                job_listing=content,
                creator=creator
            )
            instance.save()

    return redirect(create_job_listing)


@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def job_listings(request):
    listings = JobListing.objects.filter(creator=request.user)
    return render(request, 'App/listings.html', {'listings': listings})


# ------------------------------- login and register views ----------------------------------------------------------

def register_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')
    else:
        form = CustomUserCreationForm()

    return render(request, 'App/register.html', {'form': form})


class CustomLoginView(LoginView):
    template_name = 'App/login.html'

    def get_success_url(self):
        return reverse_lazy('create_job_listing')
