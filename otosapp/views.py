from django.contrib import messages
from django.forms import inlineformset_factory
from django.utils import timezone
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required, user_passes_test
from otosapp.models import Choice, User, Role, Category, Question, Test, Answer, MessageThread, Message
from .forms import CustomUserCreationForm, UserUpdateForm, CategoryUpdateForm, CategoryCreationForm, QuestionForm, ChoiceFormSet
from .decorators import admin_required, admin_or_teacher_required, students_required
from django.db import transaction
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Count, Avg, Max, Q
import json


def home(request):
    context = {}
    
    if request.user.is_authenticated:
        if hasattr(request.user, 'role') and request.user.role and request.user.role.role_name == 'Student':
            # Data untuk student dashboard - hanya test yang sudah submitted
            user_tests = Test.objects.filter(student=request.user, is_submitted=True).order_by('-date_taken')
            
            # Check for ongoing test (not submitted and not timed out)
            ongoing_test = Test.objects.filter(
                student=request.user, 
                is_submitted=False
            ).first()
            
            # If ongoing test exists, check if it's still valid (not timed out)
            if ongoing_test:
                if ongoing_test.is_time_up():
                    # Auto-submit expired test
                    ongoing_test.is_submitted = True
                    ongoing_test.end_time = timezone.now()
                    ongoing_test.calculate_score()
                    ongoing_test.save()
                    ongoing_test = None  # Clear ongoing test
                elif not ongoing_test.start_time:
                    # If no start_time, this test is invalid, remove it
                    ongoing_test = None
            
            # Statistik untuk student
            total_tests = user_tests.count()
            completed_tests = user_tests.filter(score__gt=0).count()
            
            # Rata-rata skor - deteksi format berdasarkan nilai maksimum
            avg_score_raw = user_tests.aggregate(avg_score=Avg('score'))['avg_score'] or 0
            max_score_in_data = user_tests.aggregate(max_score=Max('score'))['max_score'] or 0
            
            # Jika skor maksimum <= 1, maka format adalah 0-1, konversi ke persen
            # Jika skor maksimum > 1, maka sudah dalam format persen
            if max_score_in_data <= 1:
                avg_score = avg_score_raw * 100
                highest_score = max_score_in_data * 100
            else:
                avg_score = avg_score_raw
                highest_score = max_score_in_data
            
            # Test terbaru (maksimal 5)
            recent_tests = user_tests[:5]
            
            # Kategori yang paling sering dikerjakan - berdasarkan test yang sudah submitted
            popular_categories = []
            if user_tests.exists():
                categories_data = {}
                for test in user_tests:
                    # Get categories from test.categories many-to-many field
                    for category in test.categories.all():
                        category_name = category.category_name
                        if category_name in categories_data:
                            categories_data[category_name] += 1
                        else:
                            categories_data[category_name] = 1
                
                # Convert to list dan sort
                popular_categories = [
                    {'category_name': name, 'count': count} 
                    for name, count in sorted(categories_data.items(), key=lambda x: x[1], reverse=True)[:3]
                ]
            
            context.update({
                'user_tests': recent_tests,
                'total_tests': total_tests,
                'completed_tests': completed_tests,
                'avg_score': round(avg_score, 1),
                'highest_score': round(highest_score, 1),
                'popular_categories': popular_categories,
                'ongoing_test': ongoing_test,
            })
        
        # Data users untuk admin (jika diperlukan)
        if request.user.is_superuser or (hasattr(request.user, 'role') and request.user.role and request.user.role.role_name == 'Admin'):
            context['users'] = User.objects.all()[:10]
    
    return render(request, 'home.html', context)


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
    
    # Add scoring status info for each category
    for category in categories:
        if category.scoring_method == 'custom':
            total_points = category.get_total_custom_points()
            category.scoring_status = {
                'complete': category.is_custom_scoring_complete(),
                'total_points': total_points
            }
        else:
            category.scoring_status = {'complete': True, 'total_points': 100}
        
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
            old_scoring_method = Category.objects.get(id=category_id).scoring_method
            new_category = form.save()
            
            # Check custom scoring validation
            if new_category.scoring_method == 'custom':
                if not new_category.is_custom_scoring_complete():
                    total_points = new_category.get_total_custom_points()
                    messages.warning(
                        request, 
                        f'Warning: Custom scoring incomplete! Total points: {total_points}/100. Please update question weights.'
                    )
            
            # Update UTBK coefficients if switching to UTBK method
            if new_category.scoring_method == 'utbk' and old_scoring_method != 'utbk':
                Test.update_utbk_difficulty_coefficients(category_id)
                messages.info(request, 'UTBK difficulty coefficients have been calculated based on existing data.')
            
            return redirect('category_list')
    else:
        form = CategoryUpdateForm(instance=category)
    
    # Add warnings for current category
    warnings = []
    if category.scoring_method == 'custom' and not category.is_custom_scoring_complete():
        total_points = category.get_total_custom_points()
        warnings.append(f'Custom scoring incomplete! Total points: {total_points}/100')
    
    context = {
        'form': form, 
        'category_id': category_id,
        'category': category,
        'warnings': warnings
    }
    return render(request, 'admin/manage_categories/category_form.html', context)

