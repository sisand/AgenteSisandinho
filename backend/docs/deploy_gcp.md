gcloud run deploy sisandinho-frontend `
>>   --source ./frontend `
>>   --platform managed `
>>   --region southamerica-east1 `
>>   --allow-unauthenticated `
>>   --set-secrets="/root/.streamlit/secrets.toml=FRONTEND_SECRETS_TOML:latest"

 gcloud run deploy sisandinho-backend `
>>   --source ./backend `
>>   --platform managed `
>>   --region southamerica-east1 `
>>   --allow-unauthenticated `
>>   --set-secrets="SUPABASE_URL=SUPABASE_URL:latest,SUPABASE_KEY=SUPABASE_KEY:latest,OPENAI_API_KEY=OPENAI_API_KEY:latest,WEAVIATE_API_KEY=WEAVIATE_API_KEY:latest,ALLOWED_API_KEYS=ALLOWED_API_KEYS:latest,HUGGING_FACE_HUB_TOKEN=HUGGING_FACE_HUB_TOKEN:latest,MOVI_TOKEN=MOVI_TOKEN:latest,ENVIRONMENT=ENVIRONMENT:latest"


