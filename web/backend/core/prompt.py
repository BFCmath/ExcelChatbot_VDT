"""
Prompt templates for Excel Chatbot
"""

# Prompt for decomposer agent
DECOMPOSER_PROMPT = """You are an expert query decomposer for hierarchical data structures, akin to those found in financial Excel spreadsheets or complex pivot tables. Your primary mission is to dissect a natural language `Query`, infer, and identify the main keywords, clearly categorizing them into row and column keywords.

**Problem Description:**
You will be dealing with matrix-like tables that possess both hierarchical rows and hierarchical columns. A query aims to identify a specific cell or set of cells, conceptually `table[row_identifier][column_identifier]`. Your crucial task is to efficiently distinguish from the natural language `Query` which parts refer to row identifiers and which refer to column identifiers, based on the provided `Row Hierarchy` and `Column Hierarchy`.

You will be provided with:
1.  `Query`: The natural language question.
2.  `Feature Rows`: A list of the names for each level in the row hierarchy (e.g., ['Country', 'Product', 'Category']).
3.  `Row Hierarchy`: A textual description of the row structure and its nested levels.
4.  `Column Hierarchy`: A textual description of the column structure and its nested levels.

Your output should be:
1.  `Thinking`: A step-by-step explanation of your reasoning process. Describe how you analyzed the `Query` and matched keywords to the `Row Hierarchy` and `Column Hierarchy`. Explain any inferences made, especially if keywords don't directly match hierarchy labels but can be logically deduced.
2.  `Row Keywords`: A list of keywords or phrases extracted from the `Query` that specify row(s).
3.  `Col Keywords`: A list of keywords or phrases extracted from the `Query` that specify column(s).

**Example 1:**

### Query
cho tôi biết cà phê đen tại việt nam có giá như thế nào vào những tháng hè

### Feature Rows
['Cà phê', 'Loại', 'Nhập Khẩu ']

### Row Hierarchy
cà phê: cà phê thường
    loại: loại 1
        nhập khẩu : việt nam, brazil, mỹ
    loại: loại 2
        nhập khẩu : việt nam, mỹ
cà phê: cà phê đen
    loại: loại 2
        nhập khẩu : việt nam

### Column Hierarchy
level_1: thời gian
    level_2: hè, đông
level_1: thu nhập
    level_2: thấp, trung bình, cao

### Thinking
Câu truy vấn là: "cho tôi biết cà phê đen tại việt nam có giá như thế nào vào những tháng hè".
Các keyword chính được xác định: "cà phê đen", "việt nam", "giá", "tháng hè".

1.  **Keyword: "cà phê đen"**
    *   Kiểm tra trong: `Row Hierarchy`.
    *   Phát hiện: "cà phê đen" nằm dưới `Feature Row` "Cà phê".
    *   Kết luận: Đây là một `Row Keyword`.

2.  **Keyword: "việt nam"**
    *   Kiểm tra trong: `Row Hierarchy`.
    *   Phát hiện: "việt nam" xuất hiện dưới `Feature Row` "Nhập Khẩu " (là một cấp con của "Loại", và "Loại" là cấp con của "Cà phê").
    *   Kết luận: Đây là một `Row Keyword`.

3.  **Keyword: "giá"**
    *   Kiểm tra trong: Cả `Row Hierarchy` và `Column Hierarchy`.
    *   Phát hiện: "giá" không xuất hiện như một nhãn trong bất kỳ schema nào.
    *   Suy luận: Có khả năng các *giá trị* trong các ô của bảng biểu thị giá, thay vì "giá" là một keyword cấu trúc cho hàng hoặc cột. Do đó, nó không được phân loại là `Row Keyword` hay `Col Keyword` cho mục đích điều hướng.

4.  **Keyword: "tháng hè"**
    *   Kiểm tra trong: `Column Hierarchy`.
    *   Phát hiện: Mặc dù "tháng" không có mặt rõ ràng, "hè" được tìm thấy ở `level_2` của `level_1` "thời gian".
    *   Suy luận: "tháng hè" đề cập đến khoảng thời gian "hè".
    *   Kết luận: Đây là một `Col Keyword`.

### Row Keywords
-   cà phê đen
-   việt nam

### Col Keywords
-   tháng hè

**Example 2:**

### Query
cho tôi biết chi phí học tập cấp 2 và cấp 1 của cả 2 học sinh

### Feature Rows
['Tên', 'Môn']

### Row Hierarchy
tên: trần bích thu
    môn: lý, toán, hóa, sinh
tên: nguyễn nam
    môn: lý, toán, hóa, sinh

### Column Hierarchy
level_1: chi phí
    level_2: cấp 1, cấp 2, tổng cộng

### Thinking
Câu truy vấn là: "cho tôi biết chi phí học tập cấp 2 và cấp 1 của cả 2 học sinh".
Các keyword chính được xác định: "chi phí học tập", "cấp 2", "cấp 1", "2 học sinh".

1.  **Keyword: "2 học sinh"**
    *   Kiểm tra trong: `Row Hierarchy`.
    *   Phát hiện: `Feature Row` "Tên" liệt kê hai tên: "trần bích thu" và "nguyễn nam".
    *   Suy luận: "2 học sinh" đề cập đến việc chọn tất cả các mục dưới `Feature Row` "Tên", bao gồm cả hai học sinh.
    *   Kết luận: Đây là một `Row Keyword` (ám chỉ toàn bộ `Feature Row` "Tên" hoặc cả hai tên cụ thể).

2.  **Keyword: "chi phí học tập"**
    *   Kiểm tra trong: `Column Hierarchy`.
    *   Phát hiện: `level_1` của `Column Hierarchy` là "chi phí".
    *   Suy luận: "chi phí học tập" ánh xạ trực tiếp đến cột "chi phí".
    *   Kết luận: Đây là một `Col Keyword`.

3.  **Keyword: "cấp 1"**
    *   Kiểm tra trong: `Column Hierarchy`.
    *   Phát hiện: "cấp 1" được tìm thấy ở `level_2` của `level_1` "chi phí".
    *   Kết luận: Đây là một `Col Keyword`.

4.  **Keyword: "cấp 2"**
    *   Kiểm tra trong: `Column Hierarchy`.
    *   Phát hiện: "cấp 2" được tìm thấy ở `level_2` của `level_1` "chi phí".
    *   Kết luận: Đây là một `Col Keyword`.

### Row Keywords
-   2 học sinh

### Col Keywords
-   chi phí học tập
-   cấp 1
-   cấp 2

*Now, process the following input:*

### Query
{query}

### Feature Rows
{feature_rows}

### Row Hierarchy
{row_structure}

### Feature Cols
{feature_cols}

### Column Hierarchy
{col_structure}

### Thinking
"""

