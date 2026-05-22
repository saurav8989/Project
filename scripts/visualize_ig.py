import json
import glob
import os

html_content = """
<!DOCTYPE html>
<html>
<head>
    <title>Nepal Immunization FHIR Implementation Guide</title>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; background-color: #f8f9fa; margin: 0; padding: 20px; color: #333; }
        .header { background: linear-gradient(135deg, #0d6efd, #0dcaf0); color: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
        h1, h2 { margin-top: 0; }
        .profile-container { background: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
        table { width: 100%; border-collapse: collapse; margin-top: 15px; }
        th, td { text-align: left; padding: 12px; border-bottom: 1px solid #dee2e6; }
        th { background-color: #f1f3f5; font-weight: 600; color: #495057; }
        tr:hover { background-color: #f8f9fa; }
        .badge { display: inline-block; padding: 4px 8px; font-size: 0.85em; font-weight: 600; background-color: #e9ecef; color: #495057; border-radius: 4px; margin-right: 5px; }
        .type-ref { background-color: #cfe2ff; color: #084298; }
        .must-support { color: #dc3545; font-weight: bold; }
        .url { font-family: monospace; font-size: 0.9em; color: #6c757d; }
    </style>
</head>
<body>
    <div class="header">
        <h1>🇳🇵 Nepal Immunization FHIR Implementation Guide</h1>
        <p>Generated FHIR R4 StructureDefinitions & Terminology</p>
    </div>
"""

files = glob.glob("fsh/fsh-generated/resources/*.json")
for file_path in files:
    with open(file_path, "r") as f:
        data = json.load(f)
    
    res_type = data.get("resourceType")
    name = data.get("name", "Unknown")
    url = data.get("url", "")
    description = data.get("description", "")
    
    if res_type == "StructureDefinition":
        html_content += f'<div class="profile-container">'
        html_content += f'<h2>Profile: {name}</h2>'
        html_content += f'<p class="url">{url}</p>'
        html_content += f'<p>{description}</p>'
        
        html_content += '<table>'
        html_content += '<tr><th>Element</th><th>Flags</th><th>Card.</th><th>Type</th><th>Description / Constraints</th></tr>'
        
        elements = data.get("differential", {}).get("element", [])
        for el in elements:
            el_id = el.get("id", "")
            card = f"{el.get('min', '')}..{el.get('max', '')}"
            if card == "..": card = ""
            
            flags = "S" if el.get("mustSupport") else ""
            
            types = []
            for t in el.get("type", []):
                t_code = t.get("code", "")
                if "targetProfile" in t:
                    profiles = [p.split("/")[-1] for p in t["targetProfile"]]
                    t_code += f"({', '.join(profiles)})"
                if "profile" in t:
                    profiles = [p.split("/")[-1] for p in t["profile"]]
                    t_code += f"({', '.join(profiles)})"
                types.append(f'<span class="badge type-ref">{t_code}</span>')
                
            desc = el.get("short", "")
            if "fixedUri" in el: desc += f" <br><b>Fixed:</b> {el['fixedUri']}"
            if "fixedCode" in el: desc += f" <br><b>Fixed:</b> {el['fixedCode']}"
            if "patternCodeableConcept" in el: 
                codes = [c.get('code') for c in el['patternCodeableConcept'].get('coding', [])]
                desc += f" <br><b>Pattern:</b> {codes}"
                
            html_content += f'<tr>'
            html_content += f'<td><b>{el_id}</b></td>'
            html_content += f'<td class="must-support">{flags}</td>'
            html_content += f'<td>{card}</td>'
            html_content += f'<td>{"".join(types)}</td>'
            html_content += f'<td>{desc}</td>'
            html_content += f'</tr>'
            
        html_content += '</table></div>'

    elif res_type == "ValueSet" or res_type == "CodeSystem":
        html_content += f'<div class="profile-container">'
        html_content += f'<h2>{res_type}: {name}</h2>'
        html_content += f'<p class="url">{url}</p>'
        html_content += f'<p>{description}</p>'
        if res_type == "CodeSystem":
            html_content += '<table><tr><th>Code</th><th>Display</th><th>Definition</th></tr>'
            for concept in data.get("concept", []):
                html_content += f"<tr><td><code>{concept.get('code')}</code></td><td>{concept.get('display')}</td><td>{concept.get('definition', '')}</td></tr>"
            html_content += '</table>'
        html_content += '</div>'

html_content += "</body></html>"

with open("outputs/fhir_ig_visualizer.html", "w") as f:
    f.write(html_content)

print("Generated HTML Viewer at outputs/fhir_ig_visualizer.html")
