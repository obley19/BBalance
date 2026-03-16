# **BÁO CÁO MILESTONE 2: CORE SEARCH ENGINE**

## **Môn: SEG301 – E-Commerce Search Engine Project**

| Thành viên | MSSV | Vai trò | Đóng góp Milestone 2 |
| :---- | :---- | :---- | :---- |
| **Trịnh Khải Nguyên** | QE190129 | Crawler Lead | SPIMI Indexer, Merging, Unit Tests |
| **Lê Hoàng Hữu** | QE190142 | Crawler Dev | Index Compression, BM25 Tuning |
| **Ngô Tuấn Hoàng** | QE190076 | Crawler Dev | Search Engine, Console App, Query Expansion |

## **1\. Tổng Quan Milestone 2**

### **1.1. Mục tiêu**

Milestone 2 tập trung xây dựng **Core Search Engine** hoàn chỉnh trên nền dữ liệu đã xử lý từ Milestone 1 (\~1.45 triệu sản phẩm, file MASTER\_DATA\_CLEAN.jsonl), bao gồm:

* Xây dựng Inverted Index bằng thuật toán **SPIMI** (Single-Pass In-Memory Indexing)  
* Triển khai thuật toán xếp hạng **BM25** (Best Matching 25\)  
* Tích hợp thành Search Engine có Query Expansion  
* Console App cho phép người dùng tìm kiếm sản phẩm  
* Viết Unit Tests kiểm thử các thành phần

## **2\. Kiến Trúc Hệ Thống**

### **2.1. Sơ đồ kiến trúc tổng quan**

graph TB  
    subgraph "Presentation Layer"  
        A\["Console App\<br/\>(run\_search.py)"\]  
    end

    subgraph "Application Layer"  
        B\["Search Engine\<br/\>(src/search/engine.py)"\]  
        C\["Query Expansion\<br/\>(Synonym Map)"\]  
    end

    subgraph "Core Engine Layer"  
        D\["BM25 Ranker\<br/\>(src/ranking/bm25.py)"\]  
        E\["SPIMI Indexer\<br/\>(src/indexer/spimi.py)"\]  
        F\["Index Compression\<br/\>(VB \+ Gamma Encoding)"\]  
        G\["N-Way Merge\<br/\>(src/indexer/merging.py)"\]  
    end

    subgraph "Data Layer"  
        H\["inverted\_index.pkl\<br/\>(\~185 MB)"\]  
        I\["metadata.pkl\<br/\>(\~33 MB)"\]  
        J\["Document Store\<br/\>(MASTER\_DATA\_CLEAN.jsonl \~1.05 GB)"\]  
    end

    subgraph "Milestone 1 Output"  
        K\["Raw Crawled Data\<br/\>Shopee | Tiki | Chợ Tốt | eBay\<br/\>\~1.45M sản phẩm"\]  
    end

    A \--\>|"user query"| B  
    B \--\> C  
    C \--\>|"expanded query"| D  
    D \--\>|"ranked doc\_ids"| B  
    B \--\>|"lookup product info"| J  
    D \--\>|"load index"| H  
    D \--\>|"load metadata"| I  
    E \--\>|"build blocks"| G  
    G \--\>|"merge"| H  
    E \--\>|"save"| I  
    E \--\>|"compress"| F  
    K \--\>|"input"| E  
    K \--\>|"input"| J

### **2.2. Workflow xây dựng Index (Offline \- chạy 1 lần)**

**Sơ đồ luồng xử lý:**

flowchart TD  
    Drive\[("MASTER\_DATA\_CLEAN.jsonl\<br/\>\~1.45M products")\] \--\>|Streaming| Reader("Streaming Reader\<br/\>O(1) RAM")  
    Reader \--\> Tokenizer("Tokenizer\<br/\>lowercase \+ split")  
    Reader \-.-\> Meta("Tính doc\_lengths\<br/\>+ avg\_doc\_length")  
    Meta \-.-\> MetaFile\[("metadata.pkl")\]  
      
    Tokenizer \--\> Check{"Block đầy?\<br/\>\> 500MB"}  
      
    Check \-- Chưa \--\> RAM\["Thêm vào Block RAM\<br/\>term → postings list"\]  
    RAM \-.-\> Tokenizer  
      
    Check \-- Rồi \--\> Flush\["Flush: Sort \+ Write\<br/\>block\_N.pkl"\]  
    Flush \-.-\> Tokenizer  
      
    Flush \--\> Merge(("N-Way Merge"))  
    Merge \--\> Out\[("inverted\_index.pkl")\]  
      
    style Drive fill:\#f9f,stroke:\#333,stroke-width:2px  
    style Out fill:\#bbf,stroke:\#333,stroke-width:2px  
    style MetaFile fill:\#bbf,stroke:\#333,stroke-width:2px

**Các bước thực hiện chính:**

1. **Đọc dữ liệu (Streaming):** Đọc tuần tự từng dòng từ file MASTER\_DATA\_CLEAN.jsonl giúp tối ưu RAM (![][image1]) thay vì load toàn bộ file. Tiến hành đếm và trích xuất chiều dài tài liệu để bảo lưu vào metadata.pkl.  
2. **Tiền xử lý (Tokenizer):** Chuẩn hóa chữ thường (lowercase) và tách token (split) đối với các trường văn bản.  
3. **Xây dựng Block (In-Memory Indexing):** Đưa các token vào block tạm trên RAM. Nếu dung lượng block đầy (vượt ngưỡng 500MB), quá trình **Flush** sẽ được kích hoạt: sắp xếp theo bảng chữ cái và đẩy ra file block\_N.pkl. Nếu chưa đầy, tiếp tục đọc dòng mới.  
4. **Gộp Block (N-Way Merge):** Ghép tuần tự các file block theo thứ tự để hợp nhất thành một inverted\_index.pkl hoàn chỉnh.