# Prompt for row handler agent
ROW_HANDLER_PROMPT = """You are an expert **Row Handler** for hierarchical data structures, akin to those found in financial Excel spreadsheets or complex pivot tables. Your mission is to analyze the input query, along with previously extracted `Row Keywords`, and then, by thinking, analyzing, and tracing within the `Row Hierarchy` and `Feature Rows`, determine the corresponding row features and their specific values that constitute the `Row Identifier`.

**Problem Description:**
You will be dealing with matrix-like tables that possess both hierarchical rows and hierarchical columns. A query aims to identify a specific cell or set of cells, conceptually `table[row_identifier][column_identifier]`. Your crucial task is to use the `Feature Rows`, `Row Hierarchy`, and the provided `Row Keywords` to precisely determine the `Row Identifier`(s) for the query. This identifier should specify the exact path(s) or selection(s) within the row hierarchy.

You will be provided with:
1.  `Query`: The original natural language question.
2.  `Feature Rows`: A list of the names for each level in the row hierarchy.
3.  `Row Hierarchy`: A textual description of the row structure and its nested levels.
4.  `Row Keywords`: A list of keywords (previously extracted) that pertain to row selection.

Your output should be:
1.  `Thinking`: A step-by-step explanation of your reasoning. Describe how you used the `Row Keywords` to interpret the user's intent, how you mapped these keywords to the `Feature Rows`, and how you navigated the `Row Hierarchy` to select specific values. Explain any assumptions made, especially for hierarchical levels not explicitly mentioned by keywords.

2.  `Row Identifier`: A structured representation of the selected row(s), showing the feature and its chosen value(s) at each relevant level of the hierarchy.
    *   The `Row Identifier` should be represented as a nested structure mirroring the `Row Hierarchy`. Each line should indent to reflect the hierarchical level.
    *   If multiple values are chosen at a certain level for a single upper-level item, list them all (e.g., separated by commas).
    *   **Using "Undefined":** The value "Undefined" should be used for a specific `Feature Row` (hierarchical level) in the `Row Identifier` path when:
        *   That hierarchical level is an intermediate step on the path to a more specific, user-requested lower-level item, but the user's query or `Row Keywords` do not specify a particular value for this intermediate level. In this case, "Undefined" means "select any/all values at this intermediate level that are on a valid path to the specified lower-level item(s)."
        *   A `Row Keyword` specifies an item at a certain level, but a parent level in the hierarchy is not explicitly specified by any keyword. "Undefined" for the parent level indicates the selection applies across all instances of that parent that contain the specified child item.
    *   If a level is specified by a `Row Keyword` and it's the deepest level of selection for that branch of the query, lower hierarchical levels under it are generally not included in the `Row Identifier` unless also specified.

**Example 1:**

### Query
cho tôi biết cà phê đen tại việt nam có giá như thế nào vào những tháng hè

### Feature Rows
['Cà phê', 'Loại', 'Nhập Khẩu ']

### Row Hierarchy
cà phê: cà phê thường
    loại: loại 1
        nhập khẩu : việt nam, brazil, mỹ
    loại: loại 2
        nhập khẩu : việt nam, mỹ
cà phê: cà phê đen
    loại: loại 2
        nhập khẩu : việt nam

### Row Keywords
['cà phê đen', 'việt nam']

### Thinking
Tôi cần tìm các `Row Identifier` cho query: "cho tôi biết cà phê đen tại việt nam có giá như thế nào vào những tháng hè".
Dựa vào `Row Keywords` đã cho: ['cà phê đen', 'việt nam']. Mục tiêu là xác định các `Feature Rows` và giá trị tương ứng để trích xuất "cà phê đen tại Việt Nam".

1.  **Phân tích `Row Keyword`: "cà phê đen"**
    *   So khớp với `Feature Rows`: "cà phê đen" thuộc về `Feature Row` là 'Cà phê'.
    *   Giá trị được chọn: "cà phê đen".

2.  **Phân tích `Row Keyword`: "việt nam"**
    *   So khớp với `Feature Rows`: "việt nam" thuộc về `Feature Row` là 'Nhập Khẩu '.
    *   Giá trị được chọn: "việt nam".

3.  **Xử lý `Feature Row` không có `Row Keyword` tương ứng: 'Loại'**
    *   `Feature Row` 'Loại' nằm giữa 'Cà phê' và 'Nhập Khẩu ' trong `Row Hierarchy`.
    *   Vì query không chỉ định rõ 'Loại', tôi giả định người dùng muốn lấy tất cả các 'Loại' phù hợp với "cà phê đen" và "nhập khẩu: việt nam". Trong trường hợp này, để chỉ định một đường dẫn đầy đủ mà không lọc cụ thể theo 'Loại', tôi sẽ gán giá trị "Undefined" cho 'Loại'. Điều này có nghĩa là bất kỳ giá trị 'Loại' nào nằm trên đường dẫn từ 'Cà phê: cà phê đen' đến 'Nhập Khẩu : việt nam' đều được chấp nhận. (Dựa trên `Row Hierarchy` được cung cấp, 'loại 2' là loại duy nhất phù hợp).

Kết hợp lại, `Row Identifier` được hình thành.

### Row Identifier
cà phê: cà phê đen
    loại: Undefined
        nhập khẩu : việt nam

**Example 2:**

### Query
cho tôi biết chi phí học tập cấp 2 và cấp 1 của cả 2 học sinh

### Feature Rows
['Tên', 'Môn']

### Row Hierarchy
tên: trần bích thu
    môn: lý, toán, hóa, sinh
tên: nguyễn nam
    môn: lý, toán, hóa, sinh

### Row Keywords
['2 học sinh']

### Thinking
Tôi cần tìm các `Row Identifier` cho query: "cho tôi biết chi phí học tập cấp 2 và cấp 1 của cả 2 học sinh".
Dựa vào `Row Keywords`: ['2 học sinh'].

1.  **Phân tích `Row Keyword`: "2 học sinh"**
    *   So khớp với `Feature Rows`: "2 học sinh" ám chỉ `Feature Row` 'Tên'.
    *   Kiểm tra `Row Hierarchy` dưới `Feature Row` 'Tên', có hai mục: "trần bích thu" và "nguyễn nam".
    *   Suy luận: "2 học sinh" có nghĩa là người dùng muốn thông tin cho cả hai học sinh này.
    *   Giá trị được chọn cho 'Tên': "trần bích thu", "nguyễn nam".

2.  **Xử lý `Feature Row` không có `Row Keyword` tương ứng: 'Môn'**
    *   Query không chỉ định môn học cụ thể. `Row Identifier` sẽ chỉ tập trung vào cấp 'Tên' dựa trên keyword. Nếu cần tất cả các môn, logic truy xuất dữ liệu sau này sẽ xử lý việc đó dựa trên cấu trúc `Row Identifier` này.

Kết hợp lại, `Row Identifier` được hình thành.

### Row Identifier
tên: trần bích thu, nguyễn nam


**Example 3:**

### Query
cho tôi biết chi phí học tập cấp 1 của cả 2 học sinh, xét 2 môn lý và toán

### Feature Rows
['Tên', 'Môn']

### Row Hierarchy
tên: trần bích thu
    môn: lý, toán, hóa
tên: nguyễn nam
    môn: lý, hóa, văn

### Row Keywords
['2 học sinh', 'lý', 'toán']

### Thinking
Tôi cần tìm các `Row Identifier` cho query: "cho tôi biết chi phí học tập cấp 1 của cả 2 học sinh, xét 2 môn lý và toán".
Dựa vào `Row Keywords`: ['2 học sinh', 'lý', 'toán'].

1.  **Phân tích `Row Keyword`: "2 học sinh"**
    *   So khớp với `Feature Rows`: "2 học sinh" ám chỉ `Feature Row` 'Tên'.
    *   Kiểm tra `Row Hierarchy` dưới `Feature Row` 'Tên', có hai mục: "trần bích thu" và "nguyễn nam".
    *   Giá trị được chọn cho 'Tên': "trần bích thu", "nguyễn nam".

2.  **Phân tích `Row Keywords`: "lý", "toán"**
    *   So khớp với `Feature Rows`: "lý" và "toán" thuộc về `Feature Row` 'Môn'.
    *   Đối với mỗi học sinh đã chọn ở bước 1, tôi sẽ xác định các môn học tương ứng:
        *   **Đối với "trần bích thu":**
            *   Kiểm tra `Row Hierarchy` cho "trần bích thu": có "lý, toán, hóa".
            *   Các môn được yêu cầu ("lý", "toán") đều có.
            *   Giá trị được chọn cho 'Môn' của "trần bích thu": "lý", "toán".
        *   **Đối với "nguyễn nam":**
            *   Kiểm tra `Row Hierarchy` cho "nguyễn nam": có "lý, hóa, văn".
            *   Môn "lý" được yêu cầu có.
            *   Môn "toán" được yêu cầu không có.
            *   Giá trị được chọn cho 'Môn' của "nguyễn nam": "lý".

Kết hợp lại, `Row Identifier` được hình thành với cấu trúc phân cấp.

### Row Identifier
tên: trần bích thu
    môn: lý, toán
tên: nguyễn nam
    môn: lý

**Example 4:**

### Query
cho tôi biết chi phí học tập cấp 1 của môn lý

### Feature Rows
['Tên', 'Môn']

### Row Hierarchy
tên: trần bích thu
    môn: lý, toán, hóa
tên: nguyễn nam
    môn: lý, hóa, văn

### Row Keywords
['lý']

### Thinking
Tôi cần tìm các `Row Identifier` cho query: "cho tôi biết chi phí học tập cấp 1 của môn lý".
Dựa vào `Row Keywords` đã cho: ['lý'].

1.  **Phân tích `Row Keyword`: "lý"**
    *   So khớp với `Feature Rows`: "lý" thuộc về `Feature Row` 'Môn'.
    *   Giá trị được chọn cho 'Môn': "lý".

2.  **Xử lý `Feature Row` cấp trên không có `Row Keyword` tương ứng: 'Tên'**
    *   `Feature Row` 'Tên' là cấp cha của 'Môn' trong `Row Hierarchy`.
    *   Query và `Row Keywords` không chỉ định một 'Tên' cụ thể.
    *   Để chỉ ra rằng chúng ta đang tìm 'Môn: lý' cho bất kỳ 'Tên' nào có môn này, chúng ta sẽ gán giá trị "Undefined" cho 'Tên'. Điều này có nghĩa là `Row Identifier` sẽ khớp với tất cả các học sinh có 'Môn: lý'.

Kết hợp lại, `Row Identifier` được hình thành.

### Row Identifier
tên: Undefined
    môn: lý

**Example 5:**

### Query
cho tôi biết chi phí học tập cả năm của nguyễn nam

### Feature Rows
['Tên', 'Môn']

### Row Hierarchy
tên: trần bích thu
    môn: lý, toán, hóa
tên: nguyễn nam
    môn: lý, hóa, văn

### Row Keywords
['nguyễn nam']

### Thinking
Tôi cần tìm các `Row Identifier` cho query: "cho tôi biết chi phí học tập cả năm của nguyễn nam".
Dựa vào `Row Keywords` đã cho: ['nguyễn nam'].

1.  **Phân tích `Row Keyword`: "nguyễn nam"**
    *   So khớp với `Feature Rows`: "nguyễn nam" thuộc về `Feature Row` 'Tên'.
    *   Giá trị được chọn cho 'Tên': "nguyễn nam".

2.  **Xử lý `Feature Row` cấp dưới không có `Row Keyword` tương ứng: 'Môn'**
    *   `Feature Row` 'Môn' là cấp con của 'Tên'.
    *   Query và `Row Keywords` không chỉ định một 'Môn' cụ thể cho "nguyễn nam".
    *   Trong trường hợp này, `Row Identifier` sẽ chỉ định 'Tên: nguyễn nam'. Điều này ngụ ý rằng tất cả các 'Môn' thuộc "nguyễn nam" đều được bao hàm hoặc có thể được truy vấn dựa trên `Row Identifier` này. Chúng ta không cần chỉ định 'Môn: Undefined' vì việc lựa chọn dừng ở cấp 'Tên'.

Kết hợp lại, `Row Identifier` được hình thành.

### Row Identifier
tên: nguyễn nam

*Now, process the following input:*
### Query
{query}

### Feature Rows
{feature_rows}

### Row Hierarchy
{row_structure}

### Row Keywords
{row_keywords}

### Thinking
"""

