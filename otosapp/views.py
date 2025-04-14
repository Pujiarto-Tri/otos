import json
from django.contrib import messages
from django.forms import inlineformset_factory
from django.utils import timezone
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required, user_passes_test
from otosapp.models import Choice, User, Role, Category, Question, Test, Answer
from .forms import CustomUserCreationForm, UserUpdateForm, CategoryUpdateForm, CategoryCreationForm, QuestionForm, ChoiceFormSet
from .decorators import admin_required, admin_or_teacher_required, students_required
from django.db import transaction
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger


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
    users_list = User.objects.all().order_by('-date_joined')
    paginator = Paginator(users_list, 10)  # Show 10 users per page
    
    page = request.GET.get('page')
    try:
        users = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page
        users = paginator.page(1)
    except EmptyPage:
        # If page is out of range, deliver last page of results
        users = paginator.page(paginator.num_pages)
        
    return render(request, 'admin/manage_user/user_list.html', {
        'users': users,
        'paginator': paginator
    })
    

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
    categories_list = Category.objects.all()
    paginator = Paginator(categories_list, 10)  # Show 10 categories per page
    
    page = request.GET.get('page')
    try:
        categories = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page
        categories = paginator.page(1)
    except EmptyPage:
        # If page is out of range, deliver last page of results
        categories = paginator.page(paginator.num_pages)
        
    form = CategoryCreationForm()
    return render(request, 'admin/manage_categories/category_list.html', {
        'categories': categories,
        'form': form,
        'paginator': paginator
    })

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
def question_list(request):
    questions_list = Question.objects.all().order_by('-pub_date')
    paginator = Paginator(questions_list, 10)  # Show 10 questions per page
    
    page = request.GET.get('page')
    try:
        questions = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page
        questions = paginator.page(1)
    except EmptyPage:
        # If page is out of range, deliver last page of results
        questions = paginator.page(paginator.num_pages)
        
    return render(request, 'admin/manage_questions/question_list.html', {
        'questions': questions,
        'paginator': paginator
    })

@login_required
@admin_or_teacher_required
def question_create(request):
    if request.method == 'POST':
        form = QuestionForm(request.POST)
        formset = ChoiceFormSet(request.POST, prefix='choices')
        
        if form.is_valid() and formset.is_valid():
            question = form.save(commit=False)
            question.created_by = request.user
            question.save()
            
            choices = formset.save(commit=False)
            for choice in choices:
                choice.question = question
                choice.save()
            
            messages.success(request, 'Question created successfully!')
            return redirect('question_list')
    else:
        form = QuestionForm()
        formset = ChoiceFormSet(prefix='choices')
    
    return render(request, 'admin/manage_questions/question_create.html', {
        'form': form,
        'formset': formset,
        'categories': Category.objects.all()
    })

@login_required
@admin_or_teacher_required
def question_update(request, question_id):
    question = get_object_or_404(Question, id=question_id)
    
    if request.method == 'POST':
        form = QuestionForm(request.POST, instance=question)
        ChoiceFormSet = inlineformset_factory(
            Question, Choice,
            fields=('choice_text', 'is_correct'),
            extra=0, can_delete=True,
            min_num=2, validate_min=True
        )
        formset = ChoiceFormSet(request.POST, instance=question, prefix='choice_set')
        
        if form.is_valid() and formset.is_valid():
            with transaction.atomic():
                question = form.save()
                formset.save()
                messages.success(request, 'Question updated successfully!')
                return redirect('question_list')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = QuestionForm(instance=question)
        ChoiceFormSet = inlineformset_factory(
            Question, Choice,
            fields=('choice_text', 'is_correct'),
            extra=0, can_delete=True,
            min_num=2, validate_min=True
        )
        formset = ChoiceFormSet(instance=question, prefix='choice_set')

    return render(request, 'admin/manage_questions/question_update.html', {
        'form': form,
        'formset': formset,
        'question': question
    })

@login_required
@admin_or_teacher_required
def question_delete(request, question_id):
    question = get_object_or_404(Question, id=question_id)
    if request.method == 'POST':
        question.delete()
        return redirect('question_list')
    return render(request, {'question': question})



##STUDENTS##

@login_required
@students_required
def tryout_list(request):
    tryout_list = Category.objects.all() 
    return render(request, 'students/tryouts/tryout_list.html', {'tryout': tryout_list})

@login_required
@students_required
def take_test(request, category_id, question):
    category = get_object_or_404(Category, id=category_id)
    questions = Question.objects.filter(category=category)

    # Get the current question index from the request
    current_question_index = question

    # Initialize a set to track answered questions
    answered_questions = set(request.session.get('answered_questions', []))

    if request.method == 'POST':
        # Process the answer for the current question
        choice_id = request.POST.get('answer')
        if choice_id:
            test = Test.objects.create(student=request.user)
            question_instance = get_object_or_404(Question, id=questions[current_question_index].id)
            choice = get_object_or_404(Choice, id=choice_id)
            Answer.objects.create(test=test, question=question_instance, selected_choice=choice)

            # Mark the question as answered
            answered_questions.add(question_instance.id)
            request.session['answered_questions'] = list(answered_questions)

            # Redirect to the next question
            next_question_index = current_question_index + 1
            if next_question_index < len(questions):
                return redirect('take_test', category_id=category_id, question=next_question_index)
            else:
                # Redirect to results or completion page
                return redirect('test_results', test_id=test.id)

    # Get the current question
    current_question = questions[current_question_index] if questions else None

    return render(request, 'students/tests/take_test.html', {
        'category': category,
        'question': current_question,
        'current_question_index': current_question_index,
        'questions': questions,
        'answered_questions': answered_questions,
    })

@login_required
@students_required
def test_results(request, test_id):
    test = get_object_or_404(Test, id=test_id)
    return render(request, 'students/tests/test_results.html', {'test': test})


