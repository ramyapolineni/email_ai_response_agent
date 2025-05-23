import json

def load_scenarios(filepath="config/responses.json"):
    with open(filepath, "r") as f:
        return json.load(f)

def get_response_template(category, email_body, scenarios, is_followup=False):
    for scenario in scenarios:
        if scenario["scenarioLabel"] == category:
            # Case 1: Standard flat templates
            if "responseTemplate" in scenario:
                return scenario.get("followupTemplate" if is_followup else "responseTemplate")

            # Case 2: Sub-scenarios with keyword matching
            if "subScenarios" in scenario:
                for sub in scenario["subScenarios"]:
                    if any(keyword.lower() in email_body.lower() for keyword in sub.get("keywords", [])):
                        return sub["responseTemplate"]
                
                # Default fallback if no keyword matches
                return scenario["subScenarios"][-1]["responseTemplate"]

    return "Thank you for your message. We'll get back to you shortly."