### **2.3. Workflow tìm kiếm (Online \- mỗi query)**

**Sơ đồ luồng xử lý:**

flowchart TD  
    Input(\["User Input\<br/\>'ip 17 prm'"\]) \--\> Exp\["Query Expansion\<br/\>'iphone 17 pro max'"\]  
    Exp \--\> Seg\["PyVi Segmentation\<br/\>'iphone 17 pro max'"\]  
    Seg \--\> Tok\["Tokenize\<br/\>\['iphone', '17', 'pro', 'max'\]"\]  
    Tok \--\> BM\["BM25 Scoring\<br/\>IDF × TF normalization"\]  
    BM \--\> Boost\["Title Relevance Boost\<br/\>Coverage-based scoring"\]  
    Boost \--\> Lookup\[("Doc Store Lookup\<br/\>Enrich title, price, link")\]  
    Lookup \--\> Div\["Platform Diversification\<br/\>Round-Robin các sàn"\]  
    Div \--\> Output(\["Display Results\<br/\>Console / UI"\])  
      
    style Input fill:\#d4edda,stroke:\#28a745,stroke-width:2px  
    style Output fill:\#d4edda,stroke:\#28a745,stroke-width:2px  
    style Lookup fill:\#f8d7da,stroke:\#dc3545,stroke-width:2px

**Các bước thực hiện chính:**

1. **Chuẩn hóa truy vấn (Preprocessing):**  
   * **Query Expansion:** Chuyển đổi các từ viết tắt phổ biến thành dạng đầy đủ (VD: ip ![][image2] iphone, prm ![][image2] pro max).  
   * **PyVi Segmentation & Tokenize:** Tách từ tiếng Việt đồng bộ với dữ liệu đã được index, chia nhỏ câu truy vấn thành các token rời rạc.  
2. **Xếp hạng kết quả (Ranking):**  
   * **BM25 Scoring:** Chấm điểm độ liên quan của từng sản phẩm thông qua thuật toán BM25 (tính toán tần suất từ khóa hiển thị).  
   * **Title Relevance Boost:** Cộng dồn điểm số (nhân hệ số) đối với các kết quả có độ bao phủ tiêu đề sát nhất với ý định người dùng (tránh các trường hợp spam keyword / phụ kiện).  
3. **Tổng hợp và Hiển thị (Display):**  
   * **Doc Store Lookup:** Truy xuất thông tin (tiêu đề, giá bán, link) trực tiếp, cực nhanh từ bộ nhớ dựa theo File Id (![][image1]).  
   * **Platform Diversification:** Lấy đan xen kết quả từ các sàn thương mại điện tử (Shopee, Tiki...) theo quy tắc vòng lặp (Round-Robin), đảm bảo kết quả đa dạng và minh bạch về giá trị.

## **3\. Chi Tiết Các Thành Phần**

### **3.1. SPIMI Indexer (src/indexer/)**

**Mục đích:** Xây dựng Inverted Index từ tập dữ liệu lớn (\~1.05 GB) mà không bị tràn RAM, sử dụng kỹ thuật chia block và merge.

#### **3.1.1. Thuật toán SPIMI (src/indexer/spimi.py)**

**Single-Pass In-Memory Indexing** hoạt động như sau:

1. **Đọc streaming:** Đọc từng dòng JSONL — O(1) RAM per document, không load toàn bộ file  
2. **Tokenize:** Lowercase \+ split theo khoảng trắng, loại token 1 ký tự (nhiễu). Ưu tiên sử dụng trường title\_segmented (đã tách từ bởi PyVi ở Milestone 1), fallback sang title\_clean và title  
3. **Build block:** Mỗi document được thêm vào block RAM hiện tại dưới dạng term → \[(doc\_id, tf)\]  
4. **Flush block:** Khi bộ nhớ ước tính vượt ngưỡng (500MB), block được **sort theo alphabet** và ghi ra file .pkl  
5. **Lưu metadata:** doc\_count, doc\_lengths, avg\_doc\_length — contract giữa Indexer và Ranker

**Code — Tokenizer & add\_document:**

\# src/indexer/spimi.py

def tokenize(self, text):  
    """Tách text thành danh sách tokens."""  
    if not text:  
        return \[\]                           \# Guard clause: tránh crash khi text rỗng  
    tokens \= text.lower().split()           \# Lowercase \+ tách theo khoảng trắng  
    return \[t for t in tokens if len(t) \> 1\]  \# Loại token 1 ký tự (nhiễu)

def add\_document(self, doc\_id, tokens):  
    """Thêm 1 document vào block hiện tại trên RAM."""  
    \# Bước 1: Đếm TF (Term Frequency) cho document này  
    tf\_map \= defaultdict(int)  
    for token in tokens:  
        tf\_map\[token\] \+= 1              \# Đếm: "iphone" xuất hiện 3 lần → tf \= 3

    \# Bước 2: Ghi posting vào inverted index trên RAM  
    for term, tf in tf\_map.items():  
        self.current\_block\[term\].append((doc\_id, tf))  \# term → \[(doc\_id, tf)\]

    \# Bước 3: Lưu chiều dài document (cho BM25 tính length normalization)  
    self.doc\_lengths\[doc\_id\] \= len(tokens)

    \# Bước 4: Ước tính RAM tăng thêm (\~50 bytes/posting)  
    self.current\_memory \+= len(tf\_map) \* 50

**Code — Vòng lặp index chính (Streaming \+ Flush):**

\# src/indexer/spimi.py — hàm build\_index()

with open(documents\_path, 'r', encoding='utf-8') as f:  
    for line in f:                                        \# Từng dòng một \= O(1) RAM  
        doc \= json.loads(line.strip())  
        doc\_id \= doc.get('id', '')

        \# Ưu tiên title\_segmented (đã tách từ bởi PyVi ở M1)  
        text \= doc.get('title\_segmented') or doc.get('title\_clean') or doc.get('title', '')  
        tokens \= self.tokenize(text)

        self.add\_document(doc\_id, tokens)  
        doc\_count \+= 1

        if self.is\_block\_full():                          \# RAM đầy?  
            block\_path \= self.write\_block\_to\_disk(blocks\_dir)  \# → Flush ra disk\!  
            block\_files.append(block\_path)

