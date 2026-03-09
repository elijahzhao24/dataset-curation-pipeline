# dataset-curation-pipeline


A scalable pipeline for transforming large, noisy image datasets into high-quality training datasets using modern vision embeddings and vector similarity search.

This system processes millions of images and removes duplicates and near-duplicates, and selects a **diverse subset of images** suitable for training machine learning models.

In addition to filtering and sampling datasets, the pipeline also supports **targeted image retrieval**. This allows users to retrieve images from the dataset that are **semantically similar to a candidate image or folder of images.** This is useful when training models that require targeted examples of a specific object, environment, or failure cases.

The pipeline leverages vision models like Meta AI's DINOv2, pgVector, and sampling algorithms used in machine learning infrastructure.

# Problem Context


Many machine learning systems rely on large image datasets collected from real-world environments. These datasets often contain:

- near-duplicate images
- poor quality frames
- redundant samples
- heavy class imbalance
- large volumes of unlabelled data

In my particular use case, our robotics camera system can capture millions of images, but only a small subset may be useful for training. 

Training on unfiltered datasets introduces several issues:

### 1. Duplicate images

Datasets often contain many identical or near-identical images captured in sequence. Training on these adds no new info, wastes compute, and **risks overfitting the model.**

### 2. Lack of Diversity

Even after deduplication, many datasets lack visual diversity, which can cause models to overfit. The unfiltered dataset may also be unbalanced, in the sense that there may be considerably more images of object/environment A, compared to B, which would cause the model to overfit.

### 3. Dataset Scale

It will take someone days/weeks to manually select the best dataset to train on when we reach hundreds of thousands of images. A scalable automated filtering pipeline that can remove duplicates, store embeddings for efficient similarity search, select a maximally diverse subset of images, and support cloud-scale storage and processing is necessary.

# Proposed Solution and System Overview

The pipeline converts a large unfiltered image dataset into a curated training dataset through the following stages:
1. Feature extraction through vector embeddings
2. Image and Metadata storage
3. Duplicate Filtering
4. Dataset Sampling
5. Image Retrieval

# Feature Extraction

As an input, this system processes images stored locally or in AWS S3. Images are processed in batches (to maximize GPU util) using PyTorch. 

The system loads a pretrained DINOv2 Vision Transformer and extracts embeddings for each image. In my specific use case, I have also decided to add an option for segmentation preprocessing. This is currently done using a custom Roboflow segmentation model to generate polygon points around the subject of interest. Helpers will then convert the polygon into a binary mask and crop the image by setting the background outside the subject to black.

The embedding pipeline performs:

1. Image loading
2. Optional segmentation preprocessing
3. Image normalization
4. Feature extraction
5. Normalize to unit vectors while preserving direction (L2 normalization)

Produces vectors of dimensions 768

# Duplicate Filtering

Each embedding is inserted into the vector database only if it is sufficiently different from existing images.

With pgvector, we can perform a nearest neighbor search:
```
SELECT ID, embedding <+> query_vector
ORDER BY embedding <+> query_vector
LIMIT 1
```

if the cosine similarity exceeds the threshold:
```
cosine_similarity >= 0.98
```
The image is discarded and considered a duplicate. Otherwise, the image is copied to the filtered dataset (copied fast across the server with S3), and emedding is inserted into the databased.

allows the database to grow without accumulating redundant images.

# Dataset Sampling

Once a filtered dataset is constructed, this repo provides a diversity sampling pipeline and an image retrieval pipeline.

### Diversity Sampling

Select a subset of k images using farthest point sampling (k-means).

**Algorithm outline (Gonzalez algorithm)**
1. Randomly select an initial image
2. Compute Distances to all other images
3. Select the image farthest from the current set
4. Mark that image as selected
5. Reapt until K images are selected

This greedy approach approximates the k-center optimization problem, producing a subset with maximal diversity.
Note: our vector query uses Hierarchical Navigable Small Worlds (HNSW), reducing search complexity from O(N) to O(logN)

### Semantic Retrieval System

Functionality allows users to retrieve k images from the dataset that are semantically similar to a candidate image or folder of images. 

**Workflow is as follows**
1. Generate embeddings for the candidate set (using the same embedding model) and compute a mean embedding vector.
2. Query the vector database for the K nearest images
3. Download matching images from S3.

This feature also turns the dataset into a semantic image search engine, enabling efficient data exploration.
