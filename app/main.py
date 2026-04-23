from services.pipeline import run_pipeline

if __name__ == "__main__":
    csv_path = "data/sample.csv"
    output = run_pipeline(csv_path)
    print(output)