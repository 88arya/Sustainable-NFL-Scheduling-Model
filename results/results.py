import pandas as pd
import matplotlib.pyplot as plt
import os
import numpy as np

script_dir = os.path.dirname(os.path.abspath(__file__))
csv_path = os.path.join(script_dir, "results.csv")

df = pd.read_csv(csv_path)

years = df['year'].astype(str)
x = np.arange(len(years))
width = 0.35

fig, ax = plt.subplots(figsize=(10,6))

rects1 = ax.bar(x - width/2, df['actual_value'], width, label='Actual')
rects2 = ax.bar(x + width/2, df['optimal_value'], width, label='Optimal')

ax.set_xlabel('Year')
ax.set_ylabel('CO2 Emissions (metric tonnes)')
ax.set_title('NFL Schedule: Actual vs Optimal CO2 Emissions')
ax.set_xticks(x)
ax.set_xticklabels(years)
ax.grid(axis='y', linestyle='--', alpha=0.7)

for i in range(len(df)):
    actual = df['actual_value'][i]
    optimal = df['optimal_value'][i]
    percent = df['percent_decrease'][i]

    y = max(actual, optimal) + 100
    ax.text(
        x[i],
        y,
        f"-{percent:.1f}%",
        ha='center', va='bottom', fontsize=10, fontweight='bold'
    )

ax.legend(loc='upper left', bbox_to_anchor=(1,1))

output_path = os.path.join(script_dir, "emissions_comparison_bar_metric_tonnes.png")
plt.savefig(output_path, dpi=300, bbox_inches='tight')

plt.show()






