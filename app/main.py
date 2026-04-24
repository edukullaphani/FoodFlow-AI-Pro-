from services.graph_pipeline import run_graph_pipeline

if __name__ == "__main__":
    csv_path = "data/sample.csv"
    output = run_graph_pipeline(csv_path)
    print(output)