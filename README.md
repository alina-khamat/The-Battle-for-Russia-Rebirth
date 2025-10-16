# The Battle for Russia’s Rebirth  
### *Interpreting Pro-War Critical Patriotism and Imperial-Nationalism on Telegram*

## 🧭 Project Overview
This repository provides replication materials for the study  **“The Battle for Russia’s Rebirth: Interpreting Pro-War Critical Patriotism and Imperial-Nationalism on Telegram.”**  
The project examines Russia’s *critical patriot* Telegram ecosystem — a faction of actors that support the invasion of Ukraine yet criticize the Kremlin for incompetence, corruption, or insufficient commitment to total victory.


## 📂 Repository Structure

```text
├──🧠 code/                                     # Source code for data collection, text analysis, and modeling
│   ├── Telegram_Data_Collection.py             # Retrieves Telegram channel data via the Telegram API and stores it in PostgreSQL
│   ├── Dependency_Parsing.py                   # Performs syntactic (spaCy-based) detection of criticism toward Russian authorities
│   ├── Fine_Tune_RuBERT_Criticism.py           # Fine-tunes the RuBERT model using the manually coded criticism dataset
│   ├── Frame_Frequency_Analysis.py             # Identifies and counts occurrences of discursive frames across messages
│   ├── Network_Analysis.py                     # Constructs and analyzes the inter-channel repost network (weighted, directed)
│   └── utils/                                  # Helper functions, logging, and configuration templates
│
├──📊 data/                                     # Processed datasets and intermediate analytical outputs
│   ├── Channels_List.csv                       # Metadata for all sampled channels (ID, label, subscriber count, cluster)
│   ├── Network_Analysis_Data/
│   │   ├── Edges.csv                           # Weighted repost connections (source, target, weight)
│   │   └── Nodes.csv                           # Nodes with structural metrics (degree, modularity, cluster class)
│   ├── Sampling_Manual_Filtering_R1_Example.csv # Example of manual filtering at R1 stage (EDSS sampling refinement)
│   └── Training_Dataset.csv                    # Manually labeled messages (criticism vs non-criticism) used for RuBERT fine-tuning
│
├── 📄 docs/                                    # Supplementary documentation and methodological appendices
│   ├── CODEBOOK.md                             # Definitions of all variables, lexicons, and coding criteria
│   ├── Sampling_Procedure.md                   # Detailed description of the Exponential Discriminative Snowball Sampling (EDSS)
│   ├── Harm_Reduction.md                       # Ethical safeguards and harm mitigation procedures for digital ethnography
│   ├── TOS_Compliance.md                       # Documentation of compliance with Telegram’s Terms of Service
│   └── Model_Description_ruBERT.md             # Technical overview of RuBERT architecture and fine-tuning parameters
│
└── 📘 README.md                                # Main repository description and replication instructions

```
## ⚙️ Methodological Pipeline

### 1️⃣ Sampling Procedure and Data Collection

**Input:**  
- Initial seed channels: `@kvmalofeev`, `@strelkovii`, `@adirect`, `@rybar`  
- Raw repost and mention data from Telegram API  

**Procedure:**  
Channel identification followed an **Exponential Discriminative Snowball Sampling (EDSS)** approach, detailed in  [`documents/Sampling_Procedure.md`](docs/Sampling_Procedure.md).  

Network expansion proceeded iteratively based on **repost ties**, adding new channels if they had been forwarded or mentioned **≥5 times** in R1 or  **≥10 times** in R2 by existing nodes since **February 24, 2022** to **September 1, 2024**.  
Each iteration was followed by **manual filtering ** to remove irrelevant  channels. An example of this filtering stage is provided in  [`data/Sampling_Manual_Filtering_R1_Example.csv`](data/Sampling_Manual_Filtering_R1_Example.csv).  

All messages and metadata were collected through the **Telegram API** via the custom Python script [`code/Telegram_Data_Collection.py`](code/Telegram_Data_Collection.py),  which saved message text, timestamps, and repost relations into a PostgreSQL database.  

The complete list of sampled channels — including channel names, IDs, and subscriber counts — is available in  [`data/Channels_List.csv`](data/Channels_List.csv).  

Due to ethical and privacy considerations, **raw message-level data are not publicly shared**. All processing complied with the harm-reduction and data-protection principles described in  [`documents/Harm_Reduction.md`](docs/Harm_Reduction.md).

**Output:**  
- Stable sample of **78 Telegram channels**  
- Approx. **670,000 messages** in database (Feb 2022 – Sept 2024) for subsequent textual and structural analysis
- Repost-based adjacency matrix for network construction  

---
### 2️⃣ Network Reconstruction and Centrality Analysis

