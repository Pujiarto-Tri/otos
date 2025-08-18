import os
import django
import sys

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'otos.settings')
django.setup()

from otosapp.models import Test, TryoutPackage, Answer

TEST_ID = 227

t = Test.objects.filter(id=TEST_ID).first()
if not t:
    print('TEST_NOT_FOUND')
    sys.exit(0)

print('Test id:', t.id)
print('Student:', getattr(t.student, 'email', None))
print('Tryout package:', getattr(getattr(t, 'tryout_package', None), 'id', None))
package = t.tryout_package

if not package:
    print('Not a package test')
    sys.exit(0)

print('Package:', package.package_name)

# Build package question list as view does
all_questions = []
for pc in package.tryoutpackagecategory_set.all().order_by('order'):
    qs = list(pc.category.question_set.all().order_by('id'))
    print(f"Category {pc.category.id} ({pc.category.category_name}): {len(qs)} questions")
    all_questions.extend([(pc.category, q) for q in qs])

print('\nTotal package questions:', len(all_questions))

answers = t.answers.select_related('question', 'selected_choice')
print('Total answers in DB for test:', answers.count())

answered_qids = {a.question.id: a for a in answers}

for idx, (cat, q) in enumerate(all_questions, start=1):
    a = answered_qids.get(q.id)
    if a:
        print(f"{idx}. QID={q.id} - ANSWERED -> choice_id={a.selected_choice.id} is_correct={a.selected_choice.is_correct}")
    else:
        print(f"{idx}. QID={q.id} - UNANSWERED")

# Summary per category
from collections import defaultdict
cat_stats = defaultdict(lambda: {'questions':0,'answered':0})
for pc in package.tryoutpackagecategory_set.all():
    qs = list(pc.category.question_set.all())
    cat_stats[pc.category.id]['questions'] = len(qs)

for a in answers:
    cat_stats[a.question.category.id]['answered'] += 1

print('\nPer-category summary:')
for cid, s in cat_stats.items():
    print(f"Category {cid}: answered {s['answered']} / {s['questions']}")

# Print test score and is_submitted
print('\nTest meta: is_submitted=', t.is_submitted, 'score=', t.score, 'current_question=', t.current_question)
