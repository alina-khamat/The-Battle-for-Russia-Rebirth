#!/usr/bin/env python3
"""
Network Analysis (Degree/Betweenness + Structural Summary)

Dependencies
------------
pip install pandas networkx
"""

import os
import math
import pandas as pd
import networkx as nx

# ========================
# CONFIG (edit as needed)
# ========================
EDGES_PATH = "data/Network_Analysis_Data/Edges.csv"
NODES_PATH = "data/Network_Analysis_Data/Nodes.csv"

OUTPUT_DIR = "outputs"

TOP_N_OVERALL = 20           # how many to show in console (overall ranking)
TOP_K_PER_CLUSTER = 3        # how many per modularity_class in saved CSVs/prints

OUT_DEGREE   = os.path.join(OUTPUT_DIR, "degree_results.csv")
OUT_BETWEEN  = os.path.join(OUTPUT_DIR, "betweenness_results.csv")
OUT_TOPK_DEG = os.path.join(OUTPUT_DIR, f"top{TOP_K_PER_CLUSTER}_per_class_degree.csv")
OUT_TOPK_BC  = os.path.join(OUTPUT_DIR, f"top{TOP_K_PER_CLUSTER}_per_class_betweenness.csv")
OUT_SUMMARY  = os.path.join(OUTPUT_DIR, "network_summary.csv")


# ----------------- helpers -----------------
def ensure_outdir(path: str):
    os.makedirs(path, exist_ok=True)


def detect_column(df: pd.DataFrame, candidates):
    """Return the first matching column name from candidates (case-insensitive)."""
    lower = {c.lower(): c for c in df.columns}
    for cand in candidates:
        if cand.lower() in lower:
            return lower[cand.lower()]
    return None


def load_and_prepare_edges(edges_path: str):
    """Read edges, detect columns, drop self-loops, coerce weights, aggregate."""
    edges = pd.read_csv(edges_path)
    print(f"Loaded {len(edges)} raw edges")

    src_col = detect_column(edges, ["source", "from", "src"]) or edges.columns[0]
    tgt_col = detect_column(edges, ["target", "to", "dst"]) or edges.columns[1]
    w_col   = detect_column(edges, ["weight", "count", "freq", "Weight"]) or None

    cols = [src_col, tgt_col] + ([w_col] if w_col else [])
    edges = edges[cols].copy()

    edges = edges.dropna(subset=[src_col, tgt_col])
    edges = edges[edges[src_col] != edges[tgt_col]]  # drop self-loops

    if w_col is None:
        edges["weight"] = 1.0
        w_col = "weight"
    else:
        edges[w_col] = pd.to_numeric(edges[w_col], errors="coerce").fillna(0)

    # collapse multi-edges
    edges = edges.groupby([src_col, tgt_col], as_index=False)[w_col].sum()
    return edges, src_col, tgt_col, w_col


def load_and_prepare_nodes(nodes_path: str):
    """Read nodes, ensure Id/Label/modularity_class exist (auto-rename if needed)."""
    nodes = pd.read_csv(nodes_path)

    if "Id" not in nodes.columns:
        nodes = nodes.rename(columns={nodes.columns[0]: "Id"})
    if "Label" not in nodes.columns:
        label_guess = detect_column(nodes, ["Label", "label", "name", "channel", "channel_name"])
        if label_guess:
            nodes = nodes.rename(columns={label_guess: "Label"})
        else:
            nodes["Label"] = nodes["Id"]  # fallback

    if "modularity_class" not in nodes.columns:
        raise ValueError("Nodes.csv must contain 'modularity_class' column (e.g., from Gephi).")

    nodes["modularity_class"] = pd.to_numeric(nodes["modularity_class"], errors="coerce")
    return nodes


def build_directed_graph(edges: pd.DataFrame, src_col: str, tgt_col: str, w_col: str):
    """Build a directed weighted NetworkX graph from edge table."""
    G = nx.DiGraph()
    G.add_weighted_edges_from(edges[[src_col, tgt_col, w_col]].itertuples(index=False, name=None))
    print(f"Graph built: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")
    return G


