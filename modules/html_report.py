import base64

def generate_html(results, target_name):
    # CSS Dark Mode "Hacker Style"
    css = """
    <style>
        body { background-color: #0e1117; color: #00ff41; font-family: 'Courier New', monospace; padding: 20px; }
        .card { border: 1px solid #333; background: #161b22; margin: 10px 0; padding: 15px; border-radius: 5px; }
        .card:hover { border-color: #00ff41; box-shadow: 0 0 10px #00ff41; }
        .tag { display: inline-block; padding: 2px 8px; border-radius: 3px; font-size: 0.8em; font-weight: bold; }
        .social { background: #1DA1F2; color: white; }
        .coding { background: #2dba4e; color: white; }
        .leak { background: #ff4b4b; color: white; }
        .adult { background: #d6006f; color: white; }
        h1 { border-bottom: 2px solid #333; padding-bottom: 10px; }
        a { color: #58a6ff; text-decoration: none; }
        .metadata { color: #8b949e; font-size: 0.9em; margin-top: 5px; }
        .stat-box { display: flex; gap: 20px; margin-bottom: 30px; }
        .stat { background: #21262d; padding: 15px; min-width: 150px; text-align: center; border-radius: 5px; }
        .stat h2 { margin: 0; color: white; }
    </style>
    """
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head><title>Rapport GhostTracker - {target_name}</title>{css}</head>
    <body>
        <h1>👻 GhostTracker Report : {target_name}</h1>
        
        <div class="stat-box">
            <div class="stat"><h2>{len(results)}</h2><p>Traces</p></div>
            <div class="stat"><h2>{sum(1 for r in results if r.get('category') == 'leaks' or 'leak' in r.get('category', ''))}</h2><p>Alertes</p></div>
        </div>

        <div id="container">
    """
    
    for res in results:
        cat = res.get('category', 'autre')
        meta_html = ""
        if res.get('metadata'):
            for k, v in res['metadata'].items():
                if "Avatar" not in k:
                    meta_html += f"<div><strong>{k}:</strong> {v}</div>"
        
        html += f"""
        <div class="card">
            <span class="tag {cat}">{cat.upper()}</span>
            <h3><a href="{res['url']}" target="_blank">{res['site']} - {res['username']}</a></h3>
            <div class="metadata">{meta_html}</div>
        </div>
        """
        
    html += "</div></body></html>"
    return html.encode('utf-8')