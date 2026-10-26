# CommunityAI — Professional UI update

A clearer civic-tech prototype for organizing community concerns and suggesting next steps.

## Features
- Plain-language report form and input validation
- Keyword-based category suggestions
- Transparent priority score: severity 40%, urgency 35%, estimated reach 25%
- Search and filter reports, update status, export CSV
- Category-based opportunity recommendations
- Map for reports with coordinates
- Fictional demo reports labelled as demo data
- Clear explanations, limitations, and responsible-use guidance
- Professional Streamlit theme

## Run on Windows
Open Command Prompt in this folder and run:

```cmd
py -m venv .venv
.venv\\Scripts\\activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

## Deploy
Upload `app.py`, `requirements.txt`, `README.md`, and `.streamlit/config.toml` to the root of your GitHub repository. Then deploy with Streamlit Community Cloud. Guide: https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app

## Honest limitations
This version does not call a generative AI model. It uses keyword rules for category suggestions and category-based checklists for recommendations. Reports are stored in Streamlit session state, not a permanent database. Demo records and coordinates are illustrative. Do not enter sensitive personal information.