@login_required
@admin_required
def category_delete(request, category_id):
    category = get_object_or_404(Category, id=category_id)
    if request.method == 'POST':
        category.delete()
        return redirect('category_list')
    return render(request, {'category': category})

@login_required
@admin_required
def update_utbk_coefficients(request, category_id):
    """Manually update UTBK difficulty coefficients for a category"""
    category = get_object_or_404(Category, id=category_id)
    
    if category.scoring_method != 'utbk':
        messages.error(request, f'Category "{category.category_name}" is not using UTBK scoring method.')
    else:
        Test.update_utbk_difficulty_coefficients(category_id)
        messages.success(request, f'UTBK difficulty coefficients updated for "{category.category_name}".')
    
    return redirect('category_list')



##Question View##

@login_required
@admin_or_teacher_required
def question_list(request):
    """Display category selection page for questions"""
    categories = Category.objects.all().order_by('category_name')
    
    # Add question count and scoring status for each category
    for category in categories:
        category.question_count = category.question_set.count()
        if category.scoring_method == 'custom':
            total_points = category.get_total_custom_points()
            category.scoring_status = {
                'complete': category.is_custom_scoring_complete(),
                'total_points': total_points
            }
        else:
            category.scoring_status = {'complete': True, 'total_points': 100}
    
    return render(request, 'admin/manage_questions/category_selection.html', {
        'categories': categories
    })

@login_required
@admin_or_teacher_required
def question_list_by_category(request, category_id):
    """Display questions filtered by category"""
    category = get_object_or_404(Category, id=category_id)
    questions_list = Question.objects.filter(category=category).order_by('-pub_date')
    
    # Add scoring status for category
    if category.scoring_method == 'custom':
        total_points = category.get_total_custom_points()
        category.scoring_status = {
            'complete': category.is_custom_scoring_complete(),
            'total_points': total_points
        }
    else:
        category.scoring_status = {'complete': True, 'total_points': 100}
    
    paginator = Paginator(questions_list, 15)  # Show 15 questions per page
    
    page = request.GET.get('page')
    try:
        questions = paginator.page(page)
    except PageNotAnInteger:
        questions = paginator.page(1)
    except EmptyPage:
        questions = paginator.page(paginator.num_pages)
        
    return render(request, 'admin/manage_questions/question_list.html', {
        'questions': questions,
        'category': category,
        'paginator': paginator
    })

@login_required
@admin_or_teacher_required
def question_create(request):
    # Pre-select category from URL parameter
    category_id = request.GET.get('category')
    initial_category = None
    if category_id:
        try:
            initial_category = Category.objects.get(id=category_id)
        except Category.DoesNotExist:
            pass
    
    if request.method == 'POST':
        form = QuestionForm(request.POST)
        formset = ChoiceFormSet(request.POST, prefix='choices')
        
        if form.is_valid() and formset.is_valid():
            question = form.save(commit=False)
            if hasattr(request.user, 'created_by'):
                question.created_by = request.user
            question.save()
            
            choices = formset.save(commit=False)
            for choice in choices:
                choice.question = question
                choice.save()
            
            messages.success(request, 'Question created successfully!')
            
            # Redirect to category-specific question list if came from there
            if question.category:
                return redirect('question_list_by_category', category_id=question.category.id)
            return redirect('question_list')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = QuestionForm()
        formset = ChoiceFormSet(prefix='choices')
        
        # Set initial category if provided
        if initial_category:
            form.fields['category'].initial = initial_category
    
    return render(request, 'admin/manage_questions/question_form.html', {
        'form': form,
        'formset': formset,
        'title': 'Add New Question'
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
        'question': question,
        'title': 'Update Question'
    })

@login_required
@admin_or_teacher_required
def question_delete(request, question_id):
    question = get_object_or_404(Question, id=question_id)
    category_id = question.category.id  # Store category ID before deletion
    
    if request.method == 'POST':
        question.delete()
        messages.success(request, 'Question deleted successfully!')
        return redirect('question_list_by_category', category_id=category_id)
    
    return render(request, 'admin/manage_questions/question_confirm_delete.html', {
        'question': question
    })

