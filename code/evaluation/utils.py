import csv


# Turn a 2-column (text, label) csv, like the hugging-face query exports, into a list of (text, label) tuples
def csv_to_list(filepath):
    data = []
    with open(filepath, newline='', encoding='utf-8') as csvfile:
        reader = csv.reader(csvfile)
        next(reader, None)  # skip header row

        for row in reader:
            if len(row) != 2:
                raise ValueError(f"Invalid row format: {row}")

            text = row[0]
            label = int(row[1])
            data.append((text, label))
        return data
