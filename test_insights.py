
import pandas as pd

from modules.insights_engine import generate_business_insights

data = pd.DataFrame({
    "Product": ["Laptop", "Phone", "Tablet", "Laptop", "Phone"],
    "Sales": [50000, 25000, 37500, 60000, 30000],
    "Profit": [10000, 5000, 7500, 12000, 6000],
    "Region": ["South", "North", "East", "South", "North"]
})

results = generate_business_insights(data)

print("\nINSIGHTAI - BUSINESS INSIGHTS\n")

for number, insight in enumerate(results, start=1):
    print(f"{number}. {insight}")
