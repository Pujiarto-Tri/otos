import os
import django
import sys

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'otos.settings')
django.setup()

from otosapp.models import Test

TEST_ID = 227

t = Test.objects.filter(id=TEST_ID).first()
if not t:
    print('TEST_NOT_FOUND')
    sys.exit(0)

print('id:', t.id)
print('student:', getattr(t.student, 'email', None))
print('is_submitted:', t.is_submitted)
print('score:', t.score)
print('tryout_package:', getattr(getattr(t, 'tryout_package', None), 'id', None))
print('categories:', [c.id for c in t.categories.all()])

answers = t.answers.select_related('question', 'selected_choice').all()
print('answers_count:', answers.count())
for a in answers:
    print('answer id:', a.id, 'question id:', getattr(a.question, 'id', None), 'selected_choice id:', getattr(a.selected_choice, 'id', None), 'is_correct:', getattr(a.selected_choice, 'is_correct', None))

# Print a small sample of question texts if available
for i, a in enumerate(answers):
    if i >= 5:
        break
    q = a.question
    print('Q sample:', q.id, str(q.question_text)[:120].replace('\n', ' '))