**Code — Flush block xuống disk:**

def write\_block\_to\_disk(self, output\_dir):  
    """Flush block hiện tại xuống ổ cứng, giải phóng RAM."""  
    \# Sort theo alphabet trước khi ghi (yêu cầu của SPIMI để merge sau)  
    sorted\_block \= {}  
    for key in sorted(self.current\_block.keys()):  
        sorted\_block\[key\] \= self.current\_block\[key\]

    block\_path \= os.path.join(output\_dir, f"block\_{self.block\_count}.pkl")  
    with open(block\_path, 'wb') as f:  
        pickle.dump(sorted\_block, f)      \# Serialize ra file nhị phân

    \# Reset trạng thái RAM  
    self.current\_block \= defaultdict(list)   \# Giải phóng RAM  
    self.current\_memory \= 0  
    self.block\_count \+= 1  
    return block\_path

**Độ phức tạp:**

* Thời gian: O(n) với n \= tổng số tokens toàn corpus — mỗi token chỉ xử lý 1 lần (single-pass)  
* Không gian: O(block\_size) RAM — không phụ thuộc kích thước corpus tổng thể  
* Ước tính bộ nhớ: \~50 bytes/posting (gồm tuple (doc\_id, tf) \+ overhead dictionary)

#### **3.1.2. N-Way Merge (src/indexer/merging.py)**

Ghép tuần tự các block index đã sort thành 1 Inverted Index hoàn chỉnh.

\# src/indexer/merging.py

def merge\_two\_blocks(block1, block2):  
    """Ghép 2 block dictionary lại thành 1."""  
    merged \= {}  
    all\_terms \= set(block1.keys()) | set(block2.keys())   \# Union tất cả terms

    for term in all\_terms:  
        \# Nối danh sách postings của cùng 1 term từ 2 block  
        list1 \= block1.get(term, \[\])  
        list2 \= block2.get(term, \[\])  
        merged\[term\] \= list1 \+ list2

    \# Sắp xếp lại theo alphabet  
    return {key: merged\[key\] for key in sorted(merged.keys())}

def n\_way\_merge(block\_files, output\_path):  
    """Ghép tất cả file block thành 1 index cuối cùng (sequential merge)."""  
    with open(block\_files\[0\], 'rb') as f:  
        merged \= pickle.load(f)          \# Load block đầu làm base

    for i in range(1, len(block\_files)):  
        with open(block\_files\[i\], 'rb') as f:  
            block \= pickle.load(f)  
        merged \= merge\_two\_blocks(merged, block)   \# Merge lần lượt từng cặp

    with open(output\_path, 'wb') as f:  
        pickle.dump(merged, f)

**Kết quả:** file inverted\_index.pkl (\~185 MB), cấu trúc: {term: \[(doc\_id, tf), ...\]}

**Lưu ý:** Hiện tại dùng sequential pairwise merge. Với số block nhỏ (\< 5 block) thì hiệu quả đủ tốt. Có thể chuyển sang min-heap k-way merge nếu cần tối ưu trong tương lai.

#### **3.1.3. Index Compression (src/indexer/compression.py)**

Triển khai 2 phương pháp nén chỉ mục theo lý thuyết Information Retrieval:

| Phương pháp | Mô tả | Ứng dụng |
| :---- | :---- | :---- |
| **Variable Byte Encoding** | Mỗi byte dùng 7 bit data \+ 1 bit cao nhất làm cờ kết thúc. Số nhỏ dùng ít byte hơn | Nén doc\_id gaps và tf trong postings list |
| **Elias Gamma Encoding** | Gồm phần unary (biểu diễn độ dài) \+ phần binary offset. Hiệu quả cho số nhỏ | Nén các khoảng cách (gaps) giữa doc\_id liền kề |

\# src/indexer/compression.py

def variable\_byte\_encode(number):  
    """  
    Mã hóa số nguyên bằng Variable Byte.  
    Mỗi byte dùng 7 bit chứa data, 1 bit cao nhất làm cờ kết thúc.  
    """  
    if number \== 0:  
        return bytes(\[128\])

    result \= \[\]  
    while True:  
        result.insert(0, number % 128\)  
        if number \< 128:  
            break  
        number \= number // 128

    result\[-1\] \+= 128    \# Đánh dấu byte cuối cùng (bit cao \= 1\)  
    return bytes(result)

def gamma\_encode(number):  
    """  
    Mã hóa số nguyên bằng Elias Gamma.  
    Gồm phần unary (biểu diễn độ dài) \+ phần offset (giá trị).  
    """  
    binary \= bin(number)\[2:\]   \# Chuyển sang nhị phân, bỏ prefix "0b"  
    length \= len(binary)

    unary \= '1' \* (length \- 1\) \+ '0'   \# Phần unary: (length-1) bit 1 \+ 1 bit 0  
    offset \= binary\[1:\]                  \# Phần offset: binary bỏ bit đầu

    return unary \+ offset

**Ví dụ:** Số 5 (binary: 101, length=3)

* Unary: 110 (2 bit 1 \+ 1 bit 0\)  
* Offset: 01 (binary bỏ bit đầu)  
* Gamma code: 11001

**Hiện trạng:** Module compression đã triển khai đầy đủ. Index hiện dùng Python pickle (tiện cho development). Dự kiến tích hợp vào pipeline ở Milestone 3\.

### **3.2. BM25 Ranker (src/ranking/bm25.py)**

**Mục đích:** Xếp hạng documents theo mức độ phù hợp với truy vấn, dựa trên mô hình xác suất.

#### **3.2.1. Công thức BM25**

