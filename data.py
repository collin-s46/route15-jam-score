import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt


# Read CSV file
df = pd.read_csv('traffic_data.csv', index_col='Date')

plt.figure(figsize=(10, 6))

#sns.barplot(x=df['Day'], y=df['Travel Time'])

#plt.title("Travel Time vs. Day of Week")

sns.barplot(x=df['Departure'], y=df['Travel Time'], hue=df['Day'], palette='muted')
sns.lineplot(x=df['Departure'], y=df['Travel Time'], legend=False)
plt.show()
# Print the DataFrame
#print(df.tail())