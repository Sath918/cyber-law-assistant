import os
import sqlite3
import shutil
from database import init_db, get_db_connection
from rag_pipeline import process_session_document, retrieve_session_context, rebuild_session_index

def run_test():
    print("--- STARTING SESSION RAG INTEGRATION TEST ---")
    
    # 1. Initialize DB
    init_db()
    
    # Clean up previous test runs
    conn = get_db_connection()
    conn.execute("DELETE FROM files WHERE user_id = 9999")
    conn.commit()
    conn.close()
    
    # 2. Setup temporary paths
    user_id = 9999
    session_id = "test_session_abc"
    other_session_id = "test_session_xyz"
    
    filename = "blue_cat_law.txt"
    filepath = os.path.join(os.path.dirname(__file__), filename)
    
    # Write temporary file
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write("Section 999 of the Secret Cyber Act states that posting pictures of blue cats is punishable by a fine of 5 fish. It was enacted on June 29, 2026.")
        
    print(f"Temporary file created at: {filepath}")
    
    try:
        # 3. Insert file into database in 'uploading' state
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO files (user_id, session_id, filename, filepath, status) VALUES (?, ?, ?, ?, ?)",
            (user_id, session_id, filename, filepath, 'uploading')
        )
        file_id = cursor.lastrowid
        conn.commit()
        conn.close()
        print(f"Inserted file in database with ID: {file_id}")
        
        # 4. Run document processing
        print("Processing document (extracting, indexing, merging)...")
        success, info = process_session_document(user_id, session_id, filepath, filename)
        
        if not success:
            print(f"FAIL: process_session_document failed: {info}")
            return
            
        print(f"SUCCESS: Document processed. File hash: {info}")
        
        # Check database status
        conn = get_db_connection()
        row = conn.execute("SELECT status, file_hash FROM files WHERE id = ?", (file_id,)).fetchone()
        conn.close()
        print(f"Database status after processing: {row['status']} (hash: {row['file_hash']})")
        if row['status'] != 'ready':
            print("FAIL: Database status is not 'ready'!")
            return
            
        # 5. Retrieve context for the session
        print("Querying session context for 'blue cats'...")
        results = retrieve_session_context(session_id, "blue cats", k=1)
        if not results:
            print("FAIL: Could not retrieve context for session!")
            return
            
        content = results[0].page_content
        source = results[0].metadata.get("source", "")
        print(f"SUCCESS: Retrieved content: \"{content}\"")
        print(f"SUCCESS: Retrieved source: \"{source}\"")
        
        if "5 fish" not in content or source != filename:
            print("FAIL: Retrieved content or source is incorrect!")
            return
            
        # 6. Verify Session Scoping: Query another session and verify no context is retrieved
        print(f"Querying DIFFERENT session ({other_session_id}) for 'blue cats'...")
        other_results = retrieve_session_context(other_session_id, "blue cats", k=1)
        if other_results:
            print(f"FAIL: Context leaked to session {other_session_id}!")
            return
        print("SUCCESS: Session isolation verified (no context leaked).")
        
        # 7. Test file deletion and index cleanup
        print("Testing file deletion...")
        conn = get_db_connection()
        conn.execute("DELETE FROM files WHERE id = ?", (file_id,))
        conn.commit()
        conn.close()
        
        # Trigger index rebuild
        rebuild_session_index(session_id)
        
        # Query again, context should be empty
        post_del_results = retrieve_session_context(session_id, "blue cats", k=1)
        if post_del_results:
            print("FAIL: Context still exists after file deletion!")
            return
        print("SUCCESS: Index successfully cleared after deleting file.")
        
    finally:
        # Cleanup physical files
        if os.path.exists(filepath):
            os.remove(filepath)
            print(f"Cleaned up physical file: {filepath}")
            
        # Clean cached index
        conn = get_db_connection()
        row = conn.execute("SELECT file_hash FROM files WHERE filepath = ?", (filepath,)).fetchone()
        conn.close()
        if row and row['file_hash']:
            from rag_pipeline import get_file_cache_path
            cache_path = get_file_cache_path(row['file_hash'])
            if os.path.exists(cache_path):
                shutil.rmtree(cache_path)
                print(f"Cleaned up cached file index: {cache_path}")
                
        # Clean session index folder
        from rag_pipeline import get_session_faiss_path
        session_path = get_session_faiss_path(session_id)
        if os.path.exists(session_path):
            shutil.rmtree(session_path)
            print(f"Cleaned up session index: {session_path}")
            
    print("--- ALL RAG INTEGRATION TESTS PASSED SUCCESSFULLY! ---")

if __name__ == '__main__':
    run_test()