score(D, Q) \= Σ IDF(qi) × \[ tf × (k1 \+ 1\) \] / \[ tf \+ k1 × (1 \- b \+ b × |D| / avgdl) \]

Trong đó:

* **IDF(qi)** \= log( (N \- n \+ 0.5) / (n \+ 0.5) \+ 1 ) — Term xuất hiện trong ít document → IDF cao  
* **tf**: Term Frequency — số lần term xuất hiện trong document D  
* **k1** (= 1.2): Kiểm soát mức bão hòa của TF (diminishing returns)  
* **b** (= 0.9): Kiểm soát mức phạt cho document dài (length normalization)  
* **|D|**: Chiều dài document (số tokens), **avgdl**: Chiều dài trung bình

#### **3.2.2. Code triển khai**

\# src/ranking/bm25.py

class BM25Ranker:  
    def \_\_init\_\_(self, k1=1.2, b=0.9):  
        self.k1 \= k1     \# Điều chỉnh qua tune.py  
        self.b \= b  
        self.idf\_cache \= {}   \# Cache tránh tính log lại nhiều lần

    def compute\_idf(self, term):  
        """Tính IDF với cache."""  
        if term in self.idf\_cache:  
            return self.idf\_cache\[term\]   \# Cache hit: trả ngay

        postings \= self.inverted\_index.get(term, \[\])  
        doc\_freq \= len(postings)   \# n: số docs chứa term

        if doc\_freq \== 0:  
            return 0.0

        \# Công thức IDF chuẩn Robertson-Spärck Jones  
        idf \= math.log((self.doc\_count \- doc\_freq \+ 0.5) / (doc\_freq \+ 0.5) \+ 1.0)  
        self.idf\_cache\[term\] \= idf   \# Lưu cache  
        return idf

    def rank(self, query, top\_k=10):  
        """Xếp hạng documents theo BM25."""  
        scores \= {}

        for term in query.lower().split():  
            postings \= self.inverted\_index.get(term, \[\])  
            idf \= self.compute\_idf(term)

            for doc\_id, tf in postings:  
                doc\_len \= self.doc\_lengths.get(doc\_id, self.avg\_doc\_length)

                \# Áp dụng công thức BM25  
                numerator \= tf \* (self.k1 \+ 1\)  
                denominator \= tf \+ self.k1 \* (1 \- self.b \+ self.b \* doc\_len / self.avg\_doc\_length)  
                term\_score \= idf \* (numerator / denominator)

                \# Tích lũy điểm cho document  
                scores\[doc\_id\] \= scores.get(doc\_id, 0\) \+ term\_score

        \# Sắp xếp giảm dần theo score, lấy top K  
        result \= sorted(scores.items(), key=lambda x: x\[1\], reverse=True)  
        return result\[:top\_k\]

#### **3.2.3. Parameter Tuning**

Sử dụng script tune.py thử nghiệm 4 bộ tham số trên 3 query mẫu:

| Bộ tham số | k1 | b | Mục đích | Nhận xét |
| :---- | :---- | :---- | :---- | :---- |
| Baseline | 1.5 | 0.75 | Chuẩn IR, cân bằng | Title dài bị spam vẫn xếp cao |
| **Đã chọn** | **1.2** | **0.9** | Phạt title dài mạnh hơn | Kết quả sạch nhất, ưu tiên title ngắn chính xác |
| Anti-stuffing | 0.8 | 0.95 | Giảm ảnh hưởng TF | Quá aggressive, title có từ lặp hợp lệ bị phạt |
| Strong | 0.5 | 1.0 | Chống keyword stuffing tối đa | Quá cực đoan, nhiều kết quả hợp lệ bị đẩy xuống |

**Lý do chọn k1=1.2, b=0.9:** Dữ liệu TMĐT có title thường ngắn (5-15 từ), nhưng một số seller thêm keyword spam (VD: "iPhone 15 giá rẻ sale sốc hot deal free ship..."). b=0.9 phạt mạnh các title dài bất thường, k1=1.2 giúp TF bão hòa nhanh hơn, giảm ảnh hưởng của keyword repetition.

### **3.3. Search Engine (src/search/engine.py)**

**Mục đích:** Module tích hợp trung tâm, kết nối SPIMI Index \+ BM25 \+ Document Store thành API tìm kiếm hoàn chỉnh.

#### **3.3.1. Query Expansion (Mở rộng truy vấn)**

Hệ thống chuyển **từ viết tắt phổ biến** sang từ đầy đủ qua bảng mapping tĩnh:

\# src/search/engine.py

SYNONYM\_MAP \= {  
    "ip": "iphone",  
    "iph": "iphone",  
    "prm": "pro max",  
    "promax": "pro max",  
    "ss": "samsung",  
    "sam": "samsung",  
    "dt": "điện thoại",  
    "mtb": "máy tính bảng",  
    "tn": "tai nghe",  
    "sac": "sạc",  
}

def expand\_query(self, query):  
    """  
    Mở rộng truy vấn: chuyển từ viết tắt sang từ đầy đủ.  
    "ip 14prm" → "iphone 14 pro max"  
    """  
    \# Bước 1: Tách các token dính nhau (VD: "14prm" → "14" \+ "prm")  
    raw\_tokens \= query.lower().split()  
    tokens \= \[\]  
    for t in raw\_tokens:  
        sub\_tokens \= re.findall(r'\[a-zA-Zàáảãạ...\]+|\\d+', t)  \# Tách chữ/số  
        tokens.extend(sub\_tokens if sub\_tokens else \[t\])

    \# Bước 2: Thay thế từ viết tắt  
    expanded \= \[SYNONYM\_MAP.get(token, token) for token in tokens\]  
    return " ".join(expanded)