def compute_degree_tables(G: nx.DiGraph, nodes: pd.DataFrame):
    """Compute weighted degrees and merge with node metadata."""
    in_deg  = dict(G.in_degree(weight="weight"))
    out_deg = dict(G.out_degree(weight="weight"))
    tot_deg = dict(G.degree(weight="weight"))

    deg_df = pd.DataFrame({
        "Id": list(G.nodes()),
        "InDegree": [in_deg.get(n, 0) for n in G.nodes()],
        "OutDegree": [out_deg.get(n, 0) for n in G.nodes()],
        "TotalDegree": [tot_deg.get(n, 0) for n in G.nodes()],
    })

    deg_df = deg_df.merge(nodes[["Id", "Label", "modularity_class"]], on="Id", how="left")
    return deg_df


def compute_betweenness_table(G: nx.DiGraph, nodes: pd.DataFrame):
    """Betweenness on undirected projection with distance = 1/weight."""
    GU = nx.Graph(G)
    for _, _, data in GU.edges(data=True):
        w = data.get("weight", 1.0)
        data["inv_w"] = 1.0 / w if w > 0 else float("inf")
    bc = nx.betweenness_centrality(GU, weight="inv_w", normalized=True)

    bc_df = (pd.DataFrame({"Id": list(bc.keys()), "Betweenness": list(bc.values())})
               .merge(nodes[["Id", "Label", "modularity_class"]], on="Id", how="left"))
    return bc_df


def top_k_per_group(df: pd.DataFrame, group_col: str, sort_col: str, k: int):
    """Return top-k rows per group using stable ranking."""
    return (
        df.assign(_rank=df.groupby(group_col)[sort_col].rank(method="first", ascending=False))
          .query("_rank <= @k")
          .sort_values([group_col, sort_col], ascending=[True, False])
          .drop(columns="_rank")
          .reset_index(drop=True)
    )


def structural_summary(G: nx.DiGraph) -> pd.DataFrame:
    """
    Structural metrics:
    - Directed GWC: reachability, density, APL, diameter, efficiency
    - Undirected LCC: same metrics
    """
    # --- Directed GWC ---
    gwc_nodes = max(nx.weakly_connected_components(G), key=len)
    G_gwc = G.subgraph(gwc_nodes).copy()
    n = G_gwc.number_of_nodes()
    m = G_gwc.number_of_edges()

    D_dir = nx.density(G_gwc)

    sum_len = 0
    Nr = 0
    diameter = 0
    for u in G_gwc.nodes():
        dist = nx.single_source_shortest_path_length(G_gwc, u)  # unweighted directed
        for v, d in dist.items():
            if v == u:
                continue
            sum_len += d
            Nr += 1
            if d > diameter:
                diameter = d
    reach = Nr / (n * (n - 1)) if n > 1 else 0
    L_dir = sum_len / Nr if Nr > 0 else float("nan")

    # Global efficiency (directed, unweighted)
    eff_sum = 0
    for u in G_gwc.nodes():
        dist = nx.single_source_shortest_path_length(G_gwc, u)
        for v in G_gwc.nodes():
            if v == u:
                continue
            d = dist.get(v, math.inf)
            eff_sum += (0 if math.isinf(d) else 1 / d)
    E_dir = eff_sum / (n * (n - 1)) if n > 1 else 0

    # --- Undirected projection on same nodes ---
    H = nx.Graph()
    H.add_nodes_from(G_gwc.nodes())
    for i, j, data in G_gwc.edges(data=True):
        w = data.get("weight", 1.0)
        if H.has_edge(i, j):
            H[i][j]["weight"] += w
        else:
            H.add_edge(i, j, weight=w)

    lcc_nodes = max(nx.connected_components(H), key=len)
    H_lcc = H.subgraph(lcc_nodes).copy()
    n_u = H_lcc.number_of_nodes()
    m_u = H_lcc.number_of_edges()

    D_undir = nx.density(H_lcc)

    sum_len_u = 0
    Nr_u = 0
    diameter_u = 0
    for u in H_lcc.nodes():
        dist = nx.single_source_shortest_path_length(H_lcc, u)  # undirected
        for v, d in dist.items():
            if v == u:
                continue
            sum_len_u += d
            Nr_u += 1
            if d > diameter_u:
                diameter_u = d
    L_undir = sum_len_u / Nr_u if Nr_u > 0 else float("nan")
    reach_u = 1.0  # inside LCC everyone is reachable

    # Global efficiency (undirected, unweighted)
    eff_sum_u = 0
    for u in H_lcc.nodes():
        dist = nx.single_source_shortest_path_length(H_lcc, u)
        for v in H_lcc.nodes():
            if v == u:
                continue
            d = dist.get(v, math.inf)
            eff_sum_u += (0 if math.isinf(d) else 1 / d)
    E_undir = eff_sum_u / (n_u * (n_u - 1)) if n_u > 1 else 0

    summary = pd.DataFrame([
        {"Graph": "Directed (GWC)", "n": n, "m": m, "Reachability": reach,
         "Density": D_dir, "APL": L_dir, "Diameter": diameter, "Efficiency": E_dir},
        {"Graph": "Undirected (projection, LCC)", "n": n_u, "m": m_u, "Reachability": reach_u,
         "Density": D_undir, "APL": L_undir, "Diameter": diameter_u, "Efficiency": E_undir}
    ])
    return summary