@login_required
@admin_required
def update_utbk_coefficients(request, category_id):
    """Update UTBK difficulty coefficients for a category"""
    category = get_object_or_404(Category, id=category_id)
    
    if category.scoring_method != 'utbk':
        messages.error(request, f'Category "{category.category_name}" is not using UTBK scoring method.')
        return redirect('question_list_by_category', category_id=category_id)
    
    try:
        # Update coefficients
        Test.update_utbk_difficulty_coefficients(category_id)
        
        # Count questions updated
        question_count = category.question_set.count()
        
        if question_count > 0:
            messages.success(
                request, 
                f'Successfully updated UTBK difficulty coefficients for {question_count} questions in "{category.category_name}".'
            )
        else:
            messages.warning(
                request, 
                f'No questions found in "{category.category_name}" to update coefficients.'
            )
            
    except Exception as e:
        messages.error(request, f'Error updating UTBK coefficients: {str(e)}')
    
    return redirect('question_list_by_category', category_id=category_id)



##STUDENTS##

@login_required
@students_required
def tryout_list(request):
    # Check if there's an ongoing test
    ongoing_test = Test.objects.filter(
        student=request.user, 
        is_submitted=False
    ).first()
    
    if ongoing_test:
        # Check if test is still valid (not timed out)
        if ongoing_test.is_time_up():
            # Auto-submit expired test
            ongoing_test.is_submitted = True
            ongoing_test.end_time = timezone.now()
            ongoing_test.calculate_score()
            ongoing_test.save()
        else:
            # Redirect to ongoing test
            category = ongoing_test.categories.first()
            if category:
                # Get current question index from session or start from 0
                session_key = f'test_session_{category.id}_{request.user.id}'
                current_question_index = 0
                
                if session_key in request.session:
                    # Get last answered question index
                    answered_questions = request.session[session_key].get('answered_questions', {})
                    if answered_questions:
                        # Find the next unanswered question
                        questions = Question.objects.filter(category=category)
                        for i, question in enumerate(questions):
                            if question.id not in answered_questions:
                                current_question_index = i
                                break
                        else:
                            # All questions answered, go to last question
                            current_question_index = len(questions) - 1 if questions else 0
                
                return redirect('take_test', category_id=category.id, question=current_question_index)
    
    # Clean up any unsubmitted test sessions for this user
    # This prevents issues when student starts a new test
    session_keys_to_remove = []
    for key in request.session.keys():
        if key.startswith(f'test_session_') and key.endswith(f'_{request.user.id}'):
            # Check if there's an associated unsubmitted test
            session_data = request.session[key]
            if 'test_id' in session_data:
                try:
                    test = Test.objects.get(id=session_data['test_id'])
                    # If test is submitted or time is up, remove session
                    if test.is_submitted or test.is_time_up():
                        session_keys_to_remove.append(key)
                except Test.DoesNotExist:
                    # Test doesn't exist, remove session
                    session_keys_to_remove.append(key)
    
    # Remove invalid sessions
    for key in session_keys_to_remove:
        if key in request.session:
            del request.session[key]
    
    tryout_list = Category.objects.all() 
    return render(request, 'students/tryouts/tryout_list.html', {'tryout': tryout_list})

