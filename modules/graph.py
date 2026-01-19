from streamlit_agraph import agraph, Node, Edge, Config

def generate_graph(results, target_name):
    nodes = []
    edges = []
    
    # 1. Création du Nœud Central (La Cible)
    # id doit être unique
    nodes.append(Node(
        id="TARGET", 
        label=target_name, 
        size=40, 
        color="#ff4b4b", # Rouge Streamlit
        shape="dot"
    ))

    # 2. Création des Nœuds Satellites (Les comptes trouvés)
    for i, res in enumerate(results):
        site_name = res['site']
        category = res.get('category', 'autre')
        
        # Choix de la couleur selon la catégorie
        node_color = "#808080" # Gris par défaut
        if category == "social": node_color = "#1DA1F2" # Bleu Twitter
        elif category == "coding" or category == "tech": node_color = "#00C853" # Vert GitHub
        elif category == "video": node_color = "#FF0000" # Rouge YouTube
        elif category == "mail-leak": node_color = "#FFD700" # Jaune Alerte
        elif category == "hors-piste": node_color = "#9C27B0" # Violet Mystère

        # ID unique pour chaque nœud (ex: node_0, node_1...)
        node_id = f"node_{i}"
        
        # Le label affiché sous le point
        label_text = f"{site_name}\n({res['username'][:10]}..)"
        
        nodes.append(Node(
            id=node_id,
            label=label_text,
            size=20,
            color=node_color,
            shape="dot"
        ))
        
        # 3. Création du Lien (Arête)
        edges.append(Edge(
            source="TARGET",
            target=node_id,
            color="#555555",
            length=200 # Distance du lien
        ))

    # 4. Configuration de la Physique du Graphe
    config = Config(
        width=700,
        height=500,
        directed=True, 
        physics=True, 
        hierarchical=False,
        nodeHighlightBehavior=True,
        highlightColor="#F7A7A6", # Couleur quand on passe la souris
        collapsible=True
    )

    # 5. Affichage
    return agraph(nodes=nodes, edges=edges, config=config)