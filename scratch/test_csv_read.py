import pandas as pd
import io

# Test reading a CSV with dots as decimal but using BR settings in read_csv
csv_data = "VALOR\n1234.56\n500.20"
df = pd.read_csv(io.StringIO(csv_data), decimal=",", thousands=".")

print("Read with decimal=',' and thousands='.' (US format input):")
print(df)
print("Types:")
print(df.dtypes)

# Observe if 1234.56 became 123456
