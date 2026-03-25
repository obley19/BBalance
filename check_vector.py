import os
import pickle

faiss_path = "data/vector_index/faiss_index.bin"
mapping_path = "data/vector_index/doc_id_mapping.pkl"

faiss_size = os.path.getsize(faiss_path)
with open(mapping_path, "rb") as f:
    doc_ids = pickle.load(f)

num_docs = len(doc_ids)
dim = 768
expected_size = num_docs * dim * 4  # float32

print(f"So luong documents: {num_docs:,}")
print(f"FAISS file thuc te:   {faiss_size:,} bytes ({faiss_size/1e9:.2f} GB)")
print(f"FAISS file ly thuyet: {expected_size:,} bytes ({expected_size/1e9:.2f} GB)")
print(f"Chenh lech: {faiss_size - expected_size:,} bytes (FAISS header)")
print()

match = abs(faiss_size - expected_size) < 100000
if match:
    print("KIEM TRA: KHOP - Data hop le!")
else:
    print("KIEM TRA: KHONG KHOP - Co van de!")
print()
print(f"5 doc_id dau: {doc_ids[:5]}")
print(f"5 doc_id cuoi: {doc_ids[-5:]}")
has_dup = len(doc_ids) != len(set(doc_ids))
print(f"Co doc_id trung lap: {has_dup}")
