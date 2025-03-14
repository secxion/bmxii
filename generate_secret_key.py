import secrets

# Generate a random 32-byte hex string
secret_key = secrets.token_hex(32)

# Save it to a .env file
with open(".env", "w") as env_file:
    env_file.write(f"FLASK_SECRET_KEY={secret_key}\n")

print(f"Secret key generated and saved to .env: {secret_key}")