| Viết tắt | Mở rộng | Ví dụ |
| :---- | :---- | :---- |
| ip, iph | iphone | "ip 17 prm" → "iphone 17 pro max" |
| prm, promax | pro max |  |
| ss, sam | samsung | "ss galaxy" → "samsung galaxy" |
| dt | điện thoại |  |
| mtb | máy tính bảng |  |
| tn | tai nghe |  |
| sac | sạc | "sac du phong" → "sạc du phong" |

#### **3.3.2. Vietnamese Word Segmentation (Tách từ tiếng Việt)**

\# src/search/engine.py

def segment\_query(self, query):  
    """  
    Tách từ tiếng Việt — đồng bộ với cách dữ liệu đã được index.  
    Quan trọng: data trong index đã qua PyVi (M1), nên query cũng phải qua PyVi  
    để token khớp nhau.  
    """  
    segmented \= ViTokenizer.tokenize(query)  
    return segmented

| Query gốc | Sau PyVi | Giải thích |
| :---- | :---- | :---- |
| "tai nghe bluetooth" | "tai\_nghe bluetooth" | Khớp token tai\_nghe trong index |
| "điện thoại iphone" | "điện\_thoại iphone" | Khớp token điện\_thoại trong index |
| "bao cao su" | "bao\_cao\_su" | Nhận diện từ ghép tiếng Việt |

#### **3.3.3. Title Relevance Boost (Tinh chỉnh điểm theo độ phù hợp title)**

**Vấn đề:** BM25 thuần túy không phân biệt được **sản phẩm chính** và **phụ kiện**. Ví dụ khi tìm "iPhone 14 Pro Max":

* Sản phẩm chính: "iPhone 14 Pro Max 256GB" (title ngắn, tập trung)  
* Phụ kiện: "Ốp lưng silicon dành cho iPhone 14 \- iPhone 14 Plus \- iPhone 14 Pro \- iPhone 14 Pro Max trong suốt" (title dài)

Cả hai đều có BM25 score tương đương vì cùng chứa các từ khóa. Nhưng người dùng muốn thấy sản phẩm chính trước.

**Giải pháp — Coverage-based scoring:**

\# src/search/engine.py — trong hàm search()

\# \--- Title Relevance Boost \---  
\# coverage \= số từ query / số từ title  
\# Title ngắn gần giống query → sản phẩm chính → boost  
\# Title dài liệt kê nhiều model → phụ kiện → phạt  
query\_words \= expanded\_query.lower().split()  
title\_words \= title.lower().split()  
coverage \= len(query\_words) / len(title\_words) if title\_words else 0

if coverage \>= 0.6:  
    boosted\_score \*= 1.8   \# Sản phẩm chính (VD: "iPhone 14 Pro Max 128GB")  
elif coverage \>= 0.4:  
    boosted\_score \*= 1.3   \# Sản phẩm \+ mô tả thêm  
elif coverage \>= 0.3:  
    boosted\_score \*= 0.7   \# Có thể là phụ kiện  
else:  
    boosted\_score \*= 0.3   \# Rõ ràng phụ kiện, title rất dài → phạt mạnh

| Coverage | Hệ số nhân | Ý nghĩa | Ví dụ |
| :---- | :---- | :---- | :---- |
| ≥ 60% | × 1.8 | Sản phẩm chính, title ngắn gần giống query | "iPhone 14 Pro Max 128GB" (5/6 \= 83%) |
| ≥ 40% | × 1.3 | Sản phẩm \+ mô tả thêm | "iPhone 14 Pro Max Chính Hãng VN/A 256GB" (5/9 \= 56%) |
| ≥ 30% | × 0.7 | Có thể là phụ kiện | title hơi dài |
| \< 30% | × 0.3 | Rõ ràng phụ kiện, title rất dài | "Kính cường lực iPhone 12-13-14-14 Plus-14 Pro-14 Pro Max" (5/16 \= 31%) |

#### **3.3.4. Platform Diversification (Đa dạng hóa kết quả theo sàn)**

**Vấn đề:** Do phân bố dữ liệu không đều (Shopee chiếm 55%, Tiki 30%), BM25 thuần túy thường trả về top 10 toàn từ 1 sàn.

**Giải pháp 2 bước:**

\# src/search/engine.py

def diversify\_results(self, results, top\_k=10, max\_per\_platform=3):  
    """  
    Round-Robin: lần lượt lấy từ mỗi sàn theo thứ tự score.  
    Đảm bảo kết quả đa dạng, không bị dominate bởi 1 sàn.  
    """  
    \# Bước 1: Lọc kết quả quá thấp so với top 1  
    \# Nếu top 1 score \= 40, chỉ giữ score \>= 8 (20% của 40\)  
    top\_score \= results\[0\]\["bm25\_score"\]  
    results \= \[r for r in results if r\["bm25\_score"\] \>= top\_score \* 0.2\]

    \# Bước 2: Nhóm theo sàn  
    by\_platform \= {}  
    for r in results:  
        by\_platform.setdefault(r\["platform"\], \[\]).append(r)

    \# Sắp xếp sàn theo score cao nhất (sàn có top 1 cao nhất đi trước)  
    platform\_order \= sorted(by\_platform.keys(),  
                            key=lambda p: by\_platform\[p\]\[0\]\["bm25\_score"\],  
                            reverse=True)

    \# Round-Robin: lấy lần lượt 1 kết quả từ mỗi sàn  
    diversified \= \[\]  
    platform\_count \= {}  
    while len(diversified) \< top\_k:  
        added \= False  
        for platform in platform\_order:  
            count \= platform\_count.get(platform, 0\)  
            if count \< len(by\_platform\[platform\]) and count \< max\_per\_platform:  
                diversified.append(by\_platform\[platform\]\[count\])  
                platform\_count\[platform\] \= count \+ 1  
                added \= True  
        if not added:  
            max\_per\_platform \+= 1   \# Nới lỏng giới hạn nếu cần

    return diversified

**Ví dụ:** BM25 trả về 8 Shopee \+ 2 Tiki \+ 1 eBay → sau diversify:

Shopee → Tiki → eBay → Shopee → Tiki → Shopee → Shopee → ...

#### **3.3.5. Document Store**

\# src/search/engine.py

def load(self):  
    """Nạp index và document store vào RAM."""  
    self.ranker.load\_index(self.index\_dir)   \# Load BM25 index

    \# Load document store: đọc JSONL gốc vào dictionary  
    \# Trade-off: \~2-3 GB RAM để đạt tốc độ lookup O(1)  
    with open(self.data\_path, 'r', encoding='utf-8') as f:  
        for line in f:  
            doc \= json.loads(line.strip())  
            doc\_id \= doc.get('id')  
            if doc\_id:  
                self.doc\_store\[doc\_id\] \= doc   \# {doc\_id: product\_info}

**RAM footprint:** \~2-3 GB RAM. Đây là trade-off có chủ đích: hy sinh RAM để đạt tốc độ lookup O(1) thay vì phải seek lại file JSONL.

#### **3.3.6. Pipeline tìm kiếm hoàn chỉnh**

\# src/search/engine.py

def search(self, query, top\_k=10):  
    \# Bước 0: Mở rộng từ viết tắt  
    \# "ip 14prm"  →  "iphone 14 pro max"  
    expanded\_query \= self.expand\_query(query)

    \# Bước 1: Tách từ tiếng Việt (đồng bộ với index)  
    \# "điện thoại"  →  "điện\_thoại"  
    segmented\_query \= self.segment\_query(expanded\_query)

    \# Bước 2: BM25 Ranking (lấy top\_k×5 để có đủ candidates cho diversify)  
    \# Nếu muốn 10 kết quả → BM25 trả 50 → các bước sau chọn 10 tốt nhất  
    ranked\_results \= self.ranker.rank(segmented\_query, top\_k=top\_k \* 5\)

    \# Bước 3: Gắn thông tin sản phẩm \+ Title Relevance Boost  
    results \= \[\]  
    for doc\_id, score in ranked\_results:  
        product \= self.doc\_store.get(doc\_id, {})  
        boosted\_score \= self.\_apply\_title\_boost(score, expanded\_query, product.get("title",""))  
        results.append({  
            "id": doc\_id,  
            "title": product.get("title", "N/A"),  
            "price": product.get("price", 0),  
            "platform": product.get("platform", "Unknown"),  
            "link": product.get("link", ""),  
            "bm25\_score": round(boosted\_score, 4),  
        })

    results.sort(key=lambda x: x\["bm25\_score"\], reverse=True)

    \# Bước 4: Platform Diversification (Round-Robin giữa các sàn)  
    return self.diversify\_results(results, top\_k)

## **4\. Testing**

### **4.1. Tổng quan**

Dự án sử dụng **pytest** với 3 test suite, tổng cộng **12 test cases**:

| Test File | Số Tests | Mô tả |
| :---- | :---- | :---- |
| tests/test\_spimi.py | 4 | SPIMI: add\_document, write/read block, doc\_lengths, memory limit |
| tests/test\_bm25.py | 5 | BM25: IDF computation, rank sorting, top\_k, output format |
| tests/test\_search.py | 3 | E2E: search returns results, relevance ordering, no results |

### **4.2. SPIMI Tests (tests/test\_spimi.py)**

\# tests/test\_spimi.py

class TestSPIMIIndexer:

    def test\_add\_document(self):  
        """Token 'iphone' xuất hiện 2 lần → tf \= 2."""  
        indexer \= SPIMIIndexer(block\_size\_mb=100)  
        indexer.add\_document("doc1", \["iphone", "15", "pro", "iphone"\])

        assert "iphone" in indexer.current\_block  
        postings \= indexer.current\_block\["iphone"\]  
        assert any(doc\_id \== "doc1" and tf \== 2 for doc\_id, tf in postings)

    def test\_write\_and\_read\_block(self):  
        """Ghi block ra disk bằng pickle → đọc lại, verify dữ liệu không bị mất."""  
        indexer \= SPIMIIndexer(block\_size\_mb=100)  
        indexer.add\_document("doc1", \["hello", "world"\])

        with tempfile.TemporaryDirectory() as tmpdir:  
            path \= indexer.write\_block\_to\_disk(tmpdir)  
            with open(path, 'rb') as f:  
                block \= pickle.load(f)  
            assert "hello" in block  
            assert "world" in block

    def test\_doc\_lengths\_tracking(self):  
        """Verify doc\_lengths dictionary tracking chính xác số tokens."""  
        indexer \= SPIMIIndexer()  
        indexer.add\_document("doc1", \["a", "b", "c"\])  
        indexer.add\_document("doc2", \["x", "y"\])

        assert indexer.doc\_lengths\["doc1"\] \== 3  
        assert indexer.doc\_lengths\["doc2"\] \== 2

    def test\_memory\_limit\_triggers\_block\_write(self):  
        """block\_size\_mb=0 → is\_block\_full() trả True ngay sau 1 document."""  
        indexer \= SPIMIIndexer(block\_size\_mb=0)  
        indexer.add\_document("doc1", \["test"\])  
        assert indexer.is\_block\_full()

### **4.3. BM25 Tests (tests/test\_bm25.py)**

\# tests/test\_bm25.py

