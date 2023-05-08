import requests
import yaml
import os.path

SERVER_ADDR = "http://localhost:5000/"
DOC_ROOT = "./doc/"
DOC_TEMPLATE = {
    """responses: 
        '200':
            content:
                "application/vnd.mason+json":
                    example: {}"""
}

resp_json = requests.get(SERVER_ADDR + "/streaming/").json()
#DOC_TEMPLATE["responses"]["200"]["content"]["application/vnd.mason+json"]["example"] = resp_json
with open(os.path.join(DOC_ROOT, "streaming/get.yml"), "w") as target:
    target.write(yaml.dump(resp_json, default_flow_style=False))