@login_required
@students_required
def take_test(request, category_id, question):
    from django.utils import timezone
    
    category = get_object_or_404(Category, id=category_id)
    questions = Question.objects.filter(category=category)

    # Get the current question index from the request
    current_question_index = question

    # Get or create a unique session key for this test session
    session_key = f'test_session_{category_id}_{request.user.id}'
    
    # Check if there's an existing unsubmitted test for this category and user
    existing_test = Test.objects.filter(
        student=request.user,
        is_submitted=False,
        categories=category
    ).first()
    
    # Initialize test session if not exists OR if existing test is submitted
    if session_key not in request.session or existing_test is None:
        # Clear any old session data
        if session_key in request.session:
            del request.session[session_key]
            
        # Create a new test instance for this session
        test = Test.objects.create(
            student=request.user,
            start_time=timezone.now(),
            time_limit=category.time_limit
        )
        # Connect test to category
        test.categories.add(category)
        
        request.session[session_key] = {
            'test_id': test.id,
            'answered_questions': {},  # question_id: choice_id
            'category_id': category_id
        }
    else:
        test_session = request.session[session_key]
        test = get_object_or_404(Test, id=test_session['test_id'])
        
        # Ensure test is connected to category
        if not test.categories.filter(id=category_id).exists():
            test.categories.add(category)
        
        # Set start_time if not set
        if not test.start_time:
            test.start_time = timezone.now()
            test.time_limit = category.time_limit
            test.save()
    
    test_session = request.session[session_key]
    
    # Check if time is up or test is already submitted
    if test.is_time_up() or test.is_submitted:
        if not test.is_submitted:
            # Time is up, auto-submit
            test.is_submitted = True
            test.end_time = timezone.now()
            test.calculate_score()
            test.save()
            
        # Clear session
        if session_key in request.session:
            del request.session[session_key]
            
        return redirect('test_results', test_id=test.id)
    
    # Get existing answers for this test
    existing_answers = Answer.objects.filter(test=test).select_related('question', 'selected_choice')
    answered_questions_dict = {answer.question.id: answer.selected_choice.id for answer in existing_answers}
    
    # Update session with existing answers
    test_session['answered_questions'] = answered_questions_dict
    request.session[session_key] = test_session

    if request.method == 'POST':
        # Process the answer for the current question
        choice_id = request.POST.get('answer')
        question_instance = get_object_or_404(Question, id=questions[current_question_index].id)
        
        # Check if this is an AJAX request (for saving answers without navigation)
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        
        if choice_id:
            # Soal dijawab - simpan jawaban
            choice = get_object_or_404(Choice, id=choice_id)
            
            # Check if answer already exists for this question
            existing_answer = Answer.objects.filter(test=test, question=question_instance).first()
            if existing_answer:
                # Update existing answer
                existing_answer.selected_choice = choice
                existing_answer.save()
            else:
                # Create new answer
                Answer.objects.create(test=test, question=question_instance, selected_choice=choice)

            # Update session
            test_session['answered_questions'][question_instance.id] = int(choice_id)
            request.session[session_key] = test_session
            
            # If this is an AJAX request, return JSON response
            if is_ajax:
                return JsonResponse({'status': 'success', 'message': 'Answer saved'})
        else:
            # Soal tidak dijawab - hapus jawaban jika ada
            existing_answer = Answer.objects.filter(test=test, question=question_instance).first()
            if existing_answer:
                existing_answer.delete()
            
            # Remove from session if exists
            if question_instance.id in test_session['answered_questions']:
                del test_session['answered_questions'][question_instance.id]
                request.session[session_key] = test_session
            
            # If this is an AJAX request, return JSON response
            if is_ajax:
                return JsonResponse({'status': 'success', 'message': 'Answer removed'})

        # If not AJAX, continue with normal navigation
        if not is_ajax:
            # Redirect to the next question
            next_question_index = current_question_index + 1
            if next_question_index < len(questions):
                return redirect('take_test', category_id=category_id, question=next_question_index)
            else:
                # All questions answered, submit the test
                if not test.is_submitted:
                    test.is_submitted = True
                    test.end_time = timezone.now()
                    test.calculate_score()
                    test.save()
                    
                    # Clear session
                    if session_key in request.session:
                        del request.session[session_key]
                
                return redirect('test_results', test_id=test.id)

    # Get the current question
    current_question = questions[current_question_index] if questions else None
    
    # Get current question's selected answer if any
    selected_choice_id = test_session['answered_questions'].get(current_question.id) if current_question else None

    return render(request, 'students/tests/take_test.html', {
        'category': category,
        'question': current_question,
        'current_question_index': current_question_index,
        'questions': questions,
        'answered_questions': set(test_session['answered_questions'].keys()),
        'selected_choice_id': selected_choice_id,
        'test_id': test.id,
        'remaining_time': test.get_remaining_time(),
        'time_limit': test.time_limit,
    })

@login_required
@students_required
def submit_test(request, test_id):
    """Submit test manually"""
    from django.utils import timezone
    
    if request.method == 'POST':
        test = get_object_or_404(Test, id=test_id, student=request.user)
        
        if not test.is_submitted:
            test.is_submitted = True
            test.end_time = timezone.now()
            test.calculate_score()
            test.save()
            
            # Clear session - Use correct category_id from test
            test_category = test.categories.first()
            if test_category:
                session_key = f'test_session_{test_category.id}_{request.user.id}'
                if session_key in request.session:
                    del request.session[session_key]
        
        return redirect('test_results', test_id=test.id)
    
    return redirect('home')

