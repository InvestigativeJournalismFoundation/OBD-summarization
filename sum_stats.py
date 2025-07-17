import pandas as pd
import matplotlib.pyplot as plt

class DocumentStatsAnalyzer:
    def __init__(self, doc_stats_path, page_tokens_path):
        self.doc_stats_path = doc_stats_path
        self.page_tokens_path = page_tokens_path
        self.doc_stats = None
        self.page_tokens = None

    def load_data(self):
        print("Loading document_stats.csv...")
        self.doc_stats = pd.read_csv(
            self.doc_stats_path,
            dtype={
                "doc_id": "category",
                "title": "string",
                "organization": "category",
                "request_number": "string",
                "description": "string",
                "created_at": "string",
                "page_count": "int16",
                "file_size": "float32",
                "token_total": "int32",
                "token_avg_per_page": "float32",
                "token_min": "int16",
                "token_max": "int16",
                "token_std_dev": "float32",
            }
        )

        print("Loading page_token_counts.csv...")
        self.page_tokens = pd.read_csv(
            self.page_tokens_path,
            dtype={
                "doc_id": "category",
                "page_number": "int16",
                "tokens_per_page": "int16"
            }
        )

    def show_summary(self):
        pd.set_option('display.max_columns', None)
        pd.set_option('display.width', None)

        print("\nDocument Stats Summary:")
        print(self.doc_stats.describe(include='all'))

        print("\nPage Token Counts Summary:")
        print(self.page_tokens['tokens_per_page'].describe())

    def plot_all(self):
        self._plot_page_count_distribution()
        self._plot_token_total_distribution()
        self._plot_avg_tokens_per_page()
        self._plot_page_token_distribution()
        self._plot_avg_tokens_by_page_number()

    def _plot_page_count_distribution(self):
        data = self.doc_stats['page_count']

        plt.figure(figsize=(10, 6))
        plt.hist(data, bins=100, edgecolor='black')

        plt.xlabel("Page Count (log scale)")
        plt.title("Distribution of Page Counts")

        plt.ylabel("Document Count")
        plt.tight_layout()
        plt.show()

        quantiles = data.quantile([0.5, 0.9, 0.95, 0.99, 0.999])
        print("\nPage Count Quantiles:")
        print(quantiles)

    def _plot_token_total_distribution(self):
        plt.figure(figsize=(10, 6))
        plt.hist(self.doc_stats['token_total'], bins=50, edgecolor='black')
        plt.title("Distribution of Total Tokens per Document")
        plt.xlabel("Total Tokens")
        plt.ylabel("Document Count")
        plt.tight_layout()
        plt.show()

    def _plot_avg_tokens_per_page(self):
        plt.figure(figsize=(10, 6))
        plt.hist(self.doc_stats['token_avg_per_page'], bins=50, edgecolor='black')
        plt.title("Average Tokens per Page per Document")
        plt.xlabel("Tokens per Page")
        plt.ylabel("Document Count")
        plt.tight_layout()
        plt.show()

    def _plot_page_token_distribution(self):
        plt.figure(figsize=(10, 6))
        plt.hist(self.page_tokens['tokens_per_page'], bins=50, edgecolor='black')
        plt.title("Distribution of Tokens per Page")
        plt.xlabel("Tokens per Page")
        plt.ylabel("Page Count")
        plt.tight_layout()
        plt.show()

    def _plot_avg_tokens_by_page_number(self):
        avg_tokens_by_page = self.page_tokens.groupby("page_number")["tokens_per_page"].mean().reset_index()
        plt.figure(figsize=(10, 6))
        plt.plot(avg_tokens_by_page["page_number"], avg_tokens_by_page["tokens_per_page"], marker='o', linestyle='-')
        plt.title("Average Tokens by Page Number")
        plt.xlabel("Page Number")
        plt.ylabel("Average Tokens")
        plt.tight_layout()
        plt.show()