# Prompt for column handler agent  
COL_HANDLER_PROMPT = """You are an expert **Column Handler** for hierarchical data structures, akin to those found in financial Excel spreadsheets or complex pivot tables. Your mission is to analyze the input query, along with previously extracted `Col Keywords`, and then, by thinking, analyzing, and tracing within the `Col Hierarchy`, determine the hierarchical paths leading to the specific columns referenced in the query, stopping at the level of detail implied by the keywords.

**Problem Description:**
You will be dealing with matrix-like tables that possess both hierarchical rows and hierarchical columns. A query aims to identify a specific cell or set of cells, conceptually `table[row_identifier][column_identifier]`. Your crucial task is to use the `Col Hierarchy` and the provided `Col Keywords` to find the path(s) to the target `column_identifier`(s). **The path should only be as deep as specified by the `Col Keywords` or the direct intent of the query. Do not extend the path to lower levels if they are not explicitly or implicitly requested.**

You will be provided with:
1.  `Query`: The original natural language question.
2.  `Column Hierarchy`: A textual description of the column structure and its nested levels (e.g., level_1, level_2, etc.).
3.  `Col Keywords`: A list of keywords (previously extracted) that pertain to column selection.

Your output should be:
1.  `Thinking`: A step-by-step explanation of your reasoning.
    *   Describe how you used the `Col Keywords` to interpret the user's intent.
    *   Detail how you mapped these keywords to specific levels and values within the `Col Hierarchy`.
    *   Explain how you constructed the hierarchical path(s) and **critically, why you stopped at a particular level of specificity** for each path. If a keyword points to `level_X`, and no further keywords or query context refine the selection to `level_X+1` under it, the identifier should terminate at `level_X`.
    *   Explain any inferences made if keywords don't directly match hierarchy labels but can be logically deduced.

2.  `Col Identifier`: A structured representation of the selected column(s).
    *   Show the hierarchical path (e.g., `level_1: value_1`, `level_2: value_2`) for each identified column target.
    *   The path for each identifier should only extend to the most specific level directly indicated or strongly implied by the `Col Keywords` and the query. For example, if "thời gian" is a keyword and maps to `level_1: thời gian`, and the query does not specify "hè" or "đông" (which might be `level_2` items under "thời gian"), then the `Col Identifier` should be `level_1: thời gian`. This implies that all sub-columns under "thời gian" are potentially relevant, but the identifier itself pinpoints "thời gian" as the queried level.
    *   If multiple distinct column paths are identified from the keywords, list each path.

**Example 1:**

### Query
cho tôi biết cà phê đen tại việt nam có giá như thế nào vào những tháng hè

### Column Hierarchy
level_1: thời gian
    level_2: hè, đông
level_1: thu nhập
    level_2: thấp, trung bình, cao

### Col Keywords
['tháng hè']

### Thinking
Tôi cần tìm các `Col Identifier` cho query: "cho tôi biết cà phê đen tại việt nam có giá như thế nào vào những tháng hè".
Dựa vào `Col Keywords` được cung cấp: ['tháng hè'].

1.  **Phân tích `Col Keyword`: "tháng hè"**
    *   Kiểm tra trong `Column Hierarchy`.
    *   Từ "tháng hè", keyword "hè" được tìm thấy ở `level_2` dưới `level_1` là "thời gian".
    *   Suy luận: Người dùng muốn lấy thông tin cho "hè".
    *   Đường đi xác định: `level_1: thời gian`, `level_2: hè`.

Kết hợp lại, `Col Identifier` được hình thành.

### Col Identifier
level_1: thời gian
    level_2: hè

**Example 2:**

### Query
cho tôi biết cà phê đen tại việt nam có giá như thế nào vào những tháng hè và tiền công trả cho nhân viên thu hoạch là bao nhiêu

### Column Hierarchy
level_1: thời gian
    level_2: hè, đông
level_1: tiền thu hoạch
    level_2: thủ công, máy

### Col Keywords
['tháng hè', 'tiền công', 'nhân viên thu hoạch']

### Thinking
Tôi cần tìm các `Col Identifier` cho query: "cho tôi biết cà phê đen tại việt nam có giá như thế nào vào những tháng hè và tiền công trả cho nhân viên thu hoạch là bao nhiêu".
Dựa vào `Col Keywords`: ['tháng hè', 'tiền công', 'nhân viên thu hoạch'].

1.  **Phân tích `Col Keyword`: "tháng hè"**
    *   Kiểm tra trong `Column Hierarchy`.
    *   Keyword "hè" từ "tháng hè" được tìm thấy ở `level_2` dưới `level_1` là "thời gian".
    *   Đường đi xác định 1: `level_1: thời gian`, `level_2: hè`.

2.  **Phân tích `Col Keywords`: "tiền công", "nhân viên thu hoạch"**
    *   Kiểm tra trong `Column Hierarchy`.
    *   "tiền công" và "nhân viên thu hoạch" cùng nhau gợi ý đến `level_1` là "tiền thu hoạch".
    *   Cụm từ "nhân viên thu hoạch" và "tiền công" ngụ ý rằng đây là chi phí cho lao động thủ công, không phải máy móc.
    *   Trong `level_1: tiền thu hoạch`, có `level_2` là "thủ công" và "máy".
    *   Suy luận: Người dùng muốn lấy thông tin cho "tiền thu hoạch" -> "thủ công".
    *   Đường đi xác định 2: `level_1: tiền thu hoạch`, `level_2: thủ công`.

Kết hợp lại, có hai `Col Identifier` được hình thành.

### Col Identifier
level_1: thời gian
    level_2: hè
level_1: tiền thu hoạch
    level_2: thủ công

**Example 3:**

### Query
cho tôi biết cà phê đen tại việt nam có giá trung bình của từng mùa và trung bình của cả năm

### Column Hierarchy
level_1: thời gian
    level_2: hè
       level_3: tháng 1, tháng 3, trung bình
    level_2: đông
       level_3: tháng 11, tháng 12, trung bình
    level_2: trung bình

### Col Keywords
['trung bình', 'từng mùa', 'trung bình của cả năm']

### Thinking
Tôi cần tìm các `Col Identifier` cho query: "cho tôi biết cà phê đen tại việt nam có giá trung bình của từng mùa và trung bình của cả năm".
Dựa vào `Col Keywords`: ['trung bình', 'từng mùa', 'trung bình của cả năm'].

1.  **Phân tích cụm từ: "trung bình của từng mùa"** (liên quan đến keywords "trung bình", "từng mùa")
    *   Kiểm tra trong `Column Hierarchy`.
    *   "Từng mùa" gợi ý đến các mục con của "thời gian" là "hè" và "đông" (đều ở `level_2`).
    *   Trong `level_2: hè`, có `level_3: trung bình`.
        *   Đường đi xác định 1: `level_1: thời gian`, `level_2: hè`, `level_3: trung bình`.
    *   Trong `level_2: đông`, có `level_3: trung bình`.
        *   Đường đi xác định 2: `level_1: thời gian`, `level_2: đông`, `level_3: trung bình`.

2.  **Phân tích cụm từ: "trung bình của cả năm"** (liên quan đến keyword "trung bình của cả năm" và "trung bình")
    *   Kiểm tra trong `Column Hierarchy`.
    *   Keyword "trung bình của cả năm" gợi ý đến giá trị "trung bình" trực tiếp dưới `level_1: thời gian`.
    *   Phát hiện `level_2: trung bình` trực thuộc `level_1: thời gian`.
    *   Đường đi xác định 3: `level_1: thời gian`, `level_2: trung bình`.

Kết hợp lại, có ba `Col Identifier` được hình thành.

### Col Identifier
level_1: thời gian
    level_2: hè
       level_3: trung bình
level_1: thời gian
    level_2: đông
       level_3: trung bình
level_1: thời gian
    level_2: trung bình

**Example 3:**

### Query
cho tôi biết cà phê chồn tại việt nam vào 2005

### Column Hierarchy
level_1: năm 2005
    level_2: hè
       level_3: tháng 1, tháng 3, trung bình
    level_2: đông
       level_3: tháng 11, tháng 12, trung bình
    level_2: trung bình
level_1: năm 2006
    level_2: hè
       level_3: tháng 1, tháng 3, trung bình

### Col Keywords
['2005']

### Thinking
Tôi cần tìm các `Col Identifier` cho query: "cho tôi biết cà phê đen tại việt nam vào 2005".
Dựa vào `Col Keywords` được cung cấp: ['2005'].

1.  **Phân tích `Col Keyword`: "2005"**
    *   Kiểm tra trong `Column Hierarchy`.
    *   Keyword "2005" khớp với `level_1: năm 2005`.
    *   Query không cung cấp thêm chi tiết nào để đi sâu hơn vào `level_2` (như "hè", "đông", hay "trung bình (của năm)") hoặc `level_3` (các tháng cụ thể) bên dưới "năm 2005".
    *   Do đó, `Col Identifier` nên dừng lại ở `level_1`, chỉ định "năm 2005" là cấp độ cột được nhắm mục tiêu. Điều này ngụ ý rằng toàn bộ dữ liệu dưới "năm 2005" có thể liên quan, nhưng định danh cột cụ thể là ở cấp độ năm.

Kết hợp lại, `Col Identifier` được hình thành.

### Col Identifier
level_1: năm 2005

*Now, process the following input:*
### Query
{query}

### Column Hierarchy
{col_structure}

### Col Keywords
{col_keywords}
"""

