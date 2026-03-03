# Index Compression - Nén chỉ mục (phần mở rộng)
# Triển khai Variable Byte Encoding và Elias Gamma Encoding


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

    # Đánh dấu byte cuối cùng (bit cao = 1)
    result[-1] += 128
    return bytes(result)


def variable_byte_decode(data):
    """Giải mã dãy bytes VB thành danh sách số nguyên."""
    numbers = []
    n = 0
    for byte in data:
        if byte < 128:
            # Chưa phải byte cuối -> tích lũy
            n = 128 * n + byte
        else:
            # Byte cuối -> hoàn thành 1 số
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

    # Chuyển sang nhị phân
    binary = bin(number)[2:]  # bỏ prefix "0b"
    length = len(binary)

    # Phần unary: (length-1) bit 1 + 1 bit 0
    unary = '1' * (length - 1) + '0'

    # Phần offset: binary bỏ bit đầu
    offset = binary[1:]

    return unary + offset
