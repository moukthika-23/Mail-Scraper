import os
from huggingface_hub import HfApi, login
from dotenv import dotenv_values

def deploy_to_hf():
    print("🚀 Starting Automated Hugging Face Deployment...")
    
    # Check for token
    token = os.environ.get("HF_TOKEN")
    if not token:
        print("❌ Error: Please set the HF_TOKEN environment variable.")
        print("Example (Powershell): $env:HF_TOKEN='hf_your_token'")
        return

    login(token=token)
    api = HfApi()

    # The repo ID on huggingface (format: username/space-name)
    # CHANGE 'CaptainShyamal' IF YOUR HUGGING FACE USERNAME IS DIFFERENT
    repo_id = "CaptainShyamal/mailsight-api"
    
    try:
        print(f"📦 Creating/Checking Space '{repo_id}'...")
        api.create_repo(repo_id=repo_id, repo_type="space", space_sdk="docker", exist_ok=True)
        
        print("🔐 Uploading secrets from .env file...")
        env_path = os.path.join("backend", ".env")
        secrets = dotenv_values(env_path)
        
        for key, value in secrets.items():
            if value and not key.startswith("DEBUG") and key != "HF_TOKEN":
                api.add_space_secret(repo_id=repo_id, key=key, value=str(value))
                print(f"  ✓ Secret {key} uploaded")
                
        print("📂 Uploading backend codebase to the Space...")
        api.upload_folder(
            folder_path="backend",
            repo_id=repo_id,
            repo_type="space"
        )
        print("✅ Deployment triggered successfully!")
        print(f"🌍 Your API will be live at: https://captainshyamal-mailsight-api.hf.space")
        
    except Exception as e:
        print(f"❌ Deployment failed: {e}")

if __name__ == "__main__":
    deploy_to_hf()
