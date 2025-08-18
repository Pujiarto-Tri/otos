from django.utils import timezone
from otosapp.models import User, Role, Category, Question, Choice, Test, Answer

# Ensure roles
role_teacher, _ = Role.objects.get_or_create(role_name='Teacher')
role_student, _ = Role.objects.get_or_create(role_name='Student')

# Create teacher
teacher, created = User.objects.get_or_create(email='teacher@example.com', defaults={'username':'teacher','role':role_teacher})
if created:
    teacher.set_password('pass')
    teacher.save()

# Create student
student, created = User.objects.get_or_create(email='student@example.com', defaults={'username':'student','role':role_student})
if created:
    student.set_password('pass')
    student.save()

# Create category
cat, _ = Category.objects.get_or_create(category_name='Smoke Test Category', defaults={'time_limit':30, 'created_by':teacher})

# Create question
q = Question.objects.create(question_text='What is 2+2?', pub_date=timezone.now(), category=cat, custom_weight=100)

# Create choices
Choice.objects.filter(question=q).delete()
c1 = Choice.objects.create(question=q, choice_text='3', is_correct=False)
c2 = Choice.objects.create(question=q, choice_text='4', is_correct=True)
c3 = Choice.objects.create(question=q, choice_text='5', is_correct=False)

# Create test
test = Test.objects.create(student=student, time_limit=30, is_submitted=False)
test.categories.add(cat)

# Create answer selecting correct choice
Answer.objects.filter(test=test).delete()
ans = Answer.objects.create(test=test, question=q, selected_choice=c2)

# Submit and calculate score
test.is_submitted = True
test.calculate_score()
print('Test score:', test.score)

# Teacher view: get tests for category
tests = Test.objects.filter(categories=cat, is_submitted=True)
print('Submitted tests for category:', tests.count())
for t in tests:
    print(t.student.email, t.score)

print('Smoke test completed')