# Original single agent prompt (keeping for reference)
SINGLE_AGENT_PROMPT = """You are an **expert interpreter of queries for hierarchically structured tabular data**. Your core mission is to deconstruct natural language requests and map them with utmost precision to specific row and column selections. This requires mastery in navigating multi-level vertical headers (`Feature Rows` with `Row Hierarchy`) and multi-level horizontal headers (`Feature Cols` with `Column Hierarchy`) to guarantee the accuracy of retrieved data, irrespective of the data's specific domain (e.g., financial, product, operational).

**Instructions**

1.  **Deep Query Deconstruction:** Meticulously dissect the user's natural language. Isolate all explicit and implicit cues for row selection (tied to `Feature Rows`) and column selection (tied to `Feature Cols`).

2.  **Precision in Row Selection (`Row Choose`):**
    *   Iterate through `Feature Rows` hierarchically.
    *   For each `Feature Row`: Pinpoint user-specified values. If a level in the `Row Hierarchy` is unaddressed by the query (e.g., 'Loại' is skipped when 'Cà phê' and 'Nhập Khẩu' are given) or if an "all-encompassing" term is used for that level, assign `Undefined`. This signals inclusion of all valid sub-options.

3.  **Strategic Column Selection & Formatting (`Col Choose`):**
    *   Identify all targeted `Feature Cols` and their sub-columns. **Crucially, if a sub-column (e.g., "Hè") is named, its parent `Feature Col` (e.g., "Thời gian") MUST be inferred.**
    *   **Strict Output Formatting for `Col Choose`:**
        *   **Specific Sub-column Path:** `'Parent Feature Col - Full Path to Leaf Sub-column'` (e.g., `'Thời gian - Năm 2024 - Hè'`).
        *   **General Parent (with sub-columns):** If a `Feature Col` with sub-columns (like 'Thời gian') is requested generally (e.g., "thời gian thu hoạch"), output **ONLY the parent `Feature Col` name** (e.g., `'Thời gian'`).
        *   **Parent (no sub-columns):** If a `Feature Col` has no sub-columns (e.g., 'Đơn giá'), output its name directly (e.g., `'Đơn giá'`).
    *   Compile these into the `Col Choose` list.

4.  **Transparent Reasoning (`Thinking` - Non-Negotiable):**
    *   Articulate your entire decision path:
        *   **Query Essence:** What is the user's core need?
        *   **Row Logic:** How did query terms map to `Feature Row` values or `Undefined`? Justify every `Undefined`.
        *   **Column Logic:** How were `Feature Cols`/sub-columns identified? How were parents inferred? **Critically, demonstrate the precise application of the `Col Choose` formatting rules (Instruction 3.b).**

5.  **Graceful Handling of Unmatched Terms:**
    *   If the query mentions terms for rows or columns that are absent from the provided `Row Hierarchy` or `Column Hierarchy`, these terms are to be disregarded. Focus solely on mapping existing, valid elements.
    
**Input Format**
The system relies on the following precisely structured inputs:

### Query:
The user's verbatim natural language request, provided as a single string.
*Example:* `"Tôi muốn xem thời gian thu hoạch Hè của cà phê đen từ Việt Nam"`

### Feature Rows:
An ordered list of strings, meticulously defining the sequence of vertical row categorization, from the broadest category to the most granular.
*Example:* `['Cà phê', 'Loại', 'Nhập Khẩu']`

### Row Hierarchy:
**A valid JSON string** is mandatory. This string encapsulates a nested dictionary structure that maps out the complete hierarchical relationships for `Feature Rows`. Keys represent category values, leading to further nested dictionaries or, at the lowest level, a list of specific string identifiers.
*Example*:
{{
  "Cà phê thường": {{
    "Loại 1": ["Việt Nam", "Brazil", "Mỹ"],
    "Loại 2": ["Việt Nam", "Mỹ"]
  }},
  "Cà phê Đen": {{
    "Loại 2": ["Việt Nam"]
  }}
}}

### Feature Cols:
A list of strings, naming all top-level column headers available in the dataset.
*Example:* `['Thời gian', 'Thu nhập', 'Đơn giá', 'Ghi chú đặc biệt']`

### Column Hierarchy:
**A valid JSON string** is mandatory. This string details the sub-column structure for `Feature Cols`.
*   Only `Feature Cols` possessing sub-columns *need* to be included as top-level keys.
*   Sub-columns are represented as nested dictionaries; a leaf sub-column is denoted by an empty dictionary `{{}}`.
*   **Crucially, `Feature Cols` that lack sub-columns (e.g., 'Đơn giá', 'Ghi chú đặc biệt') can either be explicitly defined with an empty dictionary (e.g., `"Đơn giá": {{}}`) or, more commonly, be entirely omitted from this JSON string. The interpreter MUST correctly identify them as direct data columns in both scenarios.**
*Example*:
{{
  "Thời gian": {{
    "Hè": {{}},
    "Đông": {{}}
  }},
  "Thu nhập": {{
    "Thấp": {{}},
    "Trung Bình": {{}},
    "Cao": {{}}
  }},
  "Đơn giá": {{}}
}}

**Output Format**
You MUST strictly adhere to the following output format. Output ONLY the specified sections (`### Thinking:`, `### Row Choose`, `### Col Choose`) and their content as described. Do not include any other text, introductions, or summaries.

### Thinking:
You MUST strictly adhere to the following output format. Output ONLY the specified sections (`### Thinking:`, `### Row Choose`, `### Col Choose`) and their content as described. Do not include any other text, introductions, or summaries.

### Row Choose
A **JSON string** representing a dictionary.
*   Keys are the names of the `Feature Rows` (as provided in the `Feature Rows` input).
*   The value for each `Feature Row` key must be:
    *   A JSON array of strings, representing the specific class(es)/value(s) selected for that `Feature Row`.
    *   The string literal `"Undefined"` (e.g., `"Loại": "Undefined"`) if no specific value was selected for that `Feature Row`.

*Example for Row Choose:*
{{
  "Cà phê": ["Cà phê Đen"],
  "Loại": "Undefined",
  "Nhập Khẩu": ["Việt Nam"]
}}

{{
  "Cà phê": ["Cà phê thường"],
  "Loại": "Undefined",
  "Nhập Khẩu": "Undefined"
}}

### Col Choose
A **JSON string** representing a list of strings. Each string in the list represents a selected column and MUST adhere to the following formats, as determined by Instruction 3:
*   `'Parent Feature Col - Sub-column'` (e.g., `"Thời gian - Hè"`) if a specific sub-column is selected or inferred.
*   `'Parent Feature Col'` (e.g., `"Thời gian"`) if a `Feature Col` with sub-columns is requested generally.
*   `'Parent Feature Col'` (e.g., `"Đơn giá"`) if the `Feature Col` has NO sub-columns.

*Example for Col Choose:*

# Query: "thời gian Hè và thu nhập Trung Bình của cà phê"
["Thời gian - Hè", "Thu nhập - Trung Bình"]

["Thời gian", "Đơn giá"]

**Example 2**
### Query: "cho tôi biết điểm trung bình 2 kì môn lý của Trần Bích Thu"
### Feature Rows: ['Tên', 'Môn']
### Row Hierarchy: 
{{
  "Trần Bích Thu": ["Lý", "Toán", "Hóa", "Sinh"],
  "Nguyễn Nam": ["Lý", "Toán", "Hóa", "Sinh"]
}}

### Feature Cols: ['Chi Phí']
### Column Hierarchy: 
Thời gian:
{{
  "Chi Phí": {{
    "Cấp 1": ["Học kì 1", "Học kì 2", "Trung Bình"],
    "Cấp 2": ["Học kì 1", "Học kì 2", "Trung Bình"],
    "Tổng cộng": {{}}
  }}
}}

### Thinking:
**1. Query Analysis:**
The user's request is: "cho tôi biết điểm trung bình 2 kì môn lý của Trần Bích Thu".
This translates to: Show the average score over 2 semesters for the subject "Lý" (Physics) for the student "Trần Bích Thu". The term "điểm" (score/points) is contextually linked to "Chi Phí" as it's the only `Feature Col`. "Trung bình 2 kì" implies an average related to semesters.

- Row-related keywords: "Trần Bích Thu", "môn lý".
- Column-related keywords: "điểm trung bình 2 kì". This implies the sub-column "Trung Bình".

**2. Row Tracing (Adhering to Instruction 2):**
The `Feature Rows` are `['Tên', 'Môn']`.
- For 'Tên': The query specifies "Trần Bích Thu". This maps directly. So, `'Tên': ['Trần Bích Thu']`.
- For 'Môn': The query specifies "môn lý". This maps to 'Lý'. 'Lý' is a valid value for 'Môn' under 'Trần Bích Thu' in the `Row Hierarchy`. So, `'Môn': ['Lý']`.

The resulting `Row Choose` selection, before formatting as a JSON string, is:
`{{'Tên': ['Trần Bích Thu'], 'Môn': ['Lý']}}`

**3. Column Tracing & Formatting (Adhering to Instruction 3):**
The `Feature Col` is `['Chi Phí']`.
- The query asks for "điểm trung bình 2 kì". "Điểm" maps to the `Feature Col` 'Chi Phí'.
- The term "trung bình" directly points to the sub-column 'Trung Bình'.
- Looking at the `Column Hierarchy` for 'Chi Phí':
    - 'Chi Phí' has sub-categories 'Cấp 1' and 'Cấp 2'.
    - Both 'Cấp 1' and 'Cấp 2' contain 'Trung Bình' as a leaf sub-column.
- The query does not specify "Cấp 1" or "Cấp 2". It asks for "trung bình 2 kì", which implies the 'Trung Bình' that is associated with semester data. Since 'Trung Bình' appears under both 'Cấp 1' and 'Cấp 2' (which are the levels containing semester data), we should select 'Trung Bình' from both these contexts.
- As per **Instruction 3, Format 1 (Specific Sub-column)**, the format is `'Parent Feature Col - Sub-column'`. In a multi-level scenario, "Sub-column" refers to the full path to the leaf.
    - The path to 'Trung Bình' under 'Cấp 1' is 'Chi Phí - Cấp 1 - Trung Bình'.
    - The path to 'Trung Bình' under 'Cấp 2' is 'Chi Phí - Cấp 2 - Trung Bình'.

The resulting `Col Choose` selection, before formatting as a JSON string, is:
`['Chi Phí - Cấp 1 - Trung Bình', 'Chi Phí - Cấp 2 - Trung Bình']`

### Row Choose
{{
  "Tên": ["Trần Bích Thu"],
  "Môn": ["Lý"]
}}

### Col Choose
["Chi Phí - Cấp 1 - Trung Bình", "Chi Phí - Cấp 2 - Trung Bình"]

Now solve this query
### Query: 
{query}
### Feature Rows: 
{feature_rows}
### Row Hierarchy: 
{row_structure}
### Feature Cols: 
{feature_cols}  
### Column Hierarchy: 
{col_structure}

### Thinking: 
"""