@login_required
@students_required
def test_results(request, test_id):
    test = get_object_or_404(Test, id=test_id)
    
    # Get category from test.categories (many-to-many relationship)
    category = test.categories.first()
    
    # If no category found from test.categories, try to get from first answer (fallback)
    if not category:
        first_answer = test.answers.first()
        category = first_answer.question.category if first_answer else None
    
    # Calculate score if not already calculated
    if test.answers.exists():
        test.calculate_score()
    
    return render(request, 'students/tests/test_results.html', {
        'test': test,
        'category': category
    })

@login_required
@students_required
def test_results_detail(request, test_id):
    """Detailed test results showing each question, correct/incorrect answers, and scoring explanation"""
    test = get_object_or_404(Test, id=test_id, student=request.user)
    
    # Get category from test.categories
    category = test.categories.first()
    if not category:
        first_answer = test.answers.first()
        category = first_answer.question.category if first_answer else None
    
    # Calculate score if not already calculated
    if test.answers.exists():
        test.calculate_score()
    
    # Get all questions and answers with detailed information
    answers = test.answers.select_related('question', 'selected_choice').prefetch_related('question__choices')
    
    # Create detailed results for each question
    question_results = []
    correct_count = 0
    total_score_earned = 0
    total_possible_score = 0
    
    for answer in answers:
        question = answer.question
        selected_choice = answer.selected_choice
        correct_choice = question.choices.filter(is_correct=True).first()
        is_correct = selected_choice.is_correct
        
        if is_correct:
            correct_count += 1
        
        # Calculate score for this question based on scoring method
        question_score = 0
        max_question_score = 0
        
        if category and category.scoring_method == 'custom':
            max_question_score = question.custom_weight
            if is_correct:
                question_score = question.custom_weight
        elif category and category.scoring_method == 'utbk':
            max_question_score = question.difficulty_coefficient
            if is_correct:
                question_score = question.difficulty_coefficient
        else:  # default scoring
            max_question_score = 100 / answers.count() if answers.count() > 0 else 0
            if is_correct:
                question_score = max_question_score
        
        total_score_earned += question_score
        total_possible_score += max_question_score
        
        question_results.append({
            'question': question,
            'selected_choice': selected_choice,
            'correct_choice': correct_choice,
            'is_correct': is_correct,
            'question_score': question_score,
            'max_question_score': max_question_score,
            'all_choices': question.choices.all()
        })
    
    # Calculate summary statistics
    total_questions = len(question_results)
    incorrect_count = total_questions - correct_count
    accuracy_percentage = (correct_count / total_questions * 100) if total_questions > 0 else 0
    
    # Get scoring method explanation
    scoring_explanation = get_scoring_explanation(category) if category else ""
    
    context = {
        'test': test,
        'category': category,
        'question_results': question_results,
        'total_questions': total_questions,
        'correct_count': correct_count,
        'incorrect_count': incorrect_count,
        'accuracy_percentage': accuracy_percentage,
        'total_score_earned': total_score_earned,
        'total_possible_score': total_possible_score,
        'scoring_explanation': scoring_explanation,
    }
    
    return render(request, 'students/tests/test_results_detail.html', context)

def get_scoring_explanation(category):
    """Get explanation for the scoring method used"""
    if not category:
        return "Tidak ada informasi sistem penilaian."
    
    if category.scoring_method == 'default':
        return f"Sistem Penilaian Default: Setiap soal memiliki bobot yang sama. Total skor dihitung dengan membagi 100 poin secara merata untuk semua soal. Jawaban benar = poin penuh, jawaban salah = 0 poin."
    
    elif category.scoring_method == 'custom':
        return f"Sistem Penilaian Custom: Setiap soal memiliki bobot berbeda sesuai tingkat kesulitan atau kepentingan. Total bobot semua soal = 100 poin. Skor akhir adalah jumlah bobot dari soal-soal yang dijawab benar."
    
    elif category.scoring_method == 'utbk':
        return f"Sistem Penilaian UTBK: Menggunakan metode penilaian berbasis tingkat kesulitan soal. Soal yang lebih sulit memiliki bobot lebih tinggi. Koefisien kesulitan dihitung berdasarkan tingkat keberhasilan siswa lain dalam menjawab soal tersebut."
    
    return "Sistem penilaian tidak diketahui."

