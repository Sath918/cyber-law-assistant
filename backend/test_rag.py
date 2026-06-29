from rag_pipeline import retrieve_context

try:
    print("Testing retrieve_context...")
    res = retrieve_context("what is cyber law?")
    print("SUCCESS")
    print(res)
except Exception as e:
    import traceback
    traceback.print_exc()