# Prompt for feature analysis
FEATURE_ANALYSIS_PROMPT = """
Read the bewow content of an excel file, think step by step, identify if this is a matrix table or a flatten table.
Reponse in the following format:
### Thinking
### Is Matrix Table?
### Name of Feature Rows
### Name of Feature Cols

Instructions:
If the table is a matrix table, Feature Rows are the columns show hierarchical structure vertically, and usually the very first columns.
Feature rows should exclude the order column like ID, ...
Feature cols are the columns that are not feature rows, usually show hierarchical structure horizontally.

Example 1
### Content
Thành Phố,Phân loại,Quận,Phường,Giới tính,Giới tính
Unnamed: 0_level_1,Unnamed: 1_level_1,Unnamed: 2_level_1,Unnamed: 3_level_1,Nam,Nữ
### Thinking
The provided content shows two header rows. The first row has `Giới tính` listed twice, and the second row provides specific sub-categories `Nam` and `Nữ` under these `Giới tính` entries. This setup, where a single header spans multiple sub-headers, signifies a hierarchical column structure, which is characteristic of a matrix table. The columns `Thành Phố`, `Phân loại`, `Quận`, `Phường` serve as identifiers for the rows.
### Is Matrix Table?
Yes

### Name of Feature Rows
Thành Phố,Phân loại,Quận,Phường

### Name of Feature Cols
Giới tính

Example 2
### Content
Thứ tự,Thành Phố,Phân loại,Quận,Phường,Thu nhập,Thu nhập,Thu nhập
Unnamed: 0_level_1,Unnamed: 1_level_1,Unnamed: 2_level_1,Unnamed: 3_level_1,Unnamed: 4_level_1,Thấp,Trung Bình,Cao
### Thinking
The provided content displays two header rows. The first row has `Thu nhập` appearing three times, and the second row provides sub-categories `Thấp`, `Trung Bình`, `Cao` under these `Thu nhập` entries. This structure, where a single header spans multiple sub-headers, is a strong indicator of a hierarchical column structure, which is characteristic of a matrix table. The initial columns (`Thứ tự`, `Thành Phố`, `Phân loại`, `Quận`, `Phường`) define the rows' attributes. `Thứ tự` appears to be an order column, which should be excluded from feature rows as per instructions.
### Is Matrix Table?
Yes

### Name of Feature Rows
Thành Phố,Phân loại,Quận,Phường
### Name of Feature Cols
Thu nhập

Example 3
### Content
Cà phê,Loại,Nhập Khẩu ,Thời gian,Thời gian,Thu nhập,Thu nhập,Thu nhập
Unnamed: 0_level_1,Unnamed: 1_level_1,Unnamed: 2_level_1,Hè,Đông,Thấp,Trung Bình,Cao
### Thinking
The provided content shows two header rows. The first row contains `Thời gian` and `Thu nhập` which are repeated, and the second row provides specific sub-categories (`Hè`, `Đông` for `Thời gian`; `Thấp`, `Trung Bình`, `Cao` for `Thu nhập`). This pattern, where a top-level header spans multiple sub-headers, is characteristic of a hierarchical column structure, indicating a matrix table. The columns `Cà phê`, `Loại`, `Nhập Khẩu` at the beginning define the row attributes.
### Is Matrix Table?
Yes

### Name of Feature Rows
Cà phê,Loại,Nhập Khẩu 
### Name of Feature Cols
Thời gian,Thu nhập

Example 4
### Content
TT,Quan hệ,Tên
### Thinking
The provided content has only one header row: `TT,Quan hệ,Tên`. There are no subsequent rows that act as sub-headers, nor are there any indications of hierarchical relationships between the existing columns (e.g., a top-level header spanning multiple sub-headers or "Unnamed: X_level_Y" columns). This structure is characteristic of a flatten table.

### Is Matrix Table?
No

### Name of Feature Rows
None
### Name of Feature Cols
None

Now solve
### Content
{excel_content}
"""

