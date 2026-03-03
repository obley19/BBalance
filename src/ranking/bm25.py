# BM25 Ranking - Thuật toán xếp hạng tìm kiếm
# Code tay, không sử dụng thư viện ranking nào

import math
import pickle


class BM25Ranker:
    """
    Thuật toán BM25 (Best Matching 25).
    Công thức:
    score(D,Q) = sum( IDF(qi) * (tf * (k1+1)) / (tf + k1*(1-b+b*|D|/avgdl)) )
    """

    def __init__(self, k1=1.2, b=0.9):
        # Tham số điều chỉnh BM25
        # k1: kiểm soát mức bão hòa của TF (term frequency)
        # b: kiểm soát mức phạt cho document dài
        self.k1 = k1
        self.b = b

        # Các biến sẽ được load từ file index
        self.inverted_index = {}
        self.doc_lengths = {}
        self.avg_doc_length = 0
        self.doc_count = 0

        # Cache lưu giá trị IDF đã tính (tránh tính lại nhiều lần)
        self.idf_cache = {}

    def load_index(self, index_dir):
        """Load inverted index và metadata từ đĩa."""
        
        # Đọc inverted index (do SPIMI tạo ra)
        index_path = index_dir + "/inverted_index.pkl"
        with open(index_path, 'rb') as f:
            self.inverted_index = pickle.load(f)

        # Đọc metadata (doc_count, doc_lengths, avg_doc_length)
        meta_path = index_dir + "/metadata.pkl"
        with open(meta_path, 'rb') as f:
            metadata = pickle.load(f)

        self.doc_lengths = metadata["doc_lengths"]
        self.avg_doc_length = metadata["avg_doc_length"]
        self.doc_count = metadata["doc_count"]

        print(f"Loaded index: {len(self.inverted_index)} terms, {self.doc_count} docs")

    def compute_idf(self, term):
        """
        Tính IDF (Inverse Document Frequency) cho 1 term.
        IDF = log( (N - n + 0.5) / (n + 0.5) + 1 )
        N = tổng số documents, n = số docs chứa term
        """
        # Kiểm tra cache trước
        if term in self.idf_cache:
            return self.idf_cache[term]

        # Lấy postings list của term
        postings = self.inverted_index.get(term, [])
        doc_freq = len(postings)  # số documents chứa term này

        if doc_freq == 0:
            return 0.0

        # Áp dụng công thức IDF
        numerator = self.doc_count - doc_freq + 0.5
        denominator = doc_freq + 0.5
        idf = math.log(numerator / denominator + 1.0)

        # Lưu vào cache
        self.idf_cache[term] = idf
        return idf

    def rank(self, query, top_k=10):
        """
        Xếp hạng documents theo query.
        Trả về list các tuple (doc_id, score) đã sắp xếp giảm dần.
        """
        if not self.inverted_index or not self.doc_lengths:
            print("Index not loaded. Please call load_index() first.")
            return []

        # Bước 1: Tokenize query (giống cách indexer tokenize)
        query_terms = []
        for t in query.lower().split():
            if len(t) > 1:
                query_terms.append(t)

        if not query_terms:
            return []

        # Bước 2: Tính điểm BM25 cho mỗi document
        # Dùng dict để tích lũy điểm: { doc_id: total_score }
        scores = {}

        for term in query_terms:
            postings = self.inverted_index.get(term, [])
            if not postings:
                continue

            # Tính IDF 1 lần cho mỗi term
            idf = self.compute_idf(term)
            if idf == 0.0:
                continue

            # Duyệt qua tất cả documents chứa term này
            for doc_id, tf in postings:
                # Lấy chiều dài document
                doc_len = self.doc_lengths.get(doc_id, self.avg_doc_length)

                # Áp dụng công thức BM25
                numerator = tf * (self.k1 + 1)
                denominator = tf + self.k1 * (1 - self.b + self.b * doc_len / self.avg_doc_length)
                term_score = idf * (numerator / denominator)

                # Cộng dồn điểm cho document này
                if doc_id in scores:
                    scores[doc_id] += term_score
                else:
                    scores[doc_id] = term_score

        # Bước 3: Sắp xếp theo điểm giảm dần và lấy top K
        result = []
        for doc_id, score in scores.items():
            result.append((doc_id, score))

        # Sort giảm dần theo score
        result.sort(key=lambda x: x[1], reverse=True)

        return result[:top_k]