class TestBM25Ranker:

    @pytest.fixture  
    def ranker\_with\_mock(self):  
        """Build BM25Ranker với dữ liệu mock."""  
        ranker \= BM25Ranker(k1=1.5, b=0.75)  
        ranker.inverted\_index \= {  
            "iphone":      \[("doc1", 3), ("doc2", 1)\],  
            "samsung":     \[("doc2", 2), ("doc3", 1)\],  
            "điện\_thoại":  \[("doc1", 2), ("doc2", 1), ("doc3", 1)\],  
        }  
        ranker.doc\_count \= 3  
        ranker.doc\_lengths \= {"doc1": 8, "doc2": 6, "doc3": 5}  
        ranker.avg\_doc\_length \= 6.33  
        return ranker

    def test\_idf\_rare\_term\_higher(self, ranker\_with\_mock):  
        """Term hiếm có IDF cao hơn term phổ biến (tính chất nghịch đảo của IDF)."""  
        idf\_rare   \= ranker\_with\_mock.compute\_idf("samsung")       \# 2/3 docs  
        idf\_common \= ranker\_with\_mock.compute\_idf("điện\_thoại")    \# 3/3 docs  
        assert idf\_rare \> idf\_common

    def test\_idf\_unknown\_term\_zero(self, ranker\_with\_mock):  
        """Term không tồn tại trong index → IDF \= 0."""  
        assert ranker\_with\_mock.compute\_idf("xyz\_nonexist") \== 0.0

    def test\_rank\_returns\_sorted(self, ranker\_with\_mock):  
        """Kết quả phải được sắp xếp giảm dần theo score."""  
        results \= ranker\_with\_mock.rank("iphone điện\_thoại", top\_k=3)  
        scores \= \[s for \_, s in results\]  
        assert scores \== sorted(scores, reverse=True)

    def test\_rank\_top\_k(self, ranker\_with\_mock):  
        """top\_k=1 → trả về đúng 1 kết quả."""  
        results \= ranker\_with\_mock.rank("iphone", top\_k=1)  
        assert len(results) \== 1

    def test\_rank\_returns\_tuples(self, ranker\_with\_mock):  
        """Output đúng contract: list\[(str, float)\]."""  
        results \= ranker\_with\_mock.rank("iphone", top\_k=2)  
        for doc\_id, score in results:  
            assert isinstance(doc\_id, str)  
            assert isinstance(score, float)

### **4.4. E2E Integration Tests (tests/test\_search.py)**

\# tests/test\_search.py

class TestSearchEngineE2E:

    @pytest.fixture  
    def sample\_system(self, tmp\_path):  
        """Build mini search engine từ 3 sample documents."""  
        docs \= \[  
            {"id": "s1", "title": "iPhone 15 Pro Max",  
             "title\_segmented": "iphone 15 pro max",  
             "price": 25000000, "platform": "shopee"},  
            {"id": "s2", "title": "Samsung Galaxy S24",  
             "title\_segmented": "samsung galaxy s24",  
             "price": 20000000, "platform": "tiki"},  
            {"id": "s3", "title": "Tai nghe iPhone chính hãng",  
             "title\_segmented": "tai\_nghe iphone chính\_hãng",  
             "price": 500000, "platform": "shopee"},  
        \]  
        \# Ghi JSONL, build index, load engine  
        data\_file \= tmp\_path / "sample.jsonl"  
        with open(data\_file, "w", encoding="utf-8") as f:  
            for d in docs:  
                f.write(json.dumps(d, ensure\_ascii=False) \+ "\\n")

        index\_dir \= str(tmp\_path / "index")  
        SPIMIIndexer(block\_size\_mb=100).build\_index(str(data\_file), index\_dir)

        engine \= SearchEngine(index\_dir=index\_dir, data\_path=str(data\_file))  
        engine.load()  
        return engine

    def test\_search\_returns\_results(self, sample\_system):  
        """Search 'iphone' → có kết quả, chứa đủ fields bm25\_score, title, platform."""  
        results \= sample\_system.search("iphone", top\_k=5)  
        assert len(results) \> 0  
        assert "bm25\_score" in results\[0\]  
        assert "title" in results\[0\]  
        assert "platform" in results\[0\]

    def test\_search\_relevance(self, sample\_system):  
        """Query 'iphone' → chỉ trả s1 và s3 (có 'iphone'), không trả s2 (Samsung)."""  
        results \= sample\_system.search("iphone", top\_k=5)  
        top\_ids \= \[r\["id"\] for r in results\]  
        assert "s1" in top\_ids  
        assert len(results) \== 2   \# s1 \+ s3 chứa "iphone"

    def test\_search\_no\_results(self, sample\_system):  
        """Query vô nghĩa → kết quả rỗng, không crash."""  
        results \= sample\_system.search("xyznonexist", top\_k=5)  
        assert len(results) \== 0

### **4.5. Chạy Tests**

\# Activate virtual environment  
venv\\Scripts\\activate

\# Run all tests  
pytest tests/ \-v

**Kết quả mong đợi:**

tests/test\_spimi.py::TestSPIMIIndexer::test\_add\_document              PASSED  
tests/test\_spimi.py::TestSPIMIIndexer::test\_write\_and\_read\_block      PASSED  
tests/test\_spimi.py::TestSPIMIIndexer::test\_doc\_lengths\_tracking      PASSED  
tests/test\_spimi.py::TestSPIMIIndexer::test\_memory\_limit\_triggers\_block\_write PASSED  
tests/test\_bm25.py::TestBM25Ranker::test\_idf\_rare\_term\_higher         PASSED  
tests/test\_bm25.py::TestBM25Ranker::test\_idf\_unknown\_term\_zero        PASSED  
tests/test\_bm25.py::TestBM25Ranker::test\_rank\_returns\_sorted          PASSED  
tests/test\_bm25.py::TestBM25Ranker::test\_rank\_top\_k                   PASSED  
tests/test\_bm25.py::TestBM25Ranker::test\_rank\_returns\_tuples          PASSED  
tests/test\_search.py::TestSearchEngineE2E::test\_search\_returns\_results PASSED  
tests/test\_search.py::TestSearchEngineE2E::test\_search\_relevance      PASSED  
tests/test\_search.py::TestSearchEngineE2E::test\_search\_no\_results     PASSED  
\================================= 12 passed in Xs \=================================

## **5\. Hiệu Năng & Đánh Giá**

### **5.1. Benchmark Indexing**

