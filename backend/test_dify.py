from app.services.dify_client import dify_client

try:
    response = dify_client.chat(
        message="Bonjour",
        user="test-user"
    )

    print("\n===== RÉPONSE DIFY =====\n")
    print(response)

except Exception as e:
    print("\nERREUR :")
    print(e)