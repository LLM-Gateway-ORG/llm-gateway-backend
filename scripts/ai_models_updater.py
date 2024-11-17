import json
import requests
import os

if __name__ == "__main__":
    try:
        # Fetching the model data
        url = "https://raw.githubusercontent.com/BerriAI/litellm/main/model_prices_and_context_window.json"
        response = requests.get(url)
        response.raise_for_status()
        llmlite_models_list = response.json()

        # Filtering models except 'sample_spec'
        litellm_models = { key: value for key, value in llmlite_models_list.items() if key != "sample_spec"}

        # Check if `ai_models_list.json` exists
        if os.path.exists("ai_models_list.json"):
            with open("ai_models_list.json", "r") as f:
                existing_data = json.load(f)
        else:
            existing_data = {"litellm_models": [], "other_models": []}

        # Update the `litellm_models` and retain `other_models`
        updated_data = {
            "litellm_models": litellm_models,
            "other_models": existing_data.get("other_models", []),
        }

        # Writing the updated data back to the JSON file
        with open("ai_models_list.json", "w") as f:
            json.dump(updated_data, f, indent=4)

        print("ai_models_list.json updated successfully.")

    except requests.RequestException as e:
        print(f"Error fetching models list: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")