@login_required
@students_required
def test_history(request):
    """Show all completed tests for the student with filtering and pagination"""
    # Get all tests for the current student
    tests = Test.objects.filter(
        student=request.user, 
        is_submitted=True
    ).select_related().prefetch_related('categories').order_by('-date_taken')
    
    # Get filter parameters
    category_filter = request.GET.get('category', '').strip()
    search = request.GET.get('search', '').strip()
    date_from = request.GET.get('date_from', '').strip()
    date_to = request.GET.get('date_to', '').strip()
    
    # Apply filters
    if category_filter and category_filter.isdigit():
        tests = tests.filter(categories__id=int(category_filter)).distinct()
    
    if search:
        # Search in both category name and test-related fields
        tests = tests.filter(categories__category_name__icontains=search).distinct()
    
    if date_from:
        try:
            tests = tests.filter(date_taken__date__gte=date_from)
        except (ValueError, TypeError):
            pass  # Invalid date format, skip filter
    
    if date_to:
        try:
            tests = tests.filter(date_taken__date__lte=date_to)
        except (ValueError, TypeError):
            pass  # Invalid date format, skip filter
    
    # Calculate statistics before pagination (for the filtered results)
    total_tests = tests.count()
    if total_tests > 0:
        avg_score = tests.aggregate(avg_score=Avg('score'))['avg_score'] or 0
        highest_score = tests.aggregate(max_score=Max('score'))['max_score'] or 0
        latest_test = tests.first()
    else:
        avg_score = 0
        highest_score = 0
        latest_test = None
    
    # Pagination
    paginator = Paginator(tests, 10)  # Show 10 tests per page
    page_number = request.GET.get('page', 1)
    
    try:
        page_obj = paginator.page(page_number)
    except PageNotAnInteger:
        page_obj = paginator.page(1)
    except EmptyPage:
        page_obj = paginator.page(paginator.num_pages)
    
    # Get all categories for filter dropdown (only categories that have tests)
    categories = Category.objects.filter(
        id__in=Test.objects.filter(
            student=request.user, 
            is_submitted=True
        ).values_list('categories__id', flat=True)
    ).distinct().order_by('category_name')
    
    # Get selected category name for display
    selected_category_name = None
    if category_filter and category_filter.isdigit():
        try:
            selected_category = Category.objects.get(id=int(category_filter))
            selected_category_name = selected_category.category_name
        except Category.DoesNotExist:
            pass
    
    context = {
        'page_obj': page_obj,
        'categories': categories,
        'total_tests': total_tests,
        'avg_score': avg_score,
        'highest_score': highest_score,
        'latest_test': latest_test,
        'current_category': category_filter,
        'current_category_name': selected_category_name,
        'current_search': search,
        'date_from': date_from,
        'date_to': date_to,
    }
    
    return render(request, 'students/tests/test_history.html', context)

@login_required
@students_required
def force_end_test(request, test_id):
    """Force end ongoing test"""
    if request.method == 'POST':
        test = get_object_or_404(Test, id=test_id, student=request.user, is_submitted=False)
        
        # Submit the test
        test.is_submitted = True
        test.end_time = timezone.now()
        test.calculate_score()
        test.save()
        
        # Clear session
        test_category = test.categories.first()
        if test_category:
            session_key = f'test_session_{test_category.id}_{request.user.id}'
            if session_key in request.session:
                del request.session[session_key]
        
        messages.success(request, 'Tryout telah diakhiri secara paksa. Skor dihitung berdasarkan jawaban yang telah dikerjakan.')
        return redirect('test_results', test_id=test.id)
    
    return redirect('home')

@login_required
def settings_view(request):
    from .forms import UserProfileForm, ProfilePictureForm, CustomPasswordChangeForm
    from django.contrib.auth import update_session_auth_hash
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'update_profile':
            form = UserProfileForm(request.POST, instance=request.user)
            if form.is_valid():
                form.save()
                messages.success(request, 'Profil berhasil diperbarui!')
                return redirect('settings')
            else:
                messages.error(request, 'Terjadi kesalahan saat memperbarui profil.')
                
        elif action == 'update_profile_picture':
            try:
                form = ProfilePictureForm(request.POST, request.FILES, instance=request.user)
                if form.is_valid():
                    # Get original file size for feedback
                    uploaded_file = request.FILES.get('profile_picture')
                    if uploaded_file:
                        original_size_kb = uploaded_file.size / 1024
                        form.save()
                        if original_size_kb > 250:
                            messages.success(
                                request, 
                                f'Foto profil berhasil diperbarui dan dikompres dari {original_size_kb:.0f}KB ke ukuran optimal!'
                            )
                        else:
                            messages.success(request, 'Foto profil berhasil diperbarui!')
                    else:
                        form.save()
                        messages.success(request, 'Foto profil berhasil diperbarui!')
                    return redirect('settings')
                else:
                    # Extract specific error messages
                    error_messages = []
                    for field, errors in form.errors.items():
                        for error in errors:
                            error_messages.append(error)
                    
                    if error_messages:
                        messages.error(request, ' '.join(error_messages))
                    else:
                        messages.error(request, 'Terjadi kesalahan saat mengupload foto profil.')
                        
            except Exception as e:
                messages.error(request, f'Terjadi kesalahan saat memproses foto profil: {str(e)}')
                return redirect('settings')
                
        elif action == 'change_password':
            current_password = request.POST.get('current_password')
            new_password = request.POST.get('new_password')
            confirm_password = request.POST.get('confirm_password')
            
            # Validate current password
            if not request.user.check_password(current_password):
                messages.error(request, 'Password saat ini tidak valid.')
                return redirect('settings')
            
            # Validate new password match
            if new_password != confirm_password:
                messages.error(request, 'Password baru dan konfirmasi password tidak cocok.')
                return redirect('settings')
            
            # Validate password strength
            if len(new_password) < 8:
                messages.error(request, 'Password harus minimal 8 karakter.')
                return redirect('settings')
            
            # Update password
            request.user.set_password(new_password)
            request.user.save()
            update_session_auth_hash(request, request.user)  # Keep user logged in
            messages.success(request, 'Password berhasil diubah!')
            return redirect('settings')
    
    context = {
        'user': request.user,
    }
    
    return render(request, 'settings.html', context)


