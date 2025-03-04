import google.generativeai as genai
import os

genai.configure(api_key="AIzaSyCKjQxgtWj-fG77rwpPe3wNT2xljUEleDU")

models = genai.list_models()
for model in models:
    print(model.name)
