from otosapp.models import Category, Question

# Check categories and questions
print("=== Database Check ===")
print(f"Total Categories: {Category.objects.count()}")
print(f"Total Questions: {Question.objects.count()}")

print("\n=== Categories with Question Count ===")
for cat in Category.objects.all()[:10]:
    question_count = cat.question_set.count()
    print(f"{cat.category_name}: {question_count} questions")

# Check if there are any questions
if Question.objects.count() > 0:
    print("\n=== Sample Questions ===")
    for q in Question.objects.all()[:3]:
        print(f"Q: {q.question_text[:50]}... (Category: {q.category.category_name})")
else:
    print("\n⚠️ NO QUESTIONS FOUND IN DATABASE")