**Input:**  
- [`data/Network_Analysis_Data/Edges.csv`](data/Network_Analysis_Data/Edges.csv) — weighted repost connections (source, target, weight)  
- [`data/Network_Analysis_Data/Nodes.csv`](data/Network_Analysis_Data/Nodes.csv) — channel metadata (ID, label, subscriber count)  
- Underlying message-level repost data extracted via [`code/Telegram_Data_Collection.py`](code/Telegram_Data_Collection.py)

**Procedure:**  
This stage reconstructs and analyzes the directed repost network among Telegram channels.  
Each **channel** is modeled as a node, and each **repost** of another channel’s message is treated as a directed, weighted edge.  

The analysis was performed using the script  [`code/Network_Analysis.py`](code/Network_Analysis.py)

Key computational steps include:
1. **Graph construction:** A directed weighted graph (`DiGraph`) is built using `networkx`, aggregating multiple reposts between the same channels.  
2. **Degree centrality:** For each node, weighted *in-degree*, *out-degree*, and *total degree* are computed to estimate both information reach and dissemination capacity.  
3. **Betweenness centrality:** Computed on the undirected projection (distance = 1/weight) to capture channels bridging otherwise weakly connected communities.  
4. **Cluster ranking:** For each *modularity class* (community), the top-3 most central channels are extracted using total degree and betweenness metrics.  
5. **Structural properties:** The script also produces a **structural summary** (directed and undirected versions), including:  
   - Graph size (nodes, edges)  
   - Reachability  
   - Density  
   - Average Path Length (APL)  
   - Diameter  
   - Global Efficiency  

Outputs are automatically exported to the `/outputs` directory for replication and inspection.

**Output:**  
- `degree_results.csv` — weighted in-, out-, and total degree for each channel  
- `betweenness_results.csv` — betweenness centrality on the undirected projection  
- `top3_per_class_degree.csv` — top 3 channels by total degree within each modularity class  
- `top3_per_class_betweenness.csv` — top 3 channels by betweenness within each modularity class  
- `network_summary.csv` — overall network-level structural metrics  
- `.gexf` file (optional) — exported for visualization in **Gephi 0.10**

  ---

### 3️⃣ Criticism Detection: Dependency Parsing and ML Classifier

**Input:**  
- Pre-processed message corpus from PostgreSQL (retrieved via `Telegram_Data_Collection.py`)  
- Linguistic resources defined in [`documents/CODEBOOK.md`](docs/CODEBOOK.md)  
- Manually annotated subset: [`data/Training_Dataset.csv`](data/Training_Dataset.csv)

**Procedure:**  
Criticism toward Russian authorities was identified through a **hybrid approach** combining  
(1) **syntactic dependency parsing** and  
(2) **machine-learning classification (RuBERT fine-tuning)**.

#### Dependency Parsing (Rule-Based Detection)
Implemented in [`code/Dependency_Parsing.py`](code/Dependency_Parsing.py), this module operationalizes linguistic criticism detection using **spaCy’s `ru_core_news_lg` model** and a dependency-based rule system.

The algorithm identifies critical statements if:
1. A **leadership-related subject** (e.g., *Путин*, *Кремль*, *администрация президента*)  
   — from `SINGLEWORD_SUBJECTS` or `MULTIWORD_SUBJECTS` —  
   appears in the syntactic tree;
2. A **negative predicate or adjective** (e.g., *врать*, *бояться*, *провалить*, *некомпетентный*, *трусливый*)  
   — from `NEGATIVE_LEMMAS` or `NEGATIVE_VERBS_WITH_NOT` —  
   directly modifies or governs the subject (or its pronoun reference);
3. Optional negation rules (e.g., “не справился”, “не решился”)  
   are handled explicitly via token dependency relations.

Each message is parsed into a dependency tree and labeled with a binary variable `is_criticism = True/False`.

The full keyword sets for political criticism and leadership subjects are provided in  
[`documents/CODEBOOK.md`](docs/CODEBOOK.md), section **“List of Keyword Sets Used in Dependency Parsing”**.

The results of dependency parsing were subsequently used to **construct the supervised training dataset** ([`data/Training_Dataset.csv`](data/Training_Dataset.csv)):  
the automatically labeled messages served as a foundation for the “criticism” class,  while randomly sampled neutral messages from the same PostgreSQL database were added to balance the dataset prior to manual validation and ML fine-tuning.

#### ML-Based Classification (Fine-Tuned RuBERT Model)
A manually annotated dataset was used to train and evaluate a **fine-tuned `RuBERT-base` model**, implemented in  
[`code/Fine_Tune_RuBERT_Criticism.py`](code/Fine_Tune_RuBERT_Criticism.py).