SCHEMA_ANALYSIS_PROMPT = """
        Read the file, think step by step, identify the feature rows and feature cols in the Excel file
        Reponse in the following format:
        ### Thinking
        ### Feature Cols
        ### Feature Rows
        
        Requirements: 
        + This is an hierachical Excel file with complex header rows and columns.
        + Explecitly analyze the merge cells in Thinking (avoid mentioning in Feature Cols and Feature Rows)
        + Follow format like in Example
        + Rely on the `Name of Feature Rows` to avoid hallucination when analyzing the `Feature Rows` (happen when the `Feature Rows` are too complex with many levels)

        
        Example 1:
        ### Content
        'Thành Phố,Phân loại,Quận,Phường,Giới tính,Unnamed: 5\r\n,,,,Nam,Nữ\r\nHồ Chí Minh,,,,,\r\n,Lớn,,,,\r\n,,Quận 1,,,\r\n,,,Phường 1,,\r\n,,,Phường 2,,\r\n,Trung Bình,,,,\r\n,,Quận 2,,,\r\n,,,Phường 1,,\r\n,,Quận 4,,,\r\n,,,Phường 14,,\r\n,,,Phường 3,,\r\nHà Nội,,,,,\r\n,,Cầu Giấy,,,\r\n,,,Phường 1,,\r\n,,,Phường 2,,\r\n,,Đống Đa,,,\r\n,,,Phường 1,,\r\n'
        
        ### Name of Feature Rows
        "Feature: Thành Phố\n['Hồ Chí Minh' 'Hà Nội']\nFeature: Phân loại\n['Lớn' 'Trung Bình']\nFeature: Quận\n['Quận 1' 'Quận 2' 'Quận 4' 'Cầu Giấy' 'Đống Đa']\nFeature: Phường\n['Phường 1' 'Phường 2' 'Phường 14' 'Phường 3']\n"
        
        ### Thinking
        The provided data represents a hierarchical structure typical of Excel files with complex headers and row labels.
        The header spans two rows. The first row contains top-level categories like "Thành Phố", "Phân loại", "Quận", "Phường", and "Giới tính". The second row provides sub-categories for "Giới tính", namely "Nam" and "Nữ". In an actual Excel file, "Giới tính" in the first row would likely be a merged cell spanning the columns above "Nam" and "Nữ". The other headers in the first row ("Thành Phố", "Phân loại", "Quận", "Phường") would likely be merged downwards to the second row.
        The rows also exhibit a hierarchical structure. The first column contains the highest level of row labels ("Thành Phố"). Subsequent columns contain nested labels ("Phân loại", "Quận", "Phường"). In an actual Excel file, these row labels would typically be represented by merged cells spanning multiple rows corresponding to their sub-categories. For example, "Hồ Chí Minh" would be a merged cell spanning all rows related to Hồ Chí Minh, "Lớn" would be merged across rows related to the "Lớn" category within Hồ Chí Minh, and so on. The structure indicates that "Phường" is the lowest level of row hierarchy before the data values would appear.
        Feature columns have many levels of hierarchy, merged cells, and nested values. We need to effectively cover these in the output.
        
        ### Feature Cols
        - Row 1, 2 | Col 1: Thành Phố
        - Row 1, 2 | Col 2: Phân loại
        - Row 1, 2 | Col 3: Quận
        - Row 1, 2 | Col 4: Phường
        - Row 1 | Col 5, 6: Giới tính
            - Row 2 | Col 5: Nam
            - Row 2 | Col 6: Nữ

        ### Feature Rows
        - Row 3 | Col 1 (Thành Phố): Hồ Chí Minh
            - Row 4 | Col 2 (Phân loại): Lớn
                - Row 5 | Col 3 (Quận): Quận 1
                    - Row 6 | Col 4 (Phường): Phường 1
                    - Row 7 | Col 4 (Phường): Phường 2
            - Row 8 | Col 2 (Phân loại): Trung Bình
                - Row 9 | Col 3 (Quận): Quận 2
                    - Row 10 | Col 4 (Phường): Phường 1
                - Row 11 | Col 3 (Quận): Quận 4
                    - Row 12 | Col 4 (Phường): Phường 14
                    - Row 13 | Col 4 (Phường): Phường 3
        - Row 14 | Col 1 (Thành Phố): Hà Nội
            - None (Phân loại)
                - Row 15 | Col 3 (Quận): Cầu Giấy
                    - Row 16 | Col 4 (Phường): Phường 1
                    - Row 17 | Col 4 (Phường): Phường 2
                - Row 18 | Col 3 (Quận): Đống Đa
                    - Row 19 | Col 4 (Phường): Phường 1

        Example 2:
        ### Content
        'Thứ tự,Cà phê,Loại,Nhập Khẩu ,Thời gian,Unnamed: 5,Thu nhập,Unnamed: 7,Unnamed: 8\r\n,,,,Hè,Đông,Thấp,Trung Bình,Cao\r\n1,Cà phê thường,,,,,,,\r\n1.1,,Loại 1,,,,,,\r\n1.1.1,,,Việt Nam,,,,,\r\n1.1.2,,,Brazil,,,,,\r\n1.1.3,,,Mỹ,,,,,\r\n1.2,,Loại 2,,,,,,\r\n1.2.1,,,Việt Nam,,,,,\r\n1.2.2,,,Mỹ,,,,,\r\n2,Cà phê Đen,,,,,,,\r\n2.1,,Loại 2,,,,,,\r\n2.1.1,,,Việt Nam,,,,,\r\n'
        
        ### Name of Feature Rows
        "Feature: Cà phê\n['Cà phê thường' 'Cà phê Đen']\nFeature: Loại\n['Loại 1' 'Loại 2']\nFeature: Nhập Khẩu\n['Việt Nam' 'Brazil' 'Mỹ']\n"
        
        ### Thinking
        The provided data simulates an Excel file with a complex header spanning two rows and hierarchical row labels.
        The header in the first row includes "Thứ tự", "Cà phê", "Loại", "Nhập Khẩu", "Thời gian", "Unnamed: 5", "Thu nhập", "Unnamed: 7", and "Unnamed: 8". The second row provides sub-categories for "Thời gian" ("Hè", "Đông") and "Thu nhập" ("Thấp", "Trung Bình", "Cao"). In a real Excel file, "Thời gian" in the first row would likely be a merged cell spanning the columns above "Hè" and "Đông". Similarly, "Thu nhập" would be merged above "Thấp", "Trung Bình", and "Cao". The labels "Thứ tự", "Cà phê", "Loại", and "Nhập Khẩu" in the first row would likely be merged downwards to the second row.
        The rows below the header exhibit a clear hierarchy, indicated by the placement of values in different columns. Column 1 ("Thứ tự") appears to be an index. Column 2 ("Cà phê") contains the highest level of row labels ("Cà phê thường", "Cà phê Đen"). Column 3 ("Loại") contains the next level ("Loại 1", "Loại 2"), and Column 4 ("Nhập Khẩu") contains the lowest level ("Việt Nam", "Brazil", "Mỹ"). In an actual Excel file, these row labels would typically be represented by merged cells spanning multiple rows corresponding to their sub-categories. For example, "Cà phê thường" would be merged across all rows related to "Cà phê thường", "Loại 1" would be merged across rows related to "Loại 1" within "Cà phê thường", and so on. The structure indicates that "Nhập Khẩu" is the lowest level of row hierarchy before the data values would appear in the columns under "Thời gian" and "Thu nhập".

        ### Feature Cols
        - Row 1, 2 | Col 1: Thứ tự
        - Row 1, 2 | Col 2: Cà phê
        - Row 1, 2 | Col 3: Loại
        - Row 1, 2 | Col 4: Nhập Khẩu
        - Row 1 | Col 5, 6: Thời gian
            - Row 2 | Col 5: Hè
            - Row 2 | Col 6: Đông
        - Row 1 | Col 7, 8, 9: Thu nhập
            - Row 2 | Col 7: Thấp
            - Row 2 | Col 8: Trung Bình
            - Row 2 | Col 9: Cao

        ### Feature Rows
        - Row 3 | Col 2 (Cà phê): Cà phê thường
            - Row 4 | Col 3 (Loại): Loại 1
                - Row 5 | Col 4 (Nhập Khẩu): Việt Nam
                - Row 6 | Col 4 (Nhập Khẩu): Brazil
                - Row 7 | Col 4 (Nhập Khẩu): Mỹ
            - Row 8 | Col 3 (Loại): Loại 2
                - Row 9 | Col 4 (Nhập Khẩu): Việt Nam
                - Row 10 | Col 4 (Nhập Khẩu): Mỹ
        - Row 11 | Col 2 (Cà phê): Cà phê Đen
            - Row 12 | Col 3 (Loại): Loại 2
                - Row 13 | Col 4 (Nhập Khẩu): Việt Nam
        
        Now solve
        ### Content
        {excel_content}
        ### Name of Feature Rows
        {feature_name_content}
"""

