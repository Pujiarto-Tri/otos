from django.contrib import messages
from django.forms import inlineformset_factory
from django.utils import timezone
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from otosapp.models import Choice, User, Role, Category, Question
from .forms import CustomUserCreationForm, UserUpdateForm, CategoryUpdateForm, CategoryCreationForm, QuestionCreationForm, QuestionUpdateForm, ChoiceFormSet
from .decorators import admin_required, admin_or_teacher_required
from django.http import HttpResponse

def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)  # Log the user in after successful registration
            return redirect('home')  # Redirect to home or another page
    else:
        form = CustomUserCreationForm()
    return render(request, 'registration/register.html', {'form': form})

##User View##

@login_required
@admin_required
def user_list(request):
    users = User.objects.all().order_by('-date_joined')
    return render(request, 'admin/manage_user/user_list.html', {'users': users})

@login_required
@admin_required
def user_create(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('user_list')
    else:
        form = CustomUserCreationForm()
    return render(request, 'admin/manage_user/user_form.html', {'form': form, 'title': 'Add New User'})

@login_required
@admin_required
def user_update(request, user_id):
    user = get_object_or_404(User, id=user_id)
    if request.method == 'POST':
        form = UserUpdateForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            return redirect('user_list')
    else:
        form = UserUpdateForm(instance=user)
    return render(request, 'admin/manage_user/user_form.html', {'form': form, 'title': 'Edit User'})

@login_required
@admin_required
def user_delete(request, user_id):
    user = get_object_or_404(User, id=user_id)
    if request.method == 'POST':
        user.delete()
        return redirect('user_list')
    return render(request, 'admin/manage_user/user_confirm_delete.html', {'user': user})


##Category View##

@login_required
@admin_required
def category_create(request):
    if request.method == 'POST':
        form = CategoryCreationForm(request.POST)
        if form.is_valid():
            form.save() 
            return redirect('category_list')
    else:
        form = CategoryCreationForm()
    return render(request, {'form': form, 'title': 'Add New Category'})

@login_required
@admin_required
def category_list(request):
    form = CategoryCreationForm()
    categories = Category.objects.all()
    return render(request, 'admin/manage_categories/category_list.html', {'categories': categories, 'form': form})

@login_required
@admin_required
def category_update(request, category_id):
    category = get_object_or_404(Category, id=category_id)
    if request.method == 'POST':
        form = CategoryUpdateForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            return redirect('category_list')
    else:
        form = CategoryUpdateForm(instance=category)
    return render(request, None, {'form': form, 'category_id': category_id})

@login_required
@admin_required
def category_delete(request, category_id):
    category = get_object_or_404(Category, id=category_id)
    if request.method == 'POST':
        category.delete()
        return redirect('category_list')
    return render(request, {'category': category})



##Question View##

@login_required
@admin_or_teacher_required
def question_create(request):
    if request.method == 'POST':
        form = QuestionCreationForm(request.POST)
        formset = ChoiceFormSet(request.POST, instance=Question())
        
        if form.is_valid() and formset.is_valid():
            question = form.save(commit=False)
            question.pub_date = timezone.now()
            question.save()
            
            # Save the formset with the question instance
            formset.instance = question
            formset.save()
            
            messages.success(request, 'Question created successfully!')
            return redirect('question_list')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = QuestionCreationForm()
        formset = ChoiceFormSet(instance=Question())

    return render(request, 'admin/manage_questions/question_list.html', {
        'form': form,
        'formset': formset,
        'title': 'Add New Question'
    })

@login_required
@admin_or_teacher_required
def question_list(request):
    form = QuestionCreationForm()
    questions = Question.objects.all()
    return render(request, 'admin/manage_questions/question_list.html', {'questions': questions, 'form': form})

# @login_required
# @admin_or_teacher_required
# def question_update(request, question_id):
#     question = get_object_or_404(Category, id=question_id)
#     if request.method == 'POST':
#         form = QuestionUpdateForm(request.POST, instance=question)
#         if form.is_valid():
#             form.save()
#             return redirect('question_list')
#     else:
#         form = QuestionUpdateForm(instance=question)
#     return render(request, None, {'form': form, 'question_id': question_id})

@login_required
@admin_or_teacher_required
def question_update(request, question_id):
    question = get_object_or_404(Question, id=question_id)  # Correct model

    if request.method == 'POST':
        form = QuestionUpdateForm(request.POST, instance=question)
        formset = ChoiceFormSet(request.POST, instance=Question())

        if form.is_valid() and formset.is_valid():
            form.save()
            formset.save()
            messages.success(request, 'Question updated successfully!')
            return redirect('question_list')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = QuestionUpdateForm()
        formset = ChoiceFormSet(instance=Question())

    return render(request, {
        'form': form,
        'formset': formset,
        'question_id': question_id,
        'title': 'Edit Question'
    })

@login_required
@admin_or_teacher_required
def question_delete(request, question_id):
    question = get_object_or_404(Question, id=question_id)
    if request.method == 'POST':
        question.delete()
        return redirect('question_list')
    return render(request, {'question': question})