Each message in the training corpus was hand-coded according to the following criteria:

> **Criticism (1):** Explicit or implicit negative evaluation of Russian authorities, leadership, or state institutions —  
> including blame, calls for accountability, accusations of incompetence, corruption, or moral weakness.  
>  
> **Non-criticism (0):** Neutral, factual, or supportive mentions of Russian leadership or institutions,  
> or critical statements directed exclusively toward external actors (e.g., Ukraine, the West).


A detailed description of the RuBERT architecture, fine-tuning parameters, and evaluation procedure is available in  
[`documents/Model_Description_ruBERT.md`](docs/Model_Description_ruBERT.md).

**Output:**   
- Fine-tuned RuBERT model weights and evaluation metrics (accuracy, F1-score)  
- The database was enriched with a new binary variable **`is_criticism`**, indicating whether each message contains criticism of Russian leadership or state institutions.

---
### 4️⃣ Frame Frequency and Discourse Analysis

**Input:**  
- [`code/Frame_Frequency_Analysis.py`](code/Frame_Frequency_Analysis.py) — Python script implementing keyword-based frame detection and aggregation  
- [`documents/CODEBOOK.md`](docs/CODEBOOK.md) — full lexicon of framing categories and associated keyword sets  
- PostgreSQL database (`telegram_data` table) containing message text, cluster labels, and timestamps  

**Procedure:**  
This module operationalizes **ideological framing analysis** by quantifying the relative salience of key discursive frames across clusters.  
Each message is **lemmatized** using one of the available Russian language backends:

- `spaCy` (`ru_core_news_lg`, `ru_core_news_md`, `ru_core_news_sm`)  
- Fallback to `pymorphy2` (if `spaCy` is unavailable)  
- Or, finally, a simplified lowercase tokenizer  

After lemmatization, the script constructs **regex patterns** for each multiword expression or keyword defined in the `FRAMES` dictionary (derived from `CODEBOOK.md`).  
Messages are scanned for these expressions, and counts are aggregated by cluster.

**Frames operationalized:**  
- *Anti-immigration sentiments and Isolationism*  
- *Anti-peace-deal conspiratorial thinking*  
- *Hawkish criticism*  
- *Left-wing Criticism*  
- *Populism*  
- *Religious language*  
- *Revanchism and Exceptionalism (Russianness)*  
- *Traditionalism*  

**Output:**  
- `frame_counts_by_cluster.csv` — number of messages per frame by cluster  
- `frame_percentages_by_cluster.csv` — relative frequency of frames per cluster (percent of total messages) 

---
## 🔒 Reproducibility and Ethical Access

This repository is designed to ensure methodological transparency rather than full data replication.  
All code, documentation, and variable definitions are provided so that other researchers can  
understand, evaluate, and adapt the analytical framework used in the study.

Due to ethical considerations and privacy risks associated with Telegram user-generated content,  
the **raw message-level dataset is not publicly released**.  
For details, see [`documents/Harm_Reduction.md`](docs/Harm_Reduction.md).

Researchers interested in reproducing specific components of the pipeline (e.g., network construction,  
frame analysis, or model fine-tuning) can use the provided scripts with their own Telegram datasets  
collected under the same methodological constraints and selection criteria  
(see [`documents/Sampling_Procedure.md`](docs/Sampling_Procedure.md)).

For academic inquiries or collaboration requests, please contact:

**Alina Khamatdinova**  
School of Politics, Philosophy, and Public Affairs  
Washington State University  
📧 [alina.khamatdinova@wsu.edu](mailto:alina.khamatdinova@wsu.edu)  

---

## 📄 Citation

If you use or reference the analytical framework, code, or documentation from this repository, please cite:

> **Blackburn, Matthew & Khamatdinova, Alina** (2025).  
> *The Battle for Russia’s Rebirth: Interpreting Pro-War Critical Patriotism and Imperial-Nationalism on Telegram.*  
> GitHub Repository: [https://github.com/alina-khamat/The-Battle-for-Russia-Rebirth](https://github.com/alina-khamat/The-Battle-for-Russia-Rebirth)

**Recommended BibTeX citation:**

```bibtex
@misc{blackburn_khamatdinova_2025,
  author       = {Matthew Blackburn and Alina Khamatdinova},
  title        = {The Battle for Russia’s Rebirth: Interpreting Pro-War Critical Patriotism and Imperial-Nationalism on Telegram},
  year         = {2025},
  url          = {https://github.com/alina-khamat/The-Battle-for-Russia-Rebirth},
  note         = {GitHub Repository and Code Appendix for the corresponding article}
}
---