# Prompt for file summary generation in multi-file system
FILE_SUMMARY_PROMPT = """You are an expert **Metadata Summarizer and Data Analyst**. Your primary task is to generate a concise yet comprehensive summary of a file based *only* on its provided structural metadata. This summary will be used to create a rich 'fingerprint' of the file, enabling effective semantic search and retrieval to determine if the file is relevant to a user's natural language question.

**Problem Description:**
You will be dealing with **matrix-like tables** that possess both **hierarchical rows and hierarchical columns**, typical of complex spreadsheets. Your analysis and summary must be based **solely** on the structural metadata provided (filename, feature names, row/column hierarchies). You will **not** have access to the actual data values within the cells. The goal is to capture the essence of what data the file likely contains and how it's structured, focusing on elements that are key for understanding its content and relevance.

**Output You Should Generate (A Structured Summary):**

Please generate a summary that clearly addresses the following aspects. Be concise and ensure all information is derived strictly from the provided metadata:

1.  **Overall Purpose/Domain:**
    *   (1-2 sentences) Based on the filename, feature names (both row and column), and the overall structure, what is the primary subject, domain, or general purpose of this file? (e.g., "Financial performance tracking," "Student academic records management," "Product inventory and sales analysis").

2.  **Time Aspect/Coverage:**
    *   (1 sentence, if applicable) If discernible from the filename (e.g., "Q3_2023"), feature names (e.g., "Year," "Month"), or the hierarchical structure (e.g., time periods nested in columns/rows), describe the likely time period, frequency, or temporal nature of the data. If not apparent, state: "Time aspect not explicitly defined in metadata."

3.  **Primary Row Entities & Breakdown:**
    *  (Focus this) What are the main items, entities, or categories being detailed down the rows? Describe how they are hierarchically broken down, referencing the `Feature Rows` and `Row Structure`. (e.g., "Rows detail individual 'Products', categorized by 'Product Line' and then by specific 'Model'." or "Rows appear to list 'Employees', potentially grouped by 'Department' and then 'Team'.").

4.  **Primary Column Metrics & Dimensions:**
    *  (Focus this) What key metrics, attributes, or dimensions are presented across the columns? Describe how they are hierarchically structured, referencing the `Feature Cols` and `Col Structure`. (e.g., "Columns represent financial 'Metrics' like 'Revenue' and 'Cost', broken down 'Quarterly' and then 'Monthly'." or "Columns show different 'Assessment Types', then specific 'Test Scores' and 'Grades'.").

5.  **Inferred Data Focus:**
    *   (1 sentence) Based on the intersection of the row and column structures, what kind of specific information or data points do the cells likely represent? (e.g., "The file likely contains numerical sales figures for specific products over defined time periods." or "This file probably tracks qualitative performance ratings for employees against various competencies.").

### **METADATA**
File: {filename}

Feature Rows: {feature_rows}
Feature Cols: {feature_cols}

Row Structure:
{row_structure}

Column Structure:
{col_structure}

Now, generate the summary:
### **SUMMARY**
"""

# Prompt for separating multi-file queries
QUERY_SEPARATOR_PROMPT = """You are an expert **Query Analyzer and Decomposer for Multi-File Environments**. Your primary mission is to take a user's natural language `User Query` and a list of `Available files and their summaries` and determine how the query maps to the available files.

If the entire query can be answered by a single file, you will associate the query with that file.
If different parts of the query relate to different files, or if the same part of a query could potentially be answered by multiple files (due to overlapping scope like different time periods for similar data), you must **decompose** the `User Query` into one or more `Separated Queries`. Each `Separated Query` should be a self-contained question targeted at a specific file that is most likely to contain the answer.

**Problem Description:**
Users often ask complex questions that might draw information from different datasets or perspectives. You are given summaries describing the content and structure of several files. Your task is to:
1.  **Analyze the User Query:** Understand the entities, metrics, timeframes, and intent expressed.
2.  **Match with File Summaries:** Compare the query's components against the `Overall Purpose/Domain`, `Time Aspect/Coverage`, `Primary Row Entities & Breakdown`, `Primary Column Metrics & Dimensions`, and `Inferred Data Focus` of each file summary.
3.  **Determine Relevance and Specificity:**
    *   If a query part clearly maps to only one file, target that file.
    *   If a query part could be answered by multiple files (e.g., "coffee prices" when you have "coffee prices 2023" and "coffee prices 2024" files, and the query doesn't specify a year), create separate queries for each potentially relevant file, *retaining the original intent of that query part*.
    *   If distinct, independent parts of a complex query map to different files, create separate, focused queries for each part, targeted at their respective files.
4.  **Formulate Separated Queries:** Each separated query should be a rephrasing or a direct segment of the original user query that makes sense in the context of the target file. It should be answerable by that specific file.

**Input You Will Receive:**

### FILE SUMMARY

### User Query

**Output You Should Generate:**

1.  **`Thinking`**:
    *   Briefly explain your overall understanding of the `User Query`.
    *   For each part of the `User Query` (or the whole query if it's simple), detail which file(s) you considered and why you selected (or didn't select) them based on their summaries.
    *   Explain your reasoning for separating the query if you did, or for keeping it whole. Highlight any ambiguities (like unspecified time) and how you handled them by potentially targeting multiple files.

2.  **`Separated Query`**:
    *   A list of "filename - query_segment" pairs.
    *   If the query is not separated, this will be a single entry.
    *   Each `query_segment` should be the natural language question intended for that specific `filename`.

**Examples:**
### FILE SUMMARY
Filename: example1.xlsx
Content:
1.  **Overall Purpose/Domain:** The file appears to contain data related to geographical areas (cities, districts, wards) broken down by gender. It likely concerns demographic information or statistics related to population distribution by gender across specific locations in Vietnam.
2.  **Time Aspect/Coverage:** Time aspect not explicitly defined in metadata.
3.  **Primary Row Entities & Breakdown:** Rows detail geographical locations, starting with 'Thành Phố' (City), then categorized by 'Phân loại' (Category), further broken down by 'Quận' (District), and finally by 'Phường' (Ward). 
4.  **Primary Column Metrics & Dimensions:** Columns represent 'Giới tính' (Gender), specifically detailing 'Nam' (Male) and 'Nữ' (Female).
5.  **Inferred Data Focus:** The file likely contains data points (e.g., counts, percentages, or other statistics) related to gender within specific geographical areas (wards, districts, cities).

Filename: example2.xlsx
Content:
1.  **Overall Purpose/Domain:** This file likely tracks international trade data for coffee, specifically focusing on export prices. The domain is related to commodity pricing and international trade statistics for coffee.        
2.  **Time Aspect/Coverage:** The data explicitly covers the year 2023.
3.  **Primary Row Entities & Breakdown:** Rows detail different types of 'Cà phê' (Coffee), categorized hierarchically by 'Loại' (Quality/Type), 'Xuất Khẩu' (Export Region), and finally by specific 'Nước' (Country).
4.  **Primary Column Metrics & Dimensions:** Columns represent 'Giá 2023' (Price 2023), specifically broken down into 'Lẻ' (Retail) and 'Sĩ' (Wholesale) prices.
5.  **Inferred Data Focus:** The cells likely contain specific 'Giá' (Price) values (Retail or Wholesale) for different types of 'Cà phê' (Coffee) exported to various 'Nước' (Countries) during 2023.

Filename: example3.xlsx
Content:
1.  **Overall Purpose/Domain:** Based on the features 'Cà phê', 'Loại', 'Nhập Khẩu ', 'Thời gian', and 'Thu nhập', the file likely concerns the analysis of coffee types and origins segmented by time periods and consumer income levels.
2.  **Time Aspect/Coverage:** The column structure includes 'Thời gian' broken down into 'Hè' and 'Đông', indicating a seasonal temporal coverage.
3.  **Primary Row Entities & Breakdown:** Rows detail various 'Cà phê' types, including 'Cà phê thường', 'Cà phê Chồn', 'Cà phê Đen', and 'Cà phê Đậm'. These are hierarchically broken down by 'Loại' (Type) and 'Nhập Khẩu ' (Origin), specifying origins like Việt Nam, Brazil, Ý, and Mỹ.
4.  **Primary Column Metrics & Dimensions:** Columns represent dimensions 'Thời gian' and 'Thu nhập'. 'Thời gian' is broken down into 'Hè' and 'Đông', while 'Thu nhập' is categorized into 'Thấp', 'Trung Bình', and 'Cao'.
5.  **Inferred Data Focus:** The file likely contains data points describing or quantifying aspects of specific coffee types/origins within defined seasonal periods and across different consumer income brackets.

Filename: example4.xlsx
Content:
1.  **Overall Purpose/Domain:** This file likely tracks international trade data for coffee, specifically focusing on export prices. The domain is related to commodity pricing and international trade statistics for coffee.        
2.  **Time Aspect/Coverage:** The data explicitly covers the year 2024.
3.  **Primary Row Entities & Breakdown:** Rows detail different types of 'Cà phê' (Coffee), categorized hierarchically by 'Loại' (Quality/Type), 'Xuất Khẩu' (Export Region), and finally by specific 'Nước' (Country).
4.  **Primary Column Metrics & Dimensions:** Columns represent 'Giá', specifically broken down into 'Lẻ' (Retail) and 'Sĩ' (Wholesale) prices.
5.  **Inferred Data Focus:** The cells likely contain specific 'Giá' (Price) values (Retail or Wholesale) for different types of 'Cà phê' (Coffee) exported to various 'Nước' (Countries) during 2024.

**Input Example 1:**
### User Query
"Cho tôi biết có bao nhiêu nữ trong thành phố hồ chí minh"

### Thinking
The user query asks for the number of females in Ho Chi Minh City. File 'example1.xlsx' summary indicates it contains demographic data by gender and location, including cities. This file is directly relevant to the entire query

### Seperated Query
example1.xlsx - Cho tôi biết có bao nhiêu nữ trong thành phố hồ chí minh



**Input Example 2:**
### User Query
"Cho tôi biết có bao nhiêu nữ và nam trong quận 1, và có bao nhiêu nam trong quận 2 phường 14"

### Thinking
The user query has two distinct parts: 1) number of females and males in District 1, and 2) number of males in Ward 14 of District 2. Both parts relate to demographic information by gender and specific administrative units (district, ward). File 'example1.xlsx' matches this data type. Since both parts can be answered by the same file but are distinct requests, they can remain as sub-parts of a query directed to example1.xlsx, or treated as conceptually separate but still targeting the same file. For clarity, I will separate them but assign both to example1.xlsx if the underlying system processes them sequentially for the same file. However, your output format asks for 'filename - query_segment'. If the intent is for the downstream agent to handle these sequentially if from the same file, the original phrasing is better. Let's assume the downstream agent is smart. The initial prompt implied 'example1.xlsx - Cho tôi biết có bao nhiêu nữ và nam trong thành phố hồ chí minh' and 'example2.xlsx - Cho tôi biết có bao nhiêu nam trong quận 2 phường 14'. This was a typo in the user's example output, it should be example1.xlsx for both if they come from the same conceptual source. I will assume it should be example1.xlsx for both based on the file content. The query targets demographic data at district and ward levels, which 'example1.xlsx' covers. The two parts are distinct information requests about different locations within the scope of 'example1.xlsx'.

### Seperated Query
example1.xlsx - Cho tôi biết có bao nhiêu nữ và nam trong quận 1
example1.xlsx - Cho tôi biết có bao nhiêu nam trong quận 2 phường 14

**Input Example 3:**
### User Query
"Cà phê đen có giá sĩ khoảng bao nhiêu"

### Thinking
The user asks for the wholesale price of black coffee. The query doesn't specify a year. File 'example2.xlsx' contains coffee export prices for 2023, including wholesale. File 'example4.xlsx' contains coffee export prices for 2024, also including wholesale. Both files are potentially relevant due to the unspecified time. Therefore, the query should be directed to both files to cover all possibilities.

### Separated Query
example2.xlsx - Cà phê đen có giá sĩ khoảng bao nhiêu
example4.xlsx - Cà phê đen có giá sĩ khoảng bao nhiêu

**Input Example 4:**
### User Query: 
"giá cà phê"

### Thinking
The user asks for 'coffee prices'. File 'example2.xlsx' explicitly covers 'Giá 2023' (Price 2023). File 'example4.xlsx' explicitly covers 'Giá' (Price) for 2024. File 'example3.xlsx' summary mentions coffee types, time, and income, but its 'Inferred Data Focus' does not suggest it contains direct price information, rather descriptive data. Therefore, 'example2.xlsx' and 'example4.xlsx' are the relevant files for 'giá cà phê'

###Separated Query
example2.xlsx - giá cà phê
example4.xlsx - giá cà phê


**Input Example 5:**
### User Query
"số lượng nam ở hà nội và đà nẵng, số lượng cà phê mỹ nhập khẩu từ brazil và cà phê loại tốt thường thu hút bao nhiêu người thu nhập cao"

### Thinking
The user query has three distinct parts: \n1. 'số lượng nam ở hà nội và đà nẵng': This concerns demographic data (number of males by city). File 'example1.xlsx' summary indicates it covers gender by location (cities).\n2. 'số lượng cà phê mỹ nhập khẩu từ brazil': This concerns coffee import origins. File 'example3.xlsx' summary indicates rows detail coffee by 'Nhập Khẩu ' (Origin), including Brazil and Mỹ (USA).\n3. 'cà phê loại tốt thường thu hút bao nhiêu người thu nhập cao': This links coffee type with consumer income. File 'example3.xlsx' summary indicates columns include 'Thu nhập' (Income) categories and rows detail coffee types. \nTherefore, the query needs to be split and targeted accordingly.

### Separated Query
example1.xlsx - số lượng nam ở hà nội và đà nẵng
example3.xlsx - số lượng cà phê mỹ nhập khẩu từ brazil
example3.xlsx - cà phê loại tốt thường thu hút bao nhiêu người thu nhập cao

Now, handle the below information and decompose the query:
### FILE SUMMARY
{files_context}

### User Query
"{query}"

### Thinking
""" 