# ======================= MESSAGING SYSTEM VIEWS =======================

@login_required
def message_inbox(request):
    """View untuk melihat daftar thread pesan"""
    user = request.user
    
    # Filter thread berdasarkan role user
    if user.role and user.role.role_name == 'Student':
        # Siswa: lihat thread yang mereka buat
        threads = MessageThread.objects.filter(student=user)
    else:
        # Guru/Admin: lihat thread yang ditugaskan ke mereka atau belum ditugaskan
        threads = MessageThread.objects.filter(
            Q(teacher_or_admin=user) | Q(teacher_or_admin=None)
        )
    
    # Filter berdasarkan status dan tipe jika ada
    status_filter = request.GET.get('status', '')
    type_filter = request.GET.get('type', '')
    search_query = request.GET.get('search', '')
    
    if status_filter:
        threads = threads.filter(status=status_filter)
    
    if type_filter:
        threads = threads.filter(thread_type=type_filter)
    
    if search_query:
        threads = threads.filter(
            Q(title__icontains=search_query) |
            Q(messages__content__icontains=search_query)
        ).distinct()
    
    # Urutkan berdasarkan aktivitas terakhir
    threads = threads.order_by('-last_activity')
    
    # Pagination
    paginator = Paginator(threads, 10)
    page = request.GET.get('page')
    try:
        threads_page = paginator.page(page)
    except PageNotAnInteger:
        threads_page = paginator.page(1)
    except EmptyPage:
        threads_page = paginator.page(paginator.num_pages)
    
    # Add unread count for each thread
    for thread in threads_page:
        thread.unread_count = thread.get_unread_count_for_user(user)
    
    # Data untuk filter options
    context = {
        'threads': threads_page,
        'status_choices': MessageThread.STATUS_CHOICES,
        'thread_type_choices': MessageThread.THREAD_TYPES,
        'current_status': status_filter,
        'current_type': type_filter,
        'current_search': search_query,
    }
    
    return render(request, 'messages/inbox.html', context)


@login_required
def create_message_thread(request):
    """View untuk membuat thread pesan baru (khusus siswa)"""
    if not (request.user.role and request.user.role.role_name == 'Student'):
        messages.error(request, 'Hanya siswa yang dapat membuat thread pesan baru.')
        return redirect('message_inbox')
    
    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        thread_type = request.POST.get('thread_type', 'general')
        category_id = request.POST.get('category', None)
        priority = request.POST.get('priority', 'normal')
        content = request.POST.get('content', '').strip()
        attachment = request.FILES.get('attachment', None)
        
        # Validasi
        if not title or not content:
            messages.error(request, 'Judul dan isi pesan harus diisi.')
        else:
            try:
                with transaction.atomic():
                    # Buat thread baru
                    thread = MessageThread.objects.create(
                        title=title,
                        thread_type=thread_type,
                        student=request.user,
                        priority=priority,
                        category_id=category_id if category_id else None
                    )
                    
                    # Buat pesan pertama
                    Message.objects.create(
                        thread=thread,
                        sender=request.user,
                        content=content,
                        attachment=attachment
                    )
                    
                    messages.success(request, 'Pesan berhasil dikirim!')
                    return redirect('message_thread', thread_id=thread.id)
                    
            except Exception as e:
                messages.error(request, f'Terjadi kesalahan: {str(e)}')
    
    # Data untuk form
    categories = Category.objects.all().order_by('category_name')
    context = {
        'categories': categories,
        'thread_type_choices': MessageThread.THREAD_TYPES,
        'priority_choices': [
            ('low', 'Rendah'),
            ('normal', 'Normal'),
            ('high', 'Tinggi'),
            ('urgent', 'Mendesak')
        ]
    }
    
    return render(request, 'messages/create_thread.html', context)


