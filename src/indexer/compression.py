# Index Compression - Nén chỉ mục
# Milestone 2: Variable Byte + Gamma Encoding (lý thuyết)
# Milestone 3: Tích hợp compress/decompress toàn bộ index vào pipeline

def variable_byte_encode(number):
    """
    Mã hóa số nguyên bằng Variable Byte.
    Mỗi byte dùng 7 bit chứa data, 1 bit cao nhất làm cờ kết thúc.
    """
    if number == 0:
        return bytes([128])

    result = []
    while True:
        result.insert(0, number % 128)
        if number < 128:
            break
        number = number // 128

    result[-1] += 128
    return bytes(result)


def variable_byte_decode(data):
    """Giải mã dãy bytes VB thành danh sách số nguyên."""
    numbers = []
    n = 0
    for byte in data:
        if byte < 128:
            n = 128 * n + byte
        else:
            n = 128 * n + (byte - 128)
            numbers.append(n)
            n = 0
    return numbers


def gamma_encode(number):
    """
    Mã hóa số nguyên bằng Elias Gamma.
    Gồm phần unary (biểu diễn độ dài) + phần offset (giá trị).
    Chỉ dùng cho số > 0.
    """
    if number <= 0:
        raise ValueError("Gamma encoding chi dung cho so > 0")

    binary = bin(number)[2:]
    length = len(binary)

    unary = '1' * (length - 1) + '0'
    offset = binary[1:]

    return unary + offset


def gamma_decode(bitstring):
    """
    Giải mã chuỗi bit Elias Gamma thành danh sách số nguyên.

    Args:
        bitstring: Chuỗi '0' và '1'

    Returns:
        List[int]: Các số đã decode
    """
    numbers = []
    i = 0

    while i < len(bitstring):
        # Đếm bit '1' liên tiếp (phần unary)
        length = 1
        while i < len(bitstring) and bitstring[i] == '1':
            length += 1
            i += 1

        i += 1  # Bỏ qua bit '0' kết thúc unary

        # Đọc (length-1) bit offset
        offset = bitstring[i:i + length - 1]
        i += length - 1

        # Ghép: '1' + offset = số gốc
        number = int('1' + offset, 2)
        numbers.append(number)

    return numbers


# ============================================================
# Milestone 3: Nén/giải nén toàn bộ inverted index
# ============================================================

def compress_index(inverted_index):
    """
    Nén toàn bộ inverted index bằng VB Encoding + Delta Encoding.

    Quy trình:
    1. Gán mỗi doc_id (string) → integer ID tăng dần
    2. Sort postings theo int ID
    3. Delta encoding: lưu gap thay vì ID tuyệt đối
    4. VB encoding: nén gap + tf thành bytes

    Args:
        inverted_index: {term: [(doc_id_str, tf), ...]}

    Returns:
        compressed: {term: bytes}
        doc_id_to_int: {doc_id_str: int}
    """
    # Bước 1: Tạo mapping doc_id string → integer
    doc_id_to_int = {}
    next_id = 1

    for postings in inverted_index.values():
        for doc_id_str, _ in postings:
            if doc_id_str not in doc_id_to_int:
                doc_id_to_int[doc_id_str] = next_id
                next_id += 1

    # Bước 2: Nén từng term
    compressed = {}
    for term, postings in inverted_index.items():
        # Chuyển sang integer IDs và sort
        int_postings = [
            (doc_id_to_int[doc_id_str], tf)
            for doc_id_str, tf in postings
        ]
        int_postings.sort(key=lambda x: x[0])

        # Delta + VB encode
        encoded = bytearray()
        prev = 0
        for did, tf in int_postings:
            gap = did - prev
            prev = did
            encoded.extend(variable_byte_encode(gap))
            encoded.extend(variable_byte_encode(tf))

        compressed[term] = bytes(encoded)

    return compressed, doc_id_to_int


def decompress_index(compressed_index, int_to_doc_id):
    """
    Giải nén toàn bộ inverted index.

    Args:
        compressed_index: {term: bytes}
        int_to_doc_id: {int: doc_id_str}

    Returns:
        {term: [(doc_id_str, tf), ...]}
    """
    index = {}

    for term, data in compressed_index.items():
        numbers = variable_byte_decode(data)
        postings = []
        prev = 0

        for i in range(0, len(numbers) - 1, 2):
            gap = numbers[i]
            tf = numbers[i + 1]
            did = prev + gap
            prev = did
            doc_id_str = int_to_doc_id.get(did, str(did))
            postings.append((doc_id_str, tf))

        index[term] = postings

    return index
