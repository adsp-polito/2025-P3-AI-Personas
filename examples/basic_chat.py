"""
Basic example showing how to use the QA service for simple chat interactions.

Run this script to see a minimal working example.
"""

from adsp.app import QAService


def main():
    # Initialize the QA service
    qa = QAService()

    print("=== Basic Chat Example ===\n")

    # Simple query
    persona_id = "default"
    query = "What kind of coffee do you like?"

    print(f"User: {query}")

    # Get response
    answer = qa.ask(persona_id=persona_id, query=query)

    print(f"Assistant: {answer}\n")

    # Follow-up query
    query2 = "Tell me more about that"
    print(f"User: {query2}")

    answer2 = qa.ask(persona_id=persona_id, query=query2)
    print(f"Assistant: {answer2}\n")

    print("=== With Metadata ===\n")

    # Get response with metadata
    response = qa.ask_with_metadata(
        persona_id=persona_id,
        query="What's your favorite brewing method?",
        session_id="example-session",
        top_k=3
    )

    print(f"Answer: {response.answer}")
    print(f"Context length: {len(response.context)} chars")
    print(f"Citations: {len(response.citations)}")


if __name__ == "__main__":
    main()
