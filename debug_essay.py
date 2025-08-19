#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'otos.settings')
django.setup()

from otosapp.models import Answer, Question, Test

# Check essay answers
print("=== DEBUG ESSAY ANSWERS ===")
essay_answers = Answer.objects.filter(text_answer__isnull=False).exclude(text_answer='')
print(f"Essay answers count: {essay_answers.count()}")

for answer in essay_answers[:5]:
    print(f"Answer ID: {answer.id}")
    print(f"Text: '{answer.text_answer}'")
    print(f"Question: {answer.question.question_text[:100]}...")
    print(f"Test ID: {answer.test.id}")
    print("---")

# Check essay questions
print("\n=== DEBUG ESSAY QUESTIONS ===")
essay_questions = Question.objects.filter(question_type='essay')
print(f"Essay questions count: {essay_questions.count()}")

for question in essay_questions[:5]:
    print(f"Question ID: {question.id}")
    print(f"Question: {question.question_text[:100]}...")
    print(f"Correct Answer: '{question.correct_answer_text}'")
    print("---")

# Check latest test
print("\n=== DEBUG LATEST TEST ===")
latest_test = Test.objects.order_by('-date_taken').first()
if latest_test:
    print(f"Latest Test ID: {latest_test.id}")
    print(f"Student: {latest_test.student.email}")
    answers = latest_test.answers.all()
    print(f"Total answers: {answers.count()}")
    for answer in answers:
        if answer.text_answer:
            print(f"  Essay answer: '{answer.text_answer}' for question {answer.question.id}")
        else:
            print(f"  Multiple choice answer: {answer.selected_choice} for question {answer.question.id}")