# ----------------- main -----------------
def main():
    ensure_outdir(OUTPUT_DIR)

    # === Load ===
    edges, src_col, tgt_col, w_col = load_and_prepare_edges(EDGES_PATH)
    nodes = load_and_prepare_nodes(NODES_PATH)
    print(f"Prepared {len(edges)} edges and {len(nodes)} nodes")

    # === Build graph ===
    G = build_directed_graph(edges, src_col, tgt_col, w_col)

    # === Degree tables ===
    deg_df = compute_degree_tables(G, nodes)
    deg_df.to_csv(OUT_DEGREE, index=False)

    # === Betweenness (undirected, 1/weight) ===
    bc_df = compute_betweenness_table(G, nodes)
    bc_df.to_csv(OUT_BETWEEN, index=False)

    # === Print Top-N overall ===
    print("\n=== Top Channels by Weighted Total Degree ===")
    print(deg_df.sort_values("TotalDegree", ascending=False)
              .head(TOP_N_OVERALL)[["Id", "Label", "modularity_class", "TotalDegree"]]
              .to_string(index=False))

    print("\n=== Top Channels by Betweenness (undirected, 1/weight) ===")
    print(bc_df.sort_values("Betweenness", ascending=False)
              .head(TOP_N_OVERALL)[["Id", "Label", "modularity_class", "Betweenness"]]
              .to_string(index=False))

    # === Top-K per modularity_class ===
    topk_deg = top_k_per_group(
        deg_df[["Id", "Label", "modularity_class", "TotalDegree"]],
        "modularity_class", "TotalDegree", TOP_K_PER_CLUSTER
    )
    topk_bc = top_k_per_group(
        bc_df[["Id", "Label", "modularity_class", "Betweenness"]],
        "modularity_class", "Betweenness", TOP_K_PER_CLUSTER
    )

    topk_deg.to_csv(OUT_TOPK_DEG, index=False)
    topk_bc.to_csv(OUT_TOPK_BC, index=False)

    print(f"\n=== Top-{TOP_K_PER_CLUSTER} per Modularity Class by Total Degree ===")
    print(topk_deg.to_string(index=False))
    print(f"\n=== Top-{TOP_K_PER_CLUSTER} per Modularity Class by Betweenness ===")
    print(topk_bc.to_string(index=False))

    # === Structural summary (GWC/LCC) ===
    summary = structural_summary(G)
    print("\n=== Structural Summary ===")
    print(summary.to_string(index=False))
    summary.to_csv(OUT_SUMMARY, index=False)

    # === Saved paths ===
    print("\nSaved:")
    print(f" - {OUT_DEGREE}")
    print(f" - {OUT_BETWEEN}")
    print(f" - {OUT_TOPK_DEG}")
    print(f" - {OUT_TOPK_BC}")
    print(f" - {OUT_SUMMARY}")


if __name__ == "__main__":
    main()
