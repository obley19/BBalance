# **Data Schema Specification (Milestone 1\)**

Tài liệu này quy định định dạng dữ liệu chuẩn cho toàn bộ dự án. Mọi script Crawler và Cleaner phải tuân thủ schema này.

## **1\. Cấu trúc File**

* **Format:** JSON Lines (.jsonl). Mỗi dòng là một object JSON hợp lệ.  
* **Encoding:** UTF-8.  
* **Naming Convention:** raw\_{source}\_{date}.jsonl (Ví dụ: raw\_tiki\_20241013.jsonl).

## **2\. Product Object Schema**

Mỗi sản phẩm được lưu trữ dưới dạng một JSON Object với các trường sau:

| Field Name | Data Type | Required | Description | Example |
| :---- | :---- | :---- | :---- | :---- |
| id | String | **Yes** | Unique ID kết hợp prefix sàn | "tiki\_123456" |
| original\_id | Int/String | **Yes** | ID gốc trên sàn | 123456 |
| title | String | **Yes** | Tên sản phẩm (Raw) | "Điện thoại iPhone 15 Pro Max" |
| price | Integer | **Yes** | Giá bán (Đã bỏ dấu chấm/phẩy) | 25000000 |
| url | String | **Yes** | Link gốc sản phẩm | "<https://tiki.vn/>..." |
| image\_url | String | No | Link ảnh thumbnail | "<https://salt.tikicdn.com/>..." |
| category | String | No | Danh mục sản phẩm | "Điện thoại \- Máy tính bảng" |
| source | String | **Yes** | Nguồn dữ liệu (tiki, shopee, chotot, ebay) | "tiki" |
| rating | Float | No | Điểm đánh giá trung bình | 4.8 |
| sold\_count | Integer | No | Số lượng đã bán | 1200 |
| description | String | No | Mô tả chi tiết (Raw HTML hoặc Text) | "\<p\>Sản phẩm chính hãng...\</p\>" |
| crawled\_at | String | **Yes** | Thời gian thu thập (ISO 8601\) | "2024-10-13T10:00:00" |

## **3\. Quy tắc Xử lý dữ liệu (Data Cleaning Rules)**

### **3.1. Price Normalization**

* Nếu giá trị rỗng hoặc không xác định \-\> Gán \-1.  
* Loại bỏ mọi ký tự không phải số (đ, ., ,, ).  
* Ví dụ: "18.990.000 ₫" \-\> 18990000\.

### **3.2. Title Normalization**

* **Crawler:** Giữ nguyên text gốc.  
* **Indexer:** Sẽ thực hiện lowercase và remove accents sau.

### **3.3. Deduplication (Khử trùng lặp)**

* **Primary Key:** Sử dụng trường id. Nếu trùng id \-\> Giữ lại bản ghi mới nhất (dựa trên crawled\_at).  
* **Fuzzy Deduplication:** (Milestone 2\) Sẽ xử lý các sản phẩm cùng tên nhưng khác ID sàn sau.

## **4\. Sample JSON Object**

{  
  "id": "tiki\_738291",  
  "original\_id": 738291,  
  "title": "Sách \- Tuổi Trẻ Đáng Giá Bao Nhiêu",  
  "price": 75000,  
  "url": "\[<https://tiki.vn/tuoi-tre-dang-gia-bao-nhieu-p738291.html\>](<https://tiki.vn/tuoi-tre-dang-gia-bao-nhieu-p738291.html>)",  
  "image\_url": "\[<https://salt.tikicdn.com/cache/280x280/ts/product/\>](<https://salt.tikicdn.com/cache/280x280/ts/product/>)...",  
  "category": "Sách tư duy \- Kỹ năng sống",  
  "source": "tiki",  
  "rating": 4.5,  
  "sold\_count": 50000,  
  "description": "Cuốn sách giúp bạn tìm thấy đam mê...",  
  "crawled\_at": "2024-10-13T14:30:00"  
}  
