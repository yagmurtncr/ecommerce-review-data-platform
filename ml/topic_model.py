"""Unsupervised topic analysis over review text (TF-IDF + KMeans).

Groups reviews into K topics and labels each cluster with its top TF-IDF terms.
A first-version, dependency-light alternative to BERTopic that still surfaces
what customers talk about (quality, shipping, price, packaging, ...).

Run:  python -m ml.topic_model --csv data/samples/reviews.csv --k 6
"""
from __future__ import annotations

import argparse

import pandas as pd


def fit_topics(texts: list[str], k: int = 6, seed: int = 42):
    from sklearn.cluster import KMeans
    from sklearn.feature_extraction.text import TfidfVectorizer

    vec = TfidfVectorizer(max_features=2000, stop_words="english", ngram_range=(1, 2))
    X = vec.fit_transform(texts)
    km = KMeans(n_clusters=k, random_state=seed, n_init=10)
    labels = km.fit_predict(X)

    terms = vec.get_feature_names_out()
    top_terms = {}
    for c in range(k):
        centroid = km.cluster_centers_[c]
        top_idx = centroid.argsort()[::-1][:6]
        top_terms[c] = [terms[i] for i in top_idx]
    return labels, top_terms


def main():
    ap = argparse.ArgumentParser(description="TF-IDF + KMeans topic analysis")
    ap.add_argument("--csv", default="data/samples/reviews.csv")
    ap.add_argument("--k", type=int, default=6)
    ap.add_argument("--out", default="data/samples/topics.csv")
    args = ap.parse_args()

    df = pd.read_csv(args.csv)
    labels, top_terms = fit_topics(df["review_text"].astype(str).tolist(), args.k)
    df["topic_cluster"] = labels
    df.to_csv(args.out, index=False)

    print(f"Fitted {args.k} topics on {len(df)} reviews -> {args.out}\n")
    for c, terms in top_terms.items():
        n = int((labels == c).sum())
        print(f"  topic {c} (n={n}): {', '.join(terms)}")


if __name__ == "__main__":
    main()