@login_required
def message_thread(request, thread_id):
    """View untuk melihat detail thread dan pesan-pesannya"""
    thread = get_object_or_404(MessageThread, id=thread_id)
    
    # Cek akses user
    user = request.user
    has_access = False
    
    if user.role and user.role.role_name == 'Student':
        # Siswa hanya bisa akses thread mereka sendiri
        has_access = (thread.student == user)
    else:
        # Guru/Admin bisa akses thread yang ditugaskan atau tidak ada yang menangani
        has_access = (thread.teacher_or_admin == user or thread.teacher_or_admin is None)
    
    if not has_access:
        messages.error(request, 'Anda tidak memiliki akses ke thread ini.')
        return redirect('message_inbox')
    
    # Assign guru/admin jika belum ada yang menangani
    if not thread.teacher_or_admin and user.role and user.role.role_name != 'Student':
        thread.teacher_or_admin = user
        thread.save()
    
    # Handle POST request (mengirim balasan)
    if request.method == 'POST':
        content = request.POST.get('content', '').strip()
        attachment = request.FILES.get('attachment', None)
        action = request.POST.get('action', 'reply')
        
        if action == 'reply' and content:
            try:
                Message.objects.create(
                    thread=thread,
                    sender=user,
                    content=content,
                    attachment=attachment
                )
                
                # Update status thread jika perlu
                if thread.status == 'closed':
                    thread.status = 'open'
                    thread.save()
                
                messages.success(request, 'Balasan berhasil dikirim!')
                return redirect('message_thread', thread_id=thread.id)
                
            except Exception as e:
                messages.error(request, f'Terjadi kesalahan: {str(e)}')
        
        elif action == 'update_status':
            new_status = request.POST.get('status')
            if new_status in dict(MessageThread.STATUS_CHOICES):
                thread.status = new_status
                thread.save()
                messages.success(request, f'Status thread diubah menjadi {dict(MessageThread.STATUS_CHOICES)[new_status]}')
                return redirect('message_thread', thread_id=thread.id)
    
    # Tandai pesan sebagai sudah dibaca
    thread.mark_as_read_for_user(user)
    
    # Ambil semua pesan dalam thread
    messages_list = thread.messages.all().order_by('created_at')
    
    context = {
        'thread': thread,
        'messages_list': messages_list,
        'status_choices': MessageThread.STATUS_CHOICES,
        'can_manage': user.role and user.role.role_name != 'Student',
    }
    
    return render(request, 'messages/thread_detail.html', context)


@login_required
@admin_or_teacher_required
def assign_thread(request, thread_id):
    """View untuk assign thread ke guru/admin tertentu"""
    thread = get_object_or_404(MessageThread, id=thread_id)
    
    if request.method == 'POST':
        teacher_id = request.POST.get('teacher_id')
        
        if teacher_id:
            try:
                teacher = User.objects.get(id=teacher_id)
                if teacher.role and teacher.role.role_name in ['Teacher', 'Admin']:
                    thread.teacher_or_admin = teacher
                    thread.save()
                    messages.success(request, f'Thread berhasil di-assign ke {teacher.username}')
                else:
                    messages.error(request, 'User yang dipilih bukan guru atau admin.')
            except User.DoesNotExist:
                messages.error(request, 'User tidak ditemukan.')
        else:
            # Unassign thread
            thread.teacher_or_admin = None
            thread.save()
            messages.success(request, 'Thread berhasil di-unassign.')
    
    return redirect('message_thread', thread_id=thread.id)


@login_required
def message_api_unread_count(request):
    """API untuk mendapatkan jumlah pesan yang belum dibaca"""
    user = request.user
    
    if user.role and user.role.role_name == 'Student':
        # Siswa: hitung pesan belum dibaca dari guru/admin
        unread_count = Message.objects.filter(
            thread__student=user,
            is_read=False
        ).exclude(sender=user).count()
    else:
        # Guru/Admin: hitung pesan belum dibaca dari siswa
        unread_count = Message.objects.filter(
            Q(thread__teacher_or_admin=user) | Q(thread__teacher_or_admin=None),
            is_read=False
        ).exclude(sender=user).count()
    
    return JsonResponse({'unread_count': unread_count})

