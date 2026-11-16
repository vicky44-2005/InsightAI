
import pandas as pd

from modules.question_engine import answer_question

data = pd.DataFrame({
    "Product": ["Laptop", "Phone", "Tablet", "Monitor"],
    "Sales": [50000, 25000, 37500, 60000],
    "Profit": [12000, 5000, 8000, 15000]
})

questions = [
    "Which product has the highest sales?",
    "What is the average sales?",
    "Show the top 2 products by sales.",
    "What is the total profit?",
    "Which product has the lowest sales?",
    "இந்த dataset ல அதிக sales எந்த productக்கு இருக்கு?"
]

for question in questions:

    print("\nQuestion:", question)

    try:
        answer = answer_question(data, question)
        print("InsightAI:", answer)

    except Exception as error:
        print("Error:", error)