ALIAS_HANDLE_PROMPT = """You are a specialized AI module within a financial Excel chatbot. Your primary function is to act as a **Query Normalizer**. Your task is to make user queries more meaningful by enriching them with information from an alias dictionary, without altering the original terms needed for data retrieval.

Your goal is to identify all known aliases within an `Initial Query` and append their corresponding full names or alternative identifiers in parentheses. **You must not replace the original alias.** This is a critical rule because the underlying Excel data often contains the alias itself (e.g., the column is named "CP", not "Chi phí").

You will be provided with two inputs:
1.  `Alias Dictionary`: A structured list of known aliases and their corresponding full or official terms.
2.  `Initial Query`: The raw, unprocessed question from the end-user.

Your sole output should be the `Enriched Query`.

**Rules for Enrichment:**

1.  **Augment, Don't Replace:** For every term in the `Initial Query` that is found as an alias in the `Alias Dictionary`, you must keep the original term and append its context in parentheses right after it.
2.  **Annotation Format:**
    *   For simple abbreviations, use the format: `Alias(Full Term)`. Example: `Chi phí(CP)`.
    *   For entities with multiple identifiers (like a nickname and a full name), use the format: `Alias(Identifier 1 - Identifier 2)`. Example: `Telemor(VTL - Viettel Timor Leste) or Viettel Timor Leste(VTL - Telemor)`.
3.  **No Match:** If a word in the query is not found in the Alias Dictionary, leave it completely unchanged.

**Example**
### Alias Dictionary:
Sheet: Từ viết tắt
TT: 1, Viết tắt: CP, Từ đầy đủ: Chi phí, Từ viết tắt khác: C.phí
TT: 2, Viết tắt: DA, Từ đầy đủ: Dự án, Từ viết tắt khác: D.án
TT: 3, Viết tắt: DT, Từ đầy đủ: Doanh thu

Sheet: Khách hàng
TT: 1, Viết tắt: Deeeplabs, Tên đầy đủ: Deeeplabs Pte Ltd
TT: 2, Viết tắt: SkyIQ, Tên đầy đủ: SKYIQ PTE.LTD
TT: 3, Viết tắt: VTL, Tên thường gọi: Telemor, Tên đầy đủ: Viettel Timor Leste

### Initial Query
CP cho sản xuất là bao nhiêu năm 2022?
### Enriched Query
CP(Chi phí) cho sản xuất là bao nhiêu năm 2022?

### Initial Query
CP cho DA tháng 1 và tháng 4 của Telemor là bao nhiêu?
### Enriched Query
CP(Chi phí) cho DA(Dự án) tháng 1 và tháng 4 của Telemor(VTL - Viettel Timor Leste) là bao nhiêu?

### Initial Query
tổng doanh thu của deeeplabs trong quý 1?
### Enriched Query
tổng doanh thu(DT) của deeeplabs(Deeeplabs Pte Ltd) trong quý 1?

### Initial Query
So sánh Doanh Thu của SkyIQ và Viettel Timor Leste.
### Enriched Query
So sánh Doanh Thu(DT) của SkyIQ(SKYIQ PTE.LTD) và Viettel Timor Leste(Telemor-VTL).

Now deal with the following case:
### Alias Dictionary:
{alias_dictionary}

### Initial Query
{user_query}
### Enriched Query
"""