| Metric | Giá trị |
| :---- | :---- |
| Input data | \~1.05 GB (MASTER\_DATA\_CLEAN.jsonl) |
| Thời gian indexing | \~3-5 phút (tùy cấu hình máy) |
| Số blocks tạo ra | 1-3 blocks (tùy block\_size\_mb) |
| Kết quả index | inverted\_index.pkl \~185 MB |
| Metadata | metadata.pkl \~33 MB |
| Tỉ lệ nén (data → index) | \~1050 MB → \~218 MB (giảm \~79%) |

### **5.2. Benchmark Search**

| Metric | Giá trị |
| :---- | :---- |
| Thời gian load engine | \~30-60 giây (load index \+ document store) |
| Thời gian search/query | \~30-100 ms |
| RAM sử dụng | \~3-4 GB (index \+ document store in-memory) |

### **5.3. Đánh giá chất lượng tìm kiếm**

Đánh giá định tính trên 3 query tiêu biểu:

| Query | Top 1 Result | Nhận xét |
| :---- | :---- | :---- |
| "iphone 15 pro max" | iPhone 15 Pro Max 256GB \- Chính hãng | ✅ Chính xác, exact match |
| "samsung galaxy s24" | Samsung Galaxy S24 Ultra 5G | ✅ Đúng sản phẩm |
| "tai nghe bluetooth" | Tai Nghe Bluetooth Không Dây TWS | ✅ Phù hợp |

**Hạn chế đã nhận diện:**

* Chưa có đánh giá định lượng (Precision@K, Recall, nDCG) do thiếu ground truth dataset  
* Query tiếng Việt có dấu và không dấu cho kết quả khác nhau (chưa xử lý accent normalization)  
* Multi-word queries chưa hỗ trợ phrase search (chỉ bag-of-words)

## **6\. Dataset & Index Statistics**

### **6.1. Dữ liệu đầu vào (từ Milestone 1\)**

| Nguồn | Số sản phẩm | Tỉ lệ |
| :---- | :---- | :---- |
| Shopee | \~800,284 | 55.0% |
| Tiki | \~435,203 | 29.9% |
| Chợ Tốt | \~114,370 | 7.9% |
| eBay | \~104,742 | 7.2% |
| **Tổng** | **\~1,454,599** | **100%** |

File: MASTER\_DATA\_CLEAN.jsonl (\~1.05 GB), đã qua pipeline xử lý của Milestone 1 (clean HTML, normalize text, deduplicate, Vietnamese word segmentation bằng PyVi).

### **6.2. Index output**

| File | Kích thước | Nội dung |
| :---- | :---- | :---- |
| inverted\_index.pkl | \~185 MB | Dictionary {term: \[(doc\_id, tf), ...\]} — Inverted Index hoàn chỉnh |
| metadata.pkl | \~33 MB | Dictionary chứa doc\_count, doc\_lengths (mỗi doc), avg\_doc\_length |

[image1]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAACgAAAAZCAYAAABD2GxlAAACuElEQVR4Xu2WvWsUURTFZ1kVxe+PuCS7m9kvXAiCxYIiWNnYqEjSiGJtY2WhWEsgIIKECP4DdoKFSCxSBNIELEQwCEELJawgyIIQC0Xi77hvkjfX2dlRtxDMgcvu3HPufWfum3m7QbCJfwytVmtrqVQ6YPMpyI2Oju63ycyoVCr7wjAc5mvecha1Wm0v2sfEhOVSkEN/TbWWSAVF94nPRJs7fM/nd2K60WjssVrBmZvlhm5xmbO8UK/Xyz3qZXI2k0m2ZwfiOyw0VSwWD0Z5rs+Q72B2GU3DrxHI34Bf9Gt8qCfxFd05ywmqVY+gx80FNC4heu4mlbhFelacZs1QmsDrarVaMPk8UzvsHpN51fUyqFr1IGaCJJMQT1yDe4mCLrageWQNMtEiuWk/Z9HPoKAexApRtZzINaKdtH0eNKmH0jKV7VGyXC6fJzfuCy0yGhyXRv1ihBuvDCaP12FoaGhXtJBvkOtJehzztRZZDMK10KyqX4wIu6P9gKAWIwzcpHQj61scme53lmUxODIycgjNkrTryUKhsJPEHLHQbDZ3b8h/gbZ3xhlciZKRQX36YossBr0dmk9Mpi2iZxNN2xm8HeXd+beYViv8scFg48FPNai325l7paMjyg9ygtpBNAvWoBa/SXJJz0CM8BB2z8cOL8NxPx8ZTDgDY8hiEH6YeEfMWe6nAYqXWSj00nnyl4hVtvKIl48B/jq1p2zeB5oXzuAV/aGwvKAeaL5xQly1nMizkB+JL3x/wOck8cblLlu9D/iTSU39Y8lG0iTdTnY4LY5aLkIeUYvFLhIXiEqQci5GcC/KU/9s/F2oVj1Y/5n+D1j+r0HzT2l33g+qVQ8Nx3IDgV4eFnjLAicslwWqtS/gwMEiE8RL86L1hfRhn9/ygYGFTof2tzQFY2Nj29DftflN/Df4ATkZ1EFjDSKlAAAAAElFTkSuQmCC>

[image2]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABMAAAAYCAYAAAAYl8YPAAAAqklEQVR4XmNgGAWjYBACZWVlWXl5+W4FBQUOdDmygJycXDkIo4uTBYCuEwO6br+ioqIZuhxZAGQQ0MAjMjIyKigSoqKiPEAJSTJwMNC7j4AGcsINAwZmBUiQVAw07BkQ/wfqj0dyG+lAXFycG2jIQqBhfehyJAGgq1yBhqxG8R6ZgAXkIiD2QJcgGQBdIw101WYpKSkRdDmSgbGxMSvQQCEgkxFdbhQMMAAAwdwthtTzqmQAAAAASUVORK5CYII=>