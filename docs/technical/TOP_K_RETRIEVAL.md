# Top-K Retrieval Exploration

This document summarizes the `top_k_comparison.ipynb` notebook that investigates retrieving different numbers of results from the vector store.

Retrieving a larger `top_k` should give the same ordering for the highest ranked items while adding only a small amount of overhead. This behaviour is confirmed in the notebook.

## Running the Notebook

Open `notebooks/top_k_comparison.ipynb` and execute the cells. The notebook generates a small corpus, encodes it using `sentence_transformers`, and compares retrieval times for `top_k` values of 5, 10 and 50.

## References

- [EMBEDDING.md](EMBEDDING.md) for details on how embeddings are generated.

## Code Files

- [notebooks/top_k_comparison.ipynb](../../notebooks/top_k_comparison.ipynb) - Jupyter notebook demonstrating top-K retrieval
